# Contributing

Keep contributions small, explainable, and offline.

- New sets need one atomic meaning, stable ordering, a review under `docs/set_reviews/`, and an
  update to the relevant set README.
- New profiles must use catalog entries with a composable `kind`, declare a conservative
  `max_outputs`, and include tests.
- New catalog entries may only use the documented fields and kinds. References stay outside normal
  search results and profile composition.
- Do not add active HTTP behavior, web shells, destructive fixtures, archive bombs, stealth
  features, or unbounded generation.

Run:

```bash
python -m unittest discover -s tests -v
python -m compileall -q web_dict_composer tests
```
