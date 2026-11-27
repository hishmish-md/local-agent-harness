#!/usr/bin/env python3
"""Check the two preview bundles without a browser, network access, or file writes.

Run: python design/qa/offline-preview-check.py [--self-test | --negative-fixture]
Exit 0: clean (or self-test passed); 1: findings; 2: invalid CLI usage.
Each bundle stands alone: relative runtime assets must exist inside it. Root-relative
URLs, <base href>, and unresolved JS asset expressions need review. Navigation links,
XML namespaces, fragment identifiers and data: URLs aren't downloads.

Limits: this smoke test inspects UTF-8 HTML/SVG/CSS/JS and common resource sinks.
It doesn't execute code, parse full CSS/JS grammars, inspect data: payloads, expand
JS-generated markup, or verify MIME, fragment IDs or browser file:// restrictions.
Aliases, escapes, module resolution and other loading APIs can defeat static checks.
External script files are checked relative to themselves; the board tab-ID + '.svg'
convention is checked explicitly. Also cold-open both previews offline in a browser
and inspect requests and interactions. A pass is not proof of zero network activity.
"""
import argparse
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


DESIGN = Path(__file__).resolve().parents[1]
SUFFIXES = {'.html', '.htm', '.svg', '.css', '.js', '.mjs'}
RESOURCE_REL = set('stylesheet icon apple-touch-icon mask-icon manifest preload modulepreload '
                   'prefetch preconnect dns-prefetch prerender import'.split())
CSS = re.compile(r'''/\*.*?(?:\*/|$)|@namespace\b[^;]*;|@import\s*["'](?P<imp>[^"']+)["']|
    \burl\(\s*(?:"(?P<dq>[^"]*)"|'(?P<sq>[^']*)'|(?P<bare>[^)]*?))\s*\)|
    "(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*' ''', re.I | re.S | re.X)
JS_TOKEN = re.compile(r'''//[^\n]*|/\*.*?(?:\*/|$)|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|
    `(?:\\.|[^`\\])*`|[\w$]+|[^\s]''', re.S | re.X)


def candidates(value):
    """Read srcset URL tokens; commas inside a data URL belong to that token."""
    while value.strip(' ,\t\r\n\f'):
        value = value.lstrip(' ,\t\r\n\f')
        url = value.split(None, 1)[0]
        value = value[len(url):]
        if url.endswith(','):
            yield url.rstrip(',')
        else:
            yield url
            value = value.partition(',')[2]


class Checker(HTMLParser):
    def __init__(self, path, root):
        super().__init__()
        self.path, self.root = path, root.resolve()
        self.issues = []
        self.block = None
        self.tab_ids = []

    def issue(self, context, message):
        self.issues.append(f'{self.path.name}:{self.getpos()[0]}: {context}: {message}')

    def asset(self, context, raw):
        value = raw.strip()
        if not value or value.startswith('#') or value.lower().startswith('data:'):
            return
        try:
            parts = urlsplit(value)
            name = unquote(parts.path)
            if parts.scheme or parts.netloc or name.startswith('/') or '\\' in name or ':' in name:
                self.issue(context, f'non-portable URL: {value}')
            elif name:
                target = (self.path.parent / name).resolve()
                if not target.is_relative_to(self.root):
                    self.issue(context, f'outside preview bundle: {value}')
                elif not target.is_file():
                    self.issue(context, f'missing file: {value}')
        except (ValueError, RuntimeError, OSError) as exc:
            self.issue(context, f'invalid URL {value!r}: {exc}')

    def css(self, text):
        for match in CSS.finditer(text):
            if match.lastgroup:
                self.asset('CSS ' + ('@import' if match.lastgroup == 'imp' else 'url'),
                           match[match.lastgroup])

    def script(self, text):
        tokens = [m[0] for m in JS_TOKEN.finditer(text) if not m[0].startswith(('//', '/*'))]
        tokens += [''] * 8  # lookahead even for an incomplete expression
        for i, t in enumerate(tokens[:-8]):
            n = i + 1
            if t in {'fetch', 'WebSocket', 'EventSource', 'Worker', 'SharedWorker', 'sendBeacon', 'importScripts', 'import'} and tokens[n] == '(':
                n += 1
            elif t in {'import', 'from'} and tokens[n][:1] in {'"', "'"}:
                pass  # static module specifier
            elif t in {'src', 'poster'} and i and tokens[i-1] == '.' and tokens[n] == '=':
                n += 1
                if (self.path == DESIGN / 'prototypes' / 'preview.html' and self.tab_ids
                        and tokens[n:n+4] == ['tab', '.', 'id', '+']
                        and tokens[n+4] in {"'.svg'", '".svg"'} and tokens[n+5] in {';', '}', ''}):
                    for board in self.tab_ids:
                        self.asset('board tab', board + '.svg')
                    continue
            elif t == 'XMLHttpRequest':
                self.issue(t, 'network API requires manual review')
                continue
            else:
                continue
            arg = tokens[n]
            if (len(arg) >= 2 and arg[0] in "'\"`" and '\\' not in arg and '${' not in arg
                    and tokens[n+1] in {')', ',', ';', '}', '', 'with', 'assert'}):
                self.asset('JS ' + t, arg[1:-1])
            else:
                self.issue('JS ' + t, 'unresolved asset expression')

    def handle_starttag(self, tag, attrs):
        a = {k: v or '' for k, v in attrs}
        if a.get('role') == 'tab' and 'id' in a:
            self.tab_ids.append(a['id'])
        if tag == 'style':
            self.block = 'style'
        if tag == 'script' and a.get('type', '').lower() in {'', 'module', 'text/javascript', 'application/javascript'}:
            self.block = 'script'
        for key, value in a.items():
            if key in {'style', 'fill', 'stroke', 'filter', 'clip-path', 'mask', 'marker-start', 'marker-mid', 'marker-end'}:
                self.css(value)
            elif key.startswith('on'):
                self.script(value)
            elif key in {'srcset', 'imagesrcset'}:
                for candidate in candidates(value):
                    self.asset(key, candidate)
            elif tag == 'base' and key == 'href':
                self.issue('base href', 'changes URL resolution; remove or review')
            elif (key in {'src', 'poster', 'background'} or (tag, key) == ('object', 'data')
                  or (key in {'href', 'xlink:href'} and tag not in {'a', 'area', 'base'}
                      and (tag != 'link' or RESOURCE_REL.intersection(a.get('rel', '').lower().split())))):
                self.asset(f'{tag}[{key}]', value)

    def handle_endtag(self, tag):
        if tag == self.block:
            self.block = None

    def handle_data(self, data):
        if self.block == 'style':
            self.css(data)
        elif self.block == 'script':
            self.script(data)


NEGATIVE = '''<svg xmlns="http://www.w3.org/2000/svg">
<a href="https://docs.invalid/"><text>Reference</text></a>
<image href="//assets.invalid/board.png"/>
<style>@import "https://assets.invalid/type.css";</style>
<script>fetch("https://api.invalid/run")</script></svg>'''


def self_test():
    here = Path(__file__).resolve().parent
    issues = scan(here / 'fixture.svg', here, NEGATIVE)
    expected = ['//assets.invalid/board.png', 'https://assets.invalid/type.css',
                'https://api.invalid/run']
    if len(issues) != len(expected) or not all(any(s in i for i in issues) for s in expected):
        raise SystemExit(f'negative fixture mismatch: {issues}')
    print('PASS: negative fixture caught three runtime references; ignored link and namespace.')


def scan(path, root, text):
    checker = Checker(path, root)
    if path.suffix.lower() == '.css':
        checker.css(text)
    elif path.suffix.lower() in {'.js', '.mjs'}:
        checker.script(text)
    else:
        checker.feed(text)
        checker.close()
    return checker.issues


def main():
    cli = argparse.ArgumentParser(description='Check static asset dependencies in both local previews.')
    modes = cli.add_mutually_exclusive_group()
    modes.add_argument('--self-test', action='store_true', help='verify embedded fixture')
    modes.add_argument('--negative-fixture', action='store_true', help='report negative fixture (exit 1)')
    args = cli.parse_args()
    if args.self_test:
        self_test()
        return 0
    issues = []
    if args.negative_fixture:
        root = DESIGN / 'qa'
        issues = scan(root / 'fixture.svg', root, NEGATIVE)
    else:
        for directory, entry in [('prototypes', 'preview.html'), ('variant-b', 'index.html')]:
            root = DESIGN / directory
            if not (root / entry).is_file():
                issues.append(f'{directory}/{entry}: missing preview entry point')
            files = sorted(p for p in root.rglob('*') if p.suffix.lower() in SUFFIXES and p.is_file())
            for path in files:
                label = path.parent.relative_to(DESIGN).as_posix()
                try:
                    if not path.resolve().is_relative_to(root.resolve()):
                        issues.append(f'{label}/{path.name}: source outside bundle')
                        continue
                    issues.extend(f'{label}/{s}' for s in scan(path, root, path.read_text(encoding='utf-8-sig')))
                except (OSError, UnicodeError) as exc:
                    issues.append(f'{label}/{path.name}: {exc}')
            print(f'{directory}: checked {len(files)} source files')
    for issue in issues:
        print(issue)
    print(f'{"FAIL" if issues else "PASS"}: {len(issues)} static asset findings')
    return int(bool(issues))


if __name__ == '__main__':
    raise SystemExit(main())
