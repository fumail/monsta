from monsta.check import BaseCheck
import time
import logging

class DNSLookup(BaseCheck):
    """Perform a DNS Lookup and test if all required records are being returned"""
    
    def __init__(self):
        BaseCheck.__init__(self)
        self.configvars['hosts']=''
        self.configvars["record"]=None
        self.configvars["recordtype"]="A"
        self.configvars["requiredanswers"]=None
        
        self.helpstrings['hosts']="Space separated list of DNS Server that should be queried. Leave empty to use the default system resolver"
        self.helpstrings["recordtype"]="Type of the record (A,NS,MX,SOA,... )"
        self.helpstrings["requiredanswers"]="Space separated list of required return values"
        self.helpstrings["record"]="Name of the record that should be queried"
        
    def lint(self):
        try:
            import DNS
        except ImportError:
            print "required pydns library not available for DNS Lookup"
            return False
        return True
                 
    def performCheck(self):
        import DNS
        
        success=True
        errors=[]
        stats={}
        
        question=self.configvars["record"]
        rtype=self.configvars["recordtype"]
        
        servers=self.configvars['hosts'].strip()
        if servers=='':
            DNS.DiscoverNameServers()
            serverlist=['',]
        else:
            serverlist=servers.split()
        
        for nameserver in serverlist:
            key=nameserver
            if nameserver=='':
                key='default'
            
            start=time.time()
            try:
                ans=DNS.DnsRequest(question, qtype=rtype, server=nameserver).req().answers
            except DNS.DNSError,e:
                success=False
                errors.append("Error trying to lookup %s/%s on %s: %s"%(question,rtype,key,str(e)))
                continue
                
            lookuptime=time.time()-start
            
            stats['responsetime-%s'%key]="%.2f"%lookuptime
            data=[x['data'] for x in ans]
            for required in self.configvars["requiredanswers"].strip().split():
                if required not in data:
                    errors.append("required answer %s not found for query %s/%s on %s"%(required,question,rtype,key))
                    success=False
                    
        return (success,errors,stats)
    
    
class DNSSerialCompare(BaseCheck):
    """Compare SOA Serials on DNS Servers"""

    def __init__(self):
        BaseCheck.__init__(self)
        self.configvars['hosts']=None
        self.configvars["zone"]=None
        
        self.helpstrings['hosts']="Space separated list of DNS Server that should be queried"
        self.helpstrings['zone']="Zonename whose SOA should be checked"
      
    def lint(self):
        try:
            import DNS
        except ImportError:
            print "required pydns library not available for DNS Lookup"
            return False
        return True

    def performCheck(self):
        import DNS
        
        success=False
        errors=[]
        stats={}
        
        servers=self.configvars['hosts'].strip()
        serverlist=servers.split()
        
        question=self.configvars['zone']
        rtype='SOA'
        
        soaserial=None
        
        answers={}
        
        for nameserver in serverlist:
            start=time.time()
            try:
                ans=DNS.DnsRequest(question, qtype=rtype, server=nameserver).req().answers
            except DNS.DNSError,e:
                success=False
                errors.append("Error trying to lookup %s/%s on %s: %s"%(question,rtype,nameserver,str(e)))
                continue
                
            lookuptime=time.time()-start
            
            stats['responsetime-%s'%nameserver]="%.2f"%lookuptime
            serial=ans[0]['data'][2][1]

            answers[nameserver]=serial
            
            #first nameserver
            if soaserial==None:
                soaserial=serial
                continue
            
            #all others
            if soaserial!=serial:
                success=False
        
        allanswers=set(answers.values())
        count=len(allanswers)
        if count==0:
            success=False
            errors.append("did not get any SOA records")
        elif count==1:
            stats['serial']=serial
            success=True
        else:
            success=False
            errors.append("different SOA records returned : %s"%answers)
        
        return (success,errors,stats)   
        