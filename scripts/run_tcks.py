"""Run every selected suite independently; never turn missing/failed tests into success."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def parse_reports(reports):
    cases=[];issues=[]
    for xml in sorted(reports.glob('TEST-*.xml')):
        try: tree=ET.parse(xml)
        except ET.ParseError as error:
            issues.append(dict(kind='REPORT_PARSE',message=str(error),report=xml.name));continue
        for test in tree.iter('testcase'):
            failure=test.find('failure'); error=test.find('error'); skip=test.find('skipped')
            problem=failure if failure is not None else error
            status='failed' if problem is not None else 'skipped' if skip is not None else 'passed'
            entry=dict(classname=test.get('classname',''),name=test.get('name',''),status=status,report=xml.name)
            if problem is not None:
                body=problem.text or problem.get('message','')
                causes=[line.strip() for line in body.splitlines() if line.strip().startswith('Caused by:')]
                message=causes[-1] if causes else problem.get('message','') or body.split('\n')[0]
                key=hashlib.sha256((problem.get('type','')+'|'+message).encode()).hexdigest()[:12]
                entry.update(issue='TCK-'+key,exception=problem.get('type',''),message=message)
                issues.append(dict(id=entry['issue'],kind='TEST_OR_DEPLOYMENT_FAILURE',message=message,
                                   test=entry['classname']+'#'+entry['name'],report=xml.name))
            cases.append(entry)
    return cases,issues


def execute(suite, run, timeout, port):
    name=suite['id']; folder=run/name;folder.mkdir(parents=True)
    reports=folder/'surefire'; log=folder/'maven.log'
    command=[shutil.which('mvn'),'-B','-ntp','-f',str(ROOT/name/'pom.xml'),'dependency:build-classpath','test',
             f'-Dmdep.outputFile={folder/"classpath.txt"}',
             f'-Dtck.reports.directory={reports}',f'-Dtck.http.port={port}']
    start=time.monotonic()
    with log.open('w',encoding='utf-8') as stream:
        process=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
                                 start_new_session=os.name!='nt')
        timed_out=False
        try: code=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            if os.name=='nt': subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=stream,stderr=stream)
            else:
                import signal
                os.killpg(process.pid,signal.SIGTERM)
            process.wait();code=124
    cases,issues=parse_reports(reports)
    counts={s:sum(c['status']==s for c in cases) for s in ['passed','failed','skipped']}
    provenance=[]
    classpath=folder/'classpath.txt'
    if classpath.exists():
        for value in classpath.read_text().strip().split(os.pathsep):
            jar=Path(value)
            if jar.is_file():
                with jar.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
                provenance.append(dict(path=str(jar),sha256=digest,bytes=jar.stat().st_size))
    (folder/'artifacts.json').write_text(json.dumps(provenance,indent=2)+'\n')
    text=log.read_text(encoding='utf-8',errors='replace')
    if timed_out: status='TIMED_OUT'
    elif not cases: status='BLOCKED_NO_RESULTS'
    elif code or counts['failed'] or issues: status='FAILED'
    elif counts['skipped']:status='INCOMPLETE_SKIPS'
    else:status='PASSED_DIAGNOSTIC'
    if code or not cases:
        errors=[line for line in text.splitlines() if '[ERROR]' in line]
        issues.append(dict(id='BUILD-'+name,kind='BUILD_OR_RUN_FAILURE',message='\n'.join(errors[-16:]) or status,report='maven.log'))
    row=dict(id=name,status=status,exitCode=code,elapsedSeconds=round(time.monotonic()-start,2),
             counts=counts,command=command,cases=cases,issues=issues)
    (folder/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    print(name,status,counts,flush=True)
    return row

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--suite',action='append');parser.add_argument('--jobs',type=int,default=1)
    parser.add_argument('--timeout',type=int,default=1800);parser.add_argument('--run-id');parser.add_argument('--port-base',type=int,default=18080);args=parser.parse_args()
    matrix=json.loads((ROOT/'matrix.json').read_text());suites=matrix['suites']
    if args.suite:
        unknown=set(args.suite)-{r['id'] for r in suites}
        if unknown:parser.error('Unknown suites: '+','.join(sorted(unknown)))
        suites=[r for r in suites if r['id'] in args.suite]
    if args.jobs<1 or args.timeout<1:parser.error('jobs and timeout must be positive')
    if args.port_base<1024 or args.port_base+len(suites)>65535:parser.error('Invalid port range')
    run_id=args.run_id or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    if Path(run_id).name!=run_id or run_id in ('.','..'):parser.error('run-id must be a directory name')
    run=ROOT/'target/runs'/run_id;run.mkdir(parents=True,exist_ok=False)
    metadata=dict(matrix=matrix,startedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  gitHead=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  gitStatus=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
                  java=subprocess.run(['java','-version'],capture_output=True,text=True).stderr,
                  maven=subprocess.run([shutil.which('mvn'),'-version'],capture_output=True,text=True).stdout,
                  matrixSha256=hashlib.sha256((ROOT/'matrix.json').read_bytes()).hexdigest())
    (run/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(execute,suite,run,args.timeout,args.port_base+i) for i,suite in enumerate(suites)]
        rows=[f.result() for f in futures]
    (run/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
    lines=['# TCK baseline '+run_id,'','Diagnostic results only. No GuicedEE implementation fixes applied.','',
           '| Suite | Status | Passed | Failed | Skipped |','| --- | --- | ---: | ---: | ---: |']
    for r in rows:lines.append(f"| {r['id']} | {r['status']} | {r['counts']['passed']} | {r['counts']['failed']} | {r['counts']['skipped']} |")
    lines+=['','A skipped or unexecuted test is not a pass. `PASSED_DIAGNOSTIC` is not certification.','',
            'Per-test records, failure signatures, commands and raw XML/logs are retained beside this file.','']
    (run/'SUMMARY.md').write_text('\n'.join(lines))
    print('Results:',run,flush=True)
    return int(any(r['status']!='PASSED_DIAGNOSTIC' for r in rows))

if __name__=='__main__':raise SystemExit(main())
