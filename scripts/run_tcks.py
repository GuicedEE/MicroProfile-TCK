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


def execute(suite, run, timeout, port, test_class=None, suite_xml=None, jvm_args_file=None):
    name=suite['id']; folder=run/(test_class or name);folder.mkdir(parents=True)
    reports=folder/'surefire'; log=folder/'maven.log'
    command=[shutil.which('mvn'),'-B','-ntp','-f',str(ROOT/name/'pom.xml'),'dependency:build-classpath','test',
             f'-Dmdep.outputFile={folder/"classpath.txt"}',
             f'-Dtck.reports.directory={reports}',f'-Dtck.http.port={port}']
    if test_class:
        # The caller compiles once before parallel class runs. Shared target output is read-only here.
        command=[shutil.which('mvn'),'-B','-ntp','-f',str(ROOT/name/'pom.xml'),'surefire:test',
                 f'-Dtest={test_class}',f'-Dtck.reports.directory={reports}',f'-Dtck.http.port={port}']
        if suite_xml:
            command.remove(f'-Dtest={test_class}')
            command.append(f'-Dtck.cdi.suite={suite_xml}')
    if jvm_args_file: command.append(f'-Dtck.jvm.args=@"{Path(jvm_args_file).as_posix()}"')
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
                try: os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError: pass
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired: pass
                # Kill surviving children even if Maven already exited after TERM.
                try: os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError: pass
            process.wait(timeout=10);code=124
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
    if test_class: row['selectedClass']=test_class
    (folder/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    print(test_class or name,status,counts,flush=True)
    return row

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--suite',action='append');parser.add_argument('--jobs',type=int,default=1)
    parser.add_argument('--timeout',type=int,default=1800);parser.add_argument('--run-id');parser.add_argument('--port-base',type=int,default=18080)
    parser.add_argument('--isolate-suite',action='append',default=[])
    parser.add_argument('--class-timeout',type=int,default=240);parser.add_argument('--class-jobs',type=int,default=2)
    parser.add_argument('--jvm-args-file',type=Path)
    args=parser.parse_args()
    if args.jvm_args_file:
        args.jvm_args_file=args.jvm_args_file.resolve(strict=True)
    matrix=json.loads((ROOT/'matrix.json').read_text());suites=matrix['suites']
    if args.suite:
        unknown=set(args.suite)-{r['id'] for r in suites}
        if unknown:parser.error('Unknown suites: '+','.join(sorted(unknown)))
        suites=[r for r in suites if r['id'] in args.suite]
    if min(args.jobs,args.timeout,args.class_timeout,args.class_jobs)<1:parser.error('jobs and timeout must be positive')
    if set(args.isolate_suite)-{s['id'] for s in suites}:parser.error('Isolation suite must be in the selected matrix')
    from run_classes import execute_classes, selection_candidates
    inventories={r['id']:r for r in json.loads((ROOT/'reports/inventory.json').read_text())}
    ports={};next_port=args.port_base
    for suite in suites:
        ports[suite['id']]=next_port
        next_port+=len(selection_candidates(suite,inventories[suite['id']])) if suite['id'] in args.isolate_suite else 1
    if args.port_base<1024 or next_port>65535:parser.error('Invalid port range')
    run_id=args.run_id or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    if Path(run_id).name!=run_id or run_id in ('.','..'):parser.error('run-id must be a directory name')
    run=ROOT/'target/runs'/run_id;run.mkdir(parents=True,exist_ok=False)
    metadata=dict(matrix=matrix,startedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  gitHead=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  gitStatus=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
                  java=subprocess.run(['java','-version'],capture_output=True,text=True).stderr,
                  maven=subprocess.run([shutil.which('mvn'),'-version'],capture_output=True,text=True).stdout,
                  matrixSha256=hashlib.sha256((ROOT/'matrix.json').read_bytes()).hexdigest(),
                  isolatedSuites=args.isolate_suite,classTimeoutSeconds=args.class_timeout,classJobs=args.class_jobs,
                  jvmArgumentsFile=str(args.jvm_args_file) if args.jvm_args_file else None,
                  jvmArgumentsSha256=hashlib.sha256(args.jvm_args_file.read_bytes()).hexdigest() if args.jvm_args_file else None)
    (run/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(execute_classes,suite,run,args.class_timeout,ports[suite['id']],args.class_jobs,args.jvm_args_file)
                 if suite['id'] in args.isolate_suite else pool.submit(execute,suite,run,args.timeout,ports[suite['id']],jvm_args_file=args.jvm_args_file) for suite in suites]
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
