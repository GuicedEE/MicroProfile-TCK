"""Inventory official binary TCKs without executing or rewriting their tests."""
import argparse
import hashlib
import json
import struct
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_ANNOTATIONS = {'Lorg/testng/annotations/Test;', 'Lorg/junit/Test;', 'Lorg/junit/jupiter/api/Test;',
                    'Lorg/junit/jupiter/params/ParameterizedTest;', 'Lorg/testng/annotations/Factory;'}

class Reader:
    def __init__(self, data): self.data, self.pos = data, 0
    def take(self, n):
        value = self.data[self.pos:self.pos+n]
        if len(value) != n: raise ValueError('Truncated class file')
        self.pos += n
        return value
    def u1(self): return self.take(1)[0]
    def u2(self): return struct.unpack('>H', self.take(2))[0]
    def u4(self): return struct.unpack('>I', self.take(4))[0]

def parse_class(data):
    r = Reader(data)
    if r.u4() != 0xcafebabe: raise ValueError('Not a JVM class')
    r.take(4)
    pool = [None] * r.u2()
    i = 1
    while i < len(pool):
        tag = r.u1()
        if tag == 1: pool[i] = r.take(r.u2()).decode('utf-8', errors='replace')
        elif tag in (7, 8, 16, 19, 20): pool[i] = r.u2()
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18): r.take(4)
        elif tag in (5, 6): r.take(8); i += 1
        elif tag == 15: r.take(3)
        else: raise ValueError(f'Unknown constant pool tag {tag}')
        i += 1
    access, name, parent = r.u2(), r.u2(), r.u2()
    r.take(2 * r.u2())
    def annotations(blob):
        a = Reader(blob)
        def value():
            tag = chr(a.u1())
            if tag == 'e': a.take(4)
            elif tag == '@': annotation()
            elif tag == '[':
                for _ in range(a.u2()): value()
            else: a.take(2)
        def annotation():
            kind = pool[a.u2()]
            for _ in range(a.u2()): a.take(2); value()
            return kind
        return [annotation() for _ in range(a.u2())]
    def attributes():
        found = []
        for _ in range(r.u2()):
            kind, body = pool[r.u2()], r.take(r.u4())
            if kind in ('RuntimeVisibleAnnotations', 'RuntimeInvisibleAnnotations'): found.extend(annotations(body))
        return found
    for _ in range(r.u2()): r.take(6); attributes()
    methods = []
    for _ in range(r.u2()):
        flags, method, descriptor = r.u2(), pool[r.u2()], pool[r.u2()]
        anns = attributes()
        if TEST_ANNOTATIONS.intersection(anns): methods.append(dict(name=method,descriptor=descriptor,annotations=anns))
    anns = attributes()
    return dict(name=pool[pool[name]].replace('/', '.'), parent=pool[pool[parent]].replace('/', '.') if parent else None,
                abstract=bool(access & 0x0600), annotations=anns, methods=methods)

def artifact(suite):
    if suite.get('distribution'):
        path = ROOT/'target/core-profile/core-profile-tck-10.0.1/artifacts'/f"{suite['artifact']}-10.0.1.jar"
        if not path.exists(): raise FileNotFoundError('Run scripts/prepare_core.py first')
        return path, suite['distribution']
    suffix = '-'+suite['classifier'] if suite.get('classifier') else ''
    relative = '/'.join([suite['group'].replace('.', '/'), suite['artifact'], suite['version'],
                         suite['artifact'] + '-' + suite['version'] + suffix + '.jar'])
    path = ROOT/'target'/'upstream'/relative
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(urllib.request.urlopen('https://repo.maven.apache.org/maven2/'+relative, timeout=60).read())
    return path, 'https://repo.maven.apache.org/maven2/'+relative

def inventory(suite):
    if suite.get('signature'):
        path=ROOT/suite['signature']
        return dict(id=suite['id'],signature=suite['signature'],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    candidateClasses=[],declaredTestMethodCount=0,
                    signatureClasses=sum(line.startswith('CLSS ') for line in path.read_text().splitlines()))
    path, url = artifact(suite)
    with zipfile.ZipFile(path) as jar:
        classes = [parse_class(jar.read(n)) for n in jar.namelist() if n.endswith('.class') and not n.startswith('META-INF/') and n != 'module-info.class']
        by_name = {c['name']:c for c in classes}
        def inherited(c, seen=None):
            seen = set() if seen is None else seen
            if c['name'] in seen: return False
            seen.add(c['name'])
            return bool(c['methods'] or TEST_ANNOTATIONS.intersection(c['annotations']) or
                        c['parent'] in by_name and inherited(by_name[c['parent']], seen))
        candidates = [c for c in classes if not c['abstract'] and inherited(c)]
        return dict(id=suite['id'], coordinate=f"{suite['group']}:{suite['artifact']}:{suite['version']}"+(':'+suite['classifier'] if suite.get('classifier') else ''),
                    url=url, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), classCount=len(classes),
                    candidateClasses=candidates, declaredTestMethodCount=sum(len(c['methods']) for c in classes),
                    suiteResources=[n for n in jar.namelist() if n.endswith('.xml') and 'testng' in n.lower()],
                    note='Static candidates include factories and inherited tests; runtime data providers determine invocation counts.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='reports/inventory.json');args=parser.parse_args()
    results=[]
    for suite in json.loads((ROOT/'matrix.json').read_text())['suites']:
        try:
            row=inventory(suite)
            print(suite['id'], len(row['candidateClasses']), 'candidate classes', flush=True)
        except Exception as error:
            row=dict(id=suite['id'],status='INVENTORY_BLOCKED',error=str(error)); print(row,flush=True)
        results.append(row)
    path=ROOT/args.output;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(results,indent=2)+'\n')
    return int(any('error' in row for row in results))

if __name__ == '__main__': raise SystemExit(main())
