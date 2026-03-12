# Opencluely

Opencluely is a desktop copilot for live sessions. This repository now uses the Opencluely
product language across Launchpad, Live Bar, Context Vault, Copilot Profiles, Assist, and
Screen Analysis while preserving the original architecture as a rewrite baseline.

## What This Repository Contains

- `Launchpad` for session launch
- `Live Bar` for always-on-top session support with transcription and chat
- `Assist` for Groq-backed response generation
- `Screen Analysis` for screenshot-based help
- `Context Vault` prompts and `Context` notes stored locally at runtime
- `Copilot Profiles` for reusable session behavior presets

## Safety Notes

- Runtime data is written to `data/` and ignored by Git
- Application logs are written to `logs/` and ignored by Git
- Provider credentials must come from environment variables
- Legacy personal context data is quarantined under `quarantine/`

## Runtime Migration Notes

- Saved profile state now lives in `data/copilot_profiles.json`
- Context notes now live in `data/context_notes.json`
- Context Vault prompts now live in `data/context_vault.json`
- Legacy runtime profile ids such as `interview_assistant`, `leetcode_helper`, `sales_assistant`,
  and `custom` are normalized to `general_copilot`, `problem_solving`, `sales_conversation`, and
  `custom_profile` during load
- Legacy runtime profile payloads in `data/templates.json` are migrated forward automatically

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

- `GROQ_API_KEY`: enables transcription, Assist, and Screen Analysis
- `HUGGINGFACE_API_KEY`: enables Hugging Face vision requests if that path is used
- `HUGGINGFACE_VISION_MODEL`: optional override for the Hugging Face model name
- `VISION_TIMEOUT_SECONDS`: optional override for screenshot analysis timeout

## External Dependencies

### Tesseract OCR

Install Tesseract if you want screen OCR support.

- Windows download: https://github.com/UB-Mannheim/tesseract/wiki
- Typical path: `C:\Program Files\Tesseract-OCR\`

### Audio Loopback Capture

The desktop app expects the Windows-compatible `pyaudiowpatch` package for WASAPI loopback
capture.

## Project Layout

```text
main.py                          Desktop bootstrap
run.bat                          Windows launcher
src/audio_capture.py             Dual audio capture worker
src/transcription.py             Local transcription fallback
src/transcription_groq.py        Groq transcription provider
src/assist_service.py            Assist response generation
src/screen_analysis.py           Screen Analysis flow
src/context_manager.py           Resume and document ingestion
src/context_notes_manager.py     Context note persistence
src/context_vault_manager.py     Context Vault prompt persistence
src/profiles/                    Copilot Profile management
src/ui/launchpad.py              Launchpad window
src/ui/live_bar.py               Live Bar shell
```

## Current Position

This codebase still carries legacy implementation debt, but the shipped naming now follows the
Opencluely system. Future work should keep the new vocabulary stable while decomposing the large
UI modules and building the full Debrief workflow.
