# Audio Pipeline Spec

## Pipeline Summary

- platform target:
- input sources:
- primary transcription provider:

## Stage Breakdown

| Stage | Input | Output | Latency Budget | Failure Modes |
| --- | --- | --- | --- | --- |
| capture | mic/system audio | frames | ms | notes |

## Chunking Strategy

- frame size:
- overlap:
- dedupe:
- buffering limits:

## Reliability Rules

- device loss behavior:
- provider cooldown behavior:
- transcript recovery behavior:

## Test Matrix

| Scenario | Expected Outcome | Notes |
| --- | --- | --- |
| mic only | transcript stable | notes |
