---
description: "Claude Code adapter for ObsidianDataWeave workflows"
trigger_phrases:
  - process note
  - enrich note
  - atomize note
  - docx import
  - обработай заметку
  - обработай документ
  - импортируй документ
  - zettelkasten правила
  - process contacts
  - обработай контакты
  - networking contacts
  - process notebook
  - обработай ноутбук
  - pull from notebooklm
  - забери из notebooklm
  - импортируй ноутбук
  - notebooklm to obsidian
  - notebooklm login
  - залогинься в notebooklm
  - авторизуйся в notebooklm
  - run research in notebook
  - запусти ресерч в ноутбуке
  - deep research into notebook
  - дип ресерч в ноутбук
  - dedupe notebook sources
  - почисти дубли в ноутбуке
  - clean up duplicate sources
  - fix broken research import
---

# ObsidianDataWeave Claude Adapter

Use the repo-local `AGENTS.md` as the primary contract.

## Intent Mapping

- Process a source `.docx` document:
  `python3 scripts/process.py "Document.docx"`
- Process a curated NotebookLM notebook:
  `python3 scripts/process_notebook.py "<notebook_id>"`
  Add `--include-sources` to pull full source texts, `--include-mindmap` for the mindmap.
- Fetch NotebookLM notes without atomizing (raw parsed JSON):
  `python3 scripts/fetch_notebook.py "<notebook_id>"`
- Process a personal note:
  `python3 scripts/process_note.py "Note Title"`
- Process a contacts/networking note:
  `python3 scripts/process_contacts.py "Contacts Note"`
- Run duplicate review:
  `python3 scripts/dedup_vault.py --dry-run`
- Run deep research directly into an existing NotebookLM notebook (safe — bypasses upstream CLI retry duplication bug):
  `python3 scripts/research_notebook.py run "<notebook_id>" "<query>"`
- Clean up duplicate / error-state sources in a NotebookLM notebook:
  `python3 scripts/research_notebook.py dedupe "<notebook_id>" --dry-run`
- Validate setup:
  `python3 scripts/doctor.py`

## NotebookLM Workflow (direct control)
- `scripts/process_notebook.py` drives the full pipeline: `fetch_notebook.py` → `atomize.py` → `generate_notes.py` → `vault_writer.py`.
- `scripts/fetch_notebook.py` emits a path to parsed JSON that is compatible with the existing atomize/generate chain.
- Both scripts require `notebooklm-py` (`pip install notebooklm-py[browser]` then `notebooklm login`).
- Pass `--profile <name>` when the user mentions a non-default NotebookLM profile.
- Stick to the local `claude` CLI rewrite path in `process_notebook.py` — do not recurse into a new Claude invocation from inside the Claude session; the script already handles that.

## How "being logged in" actually works
- NotebookLM auth is **file-based**: the session lives at `~/.notebooklm/storage_state.json` and a Playwright browser profile at `~/.notebooklm/browser_profile/`.
- Once the user runs `notebooklm login` and signs in once, that file persists. Every subsequent run just reads it — no browser popup, no OAuth dance, no token refresh that the agent needs to handle.
- There is nothing in memory to "log in again" per session. If `storage_state.json` exists and is valid, the scripts go through silently.

## Handling NotebookLM Auth Errors
If `fetch_notebook.py` or `process_notebook.py` exits with `NOTEBOOKLM_AUTH_REQUIRED`:
1. Say that the preflight failed because `notebooklm-py` is missing or the session file is not there yet, and that login requires a real terminal window (not Claude's shell).
2. If `.venv/` does not exist, create it: `python3 -m venv .venv`
3. Run the setup script (installs deps, skips login intentionally because we are not on a TTY):
   `.venv/bin/python scripts/notebooklm_setup.py --skip-login`
4. Ask the user to open a fresh terminal in the repo directory and run `.venv/bin/notebooklm login`, sign in to Google in the Chromium window, come back to that terminal, and press ENTER.
5. When the user confirms, retry the original `process_notebook.py` / `fetch_notebook.py` command.
6. If setup exits non-zero, relay stderr verbatim and stop — do not try to pip-install things manually. Exit code `3` specifically means Claude's shell isn't a TTY, which is normal — just always pass `--skip-login` when invoking the setup script from inside Claude.

## Deep research via research_notebook.py (do not use the upstream CLI directly)

**Do not invoke `notebooklm source add-research "<query>" --mode deep --import-all`.**
The upstream CLI wraps `client.research.import_sources()` in a retry loop that
re-imports the full source list on every RPC timeout, without deduping against
the notebook's existing sources. Result: notebooks end up with N× duplicates
after N retries. Concretely we hit 392 sources instead of ~78 in one run.
Bug is tracked upstream as `teng-lin/notebooklm-py` issue #241.

Use `scripts/research_notebook.py run` instead. It calls the `notebooklm-py`
Python library directly, which upstream explicitly documents as
*one-shot behavior*, so IMPORT_RESEARCH is a single call and cannot duplicate:

```
python3 scripts/research_notebook.py run "<notebook_id>" "<query>"
```

Options: `--mode fast|deep` (default deep), `--source web|drive`,
`--max-sources N`, `--poll-interval`/`--poll-timeout`, `--profile <name>`,
`--dry-run` (plan only).

If a notebook was already poisoned by the broken CLI, clean it up:

```
python3 scripts/research_notebook.py dedupe "<notebook_id>" --dry-run
python3 scripts/research_notebook.py dedupe "<notebook_id>" --include-error --non-interactive
```

`dedupe` groups sources by URL (with title as fallback), keeps the first
occurrence of each group, and can optionally delete sources stuck in error
state. Always preview with `--dry-run` before running destructive deletes.

## Rules
- Prefer the repository's `AGENTS.md`, `rules/*.md`, and script help output over global instructions.
- Treat this file as a Claude-specific entrypoint, not as the canonical source of project behavior.
- Reuse the same local commands that Codex would run from the repository.
