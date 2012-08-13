from distutils.core import setup
import glob
import sys
import os

sys.path.insert(0,'src')

#store old content of version file here
#if we have git available, temporarily overwrite the file
#so we can report the git commit id in fuglu --version 
OLD_VERSFILE_CONTENT=None
VERSFILE='src/monsta/__init__.py'

def git_version():
    from monsta import MONSTA_VERSION
    global VERSFILE,OLD_VERSFILE_CONTENT
    try:
        import subprocess
        x=subprocess.Popen(['git','describe'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        ret=x.wait()
        if ret==0:
            stdout,stderr=x.communicate()
            vers=stdout.strip()
            #replace fuglu version in file
            if os.path.isfile(VERSFILE):
                OLD_VERSFILE_CONTENT=open(VERSFILE,'r').read()
                buff=OLD_VERSFILE_CONTENT.replace(MONSTA_VERSION,vers)
                open(VERSFILE,'w').write(buff)
            return vers
        else:
            return MONSTA_VERSION
    except Exception,e:
        return MONSTA_VERSION


setup(name = "monsta",
    version = git_version(),
    description = "Monsta Monitoring Daemon",
    url = "https://github.com/gryphius/monsta",
    author = "O. Schacher",
    author_email = "oli@wgwh.ch",
    package_dir={'':'src'},
    packages = ['monsta','monsta.check','monsta.notification'],
    scripts = ["scripts/main/monsta"],
    long_description = """Monsta Monitoring Daemon""" ,
    data_files=[
                ('/etc/monsta',glob.glob('conf/*.dist')),
   #             ('/etc/init.d',['scripts/init.d-centos/monsta']),
                ]
)


#cleanup
if OLD_VERSFILE_CONTENT!=None:
    open(VERSFILE,'w').write(OLD_VERSFILE_CONTENT)
    

