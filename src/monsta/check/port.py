from monsta.check import BaseCheck
import socket
import time
import logging

        
class SimplePortCheck(BaseCheck):
    """Connects to a port and checks if a specific string is sent to the client"""
    def __init__(self):
        BaseCheck.__init__(self)
        self.configvars['timeout']=10
        self.configvars['host']=None
        self.configvars['port']=None
        self.configvars['expect']=''
        
        self.helpstrings['timeout']="Connection timeout in seconds"
        self.helpstrings['host']="Hostname or ip address"
        self.helpstrings['port']="Port that should be connected to"
        self.helpstrings['expect']='string that must be in the first line read from a server banner. Leave empty to just test the successful port connect'
        
    def performCheck(self):
        host=self.configvars['host']
        port=int(self.configvars['port'])
        timeout=float(self.configvars['timeout'])
        success=False
        errors=[]
        stats={}
        
        
        con=None
        try:
            start=time.time()
            con=socket.create_connection((host,port), timeout)
            connecttime=time.time()-start
            stats['connecttime']="%.2f"%connecttime
            expect=self.configvars['expect'].strip()
            if expect.strip()!='':
                bannerstart=time.time()
                banner = con.makefile().readline()
                bannertime=time.time()-bannerstart
                stats['bannertine']="%.2f"%bannertime
                if banner.find(expect)>-1:
                    success=True
                else:
                    logging.info("expected string '%s' not in banner '%s'"%(expect,banner))
            else:
                success=True # connect is enough
                
            
            
            
        except Exception,e:
            errors.append(str(e))
        
        if con!=None:
            try:
                con.close()
            except:
                pass
        
        return (success,errors,stats)
        
        
        
        
        
        
        
        
        
        
#class ESMTPPortCheck(ExpectPortCheck):
#    """Tests if an ESMTP Server is reachable"""
#    def __init__(self):
#        ExpectPortCheck.__init__(self)
#        self.configvars['port']=25
#        self.configvars['expect']='ESMTP'
#
#class IMAPPortCheck(ExpectPortCheck):
#    """Tests if an IMAP Server is reachable"""
#    def __init__(self):
#        ExpectPortCheck.__init__(self) 
#        self.configvars['port']=143
#        self.configvars['expect']='IMAP4rev1'
#        