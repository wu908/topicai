"""Reset the throwaway E2E data directory.

Invoked by playwright.config.ts as the backend webServer prelude:
`python e2e_reset.py && python -m uvicorn ...`. Kept as a file (not an
inline `python -c`) because cmd.exe on Windows mangles nested quotes in
inline payloads.

The target directory comes from E2E_DATA_DIR so the path stays a single
source of truth computed in the config.
"""

import os
import shutil

target = os.environ.get("E2E_DATA_DIR")
if target:
    shutil.rmtree(target, ignore_errors=True)
    os.makedirs(target, exist_ok=True)
