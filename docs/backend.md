# Backend Notes

The backend modules that were worth preserving now live under `src/backend/`.

## Structure

- `src/backend/settings.py`: shared environment-driven backend settings
- `src/backend/audio_capture/`: microphone/system capture plus local and Groq transcription adapters
- `src/backend/groq/`: Groq-backed assist and screen analysis services

## Current Status

- The backend is restored and organized, but it is not yet wired back into the floating bar UI
- The shell can keep running with only `requirements.txt`
- If you want to work on capture/transcription again, install `requirements-backend.txt`

## Runtime

- Backend runtime data still resolves through `src/runtime/paths.py`
- Local JSON state stays outside the repository in the external app runtime home
