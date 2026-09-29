# Release audit

Verification checklist for the public submission repository:

- **No raw tracking data:** No raw optical coordinates, velocities, ball trajectories, or `.bz2` feeds are included.
- **No private paths or credentials:** No local paths (`C:\...`, `/home/...`), internal repo names, API keys, or tokens exist in tracked files or Git history.
- **Fresh Git history:** Initialized in a fresh directory to prevent recovery of historical development artifacts.
- **Checksums verified:** Derived tables in `data/derived/` match the hashes recorded in `manifest.json`.
