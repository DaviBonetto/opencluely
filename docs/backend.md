# Backend Notes

Opencluely now has a real backend wired into the floating bar instead of placeholder data.

## What Exists Now

- `src/backend/contracts/`: typed session, provider, transcript, note, and screen context models
- `src/backend/providers/`: Groq STT, Gemini Live STT, local faster-whisper STT, assist, vision, and provider selection
- `src/backend/services/`: rolling transcript store, local notes engine, and screen capture
- `src/backend/session/`: Qt-safe session orchestrator, prompt composition, and persistence
- `src/backend/audio_capture/`: Windows-first microphone, loopback, and mixed capture pipeline
- `src/ui/floating_bar.py`: real controller/view integration for Chat, Transcript, Notes, top actions, and options

## Provider Strategy

- STT `auto`: Groq Whisper Turbo -> Gemini Live -> local faster-whisper
- Assist `auto`: Gemini -> Groq -> local degraded summary mode
- Screen analysis: Gemini first, Groq vision fallback, clear degraded state if neither is available

Current defaults in `src/backend/settings.py`:

- `GROQ_AUDIO_MODEL=whisper-large-v3-turbo`
- `GEMINI_LIVE_MODEL=gemini-2.5-flash-native-audio-preview-12-2025`
- `OPENCLUELY_STT_PROVIDER=auto`
- `OPENCLUELY_AUDIO_SOURCE=auto`

## Session Behavior

- The floating bar autostarts a listening session
- `Pause` pauses capture without killing the session
- `Stop` stops capture/transcription cleanly
- `View screen` toggles screen-aware mode and captures immediately when enabled
- `Incognito` disables durable sensitive persistence and clears temporary screenshots
- `Options` exposes provider selection, audio source selection, key detection, restart, reset, and manual screen capture

## Persistence And Privacy

- Runtime data stays outside the repository through `src/runtime/paths.py`
- Sessions are persisted under the runtime home only when `OPENCLUELY_PERSIST_SESSION_DATA=true`
- Incognito mode redacts transcript/chat/notes/screen summary from persisted state
- Temporary screenshots are cleared when incognito is enabled or the session is closed/reset

## Validation

Backend tests:

```powershell
python -m unittest discover -s tests/backend -p "test_*.py"
```

UI smoke tests:

```powershell
python -m unittest discover -s tests/ui -p "test_*.py"
```

Headless bootstrap smoke:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
@'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("src").resolve()))
from PySide6.QtWidgets import QApplication
from ui.floating_bar import FloatingBar
app = QApplication([])
bar = FloatingBar({"language": "pt-BR"}, autostart=False)
print("smoke-ok")
bar.close()
app.quit()
'@ | python -
```

## Honest Limitations

- No speaker diarization is fabricated; transcripts are single-stream unless a provider exposes reliable structure
- Screen context is on-demand or toggled, not continuous background capture
- Gemini Live requires `google-genai` plus a valid `GEMINI_API_KEY`
- The combined command `python -m unittest discover -s tests -p "test_*.py"` is not used because the legacy `tests/backend` and `tests/ui` folder names shadow `src/backend` and `src/ui` during root-level discovery
