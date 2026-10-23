"""Install official Core Profile distribution artifacts missing from Maven Central."""
import hashlib
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://download.eclipse.org/jakartaee/coreprofile/10.0/jakarta-core-profile-tck-10.0.1.zip'
SHA256 = '0fa5ead035817dc8e408354d9a70053802383d503fe1413abb33491daba263f8'

def main():
    directory = ROOT/'target/core-profile'; directory.mkdir(parents=True,exist_ok=True)
    archive = directory/'distribution.zip'
    if not archive.exists(): archive.write_bytes(urllib.request.urlopen(URL,timeout=60).read())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256: raise ValueError('Core Profile distribution SHA-256 mismatch')
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            destination = (directory/name).resolve()
            if not destination.is_relative_to(directory.resolve()): raise ValueError('Unsafe archive entry')
        z.extractall(directory)
    artifacts=directory/'core-profile-tck-10.0.1/artifacts'
    mvn=shutil.which('mvn')
    for name in ['core-profile-tck-impl','cdi-lite-tck-suite','rest-tck-suite','core-tck-jsonp-extension']:
        subprocess.run([mvn,'-B','-N','-f',str(ROOT/'pom.xml'),'org.apache.maven.plugins:maven-install-plugin:3.2.0:install-file',
                        '-DgroupId=jakarta.ee.tck.coreprofile',f'-DartifactId={name}','-Dversion=10.0.1','-Dpackaging=jar',
                        f'-Dfile={artifacts/(name+"-10.0.1.jar")}','-DgeneratePom=true'],cwd=directory,check=True)

if __name__=='__main__': main()
