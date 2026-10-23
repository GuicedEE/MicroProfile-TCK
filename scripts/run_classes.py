"""Run an entire inventoried suite in bounded Maven processes, one per selected class."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

from run_tcks import ROOT, execute


def selections(suite, inventory):
    if suite.get('officialSelection') or suite.get('signature'):
        raise ValueError('Official XML/group and signature suites require run_tcks.py; class filtering would change their contract')
    return [suite['factory']] if suite.get('factory') else sorted(c['name'] for c in inventory['candidateClasses'])


def aggregate(suite, rows, elapsed):
    if not rows: raise ValueError('Cannot report success for an empty class execution set')
    cases=[];issues=[]
    for row in rows:
        prefix='classes/'+row['selectedClass']+'/surefire/'
        cases.extend(dict(c,report=prefix+c['report']) for c in row['cases'])
        issues.extend(dict(i,selectedClass=row['selectedClass'],
                           report='classes/'+row['selectedClass']+'/'+('surefire/' if i['report'].endswith('.xml') else '')+i['report']) for i in row['issues'])
    counts={key:sum(r['counts'][key] for r in rows) for key in ['passed','failed','skipped']}
    statuses={r['status'] for r in rows}
    status=next((s for s in ['TIMED_OUT','BLOCKED_NO_RESULTS','FAILED','INCOMPLETE_SKIPS'] if s in statuses),'PASSED_DIAGNOSTIC')
    return dict(id=suite['id'],status=status,exitCode=int(status!='PASSED_DIAGNOSTIC'),elapsedSeconds=round(elapsed,2),
                counts=counts,cases=cases,issues=issues,command=[r['command'] for r in rows],
                executionMode='separate-class-processes',selectedClasses=[r['selectedClass'] for r in rows],
                classResults=[{k:r[k] for k in ['selectedClass','status','exitCode','counts','elapsedSeconds']} for r in rows])


def execute_classes(suite,run,timeout,port,jobs):
    inventory=next(r for r in json.loads((ROOT/'reports/inventory.json').read_text()) if r['id']==suite['id'])
    classes=selections(suite,inventory)
    folder=run/suite['id'];folder.mkdir();(folder/'classes').mkdir()
    command=[shutil.which('mvn'),'-B','-ntp','-f',str(ROOT/suite['id']/'pom.xml'),
             'dependency:build-classpath','test-compile',f'-Dmdep.outputFile={folder/"classpath.txt"}']
    try:
        with (folder/'prepare.log').open('w') as stream:
            subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=600)
    except (subprocess.SubprocessError,OSError) as error:
        result=dict(id=suite['id'],status='BLOCKED_NO_RESULTS',exitCode=1,elapsedSeconds=0,
                    counts=dict(passed=0,failed=0,skipped=0),cases=[],command=command,
                    issues=[dict(id='PREPARE-'+suite['id'],kind='BUILD_OR_RUN_FAILURE',message=str(error),report='prepare.log')],
                    selectedClasses=classes,classResults=[],executionMode='separate-class-processes')
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    artifacts=[]
    import os
    for value in (folder/'classpath.txt').read_text().strip().split(os.pathsep):
        path=Path(value)
        if path.is_file(): artifacts.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (folder/'artifacts.json').write_text(json.dumps(artifacts,indent=2)+'\n')
    start=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures=[pool.submit(execute,suite,folder/'classes',timeout,port+i,name) for i,name in enumerate(classes)]
        rows=[f.result() for f in futures]
    result=aggregate(suite,rows,time.monotonic()-start)
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--suite',required=True);parser.add_argument('--run-id',required=True)
    parser.add_argument('--jobs',type=int,default=2);parser.add_argument('--timeout',type=int,default=240)
    parser.add_argument('--port-base',type=int,default=23080);args=parser.parse_args()
    if args.jobs<1 or args.timeout<1: parser.error('jobs and timeout must be positive')
    if Path(args.run_id).name!=args.run_id or args.run_id in ('.','..'): parser.error('Invalid run ID')
    matrix=json.loads((ROOT/'matrix.json').read_text())
    suite=next((s for s in matrix['suites'] if s['id']==args.suite),None)
    if suite is None: parser.error('Unknown suite')
    inventory=next(r for r in json.loads((ROOT/'reports/inventory.json').read_text()) if r['id']==args.suite)
    classes=selections(suite,inventory)
    if not classes or len(classes)!=len(set(classes)): parser.error('Empty or duplicate class selection')
    if args.port_base<1024 or args.port_base+len(classes)>65535: parser.error('Invalid port range')
    run=ROOT/'target/runs'/args.run_id;run.mkdir(parents=True,exist_ok=False)
    metadata=dict(matrix=matrix,startedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  gitHead=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  gitStatus=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
                  java=subprocess.run(['java','-version'],capture_output=True,text=True).stderr,
                  maven=subprocess.run([shutil.which('mvn'),'-version'],capture_output=True,text=True).stdout,
                  matrixSha256=hashlib.sha256((ROOT/'matrix.json').read_bytes()).hexdigest(),
                  selectedClasses=classes,classTimeoutSeconds=args.timeout)
    (run/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n')
    result=execute_classes(suite,run,args.timeout,args.port_base,args.jobs)
    rows=result['classResults']
    (run/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    lines=['# Isolated class run: '+args.suite,'',
           'Every inventoried class was selected. Timeouts and missing results remain incomplete.','',
           '| Class | Status | Passed | Failed | Skipped |','| --- | --- | ---: | ---: | ---: |']
    for r in rows: lines.append(f"| {r['selectedClass']} | {r['status']} | {r['counts']['passed']} | {r['counts']['failed']} | {r['counts']['skipped']} |")
    (run/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    print('Results:',run,result['status'],result['counts'])
    return result['exitCode']


if __name__=='__main__': raise SystemExit(main())
