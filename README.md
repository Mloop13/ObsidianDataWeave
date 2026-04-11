<div align="center">

# ObsidianDataWeave

**Research docs from Google Drive → structured atomic notes in Obsidian. One command, fully automated.**

**Исследовательские документы из Google Drive → структурированные атомарные заметки в Obsidian. Одна команда, полная автоматизация.**

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)
![Codex](https://img.shields.io/badge/Codex-AGENTS.md-green)

---

[**На русском**](#русский) | [**In English**](#english)

</div>

---

<a id="русский"></a>

## На русском

### Что это

ObsidianDataWeave — навык для [Claude Code](https://docs.anthropic.com/en/docs/claude-code) и [Codex](https://github.com/openai/codex), который скачивает `.docx` файлы из Google Drive, разбивает их на атомарные заметки по методологии MOC + Zettelkasten, присваивает теги и вики-ссылки, и записывает результат напрямую в ваш vault Obsidian. Также умеет обогащать и атомизировать существующие заметки в vault.

### Установка

```bash
git clone https://github.com/howdeploy/ObsidianDataWeave.git
cd ObsidianDataWeave
bash install.sh --vault-path "/путь/к/вашему/vault"
```

Или скопируйте этот промпт в Claude Code или Codex — он сделает всё сам:

```
Клонируй https://github.com/howdeploy/ObsidianDataWeave.git и запусти bash install.sh --vault-path "/путь/к/vault" в клонированной директории.
```

Установщик:
- Проверит Python 3.10+ и установит зависимости (`python-docx`, `pyyaml`)
- Создаст `config.toml` с путём к vault
- Зарегистрирует навык глобально в `~/.claude/skills/obsidian-dataweave/`
- Добавит блок в `~/.claude/CLAUDE.md`

После установки навык работает **из любой директории**.

#### Режимы установки

| Режим | Флаг | Что делает |
|-------|------|-----------|
| **claude** (по умолчанию) | `--mode claude` | Зависимости + config + глобальный навык в `~/.claude/` |
| **codex** | `--mode codex` | Зависимости + config + проверка `AGENTS.md` |
| **local** | `--mode local` | Только зависимости + config |

### Как использовать

После установки просто говорите Claude Code что нужно:

```
Обработай документ "Архитектура второго мозга.docx"
```

```
Обработай заметку "Мои мысли о продуктивности"
```

```
Скачай мои файлы с Google Drive и разбей на атомарные заметки
```

```
Проверь настройку — запусти doctor
```

Ещё примеры:

| Что сказать | Что произойдёт |
|-------------|---------------|
| `process МойДокумент.docx` | Полный цикл: скачать → разобрать → атомизировать → записать в vault |
| `process МойДокумент.docx --non-interactive --on-conflict skip` | То же, без вопросов (для автоматизации) |
| `обработай заметку "Название"` | Enrich или atomize существующей заметки |
| `process_note "Note" --mode atomize` | Принудительная атомизация заметки |
| `dedup --dry-run` | Показать дубликаты без изменений |

### NotebookLM как источник

Помимо `.docx` из Google Drive, ObsidianDataWeave умеет брать заметки из notebook'ов NotebookLM через `scripts/process_notebook.py <notebook_id>`. Атомайзер видит все заметки нотбука как один корпус и строит вики-ссылки поверх нескольких источников одновременно.

#### Первый вход в аккаунт

Сессия Google сохраняется в `~/.notebooklm/storage_state.json` и переиспользуется — вход одноразовый.

1. Создайте venv и установите зависимости:

```bash
python3 -m venv .venv
.venv/bin/python scripts/notebooklm_setup.py --skip-login
```

Скрипт поставит `notebooklm-py[browser]` и браузер Playwright Chromium в активный venv. Флаг `--skip-login` отделяет установку от интерактивного входа — логин делаем вручную в следующем шаге, потому что `notebooklm login` требует настоящий TTY.

> **Arch / Manjaro / Debian:** системный `pip` заблокирован PEP 668, так что venv обязателен. Скрипт автоматически определяет venv и больше не передаёт `--user`. Без venv (на обычный системный Python) установка упадёт с подсказкой создать venv.

2. **Откройте отдельное окно терминала** и выполните:

```bash
cd /путь/к/ObsidianDataWeave
.venv/bin/notebooklm login
```

> Не запускайте это через префикс `!` в Claude Code или Codex — у такой сессии нет интерактивного stdin, и `notebooklm login` упадёт с `Aborted!` в момент ожидания `ENTER`.

3. В открывшемся окне Chromium войдите в Google-аккаунт и дождитесь загрузки главной NotebookLM.

4. Вернитесь в терминал и нажмите **ENTER** — `storage_state.json` сохранится.

Проверка: файл `~/.notebooklm/storage_state.json` должен появиться.

#### Использование

```bash
.venv/bin/python scripts/process_notebook.py <notebook_id>
```

`<notebook_id>` — последний сегмент URL вашего нотбука: `https://notebooklm.google.com/notebook/<notebook_id>`. Флаги `--include-sources` и `--include-mindmap` добавляют индексированные источники и mind map. Для нескольких аккаунтов используйте `--profile <имя>`.

#### Безопасный запуск deep research

Не пользуйтесь `notebooklm source add-research "<query>" --mode deep --import-all` напрямую: в upstream-CLI есть баг ([teng-lin/notebooklm-py#241](https://github.com/teng-lin/notebooklm-py/issues/241)) — при таймауте IMPORT_RESEARCH CLI повторяет импорт полного списка источников без дедупликации, и нотбук получает N× дубликатов. У нас ловилось в боевом режиме: 78 источников → 392 после четырёх ретраев.

Вместо CLI используйте `scripts/research_notebook.py`, который ходит в `notebooklm-py` как библиотека (upstream гарантирует one-shot поведение для библиотечных вызовов):

```bash
.venv/bin/python scripts/research_notebook.py run "<notebook_id>" "<query>"
.venv/bin/python scripts/research_notebook.py run "<notebook_id>" "<query>" --dry-run
```

Опции: `--mode fast|deep` (по умолчанию deep), `--source web|drive`, `--max-sources N`, `--poll-interval` / `--poll-timeout`, `--profile <имя>`, `--dry-run`.

Если нотбук уже был отравлен сломанным CLI, почистите его:

```bash
.venv/bin/python scripts/research_notebook.py dedupe "<notebook_id>" --dry-run
.venv/bin/python scripts/research_notebook.py dedupe "<notebook_id>" --include-error --non-interactive
```

`dedupe` группирует источники по URL (с fallback на title), оставляет первую копию каждой группы и по желанию удаляет источники в error-state. Всегда сначала `--dry-run`.

### Что происходит под капотом

```
Google Drive → fetch → parse → atomize (Claude) → generate → write → Obsidian vault
```

1. **Fetch** — `rclone` скачивает `.docx` из Google Drive во временную директорию
2. **Parse** — извлекает заголовки, абзацы и таблицы в JSON
3. **Atomize** — Claude читает JSON и генерирует план атомизации (заголовки, теги, вики-ссылки)
4. **Generate** — создаёт `.md` файлы с YAML-фронтматером
5. **Write** — перемещает готовые заметки в папки vault, дедупликация по `(source_doc, title)`

Для личных заметок процесс проще:

```
Vault note → detect mode → rewrite (Claude) → write back
```

- **Enrich** — короткая заметка → добавляет теги, вики-ссылки, расширяет текст (1 → 1)
- **Atomize** — длинная заметка → разбивает на атомарные заметки + MOC (1 → N)

### MOC + Zettelkasten

**MOC (Map of Content)** — навигационный хаб: собирает ссылки на все атомарные заметки из документа. Один MOC на документ.

**Атомарные заметки** — одна идея, 150–600 слов, самодостаточные. Связаны `[[вики-ссылками]]` друг с другом и с MOC.

**Smart Connections** находит семантически близкие заметки через локальные эмбеддинги — второй слой связей поверх ручных.

### Шаблоны

Директория `templates/` содержит стартовую структуру vault:

- `Notes/Atomic Note Example.md` — пример атомарной заметки
- `MOCs/Topic Map - MOC.md` — пример MOC

### Конфигурация

Файл `config.toml` (создаётся при установке, не коммитится):

```toml
[vault]
vault_path = "/путь/к/вашему/vault"          # обязательно, абсолютный путь
notes_folder = "Research & Insights"          # куда пишутся атомарные заметки
moc_folder = "Guides & Overviews"             # куда пишутся MOC
source_folder = "Sources"                      # ссылки на исходники

[rclone]
remote = "gdrive:"                             # имя rclone remote
staging_dir = "/tmp/dw/staging"               # временная директория
```

### Требования

- Python 3.10+ (рекомендуется 3.11+)
- [rclone](https://rclone.org/) с доступом к Google Drive (для импорта `.docx`)
- [Claude Code](https://claude.ai/code) или [Codex](https://github.com/openai/codex)
- `vault_path` в `config.toml` — абсолютный путь к вашему Obsidian vault

**Обязательные плагины Obsidian:**

- [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) — векторный семантический поиск по vault (локальные эмбеддинги, без API ключа). Рекомендуемая модель: `TaylorAI/bge-micro-v2` — готовый конфиг в `templates/.smart-env/`
- [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) — HTTP-интерфейс для чтения/записи vault. Нужен для MCP Obsidian
- [MCP Obsidian](https://github.com/MarkusPfundstein/mcp-obsidian) — MCP-сервер, соединяющий Claude Code с Obsidian через Local REST API. Зависит от Local REST API

**Смежные проекты:**

- [NotebookLM++](https://github.com/howdeploy/notebooklmplusplus) — Chrome-расширение для [NotebookLM](https://notebooklm.google.com), которое добавляет массовый импорт: веб-страницы, YouTube-видео, Shorts, плейлисты, каналы целиком, комментарии и PDF-снимки страниц. Если вы используете NotebookLM как второй мозг наряду с Obsidian — это расширение закрывает ту же задачу на стороне Google: быстро собрать источники в нотбук для AI-анализа

### Структура проекта

```
ObsidianDataWeave/
├── scripts/
│   ├── process.py            # Главный пайплайн (.docx → vault)
│   ├── process_note.py       # Обработка личных заметок (enrich/atomize)
│   ├── fetch_docx.sh         # Скачивание с Google Drive
│   ├── parse_docx.py         # .docx → JSON
│   ├── atomize.py            # JSON → план атомизации (через Claude)
│   ├── generate_notes.py     # План → .md файлы
│   ├── vault_writer.py       # Staging → vault (с дедупликацией)
│   ├── dedup_vault.py        # Поиск и мерж дубликатов
│   ├── scan_vault.py         # Сканирование существующих заметок
│   ├── rewrite_backend.py    # Бэкенд семантической перезаписи (Claude CLI)
│   ├── config.py             # Загрузчик конфигурации
│   └── doctor.py             # Проверка окружения
├── rules/
│   ├── atomization.md        # Правила атомизации
│   ├── taxonomy.md           # Правила таксономии тегов
│   └── personal_notes.md     # Правила обработки личных заметок
├── templates/                # Стартовая структура vault
├── tests/                    # Регрессионные тесты
├── docs/                     # Документация для агентов
├── AGENTS.md                 # Контракт агента (Claude Code + Codex)
├── SKILL.md                  # Claude-адаптер
├── SKILL_PERSONAL.md         # Промпт для обработки личных заметок
├── tags.yaml                 # Каноничный список тегов
├── config.example.toml       # Шаблон конфигурации
├── install.sh                # Установщик с глобальной регистрацией
└── requirements.txt          # Python-зависимости
```

### Лицензия

MIT — см. [LICENSE](LICENSE).

---

<a id="english"></a>

## In English

### What is this

ObsidianDataWeave is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Codex](https://github.com/openai/codex) skill that fetches `.docx` files from Google Drive, splits them into atomic notes using the MOC + Zettelkasten methodology, assigns tags and wikilinks, and writes the results directly to your Obsidian vault. It can also enrich and atomize existing notes in your vault.

### Install

```bash
git clone https://github.com/howdeploy/ObsidianDataWeave.git
cd ObsidianDataWeave
bash install.sh --vault-path "/path/to/your/obsidian/vault"
```

Or copy this prompt into Claude Code or Codex — it handles everything:

```
Clone https://github.com/howdeploy/ObsidianDataWeave.git and run bash install.sh --vault-path "/path/to/vault" in the cloned directory.
```

The installer will:
- Check Python 3.10+ and install dependencies (`python-docx`, `pyyaml`)
- Create `config.toml` with your vault path
- Register the skill globally in `~/.claude/skills/obsidian-dataweave/`
- Add a helper block to `~/.claude/CLAUDE.md`

After installation the skill works **from any directory**.

#### Install modes

| Mode | Flag | What it does |
|------|------|-------------|
| **claude** (default) | `--mode claude` | Deps + config + global skill in `~/.claude/` |
| **codex** | `--mode codex` | Deps + config + verify `AGENTS.md` |
| **local** | `--mode local` | Deps + config only |

### How to use

After installation, just tell Claude Code what you need:

```
Process the document "Second Brain Architecture.docx"
```

```
Process note "My thoughts on productivity"
```

```
Download my files from Google Drive and split into atomic notes
```

```
Check setup — run doctor
```

More examples:

| What to say | What happens |
|-------------|-------------|
| `process MyDocument.docx` | Full cycle: download → parse → atomize → write to vault |
| `process MyDocument.docx --non-interactive --on-conflict skip` | Same, no prompts (for automation) |
| `process note "Title"` | Enrich or atomize an existing note |
| `process_note "Note" --mode atomize` | Force atomization of a note |
| `dedup --dry-run` | Show duplicates without changes |

### NotebookLM as a source

In addition to `.docx` from Google Drive, ObsidianDataWeave can pull curated notes from NotebookLM notebooks via `scripts/process_notebook.py <notebook_id>`. The atomizer sees every note in the notebook as one batch and can build wikilinks across multiple sources at once.

#### First-time login

The Google session is stored in `~/.notebooklm/storage_state.json` and reused — you only log in once.

1. Create a venv and install the dependencies:

```bash
python3 -m venv .venv
.venv/bin/python scripts/notebooklm_setup.py --skip-login
```

The script installs `notebooklm-py[browser]` and the Playwright Chromium browser into the active venv. The `--skip-login` flag separates installation from the interactive login — we handle the login manually in the next step because `notebooklm login` needs a real TTY.

> **Arch / Manjaro / Debian:** the system `pip` is locked down by PEP 668, so a venv is required. The script auto-detects venv and no longer passes `--user`. Running it against the system Python without a venv will fail fast with guidance to create one.

2. **Open a separate terminal window** and run:

```bash
cd /path/to/ObsidianDataWeave
.venv/bin/notebooklm login
```

> Do not run this via the `!` prefix inside Claude Code or Codex — such a session has no interactive stdin, and `notebooklm login` will abort with `Aborted!` the moment it asks you to press `ENTER`.

3. Sign in to Google in the Chromium window that opens and wait until the NotebookLM homepage loads.

4. Return to the terminal and press **ENTER** — `storage_state.json` is saved.

Verify: the file `~/.notebooklm/storage_state.json` should now exist.

#### Usage

```bash
.venv/bin/python scripts/process_notebook.py <notebook_id>
```

`<notebook_id>` is the last URL segment of your notebook: `https://notebooklm.google.com/notebook/<notebook_id>`. Flags `--include-sources` and `--include-mindmap` add indexed source fulltext and mind maps. For multi-account setups use `--profile <name>`.

#### Running deep research safely

Do not use `notebooklm source add-research "<query>" --mode deep --import-all` directly — there is a known upstream bug ([teng-lin/notebooklm-py#241](https://github.com/teng-lin/notebooklm-py/issues/241)): on an IMPORT_RESEARCH timeout the CLI retries with the full source list without deduping, leaving N× duplicates. We hit it in anger: 78 research sources → 392 after four retries.

Use `scripts/research_notebook.py` instead. It drives `notebooklm-py` as a Python library, which upstream explicitly documents as one-shot:

```bash
.venv/bin/python scripts/research_notebook.py run "<notebook_id>" "<query>"
.venv/bin/python scripts/research_notebook.py run "<notebook_id>" "<query>" --dry-run
```

Options: `--mode fast|deep` (default `deep`), `--source web|drive`, `--max-sources N`, `--poll-interval` / `--poll-timeout`, `--profile <name>`, `--dry-run`.

If a notebook was already poisoned by the broken CLI, clean it up:

```bash
.venv/bin/python scripts/research_notebook.py dedupe "<notebook_id>" --dry-run
.venv/bin/python scripts/research_notebook.py dedupe "<notebook_id>" --include-error --non-interactive
```

`dedupe` groups sources by URL (with title as fallback), keeps the first occurrence per group, and can also delete sources stuck in error state. Always start with `--dry-run`.

### How it works

```
Google Drive → fetch → parse → atomize (Claude) → generate → write → Obsidian vault
```

1. **Fetch** — `rclone` downloads `.docx` from Google Drive to a staging directory
2. **Parse** — extracts headings, paragraphs, and tables into JSON
3. **Atomize** — Claude reads JSON and generates an atom plan (titles, tags, wikilinks)
4. **Generate** — creates `.md` files with YAML frontmatter
5. **Write** — moves notes to vault folders, deduplicates by `(source_doc, title)`

For personal notes the process is simpler:

```
Vault note → detect mode → rewrite (Claude) → write back
```

- **Enrich** — short note → adds tags, wikilinks, expands text (1 → 1)
- **Atomize** — long note → splits into atomic notes + MOC (1 → N)

### MOC + Zettelkasten

**MOC (Map of Content)** — a navigation hub collecting links to all atomic notes from a document. One MOC per document.

**Atomic notes** — one idea, 150–600 words, fully self-contained. Connected via `[[wikilinks]]` to each other and to the MOC.

**Smart Connections** finds semantically similar notes via local embeddings — a second layer of connections on top of manual links.

### Templates

The `templates/` directory contains a starter vault structure:

- `Notes/Atomic Note Example.md` — example atomic note
- `MOCs/Topic Map - MOC.md` — example MOC

### Configuration

`config.toml` (created during installation, never committed):

```toml
[vault]
vault_path = "/path/to/your/obsidian/vault"   # required, absolute path
notes_folder = "Research & Insights"           # atomic notes destination
moc_folder = "Guides & Overviews"              # MOC files destination
source_folder = "Sources"                       # source document references

[rclone]
remote = "gdrive:"                              # rclone remote name
staging_dir = "/tmp/dw/staging"                # temporary staging area
```

### Requirements

- Python 3.10+ (3.11+ recommended)
- [rclone](https://rclone.org/) configured with Google Drive access (for `.docx` import)
- [Claude Code](https://claude.ai/code) or [Codex](https://github.com/openai/codex)
- `vault_path` in `config.toml` — absolute path to your Obsidian vault

**Required Obsidian plugins:**

- [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) — vector semantic search across your vault (local embeddings, no API key). Recommended model: `TaylorAI/bge-micro-v2` — ready-made config in `templates/.smart-env/`
- [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) — HTTP interface for reading/writing vault contents. Required by MCP Obsidian
- [MCP Obsidian](https://github.com/MarkusPfundstein/mcp-obsidian) — MCP server connecting Claude Code to Obsidian via Local REST API. Depends on Local REST API

**Related projects:**

- [NotebookLM++](https://github.com/howdeploy/notebooklmplusplus) — Chrome extension for [NotebookLM](https://notebooklm.google.com) that adds bulk import: web pages, YouTube videos, Shorts, playlists, entire channels, comments, and PDF page snapshots. If you use NotebookLM as a second brain alongside Obsidian, this extension covers the same workflow on the Google side: quickly gather sources into a notebook for AI analysis

### Project structure

```
ObsidianDataWeave/
├── scripts/
│   ├── process.py            # Main pipeline (.docx → vault)
│   ├── process_note.py       # Personal note processing (enrich/atomize)
│   ├── fetch_docx.sh         # Download from Google Drive
│   ├── parse_docx.py         # .docx → JSON
│   ├── atomize.py            # JSON → atom plan (via Claude)
│   ├── generate_notes.py     # Plan → .md files
│   ├── vault_writer.py       # Staging → vault (with deduplication)
│   ├── dedup_vault.py        # Find and merge duplicate notes
│   ├── scan_vault.py         # Scan existing vault notes
│   ├── rewrite_backend.py    # Semantic rewrite backend (Claude CLI)
│   ├── config.py             # Configuration loader
│   └── doctor.py             # Environment check
├── rules/
│   ├── atomization.md        # Atomization rules
│   ├── taxonomy.md           # Tag taxonomy rules
│   └── personal_notes.md     # Personal note processing rules
├── templates/                # Starter vault structure
├── tests/                    # Regression tests
├── docs/                     # Agent-facing documentation
├── AGENTS.md                 # Agent contract (Claude Code + Codex)
├── SKILL.md                  # Claude adapter
├── SKILL_PERSONAL.md         # Prompt header for personal note processing
├── tags.yaml                 # Canonical tag list
├── config.example.toml       # Configuration template
├── install.sh                # Installer with global skill registration
└── requirements.txt          # Python dependencies
```

### License

MIT — see [LICENSE](LICENSE).
