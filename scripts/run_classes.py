"""Run an entire inventoried suite in bounded Maven processes, one per selected class."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import shutil
import subprocess
import time
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from run_tcks import ROOT, execute


def selections(suite, inventory):
    if suite.get('officialSelection') or suite.get('signature'):
        raise ValueError('Official XML/group and signature suites require run_tcks.py; class filtering would change their contract')
    return [suite['factory']] if suite.get('factory') else sorted(c['name'] for c in inventory['candidateClasses'])


def selection_candidates(suite,inventory):
    if suite['id']=='cdi-lite': return sorted(c['name'] for c in inventory['candidateClasses'])
    return selections(suite,inventory)


def split_cdi_xml(source,classes,directory):
    paths={}
    for name in classes:
        tree=ET.parse(source);tests=tree.findall('test')
        if len(tests)!=1: raise ValueError('Unsupported official CDI suite structure')
        test=tests[0]
        for packages in test.findall('packages'): test.remove(packages)
        if test.find('classes') is not None: raise ValueError('Official CDI suite already contains explicit classes')
        ET.SubElement(ET.SubElement(test,'classes'),'class',name=name)
        path=directory/(name+'.xml')
        tree.write(path,encoding='utf-8',xml_declaration=True)
        paths[name]=path
    return paths


def discover_cdi(folder,inventory):
    source=ROOT/'target/core-profile/core-profile-tck-10.0.1/artifacts/cdi-lite-tck-suite-10.0.1.xml'
    classpath=os.pathsep.join([str(ROOT/'cdi-lite/target/test-classes'),str(ROOT/'cdi-lite/target/classes'),
                              (folder/'classpath.txt').read_text().strip()])
    selected=folder/'selected-methods.txt'
    with (folder/'discovery.log').open('w') as stream:
        subprocess.run(['java','-cp',classpath,'com.guicedee.tck.porting.CdiSuiteDiscovery',str(source),str(selected),
                        str(folder/'discovery')],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=120)
    methods=selected.read_text().splitlines()
    classes=sorted({m.split('#')[0] for m in methods})
    if not classes or not set(classes)<={c['name'] for c in inventory['candidateClasses']}:
        raise ValueError('Official CDI discovery disagrees with artifact inventory')
    directory=folder/'suite-selection';directory.mkdir()
    paths=split_cdi_xml(source,classes,directory)
    partitioned=folder/'partitioned-methods.txt'
    with (folder/'partition-discovery.log').open('w') as stream:
        subprocess.run(['java','-cp',classpath,'com.guicedee.tck.porting.CdiSuiteDiscovery',str(directory),str(partitioned),
                        str(folder/'partition-discovery')],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=120)
    if set(partitioned.read_text().splitlines())!=set(methods):
        raise ValueError('Partitioned CDI suite does not select exactly the official method set')
    manifest=dict(source=str(source),sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  selectedMethods=methods,selectedClasses=classes,
                  note='Pinned TestNG selected identical method sets from official XML and every generated class suite; interceptor prevented invocation during discovery.')
    (folder/'selection.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return classes,paths


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


def execute_classes(suite,run,timeout,port,jobs,jvm_args_file=None):
    inventory=next(r for r in json.loads((ROOT/'reports/inventory.json').read_text()) if r['id']==suite['id'])
    classes=selection_candidates(suite,inventory)
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
    for value in (folder/'classpath.txt').read_text().strip().split(os.pathsep):
        path=Path(value)
        if path.is_file(): artifacts.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (folder/'artifacts.json').write_text(json.dumps(artifacts,indent=2)+'\n')
    suite_paths={}
    if suite['id']=='cdi-lite': classes,suite_paths=discover_cdi(folder,inventory)
    start=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures=[pool.submit(execute,suite,folder/'classes',timeout,port+i,name,suite_paths.get(name),jvm_args_file) for i,name in enumerate(classes)]
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
    classes=selection_candidates(suite,inventory)
    if not classes or len(classes)!=len(set(classes)): parser.error('Empty or duplicate class selection')
    if args.port_base<1024 or args.port_base+len(classes)>65535: parser.error('Invalid port range')
    run=ROOT/'target/runs'/args.run_id;run.mkdir(parents=True,exist_ok=False)
    metadata=dict(matrix=matrix,startedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  gitHead=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  gitStatus=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
                  java=subprocess.run(['java','-version'],capture_output=True,text=True).stderr,
                  maven=subprocess.run([shutil.which('mvn'),'-version'],capture_output=True,text=True).stdout,
                  matrixSha256=hashlib.sha256((ROOT/'matrix.json').read_bytes()).hexdigest(),
                  selectionCandidates=classes,classTimeoutSeconds=args.timeout)
    (run/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n')
    result=execute_classes(suite,run,args.timeout,args.port_base,args.jobs)
    rows=result['classResults']
    (run/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    lines=['# Isolated class run: '+args.suite,'',
           'Every selected class was attempted; CDI selection preserves official groups. Timeouts and missing results remain incomplete.','',
           '| Class | Status | Passed | Failed | Skipped |','| --- | --- | ---: | ---: | ---: |']
    for r in rows: lines.append(f"| {r['selectedClass']} | {r['status']} | {r['counts']['passed']} | {r['counts']['failed']} | {r['counts']['skipped']} |")
    (run/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    print('Results:',run,result['status'],result['counts'])
    return result['exitCode']


if __name__=='__main__': raise SystemExit(main())
