# Brand System Spec

## Brand Core

- Brand name: Opencluely
- Brand promise: Calm, reliable live assistance for high-stakes conversations and screen-led work.
- Product category: Desktop copilot for meetings, interviews, reviews, and live problem-solving.
- Trust posture: Premium, disciplined, technically credible, and quietly confident.

## Wordmark

- Typeface: Inter
- Weight: Semibold
- Tracking: -0.07
- Usage rules:
  - The logo is wordmark-only: `Opencluely`
  - Do not add mascots, symbols, emoji, badges, or companion icons to the primary mark
  - Use Inter Semibold with optical tightness preserved; never substitute a playful or rounded font
  - Prefer white wordmark on dark shells and deep blue wordmark on soft-light surfaces
  - Minimum clear space: the width of the `O` on all sides
  - Never condense, outline, shadow, bevel, distort, or gradient-fill the wordmark

## Color System

| Role | Name | Hex | Usage |
| --- | --- | --- | --- |
| primary | Opencluely Blue | #4F86F7 | CTA, active states, highlights, focus rings |
| base light | Cloud White | #F8F8FF | Primary text on dark shells, light surfaces, wordmark on dark UI |
| shell | Deep Navy | #08111F | App background and shell base |
| panel | Midnight Glass | #0D1527 | Cards, inputs, floating panes |
| elevated panel | Ink Blue | #101B31 | Top bar, elevated controls, secondary buttons |
| hover | Slate Lift | #162544 | Hovered buttons and active surfaces |
| border | Frosted Blue Line | rgba(130, 166, 249, 0.16) | Dividers and subtle structure |
| border active | Focus Blue Line | rgba(79, 134, 247, 0.34) | Focus and selected states |
| secondary text | Muted Steel | #9FB0CC | Labels, metadata, helper text |
| success | Signal Green | #4ADE80 | Live/connected status only |

## Typography System

| Role | Typeface | Weight | Size Guidance | Notes |
| --- | --- | --- | --- | --- |
| wordmark | Inter | Semibold | 14-22 px | Tracking -0.07 |
| display | Inter | Semibold | 22-28 px | Reserved for surface titles |
| title | Inter | Semibold | 16-20 px | Cards, modal titles, key modules |
| body | Inter | Regular | 13-15 px | Default product copy |
| label | Inter | Medium | 11-13 px | Section labels, metadata, controls |
| mono | JetBrains Mono or SF Mono | Regular/Medium | 12-14 px | Code, logs, transcripts with structure |

## Visual Rules

- The shell should feel glassy, dark, and highly controlled, never toy-like.
- Surfaces use low-noise depth: deep navy foundations, thin blue borders, soft blur, restrained shadow.
- Accent blue is sparse and meaningful. It should signal intent, focus, or action, not decorate.
- Icons must be simple, line-based, and utilitarian. Avoid cute, playful, or mascot-style iconography.
- Buttons should read as tools, not pills from a consumer chat app.
- Rounded corners stay in the 10-16 px range. Avoid overly bubbly geometry.
- Loading, active, and recording states should be crisp and legible, not flashy.

## Tone Of Voice

- Do:
  - Sound calm, direct, and prepared
  - Use short operational language
  - Prefer evidence, clarity, and next-step framing
  - Write like a premium work tool, not a social app
- Do not:
  - Use slang, hype, jokes, mascots, or insider nicknames
  - Sound overly apologetic, theatrical, or salesy
  - Use vague labels like `AI Help` when a concrete verb exists
  - Over-explain obvious actions in UI chrome
- UI copy examples:
  - `Launch Session`
  - `Assist`
  - `Screen`
  - `Ask`
  - `Prep Deck`
  - `Context Brief`
  - `Live transcript will appear here...`

## Naming System

| Surface | Rule | Example |
| --- | --- | --- |
| product | Single wordmark, no suffix | Opencluely |
| surface | Noun or noun phrase | Session Launchpad |
| action | Short verb | Assist |
| persistent utility | Concrete noun | Notes |
| guided preparation | Practical noun phrase | Prep Deck |
| reusable configuration | Brief, not template | Blank Brief |
| backend or architecture term | Reserved for docs only | Context Vault |

## Feature Naming Rules

- Prefer literal nouns and verbs over metaphor.
- Use maximum two words for primary navigation and top-bar actions.
- Avoid `AI`, `smart`, `magic`, `copilot`, `buddy`, `parrot`, or mascot-adjacent language in the primary UI.
- Use `brief` for reusable session presets.
- Use `deck` only for curated prep material; do not expand it into broader knowledge storage.
- Reserve `vault` for future architecture and documentation surfaces, not current end-user chrome.

## Header And Logo Usage Rules

- The top bar must display only the `Opencluely` wordmark on the left.
- Remove the legacy product name completely from the shell header.
- Do not pair the wordmark with birds, avatars, initials, or an app icon in the main shell.
- Top-bar actions must be compact, verbal, and aligned to utility: `Assist`, `Screen`, and `Ask`.
- The top bar should stay visually lighter than the main background but darker than content cards.
- Recording and active indicators may use green, but the brand itself stays blue and white.

## Deprecated Terms

| Old Term | New Term | Status | Notes |
| --- | --- | --- | --- |
| ParakeetAI Clone | Opencluely | replace | old brand must disappear from product UI and bootstrap surfaces |
| Parakeet | Opencluely | replace | do not preserve mascot tone |
| LALA | Prep Deck | replace | removes personal and insider framing |
| Template | Brief | replace in UI | internal code may transition separately |
| AI Help | Assist | replace | too generic and weak |
| Analyze Screen | Screen | replace | keep compact in top bar |
| Chat | Ask | replace | clearer action framing |

## Final Recommendation For The LALA Replacement

- Final replacement: `Prep Deck`
- Why it wins:
  - It is concrete and memorable without sounding playful
  - It preserves the useful concept of curated preparation material
  - It does not leak personal history, school context, or insider language
  - It fits both interviews and broader live-work scenarios

## Approval Checklist

- [x] No Parakeet naming remains in target brand
- [x] LALA replacement selected
- [x] Tone is stable and reusable
- [x] Colors and typography are implementation-ready
