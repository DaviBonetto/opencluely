# Opencluely

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![Gemini](https://img.shields.io/badge/AI-Gemini-4285F4)](https://ai.google.dev/)
[![Groq](https://img.shields.io/badge/AI-Groq-F55036)](https://groq.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/github/license/DaviBonetto/opencluely)](LICENSE)

Opencluely is a Windows-first desktop meeting assistant with a floating AI bar.
It combines live transcription, meeting-aware chat, notes, and optional screen context
in a compact PySide6 shell designed for real use instead of a static mockup.

## Highlights

- Floating desktop bar wired to a live session backend
- Real-time transcription with Gemini Live, Groq Whisper, and local fallback adapters
- Meeting-aware chat that can still answer general questions
- Incremental notes, screen-aware context, and optional persisted session state
- Runtime files stored outside the repository for a cleaner workspace

## Current Runtime

- `main.py` boots the desktop app
- `src/backend/` now contains the real session backend: capture, provider adapters, transcript store, notes, screen context, and persistence
- `src/ui/floating_bar.py` is the source-of-truth floating bar and is now wired to Chat, Transcript, Notes, providers, and top actions
- `src/ui/live_bar.py` keeps the existing import path stable for the app flow
- `src/runtime/paths.py` centralizes runtime directories for logs and app data outside the repo
- `assets/fonts/` stores the bundled Inter font used by the shell

## Architecture At A Glance

```text
Audio Capture -> STT Provider -> Transcript Store -> Session Orchestrator
                                                   |- Notes Engine
                                                   |- Screen Capture + Vision
                                                   `- Chat Provider -> Floating Bar UI
```

The desktop shell in `src/ui/` talks to a session backend in `src/backend/session/`.
That backend coordinates provider selection, transcript updates, notes, screen summaries,
and assistant responses without pushing provider-specific logic into the UI.

## Repository Layout

```text
assets/
  fonts/                     Bundled Inter font and its upstream license
docs/
  Codex_Orchestrator/        Archived planning and implementation packets
  legal/                     Third-party notices
  reference-images/          Reference captures used during design work
main.py                      Desktop bootstrap
run.bat                      Windows launcher
scripts/
  clean_local.ps1            Local cleanup helper for repo caches and stale runtime leftovers
src/
  backend/
    audio_capture/           Windows-first capture plus chunk/frame emission
    contracts/               Typed session/provider contracts
    providers/               Groq, Gemini, and local adapters
    services/                Transcript store, notes, and screen capture
    session/                 Session orchestrator, prompt composition, persistence
    settings.py              Shared backend environment settings
  runtime/
    paths.py                 Shared runtime paths for logs and local data
  ui/
    floating_bar.py          New floating bar implementation
    live_bar.py              Compatibility wrapper for the current app flow
```

## Tech Stack

- **Language**: Python 3.13
- **Desktop UI**: PySide6 / Qt
- **Realtime STT**: Gemini Live and Groq Whisper
- **Fallback STT**: local faster-whisper adapter
- **Vision Context**: Gemini and Groq multimodal analyzers
- **Runtime Storage**: local files outside the repository root

## Quick Start

### 1. Install the core desktop runtime

```powershell
pip install -r requirements.txt
```

### 2. Install the optional backend providers

```powershell
pip install -r requirements-backend.txt
```

### 3. Configure provider keys

```powershell
$env:GROQ_API_KEY = "..."
$env:GEMINI_API_KEY = "..."
$env:GEMINI_ASSIST_API_KEY = "..."
```

If `GEMINI_ASSIST_API_KEY` is omitted, chat falls back to `GEMINI_API_KEY`.

### 4. Launch Opencluely

#### Windows launcher

```bat
run.bat
```

#### Manual bootstrap

```powershell
python main.py
```

## Configuration

### Common environment variables

```powershell
$env:GROQ_API_KEY = "..."
$env:GEMINI_API_KEY = "..."
$env:GEMINI_ASSIST_API_KEY = "..."
$env:OPENCLUELY_STT_PROVIDER = "auto"
$env:OPENCLUELY_ASSIST_PROVIDER = "auto"
$env:OPENCLUELY_AUDIO_SOURCE = "auto"
$env:OPENCLUELY_HOME = "$env:LOCALAPPDATA\Opencluely"
```

### Provider values

- `OPENCLUELY_STT_PROVIDER`: `auto`, `gemini`, `groq`, `local`
- `OPENCLUELY_ASSIST_PROVIDER`: `auto`, `gemini`, `groq`, `local`
- `OPENCLUELY_AUDIO_SOURCE`: `auto`, `microphone`, `loopback`, `mixed`

### Runtime defaults

- STT defaults to `auto`
- Assistant defaults to `auto`
- Audio source defaults to `auto`
- Runtime home defaults to `%LOCALAPPDATA%\Opencluely`

## Provider Strategy

- **Chat**: Gemini is the preferred assistant backend when configured
- **Live transcription**: `auto` prefers Gemini Live first, then Groq
- **Audio source**: `auto` prefers mixed capture when microphone and loopback are both available
- **Screen context**: Gemini vision is preferred, with Groq as fallback

## Validation

### Focused backend tests

```powershell
python -m unittest discover -s tests/backend -p "test_*.py"
```

### UI smoke tests

```powershell
python -m unittest discover -s tests/ui -p "test_*.py"
```

### Lightweight syntax verification

```powershell
python -m compileall src
```

## Runtime Files And Logs

- Runtime files now live outside the repository by default
- On Windows the default runtime home is `%LOCALAPPDATA%\Opencluely`
- Set `OPENCLUELY_HOME` if you want to override that location
- Logs are written under `%LOCALAPPDATA%\Opencluely\logs`
- Persisted sessions and screenshots are stored under the runtime data directory
- `quarantine/` remains ignored if you need a private local scratch folder in the repo

## Cleanup Helpers

- Run `powershell -ExecutionPolicy Bypass -File scripts\clean_local.ps1` to remove repo-local
  caches, stale runtime leftovers, smoke artifacts, and quarantine material without touching
  tracked source files.

## Troubleshooting

### The app starts but a provider is unavailable

- Confirm the corresponding API key is set in the current shell
- Open the floating bar options menu and check provider readiness lines
- Review the latest log file under `%LOCALAPPDATA%\Opencluely\logs`

### Groq returns `429`

- Prefer `auto` or Gemini Live for sustained realtime transcription
- Keep Groq for fallback or lower-frequency chunk transcription scenarios

### Gemini Live stops or reconnects

- Check the latest runtime log for websocket or session errors
- Restart listening from the options menu after updating environment variables

### The workspace shows local clutter again

- Run `scripts\clean_local.ps1`
- Keep separate scratch projects outside the repository root when possible

## Docs and Notices

- Planning and archived implementation material lives in [docs/Codex_Orchestrator](docs/Codex_Orchestrator)
- Visual references live in [docs/reference-images](docs/reference-images)
- Third-party asset notices live in [docs/legal/THIRD_PARTY_NOTICES.md](docs/legal/THIRD_PARTY_NOTICES.md)
- Backend restoration notes live in [docs/backend.md](docs/backend.md)
- The current repository license posture is documented in [LICENSE](LICENSE)

## Status

The repository is intentionally slimmer now: the old PyQt workflow, legacy shell support files,
and archived reference material have been separated so future work can build directly on the new
floating bar without dragging old runtime paths behind it. The useful backend pieces now live in
`src/backend/` as optional modules instead of spreading across the root of `src/`.
