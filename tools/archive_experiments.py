"""Copy an audited snapshot of the local AgentDojo experiments into docs/data.

Usage:
  python tools/archive_experiments.py --agentdojo-root PATH --recovery-root PATH
The source files are copied byte-for-byte. The source directories are never modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path

KEY_PATTERNS = {
    "OpenAI-style key": re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(rb"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    "Slack token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
    "AWS key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_copy(source: Path, target: Path) -> str:
    if not source.is_file():
        raise FileNotFoundError(source)
    payload = source.read_bytes()
    matches = [name for name, pattern in KEY_PATTERNS.items() if pattern.search(payload)]
    if matches:
        raise ValueError(f"Credential-like content in {source.name}: {', '.join(matches)}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def bool_value(value: str) -> bool | None:
    lowered = str(value).lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def archive(agentdojo: Path, recovery: Path, out: Path) -> None:
    runs = agentdojo / "runs"
    attack_roots = [
        runs / "repro_deepseek_workspace_all_attacks_v0135/workspace_v122_direct_injecagent_20260912T150608Z",
        runs / "repro_deepseek_slack_all_attacks_v0135/slack4_v0135_20260910T054558Z",
        runs / "repro_deepseek_banking_all_attacks_v0122",
        runs / "repro_deepseek_banking_v0122_144",
        runs / "repro_deepseek_travel_all_attacks_v0135/travel4_v0135_20260910T071508Z",
    ]
    selected: dict[tuple[str, str, str, str], dict[str, str]] = {}
    csv_files: list[Path] = []
    for root in attack_roots:
        for csv_path in sorted(root.rglob("*results.csv")):
            suite = next(name for name in ("workspace", "slack", "banking", "travel") if name in str(root))
            attack = next(
                (part for part in csv_path.parts if part in
                 ("direct", "injecagent", "ignore_previous", "important_instructions", "system_message")),
                "important_instructions" if "banking_v0122_144" in str(root) else None,
            )
            if attack is None:
                continue
            csv_files.append(csv_path)
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    if bool_value(row.get("injection_goal_achieved", "")) is None or row.get("infra_error"):
                        continue
                    key = (suite, attack, row["user_task"], row["injection_task"])
                    selected[key] = row

    attack_index = []
    for (suite, attack, user_task, injection_task), row in sorted(selected.items()):
        source = Path(row["trace_path"])
        if not source.is_file():
            raise FileNotFoundError(source)
        rel = Path("agentdojo/attack-trajectories") / suite / attack / user_task / f"{injection_task}.json"
        digest = checked_copy(source, out / rel)
        attack_index.append({
            "suite": suite, "attack": attack, "user_task": user_task,
            "injection_task": injection_task, "utility": bool_value(row["utility"]),
            "checker_positive": bool_value(row["injection_goal_achieved"]),
            "sha256": digest, "path": rel.as_posix(),
        })
    if len(attack_index) != 2820:
        raise ValueError(f"Expected 2820 canonical attack trajectories, found {len(attack_index)}")

    for source in csv_files:
        rel = source.relative_to(runs)
        checked_copy(source, out / "agentdojo/run-results" / rel)
    benign_roots = {
        "workspace": runs / "repro_deepseek_workspace/20260828T103746Z/raw_traces",
        "slack": runs / "repro_deepseek_slack/20260828T115535Z/raw_traces",
        "banking": runs / "repro_deepseek_banking_benign/20260908T122604Z/raw_traces",
        "travel": runs / "repro_deepseek_travel_benign/20260908T122610Z/raw_traces",
    }
    benign_index = []
    for suite, root in benign_roots.items():
        for source in sorted(root.rglob("*.json")):
            user_task = next(part for part in source.parts if part.startswith("user_task_"))
            rel = Path("agentdojo/benign-trajectories") / suite / f"{user_task}.json"
            digest = checked_copy(source, out / rel)
            benign_index.append({"suite": suite, "user_task": user_task,
                                 "sha256": digest, "path": rel.as_posix()})
    if len(benign_index) != 97:
        raise ValueError(f"Expected 97 benign trajectories, found {len(benign_index)}")

    historical = runs / "repro_deepseek_slack_ignore_previous/20260908T151138Z"
    historical_index = []
    with (historical / "slack_ignore_previous_results.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            source = Path(row["trace_path"])
            rel = (Path("agentdojo/historical/slack-ignore-previous-v1.1.1/trajectories")
                   / row["user_task"] / f"{row['injection_task']}.json")
            digest = checked_copy(source, out / rel)
            historical_index.append({
                "user_task": row["user_task"],
                "injection_task": row["injection_task"],
                "utility": bool_value(row["utility"]),
                "checker_positive": bool_value(row["injection_goal_achieved"]),
                "sha256": digest,
                "path": rel.as_posix(),
            })
    if len(historical_index) != 105:
        raise ValueError(f"Expected 105 historical Slack trajectories, found {len(historical_index)}")
    hist_dir = Path("agentdojo/historical/slack-ignore-previous-v1.1.1")
    for filename in ("slack_ignore_previous_results.csv",
                     "slack_ignore_previous_summary.csv", "repro_manifest.json"):
        checked_copy(historical / filename, out / hist_dir / filename)
    write_json(out / hist_dir / "index.json", historical_index)

    for source, rel in [
        (agentdojo / "version_manifest.json", Path("agentdojo/version_manifest.json")),
        (runs / "agentdojo_deepseek_reproduction_report_20260916/EXPERIMENT_REPORT.md",
         Path("agentdojo/EXPERIMENT_REPORT.md")),
        (runs / "incident_triage_20260914/incident_triage.jsonl",
         Path("triage/incident_triage.jsonl")),
        (runs / "incident_triage_20260914/incident_triage_summary.md",
         Path("triage/incident_triage_summary.md")),
        (runs / "recovery_opportunity_characterization_20260914/recovery_opportunity_characterization.jsonl",
         Path("triage/recovery_opportunity_characterization.jsonl")),
    ]:
        checked_copy(source, out / rel)

    stage3c = recovery / "artifacts/stage3c"
    for source in sorted(stage3c.glob("*.json")):
        checked_copy(source, out / "recovery-pilot/summaries" / source.name)
    recovery_index = []
    for source in sorted((stage3c / "runs").rglob("c3_run_001.json")):
        rel_run = source.relative_to(stage3c / "runs")
        result_rel = Path("recovery-pilot/runs") / rel_run
        snapshot = source.with_name("c3_run_001.final_environment.json")
        snapshot_rel = result_rel.with_name(snapshot.name)
        result_hash = checked_copy(source, out / result_rel)
        snapshot_hash = checked_copy(snapshot, out / snapshot_rel)
        record = json.loads(source.read_text(encoding="utf-8"))
        recovery_index.append({
            "incident_id": record["trajectory_id"], "policy": record["policy"],
            "benchmark_utility": record["benchmark_utility"],
            "further_harm_occurred": record["further_harm_occurred"],
            "repair_outcome": record["repair_outcome"], "task_outcome": record["task_outcome"],
            "execution_error": record["execution_error"],
            "result_sha256": result_hash, "final_environment_sha256": snapshot_hash,
            "result_path": result_rel.as_posix(),
            "final_environment_path": snapshot_rel.as_posix(),
        })
    if len(recovery_index) != 95:
        raise ValueError(f"Expected 95 recovery results, found {len(recovery_index)}")
    manifest = {
        "schema_version": 1,
        "scope": "AgentDojo DeepSeek reproduction and Stage-3C recovery pilot",
        "attack_trajectories": len(attack_index),
        "main_attack_trajectories": sum(x["attack"] != "system_message" for x in attack_index),
        "checker_positive_main": sum(x["checker_positive"] is True and x["attack"] != "system_message" for x in attack_index),
        "benign_trajectories": len(benign_index),
        "historical_slack_trajectories": len(historical_index),
        "recovery_results": len(recovery_index),
        "recovery_snapshots": len(recovery_index),
        "attack_by_suite": dict(sorted(Counter(x["suite"] for x in attack_index if x["attack"] != "system_message").items())),
        "files": {
            "attack_index": "agentdojo/attack-index.json",
            "benign_index": "agentdojo/benign-index.json",
            "historical_slack_index": "agentdojo/historical/slack-ignore-previous-v1.1.1/index.json",
            "recovery_index": "recovery-pilot/run-index.json",
        },
    }
    write_json(out / "agentdojo/attack-index.json", attack_index)
    write_json(out / "agentdojo/benign-index.json", benign_index)
    write_json(out / "recovery-pilot/run-index.json", recovery_index)
    write_json(out / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agentdojo-root", type=Path, required=True)
    parser.add_argument("--recovery-root", type=Path, required=True)
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).resolve().parents[1] / "docs/data")
    args = parser.parse_args()
    archive(args.agentdojo_root, args.recovery_root, args.out)

