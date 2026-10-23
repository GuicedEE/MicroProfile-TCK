"""Keep a durable, explicit composite baseline without copying upstream binaries into Git."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='append',required=True)
    parser.add_argument('--output',default='reports/baseline-2026-10-23');args=parser.parse_args()
    matrix=json.loads((ROOT/'matrix.json').read_text());inventories={r['id']:r for r in json.loads((ROOT/'reports/inventory.json').read_text())}
    chosen={}
    for run_name in args.run:
        directory=ROOT/'target/runs'/run_name
        for path in directory.glob('*/result.json'):
            result=json.loads(path.read_text());result['run']=run_name;chosen[result['id']]=result
    missing={r['id'] for r in matrix['suites']}-set(chosen)
    if missing:raise ValueError('No completed run record for: '+', '.join(sorted(missing)))
    out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True)
    summaries=[];findings={};cases=[];provenance=[]
    for suite in matrix['suites']:
        r=chosen[suite['id']];inventory=inventories[suite['id']]
        observed={c['classname'] for c in r['cases']}
        candidates={c['name'] for c in inventory['candidateClasses']}
        row={k:r[k] for k in ['id','run','status','exitCode','elapsedSeconds','counts']}
        row['upstreamCandidateClasses']=len(candidates)
        row['unobservedCandidateClasses']=sorted(candidates-observed)
        row['selection']=suite.get('officialSelection') or suite.get('factory') or suite.get('signature') or 'All inventoried concrete test classes'
        row['coverageNote']='Unobserved classes are not counted as passed; factories and official CDI Lite groups change the execution set.'
        summaries.append(row)
        for case in r['cases']:cases.append(dict(suite=r['id'],run=r['run'],**case))
        for issue in r['issues']:
            key=issue.get('id') or 'REPORT-'+r['id']
            if key not in findings:findings[key]=dict(id=key,state='OPEN',kind=issue['kind'],message=issue['message'],occurrences=[])
            findings[key]['occurrences'].append(dict(suite=r['id'],run=r['run'],test=issue.get('test'),report=issue['report']))
        raw=ROOT/'target/runs'/r['run']/r['id']
        provenance.append(dict(suite=r['id'],run=r['run'],command=r['command'],
                               rawFiles=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                                         for p in sorted(raw.rglob('*')) if p.is_file() and p.suffix in ['.xml','.log','.json','.dump','.dumpstream','.txt']]))
    environments={name:json.loads((ROOT/'target/runs'/name/'environment.json').read_text()) for name in sorted({r['run'] for r in summaries})}
    (out/'environments.json').write_text(json.dumps(environments,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    (out/'findings.json').write_text(json.dumps(list(findings.values()),indent=2)+'\n')
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (out/'cases.jsonl').write_text(''.join(json.dumps(c)+'\n' for c in cases))
    for source in ['matrix.json','reports/inventory.json']:
        (out/Path(source).name).write_bytes((ROOT/source).read_bytes())
    lines=['# Baseline: 23 October 2026','','GuicedEE 2.4.1; Java 25. No GuicedEE implementation fixes applied.','',
           'This is a composite diagnostic baseline. Each suite names its exact run; corrected harness runs replace earlier wiring failures. '
           'Raw test counts include lifecycle/configuration entries emitted by the upstream test engines. They are not a count of specification assertions.','',
           '| Suite | Status | Passed | Failed | Skipped |','| --- | --- | ---: | ---: | ---: |']
    for row in summaries:lines.append(f"| {row['id']} | {row['status']} | {row['counts']['passed']} | {row['counts']['failed']} | {row['counts']['skipped']} |")
    lines+=['','## Tracking records','',
            '- [Per-test records](cases.jsonl): every reported test/lifecycle result.',
            '- [Open findings](findings.json): failure signatures and affected tests; no failures have been waived.',
            '- [Coverage](summary.json): unobserved classes, factory/group selections, status and run provenance.',
            '- [Upstream inventory](inventory.json): artifact coordinates, checksums and annotated methods.',
            '- [Evidence hashes](provenance.json): exact commands and hashes of raw reports retained under `target/runs/`.',
            '- [Run environments](environments.json): Java, Maven, matrix and working-tree state captured when each run began.',
            '- [Work register](../WORK_REGISTER.md): shared harness and runtime investigation items.','',
            'All results are diagnostic. The embedded adapter has deployment-isolation limitations; blocked, skipped and unobserved tests prevent a compatibility claim.','']
    interventions=[]
    for row in summaries:
        raw=ROOT/'target/runs'/row['run']/row['id']
        for note in sorted(raw.glob('*-timeout.txt')):
            interventions.append(f"- {row['id']}: {note.read_text().strip()}")
    if interventions: lines+=['## Run interventions','']+interventions+['']
    (out/'README.md').write_text('\n'.join(lines))
    print(len(summaries),'suites;',len(cases),'reported entries;',len(findings),'open failure signatures')

if __name__=='__main__':main()
