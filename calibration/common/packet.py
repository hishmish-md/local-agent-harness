"""Offline packet checks and single-file anonymous envelope. Python 3.9+."""
import argparse, hashlib, json, secrets, zipfile
from pathlib import Path
R = Path(__file__).resolve().parent

def manifest():
    return ''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in sorted(R.iterdir(), key=lambda path: path.name) if p.is_file() and p.name != 'SHA256SUMS')

def private(p):
    p = p.resolve()
    if any((a/'.git').exists() for a in (p,*p.parents)):
        raise SystemExit('Use a private location outside every repository')
    return p

if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    commands = cli.add_subparsers(dest='cmd', required=True)
    for cmd in ('manifest','verify'): commands.add_parser(cmd)
    pack = commands.add_parser('pack'); pack.add_argument('response',type=Path); pack.add_argument('directory',type=Path)
    relay = commands.add_parser('relay'); relay.add_argument('archive',type=Path)
    a = cli.parse_args()
    if a.cmd == 'manifest':
        import sys
        sys.stdout.buffer.write(manifest().encode()); raise SystemExit
    if (R/'SHA256SUMS').read_bytes() != manifest().encode(): raise SystemExit('Manifest mismatch; stop')
    if a.cmd == 'verify': print('SHA-256 OK')
    if a.cmd == 'pack':
        data = json.loads(private(a.response).read_text(encoding='utf-8-sig'))
        template = json.loads((R/'starter.json').read_text())
        if not isinstance(data,dict) or data.keys()!=template.keys() or not all(isinstance(data[m],dict) and data[m].keys()==template[m].keys() for m in template): raise SystemExit('Unexpected fields')
        dest = private(a.directory); dest.mkdir(parents=True,exist_ok=True)
        alias = secrets.token_hex(8)
        with zipfile.ZipFile(dest/(alias+'.zip'),'x') as z:
            z.writestr(zipfile.ZipInfo('response.json'),json.dumps({'alias':alias,'response':data},sort_keys=True,indent=2))
        print(alias)
    if a.cmd=='relay':
        with zipfile.ZipFile(private(a.archive)) as z:
            if z.namelist()!=['response.json']: raise SystemExit('Unexpected archive')
            print(z.read('response.json').decode('utf-8'))
