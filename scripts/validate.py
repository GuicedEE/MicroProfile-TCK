"""Fail if the committed suite matrix silently drops tests or uses the wrong engine."""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NS={'m':'http://maven.apache.org/POM/4.0.0'}
REQUIRED={'config','health','fault-tolerance','jwt','openapi','rest-client','context-propagation','graphql',
          'reactive-messaging','reactive-streams','lra','metrics-api','metrics-rest','metrics-optional',
          'telemetry-tracing','telemetry-metrics','telemetry-logs','core-profile','cdi-lite','cdi-lang-model',
          'jakarta-rest','jsonb','jsonp','jsonp-pluggability','jakarta-inject','annotations-signature'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--inventory',default='reports/inventory.json');args=parser.parse_args()
    suites=json.loads((ROOT/'matrix.json').read_text())['suites']
    ids=[s['id'] for s in suites]
    assert len(ids)==len(set(ids)) and set(ids)==REQUIRED,'Suite matrix is incomplete or contains duplicates'
    modules={e.text for e in ET.parse(ROOT/'pom.xml').findall('m:modules/m:module',NS)}
    assert modules==REQUIRED|{'harness'},'Reactor and matrix differ'
    inventories={r['id']:r for r in json.loads((ROOT/args.inventory).read_text())}
    committed=json.loads((ROOT/'reports/inventory.json').read_text())
    assert inventories=={r['id']:r for r in committed},'Upstream inventory differs from committed coverage; review and regenerate selection'
    assert set(inventories)==REQUIRED,'Inventory is incomplete'
    for suite in suites:
        name=suite['id'];pom=ROOT/name/'pom.xml';tree=ET.parse(pom);text=pom.read_text();inventory=inventories[name]
        assert 'error' not in inventory,(name,'inventory failed')
        assert 'testFailureIgnore' not in text,(name,'failure suppression')
        assert suite['engine']=='sigtest' or '<skipTests>true' not in text,(name,'tests disabled')
        if suite.get('signature'):
            assert inventory['signatureClasses']>0
            continue
        matches=[d for d in tree.findall('m:dependencies/m:dependency',NS)
                 if d.findtext('m:groupId',namespaces=NS)==suite['group'] and d.findtext('m:artifactId',namespaces=NS)==suite['artifact']
                 and d.findtext('m:classifier',default=None,namespaces=NS)==suite.get('classifier')]
        assert matches and matches[0].findtext('m:version',namespaces=NS)==suite['version'],(name,'TCK coordinate drift')
        if name=='cdi-lite':
            assert 'cdi-lite-tck-suite-10.0.1.xml' in text
        else:
            expected={suite['factory'].replace('.','/')+'.java'} if suite.get('factory') else {c['name'].replace('.','/')+'.java' for c in inventory['candidateClasses']}
            selected={e.text for e in tree.findall('.//m:includes/m:include',NS)}
            assert expected and selected==expected,(name,'test selection differs from inventory')
        if suite.get('factory'):
            assert (ROOT/name/'src/test/java'/(suite['factory'].replace('.','/')+'.java')).exists()
        for candidate in inventory['candidateClasses']:
            for method in candidate['methods']:
                anns=method['annotations']
                if 'Lorg/junit/Test;' in anns: assert suite['engine']=='junit4',(name,'wrong JUnit engine')
                if 'Lorg/junit/jupiter/api/Test;' in anns: assert suite['engine']=='junit5',(name,'wrong Jupiter engine')
                if 'Lorg/testng/annotations/Test;' in anns: assert suite['engine']=='testng',(name,'wrong TestNG engine')
    print('Validated 26 suite modules, official coordinates, engines, factories and complete class selection.')

if __name__=='__main__':main()
