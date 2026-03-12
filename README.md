# Opencluely

Opencluely is a desktop assistant shell for live meetings, interviews, sales calls, and
screen-led workflows. This repository also includes the orchestrator and audit documents
used to harden the product brand and UX.

## What This Repository Contains

- A floating always-on-top live assistance overlay built with `PyQt5`
- Dual audio capture for microphone plus system loopback
- Local and Groq-based transcription paths
- Groq-powered assist generation
- Screenshot analysis for on-screen questions and code
- Session briefs, notes, and Prep Deck state stored locally at runtime

## Safety Notes

- Runtime data is written to `data/` and ignored by Git
- Application logs are written to `logs/` and ignored by Git
- Provider credentials must come from environment variables
- The repository does not rely on committed personal notes or prep answers

## Quick Start

### Windows

```bat
run.bat
```

### Manual

```powershell
pip install -r requirements.txt
$env:GROQ_API_KEY="gsk_your_key_here"
python main.py
```

## Environment Variables

- `GROQ_API_KEY`: enables transcription and AI answer generation
- `HUGGINGFACE_API_KEY`: enables Hugging Face vision requests if that path is used
- `HUGGINGFACE_VISION_MODEL`: optional override for the Hugging Face model name
- `VISION_TIMEOUT_SECONDS`: optional override for screenshot analysis timeout

## External Dependencies

### Tesseract OCR

Install Tesseract if you want screen OCR support.

- Windows download: https://github.com/UB-Mannheim/tesseract/wiki
- Typical path: `C:\Program Files\Tesseract-OCR\`

### Audio Loopback Capture

The desktop assistant expects the Windows-compatible `pyaudiowpatch` package for WASAPI
loopback capture.

## Project Layout

```text
main.py                    Desktop bootstrap
run.bat                    Windows launcher
src/audio_capture.py       Dual audio capture worker
src/transcription.py       Local transcription fallback
src/transcription_groq.py  Groq transcription provider
src/ai_helper.py           Assist generation helper
src/screen_analyzer.py     Screenshot analysis flow
src/context_manager.py     Resume and document ingestion
src/templates/             Session brief management
src/ui/                    Session setup and overlay shell
```

## Current Position

This repository now carries the Opencluely product name and core brand direction while
still preserving orchestrator artifacts that document the migration from the earlier
legacy baseline.
