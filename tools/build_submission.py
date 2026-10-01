"""Build a deterministic source archive with an embedded SHA-256 manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.1.0"


def build(output):
    output = Path(output).resolve()
    if output.is_relative_to(ROOT / "src") or output.is_relative_to(ROOT / "data"):
        raise ValueError("Choose an artifact directory outside the source and data trees")
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    paths = sorted({name for name in names if name and (ROOT/name).is_file()
        and name != "SUBMISSION_COMPLETENESS_AUDIT.md" and not name.startswith(".github/")})
    files = {}
    for name in paths:
        if name.endswith((".jsonl", ".jsonl.bz2", ".h5")) or "private_cache/" in name or "private_index/" in name:
            raise ValueError(f"Private raw artifact refused: {name}")
        files[name] = (ROOT/name).read_bytes()
    manifest = {"version": VERSION, "format": "source checkout; install with pip -e .",
        "submission_ref": "ssac27-abstract-v" + VERSION,
        "files": {name: {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)} for name, content in files.items()}}
    files["SUBMISSION_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"ssac27-source-v{VERSION}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(f"fragility-v{VERSION}/{name}", date_time=(2026, 10, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[name])
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{digest}  {archive.name}\n")
    with zipfile.ZipFile(archive) as z:
        for name, spec in manifest["files"].items():
            assert hashlib.sha256(z.read(f"fragility-v{VERSION}/{name}")).hexdigest() == spec["sha256"]
    print(json.dumps({"archive": str(archive), "source_files": len(paths), "bytes": archive.stat().st_size,
        "sha256": digest, "manifest_verified": True}, indent=2))
    return archive


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "dist")
    build(ap.parse_args().output)
