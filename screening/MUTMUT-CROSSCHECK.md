# Cross-check: testloop's mutation engine vs mutmut 3.8.0

Done 2026-10-17 (roadmap M1 open item). Same tests, same module, mutmut's own
operators and runner versus testloop's AST engine.

| Module and suite | testloop | mutmut | Note |
|---|---|---|---|
| toy `intervals.py`, strong suite | 87.5% (28/32) | 86.0% (37/43) | Agree |
| toy `intervals.py`, weak suite | 28.1% (9/32) | 51.2% (22/43) | Same ordering; mutmut also mutates assignments such as `self.lo = None`, which even weak tests trip over |
| inflection `__init__.py`, project tests | 92.0% (184/200 pinned) | 56.2% (223/397) | 169 of mutmut's 174 survivors are in `_irregular()`, which runs at import time. mutmut 3 switches mutants on per function call, so it cannot test code executed during import and reports those mutants as surviving. Excluding them, mutmut gives 97.8% (223/228) |
| slugify, jsonpointer | — | did not run | mutmut copies only the source tree into `mutants/`; these test suites need other repository files (`tools/`, `bin/`) and mutmut's stats run failed even with `also_copy` |

Reading: where both tools work, they agree closely on a strong suite and rank
suites the same way. mutmut 3 has a blind spot for import-time code that our
engine does not have, which is a further argument for the own engine besides
mutant pinning. To report in Chapter 3 under the validity of the mutation tool.
