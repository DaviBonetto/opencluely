# Provider Orchestration Matrix

## Provider Summary

| Provider | Role | Allowed Capabilities | Forbidden Capabilities |
| --- | --- | --- | --- |
| Groq | live transcription | STT | image workflows |
| Gemini | image and answer workflows | image, grounded answer generation | live STT |

## Routing Rules

| Use Case | Provider | Why | Fallback |
| --- | --- | --- | --- |
| live transcript | Groq | latency and volume | none/degraded |

## Key Handling Policy

- storage mechanism:
- redaction rules:
- logging rules:
- rotation guidance:

## Failure States

| Failure | User-Facing Behavior | Retry Policy | Severity |
| --- | --- | --- | --- |
| rate limit | cooldown state | backoff | med/high |

## Security Notes

- secrets must never appear in:
- diagnostics may include:
- diagnostics must exclude:
