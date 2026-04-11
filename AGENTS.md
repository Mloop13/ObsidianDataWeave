# ObsidianDataWeave Agent Contract

## Purpose
This repository converts source `.docx` documents and existing Obsidian notes into Zettelkasten-style notes with MOC structure.

Agents should treat this file as the canonical integration contract for both Claude Code and Codex.

## Supported Workflows
1. Process a source document into atomic notes and MOC:
   `python3 scripts/process.py "Document.docx"`
   Safe automation form:
   `python3 scripts/process.py "Document.docx" --non-interactive --on-conflict skip`
2. Process a curated NotebookLM notebook into atomic notes and MOC:
   `python3 scripts/process_notebook.py "<notebook_id>"`
   Safe automation form:
   `python3 scripts/process_notebook.py "<notebook_id>" --non-interactive --on-conflict skip`
   Optional inputs: `--include-sources`, `--include-mindmap`, `--profile <name>`.
3. Process an existing personal note in the vault:
   `python3 scripts/process_note.py "Note Title"`
   Safe automation form:
   `python3 scripts/process_note.py "Note Title" --mode atomize --non-interactive --on-conflict skip`
4. Process a contacts/networking note into individual contact cards:
   `python3 scripts/process_contacts.py "Contacts Note"`
   Safe automation form:
   `python3 scripts/process_contacts.py "Contacts Note" --non-interactive --on-conflict skip`
5. Generate markdown files from an existing atom plan JSON:
   `python3 scripts/generate_notes.py /path/to/atom-plan.json`
6. Copy staged markdown files into the vault:
   `python3 scripts/vault_writer.py --staging /path/to/staging --atom-plan /path/to/atom-plan.json`
7. Find duplicate note candidates or run semantic dedup:
   `python3 scripts/dedup_vault.py --dry-run`
8. Run environment checks before operating on the vault:
   `python3 scripts/doctor.py`
9. Run deep research directly into a NotebookLM notebook (bypasses the upstream
   CLI retry duplication bug, see "Why research_notebook.py exists" below):
   `python3 scripts/research_notebook.py run "<notebook_id>" "<query>"`
   Safe automation form:
   `python3 scripts/research_notebook.py run "<notebook_id>" "<query>" --non-interactive`
   Dry-run preview of what would be imported:
   `python3 scripts/research_notebook.py run "<notebook_id>" "<query>" --dry-run`
10. Clean up duplicate/error sources in an existing NotebookLM notebook:
    `python3 scripts/research_notebook.py dedupe "<notebook_id>" --dry-run`
    Safe automation form:
    `python3 scripts/research_notebook.py dedupe "<notebook_id>" --include-error --non-interactive`

## Workflow Mapping
Common user intent -> command:

- "process/import this .docx" -> `python3 scripts/process.py "<file>.docx"`
- "process/import this .docx without prompts" -> `python3 scripts/process.py "<file>.docx" --non-interactive --on-conflict skip`
- "process notebook" / "обработай ноутбук" / "pull from NotebookLM" -> `python3 scripts/process_notebook.py "<notebook_id>"`
- "process notebook with sources" -> `python3 scripts/process_notebook.py "<notebook_id>" --include-sources`
- "process notebook without prompts" -> `python3 scripts/process_notebook.py "<notebook_id>" --non-interactive --on-conflict skip`
- "fetch notebook notes only" (no atomization) -> `python3 scripts/fetch_notebook.py "<notebook_id>"`
- "process/enrich/atomize this note" -> `python3 scripts/process_note.py "<note title or path>"`
- "process contacts" / "обработай контакты" -> `python3 scripts/process_contacts.py "<note title or path>"`
- "atomize this note without prompts" -> `python3 scripts/process_note.py "<note title or path>" --mode atomize --non-interactive --on-conflict skip`
- "show duplicate candidates" -> `python3 scripts/dedup_vault.py --dry-run --skip-claude`
- "run full dedup review" -> `python3 scripts/dedup_vault.py`
- "write staged notes without prompts" -> `python3 scripts/vault_writer.py --staging "<dir>" --atom-plan "<plan.json>" --non-interactive --on-conflict skip`
- "run dedup without prompts" -> `python3 scripts/dedup_vault.py --non-interactive --decision skip`
- "render markdown from atom plan" -> `python3 scripts/generate_notes.py "<plan.json>"`
- "check setup/prereqs" -> `python3 scripts/doctor.py`
- "run deep research in notebook" / "запусти ресерч в ноутбук" / "deep research into notebook" -> `python3 scripts/research_notebook.py run "<notebook_id>" "<query>"`
- "dry-run research import" -> `python3 scripts/research_notebook.py run "<notebook_id>" "<query>" --dry-run`
- "dedupe notebook sources" / "почисти дубли источников в ноутбуке" -> `python3 scripts/research_notebook.py dedupe "<notebook_id>" --dry-run`
- "clean up broken research import" -> `python3 scripts/research_notebook.py dedupe "<notebook_id>" --include-error --non-interactive`

## Important Constraints
- `scripts/vault_writer.py` is the only script allowed to write generated note files into `vault_path`.
- `scripts/process.py`, `scripts/process_note.py`, and `scripts/process_notebook.py` rely on the local `claude` CLI (or `codex`) for the semantic rewrite step.
- `scripts/fetch_notebook.py` and `scripts/process_notebook.py` require `notebooklm-py` to be installed and an authenticated NotebookLM session (`notebooklm login`).
- Agents must prefer repo-local files over global home-directory files.
- `config.toml` is local, machine-specific state. Never overwrite it unless explicitly asked.
- `processed.json`, `dedup_reviewed.json`, staging artifacts, and vault contents are runtime state. Do not delete them unless explicitly asked.

## Required Local Files
- `config.toml`: local runtime configuration
- `tags.yaml`: canonical taxonomy
- `rules/atomization.md`: note-splitting rules
- `rules/taxonomy.md`: tags, MOC, wikilink rules
- `rules/personal_notes.md`: personal note rules
- `SKILL.md`: Claude-facing adapter over this contract
- `SKILL_PERSONAL.md`: prompt header for personal note processing
- `SKILL_CONTACTS.md`: prompt header for contact note processing
- `rules/contacts.md`: contact note rules

## CLI Contracts
- `scripts/process.py`
  - Input: `.docx` filename or atom plan JSON with `--from-plan`
  - Safe automation flags for final vault writes: `--non-interactive --on-conflict skip|overwrite`
  - Output: summary to stdout, diagnostics to stderr
- `scripts/process_note.py`
  - Input: note title, filename, or absolute path
  - Safe automation flags for atomize writes: `--non-interactive --on-conflict skip|overwrite`
  - Output: writes updated/generated notes into the vault
- `scripts/process_contacts.py`
  - Input: note title, filename, or absolute path (containing contacts)
  - Safe automation flags: `--non-interactive --on-conflict skip|overwrite`
  - Output: writes individual contact notes + MOC to vault
- `scripts/generate_notes.py`
  - Input: atom plan JSON
  - Output: staging directory path to stdout
- `scripts/vault_writer.py`
  - Input: `--staging`, optional `--atom-plan`
  - Safe automation flags: `--non-interactive --on-conflict skip|overwrite`
  - Output: summary to stdout and stderr
- `scripts/dedup_vault.py`
  - Input: vault notes from configured vault path
  - Safe automation flags: `--non-interactive --decision merge|keep|skip`
  - Output: diagnostics to stderr, updates vault on confirmed merges
- `scripts/research_notebook.py`
  - Input: `run <notebook_id> "<query>"` or `dedupe <notebook_id>`
  - `run` flags: `--mode fast|deep` (default deep), `--source web|drive`, `--max-sources N`, `--poll-interval N`, `--poll-timeout N`, `--profile NAME`, `--dry-run`, `--non-interactive`
  - `dedupe` flags: `--key auto|url|title`, `--include-error`, `--dry-run`, `--non-interactive`, `--profile NAME`
  - Behavior: drives `notebooklm-py` Python API directly, so IMPORT_RESEARCH is a one-shot call with no retry-on-timeout duplication. Dedupe subcommand groups existing sources by URL (or title) and deletes everything except the first occurrence per group, optionally also removing sources in error state.
  - Output: progress + summary on stderr; dry-run plan or empty-plan JSON on stdout

## Recommended Agent Behavior
- Start with `python3 scripts/doctor.py` if setup is uncertain.
- Use `--dry-run` modes before destructive or high-impact operations.
- Prefer `--non-interactive` plus an explicit conflict/decision policy when running from an agent.
- Quote filenames with spaces or Cyrillic characters.
- When a task is unclear, inspect the relevant script help first.

## NotebookLM Auth Handling
- NotebookLM "login state" is a file on disk (`~/.notebooklm/storage_state.json` + `~/.notebooklm/browser_profile/`). Every run re-reads it; there is no in-memory session the agent needs to refresh. Once the user has logged in on this machine, subsequent runs go through without any browser prompt.
- `fetch_notebook.py` and `process_notebook.py` perform a pre-flight auth check (`check_auth_or_exit()`) before opening any network clients.
- Both scripts exit with code `2` and emit `NOTEBOOKLM_AUTH_REQUIRED` on stderr when the user is not authenticated OR when `notebooklm-py` is missing entirely.
- The canonical flow uses a **project venv** (`.venv/`) — system pip is blocked by PEP 668 on Arch/Manjaro/Debian. `scripts/notebooklm_setup.py` auto-detects venv and skips `--user` when inside one.
- Agent contract when `NOTEBOOKLM_AUTH_REQUIRED` is observed:
  1. Tell the user that dependencies will be installed automatically, but the actual browser login has to happen in a separate terminal window (because `notebooklm login` needs a real TTY to read the `ENTER` keypress; running it from Claude Code's shell aborts with `Aborted!`).
  2. Ensure a venv exists (create with `python3 -m venv .venv` if missing) and run:
     `.venv/bin/python scripts/notebooklm_setup.py --skip-login`
     This installs `notebooklm-py[browser]` and Playwright Chromium into the venv. Safe to run repeatedly and safe to run from a non-TTY shell (login is skipped).
  3. Ask the user to open a separate terminal window in the repo directory and run:
     `.venv/bin/notebooklm login`
     Sign in to Google in the Chromium window, wait for the NotebookLM homepage, return to that terminal and press ENTER. The session persists at `~/.notebooklm/storage_state.json`.
  4. When the user confirms, retry the original `process_notebook.py <notebook_id>` command. The preflight should now pass silently.
  5. Do not manually chain `pip install`, `playwright install`, and `notebooklm login` — always go through the setup script for steps 1–2.
  6. If the setup script exits non-zero, relay its stderr to the user and stop — do not attempt ad-hoc recovery. Exit code `3` specifically means "stdin is not a TTY and login was requested" — always invoke with `--skip-login` from the agent's shell.

- `scripts/notebooklm_setup.py`
  - Input: none (flags: `--skip-login`, `--reinstall`)
  - Behavior: auto-detects venv vs system Python; uses `pip --user` only outside a venv; refuses to launch `notebooklm login` on a non-TTY stdin
  - Output: diagnostics to stderr; exit 0 on success, 1 on install/login failure, 2 on missing auth file after login, 3 on missing TTY when login is requested
  - Use this as the canonical entrypoint whenever `NOTEBOOKLM_AUTH_REQUIRED` is observed

- `scripts/fetch_notebook.py`
  - Input: NotebookLM `notebook_id`
  - Optional flags: `--include-sources`, `--include-mindmap`, `--profile <name>`, `-o <path>`
  - Output: parsed-JSON path to stdout (compatible with `atomize.py`); diagnostics to stderr
  - Prereq: `notebooklm-py` installed + `notebooklm login` completed

- `scripts/process_notebook.py`
  - Input: NotebookLM `notebook_id`
  - Optional flags: `--include-sources`, `--include-mindmap`, `--profile <name>`
  - Safe automation flags: `--non-interactive --on-conflict skip|overwrite`
  - Output: summary to stdout; runs the full fetch -> atomize -> generate -> write pipeline
  - Prereq: same as `fetch_notebook.py`, plus `claude`/`codex` CLI for the rewrite step

## Why research_notebook.py exists

The upstream `notebooklm-py` CLI command
`notebooklm source add-research "<query>" --mode deep --import-all`
wraps `client.research.import_sources()` in an exponential-backoff retry loop that kicks in on `RPCTimeoutError`. Each retry re-imports the full source list without deduping against what's already in the notebook, so a single IMPORT_RESEARCH RPC that times out N times leaves N× duplicates. We hit this concretely: 78 research sources, 4 retries, 392 imported sources instead of ~78. Tracked upstream as `teng-lin/notebooklm-py` issue #241 (open).

Upstream explicitly documents the escape hatch in `src/notebooklm/cli/helpers.py::import_with_retry`:

> This is intentionally CLI-only policy. Library consumers calling `client.research.import_sources()` directly still get one-shot behavior.

`scripts/research_notebook.py` takes that escape hatch. It drives the research flow through the `notebooklm-py` Python API, so IMPORT_RESEARCH is a single call with no silent retry — duplication literally cannot happen through this code path. The `dedupe` subcommand is the cleanup for notebooks already poisoned by the CLI bug.

**Agents must prefer `research_notebook.py run` over `notebooklm source add-research --import-all`** until the upstream bug is fixed.

## Validation Commands
- `pytest -q`
- `python3 scripts/process.py --help`
- `python3 scripts/process_note.py --help`
- `python3 scripts/process_notebook.py --help`
- `python3 scripts/fetch_notebook.py --help`
- `python3 scripts/dedup_vault.py --help`
- `python3 scripts/doctor.py`
