"""Resolve the CDI runtime's real module graph, keeping Arquillian on the test classpath."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from run_tcks import ROOT


def main():
    folder=ROOT/'target/jpms-cdi';folder.mkdir(parents=True,exist_ok=True)
    version=json.loads((ROOT/'matrix.json').read_text())['guicedee']
    pom=f'''<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>
<groupId>com.guicedee.tck</groupId><artifactId>cdi-runtime-resolution</artifactId><version>1</version>
<dependencies><dependency><groupId>com.guicedee</groupId><artifactId>inject</artifactId><version>{version}</version></dependency>
<dependency><groupId>com.guicedee</groupId><artifactId>cdi</artifactId><version>{version}</version></dependency></dependencies></project>'''
    (folder/'pom.xml').write_text(pom)
    with (folder/'resolve.log').open('w') as log:
        subprocess.run([shutil.which('mvn'),'-B','-ntp','-f',str(folder/'pom.xml'),
                        'org.apache.maven.plugins:maven-dependency-plugin:3.11.0:build-classpath',
                        f'-Dmdep.outputFile={folder/"modulepath.txt"}'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
    paths=[Path(p) for p in (folder/'modulepath.txt').read_text().strip().split(os.pathsep)]
    modulepath=os.pathsep.join(p.as_posix() for p in paths)
    roots='com.guicedee.cdi,com.guicedee.guicedinjection'
    with (folder/'module-resolution.log').open('w') as log:
        subprocess.run(['java','--module-path',modulepath,'--add-modules',roots,'--show-module-resolution','-version'],
                       stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    (folder/'jvm.args').write_text('--module-path\n"'+modulepath+'"\n--add-modules\n'+roots+'\n')
    manifest=dict(roots=roots,guicedeeVersion=version,artifacts=[dict(path=p.as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths],
                  note='Runtime artifacts unchanged; testing libraries remain on the classpath. Module resolution alone is not a startup or compatibility pass.')
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('CDI JPMS argument file:',folder/'jvm.args')


if __name__=='__main__': main()
