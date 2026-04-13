# Windows Bootstrap Audit

Audit target: `scripts/windows/bootstrap.ps1`.

## Scope reviewed
- Python launcher detection and compatibility checks.
- Virtual environment creation/reuse behavior.
- Dependency install flow (core, optional, dev).
- ArcWelder provisioning and failure conditions.
- Smoke checks and optional test execution path.

## Verified behaviors
- Fails fast outside Windows (`OS` guard).
- Validates Python launcher candidates and version-compatible invocation.
- Creates venv when missing, reuses when present.
- Installs `requirements.txt` always.
- Installs `requirements-optional.txt` when `InstallOpen3D` is enabled (default true).
- Installs `requirements-dev.txt` when `InstallDev` is set.
- Enforces ArcWelder presence via local path or URL provisioning.
- Runs smoke import checks and optional pytest execution.

## Error handling quality
- Strong explicit hard-fail behavior via `$ErrorActionPreference = "Stop"`.
- Clear user-facing messages for common setup failures.
- Script exits on unresolved prerequisites instead of silently degrading.

## Gaps and follow-up recommendations
1. ArcWelder URL download has no checksum/signature verification.
2. No retry/backoff around network fetch for ArcWelder URL path.
3. Test execution path depends on `-InstallDev`; this is intentional but should stay clearly documented.
4. No dedicated CI job executes the PowerShell bootstrap end-to-end on Windows runners yet.

## Current status
- Script is functionally complete for current CLI-first installer strategy.
- Residual risk is concentrated in binary-download trust verification and full CI execution parity.
