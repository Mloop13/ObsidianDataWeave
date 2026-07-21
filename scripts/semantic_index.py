"""semantic_index.py — semantic (embedding) search over the Obsidian vault.

Complements memory_index.py (FTS5, lexical): this layer embeds every note with
a local Ollama model (bge-m3 by default) and stores the vectors in a sqlite-vec
virtual table, so search can match by MEANING rather than exact words. FTS5 stays
the source of truth for exact terms (project names, tags, ids like F41.2); this
adds the semantic half. `hybrid` fuses both via Reciprocal Rank Fusion.

The vector DB lives OUTSIDE the vault, next to the FTS DB but as its own file
(<slug>-<hash>-vec.db) so the loadable-extension connection is isolated:
    <db_dir>/<vault-slug>-<hash>-vec.db     db_dir default: ~/.cache/obsidian-dataweave

Prerequisite (one-time, manual): pull the embedding model —
    ollama pull bge-m3

Usage:
    python scripts/semantic_index.py build                 # full (re)index
    python scripts/semantic_index.py update                # incremental by mtime/size
    python scripts/semantic_index.py search "query" [--limit 10] [--json]
    python scripts/semantic_index.py hybrid "query" [--limit 10] [--json]
    python scripts/semantic_index.py status

Config (config.toml):
    [semantic]
    enabled = true
    model = "bge-m3"
    ollama_url = "http://localhost:11434"
    dimensions = 1024
    chunk_chars = 6000        # split point; ~2.5 chars/token (Cyrillic) → under 8192 ctx
    chunk_overlap = 200
    batch_size = 16
    db_dir = ""               # empty → same dir as the FTS index
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from scripts.config import load_config
    from scripts.memory_index import (
        _HEADING_RE,
        db_path_for_vault,
        parse_note,
        scan_files,
        vault_path_from,
    )
except ModuleNotFoundError:
    from config import load_config
    from memory_index import (
        _HEADING_RE,
        db_path_for_vault,
        parse_note,
        scan_files,
        vault_path_from,
    )

try:
    import sqlite_vec
except ImportError:  # pragma: no cover - reported at first use
    sqlite_vec = None


# ── config helpers ────────────────────────────────────────────────────────────


def semantic_config(config: dict) -> dict:
    """Normalize the [semantic] section with defaults."""
    raw = config.get("semantic", {}) or {}
    return {
        "enabled": bool(raw.get("enabled", True)),
        "model": str(raw.get("model", "bge-m3")).strip() or "bge-m3",
        "ollama_url": str(raw.get("ollama_url", "http://localhost:11434")).strip()
        or "http://localhost:11434",
        "dimensions": int(raw.get("dimensions", 1024)),
        "chunk_chars": int(raw.get("chunk_chars", 6000)),
        "chunk_overlap": int(raw.get("chunk_overlap", 200)),
        "batch_size": max(1, int(raw.get("batch_size", 16))),
        "db_dir": str(raw.get("db_dir", "") or ""),
    }


def vec_db_path(vault_path: Path, db_dir: str = "") -> Path:
    """Vector DB path — the FTS path with a -vec suffix (same slug + hash)."""
    base = db_path_for_vault(vault_path, db_dir)
    return base.with_name(f"{base.stem}-vec{base.suffix}")


# ── Ollama embeddings ─────────────────────────────────────────────────────────


def embed(texts: list[str], sem: dict) -> list[list[float]]:
    """POST /api/embed — batch; Ollama returns L2-normalized dense vectors."""
    url = sem["ollama_url"].rstrip("/") + "/api/embed"
    body = json.dumps({"model": sem["model"], "input": texts}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
    except (OSError, urllib.error.URLError) as exc:
        raise RuntimeError(
            f"Ollama unreachable at {sem['ollama_url']} — is `ollama serve` running "
            f"and is the model '{sem['model']}' pulled (`ollama pull {sem['model']}`)? ({exc})"
        ) from exc
    embs = data.get("embeddings")
    if not embs:
        raise RuntimeError(
            f"Ollama /api/embed returned no embeddings — is '{sem['model']}' an "
            f"embedding model? Try: ollama pull {sem['model']}"
        )
    return embs


# ── chunking ──────────────────────────────────────────────────────────────────


def _split_sections(body: str) -> list[tuple[str, str]]:
    """Split note body into (heading_text, section_text) pairs on markdown headings."""
    matches = list(_HEADING_RE.finditer(body))
    if not matches:
        return [("", body)]
    sections: list[tuple[str, str]] = []
    if matches[0].start() > 0 and body[: matches[0].start()].strip():
        sections.append(("", body[: matches[0].start()]))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections.append((m.group(1).strip(), body[m.end():end]))
    return sections


def _hard_split(text: str, chunk_chars: int, overlap: int) -> list[str]:
    if len(text) <= chunk_chars:
        return [text]
    step = max(1, chunk_chars - overlap)
    return [text[pos:pos + chunk_chars] for pos in range(0, len(text), step)]


def chunk_note(note: dict, chunk_chars: int, overlap: int) -> list[dict]:
    """One note → 1+ chunks. Small notes are a single chunk; large ones split by
    heading, with each chunk prefixed by the note title for context."""
    title = note["title"]
    header = f"{title}\n{note['headings']}".strip()
    combined = f"{header}\n{note['body']}".strip()
    if len(combined) <= chunk_chars:
        return [{"chunk_id": f"{note['path']}#0", "heading": "", "text": combined}]

    chunks: list[dict] = []
    ordinal = 0
    for heading_text, section in _split_sections(note["body"]):
        section = section.strip()
        if not section:
            continue
        prefix = f"{title}\n{heading_text}".strip() if heading_text else title
        prefixed = f"{prefix}\n{section}".strip()
        for piece in _hard_split(prefixed, chunk_chars, overlap):
            chunks.append(
                {"chunk_id": f"{note['path']}#{ordinal}", "heading": heading_text, "text": piece}
            )
            ordinal += 1
    if not chunks:
        chunks = [{"chunk_id": f"{note['path']}#0", "heading": "", "text": combined[:chunk_chars]}]
    return chunks


def _batched(seq: list, n: int):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# ── sqlite / schema ───────────────────────────────────────────────────────────


def open_vec_db(db_path: Path, dims: int) -> sqlite3.Connection:
    if sqlite_vec is None:
        raise RuntimeError("sqlite-vec is not installed — run: pip install sqlite-vec==0.1.9")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.enable_load_extension(True)
    except AttributeError as exc:  # pragma: no cover - Windows build without ext support
        conn.close()
        raise RuntimeError(
            "this Python's sqlite3 has no loadable-extension support "
            "(enable_load_extension missing)"
        ) from exc
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    ensure_vec_schema(conn, dims)
    return conn


def ensure_vec_schema(conn: sqlite3.Connection, dims: int) -> None:
    """Create tables if missing. A dimensions change forces a rebuild."""
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    row = conn.execute("SELECT value FROM meta WHERE key='dimensions'").fetchone()
    if row and row[0] != str(dims):
        print(
            f"INFO: embedding dimensions changed {row[0]} → {dims} — rebuilding vector index",
            file=sys.stderr,
        )
        conn.execute("DROP TABLE IF EXISTS notes_vec")
        conn.execute("DROP TABLE IF EXISTS vec_chunks")
        conn.execute("DROP TABLE IF EXISTS vec_files")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS vec_files ("
        " path TEXT PRIMARY KEY, mtime REAL NOT NULL, size INTEGER NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS vec_chunks ("
        " rowid INTEGER PRIMARY KEY, chunk_id TEXT UNIQUE NOT NULL,"
        " path TEXT NOT NULL, folder TEXT, title TEXT, heading TEXT)"
    )
    conn.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS notes_vec USING vec0(embedding float[{dims}])"
    )
    conn.execute(
        "INSERT INTO meta(key, value) VALUES('dimensions', ?)"
        " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(dims),),
    )
    conn.commit()


def _delete_path(conn: sqlite3.Connection, rel: str) -> None:
    rows = conn.execute("SELECT rowid FROM vec_chunks WHERE path = ?", (rel,)).fetchall()
    for (rid,) in rows:
        conn.execute("DELETE FROM notes_vec WHERE rowid = ?", (rid,))
    conn.execute("DELETE FROM vec_chunks WHERE path = ?", (rel,))


# ── index operations ──────────────────────────────────────────────────────────


def update_index(config: dict, *, full: bool = False, quiet: bool = False) -> dict:
    """Build (full=True) or incrementally refresh the vector index. Returns stats."""
    sem = semantic_config(config)
    vault_path = vault_path_from(config)
    if not vault_path.is_dir():
        raise ValueError(f"vault_path does not exist: {vault_path}")

    db_path = vec_db_path(vault_path, sem["db_dir"])
    conn = open_vec_db(db_path, sem["dimensions"])
    try:
        if full:
            conn.execute("DELETE FROM notes_vec")
            conn.execute("DELETE FROM vec_chunks")
            conn.execute("DELETE FROM vec_files")
            conn.commit()

        on_disk = scan_files(vault_path)
        in_db = {
            path: (mtime, size)
            for path, mtime, size in conn.execute("SELECT path, mtime, size FROM vec_files")
        }
        changed = [
            p for p, sig in on_disk.items()
            if p not in in_db or (abs(in_db[p][0] - sig[0]) > 1e-6 or in_db[p][1] != sig[1])
        ]
        removed = [p for p in in_db if p not in on_disk]

        for rel in removed:
            _delete_path(conn, rel)
            conn.execute("DELETE FROM vec_files WHERE path = ?", (rel,))

        total_chunks = 0
        for rel in changed:
            _delete_path(conn, rel)
            note = parse_note(vault_path / rel, vault_path)
            chunks = chunk_note(note, sem["chunk_chars"], sem["chunk_overlap"])
            for batch in _batched(chunks, sem["batch_size"]):
                vectors = embed([c["text"] for c in batch], sem)
                if vectors and len(vectors[0]) != sem["dimensions"]:
                    raise RuntimeError(
                        f"model '{sem['model']}' returned {len(vectors[0])}-dim vectors "
                        f"but [semantic].dimensions={sem['dimensions']} — fix the config"
                    )
                for c, vec in zip(batch, vectors):
                    cur = conn.execute(
                        "INSERT INTO vec_chunks(chunk_id, path, folder, title, heading)"
                        " VALUES (?, ?, ?, ?, ?)",
                        (c["chunk_id"], note["path"], note["folder"], note["title"], c["heading"]),
                    )
                    conn.execute(
                        "INSERT INTO notes_vec(rowid, embedding) VALUES (?, ?)",
                        (cur.lastrowid, sqlite_vec.serialize_float32(vec)),
                    )
                    total_chunks += 1
            mtime, size = on_disk[rel]
            conn.execute(
                "INSERT INTO vec_files(path, mtime, size) VALUES (?, ?, ?)"
                " ON CONFLICT(path) DO UPDATE SET mtime=excluded.mtime, size=excluded.size",
                (rel, mtime, size),
            )
            conn.commit()

        conn.execute(
            "INSERT INTO meta(key, value) VALUES('last_update', ?)"
            " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(int(time.time())),),
        )
        conn.commit()
    finally:
        conn.close()

    stats = {
        "db": str(db_path),
        "indexed": len(changed),
        "removed": len(removed),
        "chunks": total_chunks,
        "total": len(on_disk),
    }
    if not quiet:
        mode = "rebuilt" if full else "updated"
        print(
            f"Vector index {mode}: {stats['indexed']} notes indexed "
            f"({stats['chunks']} chunks), {stats['removed']} removed, "
            f"{stats['total']} notes total\nDB: {db_path}"
        )
    return stats


# ── search ────────────────────────────────────────────────────────────────────


def search(config: dict, query: str, *, limit: int = 10) -> list[dict]:
    """Semantic KNN search. Returns best chunk per note, nearest first."""
    sem = semantic_config(config)
    vault_path = vault_path_from(config)
    db_path = vec_db_path(vault_path, sem["db_dir"])
    if not db_path.exists():
        raise RuntimeError(
            f"vector index not built yet ({db_path}) — run: "
            f"python scripts/semantic_index.py build"
        )
    qvec = embed([query], sem)[0]
    conn = open_vec_db(db_path, sem["dimensions"])
    try:
        rows = conn.execute(
            "SELECT c.path, c.folder, c.title, c.heading, v.distance"
            " FROM notes_vec v JOIN vec_chunks c ON c.rowid = v.rowid"
            " WHERE v.embedding MATCH ? AND k = ?"
            " ORDER BY v.distance",
            (sqlite_vec.serialize_float32(qvec), max(1, limit) * 4),
        ).fetchall()
    finally:
        conn.close()

    best: dict[str, dict] = {}
    for path, folder, title, heading, dist in rows:
        if path not in best or dist < best[path]["distance"]:
            best[path] = {
                "path": path,
                "folder": folder,
                "title": title,
                "heading": heading,
                "distance": round(dist, 4),
            }
    return sorted(best.values(), key=lambda r: r["distance"])[:limit]


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, key in enumerate(ranking, start=1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
    return scores


def hybrid_search(config: dict, query: str, *, limit: int = 10) -> list[dict]:
    """Fuse FTS5 (lexical) and semantic rankings via Reciprocal Rank Fusion."""
    try:
        try:
            from scripts.memory_index import search as fts_search
        except ModuleNotFoundError:
            from memory_index import search as fts_search
        fts = fts_search(config, query, limit=limit * 2)
    except (RuntimeError, ValueError):
        fts = []  # FTS index missing/failed — degrade to pure semantic
    sem = search(config, query, limit=limit * 2)

    fused = reciprocal_rank_fusion([[r["path"] for r in fts], [r["path"] for r in sem]])
    by_path = {r["path"]: r for r in sem}
    by_path.update({r["path"]: r for r in fts})  # prefer FTS row (carries snippet)
    ranked = sorted(fused.items(), key=lambda kv: -kv[1])[:limit]
    return [{"path": p, "rrf": round(s, 4), **by_path[p]} for p, s in ranked]


# ── status ────────────────────────────────────────────────────────────────────


def status(config: dict) -> dict:
    sem = semantic_config(config)
    vault_path = vault_path_from(config)
    db_path = vec_db_path(vault_path, sem["db_dir"])
    if not db_path.exists():
        return {"db": str(db_path), "exists": False, "model": sem["model"]}
    conn = open_vec_db(db_path, sem["dimensions"])
    try:
        files = conn.execute("SELECT count(*) FROM vec_files").fetchone()[0]
        chunks = conn.execute("SELECT count(*) FROM vec_chunks").fetchone()[0]
        meta = dict(conn.execute("SELECT key, value FROM meta"))
    finally:
        conn.close()
    return {
        "db": str(db_path),
        "exists": True,
        "model": sem["model"],
        "notes": files,
        "chunks": chunks,
        "dimensions": meta.get("dimensions", "?"),
        "size_kb": db_path.stat().st_size // 1024,
        "last_update": meta.get("last_update", "never"),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────


def _print_results(results: list[dict]) -> None:
    if not results:
        print("no matches")
        return
    for r in results:
        score = r.get("rrf", r.get("distance"))
        head = f" — {r['heading']}" if r.get("heading") else ""
        print(f"{score:>8}  {r['path']}{head}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Semantic (embedding) index over the vault")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="full rebuild of the vector index")
    sub.add_parser("update", help="incremental refresh (mtime/size)")
    sub.add_parser("status", help="show vector index status")
    for name in ("search", "hybrid"):
        p = sub.add_parser(name, help=f"{name} search")
        p.add_argument("query")
        p.add_argument("--limit", type=int, default=10)
        p.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    config = load_config(strict=True)
    sem = semantic_config(config)
    if not sem["enabled"] and args.cmd not in ("status",):
        print("semantic search is disabled ([semantic].enabled = false)", file=sys.stderr)
        return 2

    try:
        if args.cmd == "build":
            update_index(config, full=True)
        elif args.cmd == "update":
            update_index(config)
        elif args.cmd == "status":
            print(json.dumps(status(config), ensure_ascii=False, indent=2))
        elif args.cmd == "search":
            results = search(config, args.query, limit=args.limit)
            print(json.dumps(results, ensure_ascii=False, indent=2)) if args.as_json else _print_results(results)
        elif args.cmd == "hybrid":
            results = hybrid_search(config, args.query, limit=args.limit)
            print(json.dumps(results, ensure_ascii=False, indent=2)) if args.as_json else _print_results(results)
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except sqlite3.OperationalError as exc:
        print(f"ERROR: vector query failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
