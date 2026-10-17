# testloop-benchmark

The benchmark the thesis is evaluated on (proposal بند ۵-د; roadmap milestone M2).

- `targets/*.toml`: one file per module under test, in the format `testloop` reads.
- `targets/*-mutants.json`: the module's pinned mutant set (Mutation Budget:
  at most 200 mutants, seed 0), made with `testloop mutants`.
- `manifest.toml` (M2): every source repository with its pinned commit and
  dependencies, plus a fetch step that clones them into `../_checkouts/`.

Status: one candidate so far, python-slugify at `35aca63`. Once the 15–25
modules are chosen and their mutant sets pinned, the repo is tagged
`benchmark-v1` and not edited again.
