<div align="center">

# ObsidianDataWeave

**Full NotebookLM control from Claude Code / Codex, .docx import with Zettelkasten atomization, and a compiled LLM Wiki layer that grows by explicit merge, plus a zero-dependency FTS5 full-text memory over the whole vault — all programmatic, all into your Obsidian vault.**

**Полное управление NotebookLM из Claude Code / Codex, импорт .docx с Zettelkasten-атомизацией и скомпилированный LLM Wiki-слой, который растёт через явный merge, плюс FTS5-полнотекстовая память по всему vault без зависимостей — всё программно, всё в ваш Obsidian vault.**

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)
![Codex](https://img.shields.io/badge/Codex-AGENTS.md-green)
![NotebookLM](https://img.shields.io/badge/NotebookLM-API%20Control-orange)
![LLM Wiki](https://img.shields.io/badge/LLM%20Wiki-Compiled%20Knowledge-teal)
![FTS5 Memory](https://img.shields.io/badge/FTS5-Vault%20Memory-9cf)

---

[**На русском**](#русский) | [**In English**](#english)

</div>

---

<a id="русский"></a>

## На русском

### Что это

ObsidianDataWeave превращает Claude Code и Codex в полноценный пульт управления NotebookLM и вашим Obsidian vault. Запускайте deep research, управляйте источниками, вытаскивайте заметки из нотбуков — всё через одну команду на естественном языке. Параллельно импортирует `.docx` из Google Drive и атомизирует их в Zettelkasten-заметки с MOC, тегами и вики-ссылками. И поверх всего — изолированный **LLM Wiki**-слой: скомпилированная база знаний по Карпати, которая накапливается через явный merge, а не пересчитывается на каждый запрос. Поиск по всему этому — **память FTS5**: локальный полнотекстовый индекс всего vault (заметки, вики, NotebookLM-импорт), обновляется сам после каждой записи.

#### Что можно делать с NotebookLM

| Возможность | Команда |
|---|---|
| Запустить deep/fast research в нотбук | `research_notebook.py run <id> "<запрос>"` |
| Безопасный one-shot импорт источников (без дубликатов) | то же, обходит [баг upstream CLI](https://github.com/teng-lin/notebooklm-py/issues/241) |
| Почистить дубли и ошибочные источники | `research_notebook.py dedupe <id>` |
| Извлечь все заметки → атомарные заметки в Obsidian | `process_notebook.py <id>` |
| Извлечь заметки + исходники + mind map | `process_notebook.py <id> --include-sources --include-mindmap` |
| Скачать заметки без атомизации | `fetch_notebook.py <id>` |

Вся работа с NotebookLM идёт через Python API (`notebooklm-py`), а не через CLI — один вызов, без retry-дупликации. Авторизация — файл на диске, без интерактивного браузера при каждом запуске.

#### Что ещё умеет

- Импорт `.docx` из Google Drive → атомарные заметки + MOC в vault
- Обогащение и атомизация существующих заметок
- Обработка контактов из сетевых заметок → персональные карточки + Networking MOC
- Дедупликация vault по семантическому сходству
- Автоматическая таксономия тегов и вики-ссылки между заметками
- **LLM Wiki** — изолированный compiled-knowledge слой (project / corpus режимы, RU/EN-шаблоны, guard-сохранение `[[вики-ссылок]]` при merge, см. [секцию ниже](#llm-wiki))
- **Память FTS5** — полнотекстовый поиск по всему vault на stdlib SQLite: `memory_index.py search "запрос" --json`, bm25-ранжирование со сниппетами, инкрементальный индекс вне vault

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

### Обновление

```bash
cd ObsidianDataWeave && git pull && bash install.sh
```

Установщик идемпотентен: симлинки навыка обновятся сами, `migrate.py` допишет
новые секции конфига (например `[memory]`) и развернёт FTS5-индекс памяти.
`config.toml` и vault не перезатираются.

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
| `обработай контакты "Контакты"` | Разбить заметку с контактами → персональные карточки + Networking MOC |
| `process_note "Note" --mode atomize` | Принудительная атомизация заметки |
| `dedup --dry-run` | Показать дубликаты без изменений |
| `запусти ресерч в ноутбуке "<id>" "<запрос>"` | Deep research в NotebookLM через API |
| `почисти дубли в ноутбуке "<id>"` | Дедупликация источников в нотбуке |
| `создай вики "<slug>"` / `init wiki "<slug>"` | Скелет новой LLM Wiki-space (project/corpus, RU/EN) |
| `залей в вики "<slug>" <путь>` | Положить статью / папку в `raw/<kind>/` |
| `собери вики "<slug>"` | Скомпилировать сырьё в страницы (с guard на `[[wikilinks]]`) |
| `проверь вики "<slug>"` | Lint: frontmatter, ссылки, изоляция контура |
| `найди в заметках "<запрос>"` | FTS5-поиск по всему vault (заметки + вики), bm25 + сниппеты |
| `перестрой индекс памяти` | Полная пересборка FTS5-индекса (`memory_index.py build`) |

### NotebookLM: полное программное управление

ObsidianDataWeave даёт Claude Code / Codex полный программный контроль над NotebookLM. Вместо ручной работы в веб-интерфейсе — вы говорите агенту что нужно, и он запускает ресерч, управляет источниками, вытаскивает заметки и атомизирует их в Obsidian. Весь API-слой работает через `notebooklm-py` как библиотеку (не CLI), что гарантирует one-shot поведение без retry-дупликации.

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

**NotebookLM → Obsidian:**
```
NotebookLM API → fetch notes/sources/mindmaps → atomize (Claude) → generate → write → Obsidian vault
```

**Deep Research → NotebookLM:**
```
research_notebook.py → notebooklm-py API (one-shot) → poll → import sources → dedupe
```

**Google Drive → Obsidian:**
```
Google Drive → rclone fetch → parse .docx → atomize (Claude) → generate → write → Obsidian vault
```

**Личные заметки:**
```
Vault note → detect mode → rewrite (Claude) → write back
```

**Память (FTS5):**
```
любая запись в vault → vault_writer → авто-обновление FTS5-индекса (вне vault)
поиск: memory_index.py search "запрос" → bm25 + сниппеты → топ заметок
```

- **Enrich** — короткая заметка → добавляет теги, вики-ссылки, расширяет текст (1 → 1)
- **Atomize** — длинная заметка → разбивает на атомарные заметки + MOC (1 → N)
- **Contacts** — заметка с контактами → персональные карточки + Networking MOC (1 → N)

### MOC + Zettelkasten

**MOC (Map of Content)** — навигационный хаб: собирает ссылки на все атомарные заметки из документа. Один MOC на документ.

**Атомарные заметки** — одна идея, 150–600 слов, самодостаточные. Связаны `[[вики-ссылками]]` друг с другом и с MOC.

**Память FTS5** (`scripts/memory_index.py`) — полнотекстовый поиск по всему vault на SQLite FTS5: нулевые зависимости (stdlib), всё локально, индекс живёт вне vault и обновляется автоматически после каждой записи. Поисковый слой для агентов: `python3 scripts/memory_index.py search "запрос" --json`.

**Smart Connections** *(legacy)* — прежний поисковый слой на локальных эмбеддингах. Заменён памятью FTS5: пайплайн его больше не использует и не требует. Плагин можно оставить ради семантических подсказок в UI Obsidian.

### LLM Wiki

Третий слой знаний поверх атомарных заметок — **скомпилированная вики** в стиле Карпати. Не RAG (не пересчитывается при каждом запросе) и не плоский набор заметок (страницы связаны вики-ссылками и имеют типы). Это долгоживущая база, которая **накапливается** через явный merge при новых ингестах: существующие `[[вики-ссылки]]` обязаны сохраняться, иначе compile падает с `WIKI_LINKS_LOST` (exit 5).

Вики живёт в изолированной папке внутри vault — `<vault>/<wiki_folder>/<slug>/` (по умолчанию `LLM Wiki/`). Атомарные заметки никогда не попадают сюда, и `wiki_compile.py` не читает заметки за пределами своей wiki-space.

**Два режима:**

- **project** — фиксированные core-страницы: overview, architecture, components, workflows, goals-and-roadmap, glossary, open-questions. Подходит для документации одной системы.
- **corpus** — только entities/concepts растут по мере ингеста. Подходит для базы знаний по чтению/исследованиям.

**Workflow:**

```bash
# 1. Создать пустую wiki-space (+ опц. --lang ru|en для русских/английских шаблонов)
python3 scripts/wiki_init.py demo --mode project --title "Demo Project"

# 2. Залить сырьё (статьи, доки, транскрипты)
python3 scripts/wiki_ingest.py demo path/to/article.md --kind articles
python3 scripts/wiki_ingest.py demo path/to/notes/ --kind docs

# 3. Скомпилировать (LLM мерджит сырьё в страницы)
python3 scripts/wiki_compile.py demo --since-last-compile

# 4. Проверить целостность
python3 scripts/wiki_lint.py demo --strict

# Инкрементальный апдейт одной страницы из одного нового raw-инпута
python3 scripts/wiki_update.py demo raw/docs/новый-файл.md
```

Все скрипты пишут через единственный writer `vault_writer.py` — атомарные пайплайны и wiki делят одну точку записи.

**Язык шаблонов.** `wiki_init.py` поддерживает `--lang en` и `--lang ru`. Значение по умолчанию берётся из `[wiki].default_lang` в `config.toml` (если не указан — `en`). Влияет только на текст SCHEMA.md, index.md, log.md, raw/_README.md и core-страниц-stub'ов; структура и контракт frontmatter одинаковы для обоих языков. Wiki-space'ы на разных языках сосуществуют в одном vault без конфликтов.

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

- [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) — HTTP-интерфейс для чтения/записи vault. Нужен для MCP Obsidian
- [MCP Obsidian](https://github.com/MarkusPfundstein/mcp-obsidian) — MCP-сервер, соединяющий Claude Code с Obsidian через Local REST API. Зависит от Local REST API

**Legacy (больше не требуется):**

- [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) — прежний слой семантического поиска (локальные эмбеддинги). Заменён памятью FTS5 (`scripts/memory_index.py`); старый конфиг в `templates/.smart-env/` оставлен для существующих установок

**Смежные проекты:**

- [NotebookLM++](https://github.com/howdeploy/notebooklmplusplus) — Chrome-расширение для [NotebookLM](https://notebooklm.google.com), которое добавляет массовый импорт: веб-страницы, YouTube-видео, Shorts, плейлисты, каналы целиком, комментарии и PDF-снимки страниц. Если вы используете NotebookLM как второй мозг наряду с Obsidian — это расширение закрывает ту же задачу на стороне Google: быстро собрать источники в нотбук для AI-анализа

### Структура проекта

```
ObsidianDataWeave/
├── scripts/
│   ├── process.py            # Главный пайплайн (.docx → vault)
│   ├── process_note.py       # Обработка личных заметок (enrich/atomize)
│   ├── process_contacts.py   # Контакты → персональные карточки + Networking MOC
│   ├── process_notebook.py   # NotebookLM нотбук → атомарные заметки (полный пайплайн)
│   ├── fetch_notebook.py     # Извлечение заметок из NotebookLM (без атомизации)
│   ├── research_notebook.py  # Deep/fast research + дедупликация источников в NotebookLM
│   ├── notebooklm_setup.py   # Установка notebooklm-py + Playwright (one-shot)
│   ├── fetch_docx.sh         # Скачивание с Google Drive
│   ├── parse_docx.py         # .docx → JSON
│   ├── atomize.py            # JSON → план атомизации (через Claude)
│   ├── generate_notes.py     # План → .md файлы
│   ├── vault_writer.py       # Staging → vault (с дедупликацией)
│   ├── dedup_vault.py        # Поиск и мерж дубликатов
│   ├── scan_vault.py         # Сканирование существующих заметок
│   ├── rewrite_backend.py    # Бэкенд семантической перезаписи (Claude CLI)
│   ├── config.py             # Загрузчик конфигурации
│   ├── doctor.py             # Проверка окружения
│   ├── memory_index.py       # Память FTS5 — индекс/поиск по всему vault (build/update/search)
│   ├── migrate.py            # Идемпотентный апгрейд установки (config + FTS5-индекс)
│   ├── wiki_init.py          # LLM Wiki — создать пустую wiki-space
│   ├── wiki_ingest.py        # LLM Wiki — приём сырья (articles/docs/transcripts/assets)
│   ├── wiki_compile.py       # LLM Wiki — главный пайплайн компиляции
│   ├── wiki_update.py        # LLM Wiki — инкрементальный апдейт одной страницы
│   ├── wiki_lint.py          # LLM Wiki — read-only проверка целостности
│   └── wiki_models.py        # LLM Wiki — ChangeSet / WikiPage / валидация
├── rules/
│   ├── atomization.md        # Правила атомизации
│   ├── taxonomy.md           # Правила таксономии тегов
│   ├── personal_notes.md     # Правила обработки личных заметок
│   ├── contacts.md           # Правила обработки контактов
│   ├── wiki_schema.md        # LLM Wiki — on-disk контракт
│   ├── wiki_compile.md       # LLM Wiki — контракт LLM для compile
│   └── wiki_update.md        # LLM Wiki — семантика инкрементального merge
├── templates/                # Стартовая структура vault (+ templates/wiki/ для LLM Wiki)
├── tests/                    # Регрессионные тесты
├── docs/                     # Документация для агентов
├── AGENTS.md                 # Контракт агента (Claude Code + Codex)
├── SKILL.md                  # Claude-адаптер
├── SKILL_PERSONAL.md         # Промпт для обработки личных заметок
├── SKILL_CONTACTS.md         # Промпт для обработки контактов
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

ObsidianDataWeave turns Claude Code and Codex into a full remote control for NotebookLM and your Obsidian vault. Run deep research, manage sources, pull notes from notebooks — all through a single natural-language command. It also imports `.docx` from Google Drive and atomizes them into Zettelkasten notes with MOC, tags, and wikilinks. On top of all that — an isolated **LLM Wiki** layer: a Karpathy-style compiled knowledge base that grows by explicit merge, never recomputed on every query. Search across all of it is the **FTS5 memory**: a local full-text index of the whole vault (notes, wiki, NotebookLM imports) that refreshes itself after every write.

#### What you can do with NotebookLM

| Capability | Command |
|---|---|
| Run deep/fast research into a notebook | `research_notebook.py run <id> "<query>"` |
| Safe one-shot source import (no duplicates) | same, bypasses [upstream CLI bug](https://github.com/teng-lin/notebooklm-py/issues/241) |
| Clean up duplicate and error-state sources | `research_notebook.py dedupe <id>` |
| Pull all notes → atomic notes in Obsidian | `process_notebook.py <id>` |
| Pull notes + source fulltext + mind maps | `process_notebook.py <id> --include-sources --include-mindmap` |
| Download notes without atomization | `fetch_notebook.py <id>` |

All NotebookLM interaction goes through the Python API (`notebooklm-py`), not the CLI — single call, no retry duplication. Auth is a file on disk, no interactive browser on every run.

#### What else it does

- Import `.docx` from Google Drive → atomic notes + MOC in vault
- Enrich and atomize existing vault notes
- Process networking contacts → individual contact cards + Networking MOC
- Deduplicate vault by semantic similarity
- Automatic tag taxonomy and cross-note wikilinks
- **LLM Wiki** — an isolated compiled-knowledge layer (project / corpus modes, RU/EN templates, hard guard that preserves existing `[[wikilinks]]` on merge, see [section below](#llm-wiki-1))
- **FTS5 Memory** — full-text search over the whole vault on stdlib SQLite: `memory_index.py search "query" --json`, bm25 ranking with snippets, incremental index kept outside the vault

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

### Upgrade

```bash
cd ObsidianDataWeave && git pull && bash install.sh
```

The installer is idempotent: skill symlinks update themselves, `migrate.py`
appends new config sections (e.g. `[memory]`) and deploys the FTS5 memory
index. `config.toml` and the vault are never overwritten.

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
| `process contacts "My Contacts"` | Split contacts note → individual cards + Networking MOC |
| `process_note "Note" --mode atomize` | Force atomization of a note |
| `dedup --dry-run` | Show duplicates without changes |
| `run research in notebook "<id>" "<query>"` | Deep research into NotebookLM via API |
| `dedupe notebook sources "<id>"` | Deduplicate sources in a notebook |
| `init wiki "<slug>"` | Scaffold a new LLM Wiki-space (project/corpus, RU/EN) |
| `ingest into wiki "<slug>" <path>` | Drop an article / folder into `raw/<kind>/` |
| `compile wiki "<slug>"` | Merge raw into pages (with `[[wikilink]]`-preservation guard) |
| `lint wiki "<slug>"` | Check frontmatter, link resolution, contour isolation |
| `search notes "<query>"` | FTS5 search across the whole vault (notes + wiki), bm25 + snippets |
| `rebuild memory index` | Full FTS5 index rebuild (`memory_index.py build`) |

### NotebookLM: full programmatic control

ObsidianDataWeave gives Claude Code / Codex full programmatic control over NotebookLM. Instead of manual work in the web UI, you tell the agent what you need and it runs research, manages sources, pulls notes, and atomizes them into Obsidian. The entire API layer uses `notebooklm-py` as a library (not the CLI), which guarantees one-shot behavior with no retry duplication.

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

**NotebookLM → Obsidian:**
```
NotebookLM API → fetch notes/sources/mindmaps → atomize (Claude) → generate → write → Obsidian vault
```

**Deep Research → NotebookLM:**
```
research_notebook.py → notebooklm-py API (one-shot) → poll → import sources → dedupe
```

**Google Drive → Obsidian:**
```
Google Drive → rclone fetch → parse .docx → atomize (Claude) → generate → write → Obsidian vault
```

**Personal notes:**
```
Vault note → detect mode → rewrite (Claude) → write back
```

**Memory (FTS5):**
```
any vault write → vault_writer → FTS5 index auto-refresh (outside the vault)
search: memory_index.py search "query" → bm25 + snippets → top notes
```

- **Enrich** — short note → adds tags, wikilinks, expands text (1 → 1)
- **Atomize** — long note → splits into atomic notes + MOC (1 → N)
- **Contacts** — networking note → individual contact cards + Networking MOC (1 → N)

### MOC + Zettelkasten

**MOC (Map of Content)** — a navigation hub collecting links to all atomic notes from a document. One MOC per document.

**Atomic notes** — one idea, 150–600 words, fully self-contained. Connected via `[[wikilinks]]` to each other and to the MOC.

**FTS5 Memory** (`scripts/memory_index.py`) — full-text search over the whole vault on SQLite FTS5: zero dependencies (stdlib), fully local, the index lives outside the vault and refreshes automatically after every write. The search layer for agents: `python3 scripts/memory_index.py search "query" --json`.

**Smart Connections** *(legacy)* — the previous search layer built on local embeddings. Superseded by the FTS5 memory: the pipeline no longer uses or requires it. You may keep the plugin for semantic suggestions in the Obsidian UI.

### LLM Wiki

A third knowledge layer on top of atomic notes — a **compiled wiki** in the Karpathy style. Not RAG (not recomputed on every query) and not a flat note pile (pages are interlinked and typed). It is a long-lived knowledge base that **accumulates** through explicit merge on each ingest: existing `[[wikilinks]]` must be preserved, otherwise compile fails with `WIKI_LINKS_LOST` (exit 5).

The wiki lives in an isolated folder inside the vault — `<vault>/<wiki_folder>/<slug>/` (default `LLM Wiki/`). Atomic notes never appear here, and `wiki_compile.py` never reads notes outside its own wiki-space.

**Two modes:**

- **project** — fixed core pages: overview, architecture, components, workflows, goals-and-roadmap, glossary, open-questions. Use for documenting a single coherent system.
- **corpus** — only entities/concepts grow as raw is ingested. Use for a reading-list / research knowledge base.

**Workflow:**

```bash
# 1. Create an empty wiki-space (+ optional --lang ru|en for template language)
python3 scripts/wiki_init.py demo --mode project --title "Demo Project"

# 2. Ingest raw inputs (articles, docs, transcripts)
python3 scripts/wiki_ingest.py demo path/to/article.md --kind articles
python3 scripts/wiki_ingest.py demo path/to/notes/ --kind docs

# 3. Compile (the LLM merges raw into pages)
python3 scripts/wiki_compile.py demo --since-last-compile

# 4. Lint the structure
python3 scripts/wiki_lint.py demo --strict

# Incremental single-page update from one new raw input
python3 scripts/wiki_update.py demo raw/docs/new-file.md
```

All scripts go through the single `vault_writer.py` writer — atomic pipelines and the wiki share the same write boundary.

**Template language.** `wiki_init.py` supports `--lang en` and `--lang ru`. The default comes from `[wiki].default_lang` in `config.toml` (falls back to `en`). Only the on-disk prose of SCHEMA.md, index.md, log.md, raw/_README.md, and core-page stubs is affected — structure and frontmatter contract are identical across languages. Wiki-spaces in different languages coexist in the same vault without conflicts.

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

- [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) — HTTP interface for reading/writing vault contents. Required by MCP Obsidian
- [MCP Obsidian](https://github.com/MarkusPfundstein/mcp-obsidian) — MCP server connecting Claude Code to Obsidian via Local REST API. Depends on Local REST API

**Legacy (no longer required):**

- [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) — the previous semantic-search layer (local embeddings). Superseded by the FTS5 memory (`scripts/memory_index.py`); the old config in `templates/.smart-env/` is kept for existing installs

**Related projects:**

- [NotebookLM++](https://github.com/howdeploy/notebooklmplusplus) — Chrome extension for [NotebookLM](https://notebooklm.google.com) that adds bulk import: web pages, YouTube videos, Shorts, playlists, entire channels, comments, and PDF page snapshots. If you use NotebookLM as a second brain alongside Obsidian, this extension covers the same workflow on the Google side: quickly gather sources into a notebook for AI analysis

### Project structure

```
ObsidianDataWeave/
├── scripts/
│   ├── process.py            # Main pipeline (.docx → vault)
│   ├── process_note.py       # Personal note processing (enrich/atomize)
│   ├── process_contacts.py   # Contacts → individual cards + Networking MOC
│   ├── process_notebook.py   # NotebookLM notebook → atomic notes (full pipeline)
│   ├── fetch_notebook.py     # Pull notes from NotebookLM (without atomization)
│   ├── research_notebook.py  # Deep/fast research + source deduplication in NotebookLM
│   ├── notebooklm_setup.py   # Install notebooklm-py + Playwright (one-shot)
│   ├── fetch_docx.sh         # Download from Google Drive
│   ├── parse_docx.py         # .docx → JSON
│   ├── atomize.py            # JSON → atom plan (via Claude)
│   ├── generate_notes.py     # Plan → .md files
│   ├── vault_writer.py       # Staging → vault (with deduplication)
│   ├── dedup_vault.py        # Find and merge duplicate notes
│   ├── scan_vault.py         # Scan existing vault notes
│   ├── rewrite_backend.py    # Semantic rewrite backend (Claude CLI)
│   ├── config.py             # Configuration loader
│   ├── doctor.py             # Environment check
│   ├── memory_index.py       # FTS5 memory — index/search the whole vault (build/update/search)
│   ├── migrate.py            # Idempotent install upgrade (config + FTS5 index)
│   ├── wiki_init.py          # LLM Wiki — create an empty wiki-space
│   ├── wiki_ingest.py        # LLM Wiki — raw input intake (articles/docs/transcripts/assets)
│   ├── wiki_compile.py       # LLM Wiki — main compile pipeline
│   ├── wiki_update.py        # LLM Wiki — incremental single-page update
│   ├── wiki_lint.py          # LLM Wiki — read-only structural check
│   └── wiki_models.py        # LLM Wiki — ChangeSet / WikiPage / validation
├── rules/
│   ├── atomization.md        # Atomization rules
│   ├── taxonomy.md           # Tag taxonomy rules
│   ├── personal_notes.md     # Personal note processing rules
│   ├── contacts.md           # Contact note processing rules
│   ├── wiki_schema.md        # LLM Wiki — on-disk contract
│   ├── wiki_compile.md       # LLM Wiki — LLM contract for compile
│   └── wiki_update.md        # LLM Wiki — incremental merge semantics
├── templates/                # Starter vault structure (+ templates/wiki/ for LLM Wiki)
├── tests/                    # Regression tests
├── docs/                     # Agent-facing documentation
├── AGENTS.md                 # Agent contract (Claude Code + Codex)
├── SKILL.md                  # Claude adapter
├── SKILL_PERSONAL.md         # Prompt header for personal note processing
├── SKILL_CONTACTS.md         # Prompt header for contact processing
├── tags.yaml                 # Canonical tag list
├── config.example.toml       # Configuration template
├── install.sh                # Installer with global skill registration
└── requirements.txt          # Python dependencies
```

### License

MIT — see [LICENSE](LICENSE).
