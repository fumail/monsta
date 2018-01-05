from monsta.check import BaseCheck
import threading
import subprocess
import traceback
import shlex


class Command(object):
    """
    Enables to run subprocess commands in a different thread with TIMEOUT option.

    From: https://gist.github.com/kirpit/1306188

    Based on jcollado's solution:
    http://stackoverflow.com/questions/1191374/subprocess-with-timeout/4825933#4825933
    """
    command = None
    process = None
    status = None
    output, error = '', ''
    timed_out=False

    def __init__(self, command):
        if isinstance(command, basestring):
            command = shlex.split(command)
        self.command = command

    def run(self, timeout=None, **kwargs):
        """ Run a command then return: (status, output, error). """
        def target(**kwargs):
            try:
                self.process = subprocess.Popen(self.command, **kwargs)
                self.output, self.error = self.process.communicate()
                self.status = self.process.returncode
            except:
                self.error = traceback.format_exc()
                self.status = -1
        # default stdout and stderr
        if 'stdout' not in kwargs:
            kwargs['stdout'] = subprocess.PIPE
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.PIPE
        # thread
        thread = threading.Thread(target=target, kwargs=kwargs)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            self.timed_out=True
            self.process.terminate()
            thread.join()
        return self.status, self.output, self.error
        
class ScriptCheck(BaseCheck):
    """Runs a local script and checks the exit status/output"""
    
    def __init__(self):
        BaseCheck.__init__(self)
        self.configvars['timeout']=10
        self.configvars['command']=None
        self.configvars['expect']=''
        
        self.helpstrings['timeout']="command timeout in seconds"
        self.helpstrings['command']="command to run with arguments"
        self.helpstrings['expect']='string that must be in the script output. leave empty to just check exit status'
        
    def performCheck(self):
        command=self.configvars['command']
        timeout=float(self.configvars['timeout'])
        expect=self.configvars['expect']
        success=True
        errors=[]
        stats={}
        
        c=Command(command)
        c_status,c_output,c_error=c.run(timeout=timeout)
        
        if c_status==0:
            if expect!='' and expect not in c_output:
                errors.append("Expected string not found in command output")
                success=False
        elif c_status==-1:
            errors.append("Command could not be executed: %s"%c_error)
            success=False
        elif c.timed_out:
            errors.append("Command took longer than configured timeout")
            success=False
        else:
            errors.append("Command exited with non-zero status %s"%c_status)
            success=False
        
        return success,errors,stats
        
        
        
  