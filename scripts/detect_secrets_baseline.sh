#!/bin/bash
# Single source of truth for detect-secrets arguments.
#
# Usage:
#   scripts/detect_secrets_baseline.sh scan   # Regenerate .secrets.baseline
#   scripts/detect_secrets_baseline.sh        # Check files (called by pre-commit)
#
set -e

DETECT_SECRETS_ARGS=(
    --disable-plugin
    AbsolutePathDetectorExperimental
    --exclude-files '\.secrets..*'
    --exclude-files '\.git.*'
    --exclude-files '\.pre-commit-config\.yaml'
    --exclude-files '\.mypy_cache'
    --exclude-files '\.pytest_cache'
    --exclude-files '\.tox'
    --exclude-files '\.venv'
    --exclude-files 'venv'
    --exclude-files 'dist'
    --exclude-files 'build'
    --exclude-files '.*\.egg-info'
    --exclude-files '.*/test/.*'
    --exclude-files '.*/test/data/.*'
    --exclude-files '.*/tests/data/.*'
    --exclude-files '.*/test.*/data/.*'
    --exclude-files '.*/.*test.*/data/.*'
    --exclude-files 'src/.*/test/data/.*'
    --exclude-files 'tests/data/.*'
)

if [ "$1" = "scan" ]; then
    detect-secrets scan "${DETECT_SECRETS_ARGS[@]}" > .secrets.baseline
    echo "Updated .secrets.baseline"
else
    # Called by pre-commit; remaining args are the staged filenames
    detect-secrets-hook "${DETECT_SECRETS_ARGS[@]}" --baseline .secrets.baseline "$@"
fi
