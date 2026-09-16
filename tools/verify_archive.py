"""Verify the published raw-file indexes and unchanged source documents."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
data = repo / "docs/data"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_index(name: str, hash_field: str, path_field: str) -> int:
    rows = json.loads((data / name).read_text(encoding="utf-8"))
    for row in rows:
        path = data / row[path_field]
        if not path.is_file() or digest(path) != row[hash_field]:
            raise ValueError(f"Missing or changed: {row[path_field]}")
    return len(rows)


manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
assert check_index("agentdojo/attack-index.json", "sha256", "path") == manifest["attack_trajectories"]
assert check_index("agentdojo/benign-index.json", "sha256", "path") == manifest["benign_trajectories"]
results = json.loads((data / "recovery-pilot/run-index.json").read_text(encoding="utf-8"))
for row in results:
    for path_field, hash_field in (
        ("result_path", "result_sha256"),
        ("final_environment_path", "final_environment_sha256"),
    ):
        path = data / row[path_field]
        if not path.is_file() or digest(path) != row[hash_field]:
            raise ValueError(f"Missing or changed: {row[path_field]}")
assert len(results) == manifest["recovery_results"]
sources = json.loads((repo / "docs/source/manifest.json").read_text(encoding="utf-8"))
readme = (repo / "README.md").read_bytes()
for row in sources:
    source = repo / "docs/source" / row["name"]
    payload = source.read_bytes()
    if hashlib.sha256(payload).hexdigest() != row["sha256"] or payload not in readme:
        raise ValueError(f"Source document changed or absent from README: {row['name']}")
print(f"OK: {manifest['attack_trajectories']} attack, {manifest['benign_trajectories']} benign, {len(results)} recovery result/snapshot pairs, {len(sources)} source documents")

