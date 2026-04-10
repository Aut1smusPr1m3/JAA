# Documentation Cloud Agents

This repository defines a three-agent documentation workflow to keep docs synchronized with code changes.

## Agents
- `DocSynth`: generate/update docs from source code and tests.
- `DocDrift`: detect mismatches between changed code and docs.
- `ReleaseDoc`: generate changelog/release notes from merged changes.

## Rules
- Agents must cite concrete files and symbols when writing technical docs.
- Agents must not invent features that are not present in code/tests.
- Behavior-changing PRs should trigger a doc drift check.

## Agent specs
See `.copilot/agents/` for implementation prompts and operating constraints.
