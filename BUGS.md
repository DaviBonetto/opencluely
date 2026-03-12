# Legacy Debt Register

This file tracks structural debt and preserved behavior that still matters as Opencluely evolves.

## Preserved Behaviors

- Floating always-on-top `Live Bar`
- `Launchpad` flow with reusable `Copilot Profiles`
- Dual-source audio capture for microphone and system audio
- Groq-based transcription and `Assist` generation
- `Screen Analysis` for on-screen prompts
- `Context Vault` prompts and `Context` note support

## Known Risks

### Security and Privacy

- Do not reintroduce hardcoded provider credentials into source control
- Do not commit runtime context notes, vault data, or generated logs
- Keep user-authored session material in `data/`, not `config/`

### Structural Debt

- `src/ui/live_bar.py` remains a large monolith and should be decomposed during rewrite
- `src/ui/launchpad.py` still carries both styling and flow logic in one file
- Provider access, persistence, and UI orchestration are still tightly coupled

### Runtime Constraints

- OCR quality depends on Tesseract availability and screenshot clarity
- Groq-based features depend on environment configuration and provider availability
- Windows loopback capture depends on `pyaudiowpatch`

## Rewrite Prerequisites

- Break UI monoliths into smaller components with explicit boundaries
- Separate provider orchestration from presentation logic
- Add tests around persistence, profile loading, and transcription orchestration
- Preserve behavior parity for the Live Bar shell before visual redesign
