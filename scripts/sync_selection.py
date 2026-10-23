"""Generate explicit upstream test-class selection, including nested OpenAPI classes."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    inventories={r['id']:r for r in json.loads((ROOT/'reports/inventory.json').read_text())}
    matrix=json.loads((ROOT/'matrix.json').read_text())
    for suite in matrix['suites']:
        name=suite['id']
        if name=='cdi-lite' or suite.get('signature'):continue  # official selection / signature engine
        classes=[suite['factory']] if suite.get('factory') else [c['name'] for c in inventories[name]['candidateClasses']]
        if not classes:raise ValueError(f'{name} has no test entry point')
        includes='<includes>'+''.join('<include>'+c.replace('.','/')+'.java</include>' for c in classes)+'</includes>'
        # Override Surefire's default nested-class exclusion. package-info is metadata, never a test.
        includes+='<excludes><exclude>**/package-info.class</exclude></excludes>'
        p=ROOT/name/'pom.xml';text=p.read_text()
        text=re.sub(r'<includes>.*?</includes>','',text,flags=re.S)
        text=re.sub(r'<excludes>.*?</excludes>','',text,flags=re.S)
        text=text.replace('<configuration><dependenciesToScan>','<configuration>'+includes+'<dependenciesToScan>')
        p.write_text(text)

if __name__=='__main__':main()
