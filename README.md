# Opencluely

Opencluely is currently a focused desktop shell prototype built around a floating AI bar.
The repository has been reduced to the active runtime, the new PySide6 UI, and the
documentation that still matters for future iterations.

## Current Runtime

- `main.py` boots the desktop app
- `src/backend/` now contains the real session backend: capture, provider adapters, transcript store, notes, screen context, and persistence
- `src/ui/floating_bar.py` is the source-of-truth floating bar and is now wired to Chat, Transcript, Notes, providers, and top actions
- `src/ui/live_bar.py` keeps the existing import path stable for the app flow
- `src/runtime/paths.py` centralizes runtime directories for logs and app data outside the repo
- `assets/fonts/` stores the bundled Inter font used by the shell

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

## Quick Start

### Windows

```bat
run.bat
```

### Manual

```powershell
pip install -r requirements.txt
python main.py
```

To work on the restored backend modules:

```powershell
pip install -r requirements-backend.txt
```

Useful provider env vars:

```powershell
$env:GROQ_API_KEY = "..."
$env:GEMINI_API_KEY = "..."
$env:OPENCLUELY_STT_PROVIDER = "auto"
$env:OPENCLUELY_AUDIO_SOURCE = "auto"
```

Optional:

```powershell
$env:OPENCLUELY_HOME = "$env:LOCALAPPDATA\Opencluely"
python main.py
```

## Local Runtime Files

- Runtime files now live outside the repository by default
- On Windows the default runtime home is `%LOCALAPPDATA%\Opencluely`
- Set `OPENCLUELY_HOME` if you want to override that location
- `quarantine/` remains ignored if you need a private local scratch folder in the repo

## Cleanup Helpers

- Run `powershell -ExecutionPolicy Bypass -File scripts\clean_local.ps1` to remove repo-local
  caches, stale runtime leftovers, smoke artifacts, and quarantine material without touching
  tracked source files.

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
