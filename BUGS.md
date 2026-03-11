# Legacy Debt Register

This file tracks legacy behavior, structural debt, and known cleanup work that should inform
the Opencluely rewrite.

## Preserved Behaviors

- Floating always-on-top interview overlay
- Session setup flow with reusable templates
- Dual-source audio capture for microphone and system audio
- Groq-based transcription and answer generation
- Screenshot analysis for on-screen prompts
- Local notes and interview-prep support

## Known Risks

### Security and Privacy

- Do not reintroduce hardcoded provider credentials into source control
- Do not commit runtime notes, prep answers, or generated logs
- Keep personal prep material in `data/`, not `config/`

### Structural Debt

- `src/ui/horizontal_overlay.py` remains a large monolith and should be decomposed during rewrite
- `src/ui/session_setup.py` still carries both styling and flow logic in one file
- Provider access, persistence, and UI orchestration are still tightly coupled

### Runtime Constraints

- OCR quality depends on Tesseract availability and screenshot clarity
- Groq-based features depend on environment configuration and provider availability
- Windows loopback capture depends on `pyaudiowpatch`

## Rewrite Prerequisites

- Break UI monoliths into smaller components with explicit boundaries
- Separate provider orchestration from presentation logic
- Add tests around persistence, template loading, and transcription orchestration
- Preserve behavior parity for the overlay shell before visual redesign
