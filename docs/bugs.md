# Runtime Notes

This file now tracks the slimmer runtime posture of the repository after the large cleanup.

## Current Shape

- The active desktop app is the floating shell in `src/ui/floating_bar.py`
- `src/ui/live_bar.py` is intentionally just the compatibility entry point used by the bootstrap
- Runtime-only material belongs in the external app home resolved by `src/runtime/paths.py`
- On Windows the default runtime home is `%LOCALAPPDATA%\Opencluely`
- Archived planning and reference material has been moved under `docs/`

## Cleanup Rules

- Do not reintroduce provider code, local state managers, or PyQt shell files unless they are wired
  into the actual runtime again
- Keep experimental screenshots, smoke renders, and generated logs out of tracked source paths
- Prefer new runtime helpers under `src/runtime/` instead of rebuilding root-level utility modules

## Known Gaps

- The new floating bar is still mostly visual and does not yet expose functional workflows
- The restored backend under `src/backend/` is organized and preserved, but not wired into the bar yet
- No automated tests cover the PySide6 shell yet
- The repo still needs a final project license decision beyond the bundled third-party notices
