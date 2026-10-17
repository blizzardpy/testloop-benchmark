"""Screen benchmark targets: pin each mutant set and score the module's own tests.

Needs testloop installed in the running interpreter. Writes one JSON per target
to screening/ and a summary table to screening/SUMMARY.md.

    python tools/screen.py --jobs 8            # all targets
    python tools/screen.py --only parse tomli-parser
"""

from __future__ import annotations

import argparse
import json
import time
import traceback
from pathlib import Path

from testloop.measure import measure
from testloop.mutation import MutantSet, sample_mutants
from testloop.runner import Runner
from testloop.sandbox import LocalSandbox
from testloop.target import Target

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "screening"


def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}"


def screen(path: Path, jobs: int, reruns: int, budget: int) -> dict:
    target = Target.from_toml(path)
    pinned = path.with_name(f"{target.name}-mutants.json")
    if pinned.exists():
        ms = MutantSet.load(pinned, target)
    else:
        ms = sample_mutants(target, budget=budget, seed=0)
        ms.save(pinned)
    loc = sum(1 for line in target.source().splitlines() if line.strip()
              and not line.strip().startswith("#"))
    runner = Runner(LocalSandbox(timeout=900), per_test_timeout=30)
    m = measure(target, None, ms, runner, reruns=reruns, jobs=jobs)
    row = m.to_dict()
    row.update(loc=loc, mutants_generated=ms.total_generated)
    return row


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--only", nargs="*")
    p.add_argument("--jobs", type=int, default=8)
    p.add_argument("--reruns", type=int, default=2)
    p.add_argument("--budget", type=int, default=200)
    args = p.parse_args()
    OUT.mkdir(exist_ok=True)
    for path in sorted((HERE / "targets").glob("*.toml")):
        tid = path.stem
        if args.only and tid not in args.only:
            continue
        started = time.monotonic()
        try:
            row = screen(path, args.jobs, args.reruns, args.budget)
            status = "ok"
        except Exception as exc:  # recorded, so one broken target does not stop the screen
            row, status = {"error": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc()}, "error"
        row.update(id=tid, status=status, screen_seconds=round(time.monotonic() - started, 1))
        (OUT / f"{tid}.json").write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{status:5} {tid:24} {row.get('error') or ''}"
              f"{'' if status != 'ok' else f'tests {row['tests_passed']}/{row['tests_total']} branch {pct(row['branch_coverage'])} ms {pct(row['mutation_score'])} ({row['mutants_total']}/{row['mutants_generated']}) {row['screen_seconds']}s'}",
              flush=True)
    write_summary()
    return 0


def write_summary() -> None:
    rows = [json.loads(p.read_text()) for p in sorted(OUT.glob("*.json"))]
    lines = ["| Target | Status | LOC | Tests (pass/total) | Flaky | Line % | Branch % | Mutation % | Mutants (pinned/generated) | Not covered | Time (s) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["status"] != "ok":
            lines.append(f"| {r['id']} | error: {r['error'][:80]} | | | | | | | | | {r['screen_seconds']} |")
            continue
        lines.append(f"| {r['id']} | ok | {r['loc']} | {r['tests_passed']}/{r['tests_total']} | {r['tests_flaky']} "
                     f"| {pct(r['line_coverage'])} | {pct(r['branch_coverage'])} | {pct(r['mutation_score'])} "
                     f"| {r['mutants_total']}/{r['mutants_generated']} | {r['mutants_not_covered']} | {r['screen_seconds']} |")
    (OUT / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
