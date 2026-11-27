# Offline integration checks

Run from the repository root with Python 3. The second discovery command is necessary: the first does not recurse into `checks/`.

```sh
python -B -m unittest discover -s workstreams/integration -p 'test_*.py' -v
python -B -m unittest discover -s workstreams/integration/checks -p 'test_*.py' -v
python -B workstreams/integration/checks/check_offline_imports.py
```

The first suite covers selection, waits, cancellation and consent. The second covers decision combinations and deadline edge cases. Dispatch records an in-memory fixture event, not a desktop action. The static check rejects explicit imports in the validator; it is not a runtime isolation test.
