#!/usr/bin/env bash
# Isolated-wheel smoke test for a local release candidate.
#
# Builds (if needed), installs the project's wheel into a temporary virtual
# environment that does not touch the project's .venv, and exercises the
# installed `cp-validate` entry point. Dependency resolution may use the
# local uv cache; it is not part of the normal offline pytest suite.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXPECTED_VERSION="${EXPECTED_VERSION:-0.2.0b1}"
WHEEL="${1:-}"

if [[ -z "$WHEEL" ]]; then
  WHEEL="dist/cp_anndata_validator-${EXPECTED_VERSION}-py3-none-any.whl"
  if [[ ! -f "$WHEEL" ]]; then
    echo "==> Building package (uv build)"
    uv build
  fi
fi

if [[ ! -f "$WHEEL" ]]; then
  echo "error: wheel not found: $WHEEL" >&2
  exit 1
fi

# Prefer a writable base dir; ignore a stale/broken TMPDIR from the caller.
_TMP_BASE="/tmp"
if [[ -n "${TMPDIR:-}" && -d "${TMPDIR}" && -w "${TMPDIR}" ]]; then
  _TMP_BASE="$TMPDIR"
fi
SMOKE_ROOT="$(mktemp -d "${_TMP_BASE}/cp-anndata-validator-smoke.XXXXXX")"
cleanup() { rm -rf "$SMOKE_ROOT"; }
trap cleanup EXIT

echo "==> Isolated env: $SMOKE_ROOT"
echo "==> Wheel: $WHEEL"

uv venv "$SMOKE_ROOT/venv"
# Install the local wheel into the temporary environment only.
uv pip install --python "$SMOKE_ROOT/venv/bin/python" "$WHEEL"

CPV="$SMOKE_ROOT/venv/bin/cp-validate"

echo "==> cp-validate --version"
VERSION_OUT="$("$CPV" --version)"
echo "$VERSION_OUT"
test "$VERSION_OUT" = "$EXPECTED_VERSION"

echo "==> cp-validate --help"
"$CPV" --help >/dev/null

echo "==> cp-validate schema list"
LIST_OUT="$("$CPV" schema list)"
echo "$LIST_OUT"
echo "$LIST_OUT" | grep -q 'generic-cell-painting'
echo "$LIST_OUT" | grep -q 'jump-cp'

echo "==> cp-validate schema show jump-cp"
SHOW_OUT="$("$CPV" schema show jump-cp)"
echo "$SHOW_OUT" | head -n 5
echo "$SHOW_OUT" | grep -q 'jump-cp v0.2.1'

echo "==> smoke_wheel.sh OK"
