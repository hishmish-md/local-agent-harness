"""Check validator.py's current zero-explicit-import baseline without running it.

Only import and from-import statements in this file's target are inspected.
Dynamic imports, injected callbacks, dependencies and runtime I/O are not checked.
"""

import ast
import sys
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "validator.py"


def explicit_imports(source, filename):
    tree = ast.parse(source, filename=filename)
    return sorted(
        (node.lineno, ast.unparse(node))
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )


def main():
    control = "def example():\n    import socket as net\n    from urllib import request\n"
    expected = [(2, "import socket as net"), (3, "from urllib import request")]
    if explicit_imports(control, "<negative control>") != expected:
        print("ERROR: negative control did not flag both nested imports", file=sys.stderr)
        return 2
    print("Negative control: both synthetic imports flagged (source not executed).")

    try:
        findings = explicit_imports(TARGET.read_bytes(), str(TARGET))
    except (OSError, SyntaxError, ValueError) as exc:
        print(f"ERROR: cannot audit {TARGET}: {exc}", file=sys.stderr)
        return 2
    if findings:
        for line, statement in findings:
            print(f"{TARGET}:{line}: unexpected explicit import: {statement}", file=sys.stderr)
        return 1
    print(f"{TARGET}: no explicit import statements found.")
    print("Static check only; dynamic imports, callbacks and runtime network activity are untested.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
