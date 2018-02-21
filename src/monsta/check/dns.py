# -*- coding: UTF-8 -*-
from monsta.check import BaseCheck
import time
try:
    from dns import resolver
    DNSPYTHON_AVAILABLE = True
except ImportError:
    DNSPYTHON_AVAILABLE = False


def dns_lookup(hostname, qtype='A', nsip=None, exc=False, nx=False):
    my_resolver = resolver.Resolver()
    if nsip is not None:
        my_resolver.nameservers = [nsip]
    
    entries = []
    try:
        request = my_resolver.query(hostname, qtype)
        for rec in request:
            entry = {'ttl': request.rrset.ttl, 'data': rec.to_text().rstrip('.')}
            if qtype == 'MX':
                prio, mxr = rec.to_text().split(None, 1)
                entry = {'ttl': request.rrset.ttl, 'data': mxr.rstrip('.'), 'prio': prio}
            entries.append(entry)
    except resolver.NoAnswer:
        pass
    except resolver.NXDOMAIN:
        if nx:
            raise
    except Exception:
        if exc:
            raise
    return entries



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
        if not DNSPYTHON_AVAILABLE:
            print("required pydns library not available for DNS Lookup")
            return False
        return True
                 
    def performCheck(self):
        success=True
        errors=[]
        stats={}
        
        question=self.configvars["record"]
        rtype=self.configvars["recordtype"]
        
        servers=self.configvars['hosts'].strip()
        if servers=='':
            serverlist=['',]
        else:
            serverlist=servers.split()
        
        for nameserver in serverlist:
            key=nameserver
            if nameserver=='':
                key='default'
            
            start=time.time()
            try:
                ans = dns_lookup(question,qtype=rtype, nsip=nameserver, exc=True, nx=True)
            except Exception as e:
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
                    
        return success,errors,stats
    
    
class DNSSerialCompare(BaseCheck):
    """Compare SOA Serials on DNS Servers"""

    def __init__(self):
        BaseCheck.__init__(self)
        self.configvars['hosts']=None
        self.configvars["zone"]=None
        
        self.helpstrings['hosts']="Space separated list of DNS Server that should be queried"
        self.helpstrings['zone']="Zonename whose SOA should be checked"
      
    def lint(self):
        if not DNSPYTHON_AVAILABLE:
            print("required pydns library not available for DNS Lookup")
            return False
        return True

    def performCheck(self):
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
                ans = dns_lookup(question, qtype=rtype, nsip=nameserver, exc=True, nx=True)
            except Exception as e:
                errors.append("Error trying to lookup %s/%s on %s: %s"%(question,rtype,nameserver,str(e)))
                continue
                
            lookuptime=time.time()-start
            
            stats['responsetime-%s'%nameserver]="%.2f"%lookuptime
            serial = None
            if ans:
                soa = ans[0]['data']
                serial = soa.split()[2]
                answers[nameserver]=serial
            
            #first nameserver
            if soaserial is None:
                soaserial=serial
                continue
        
        allanswers=set(answers.values())
        count=len(allanswers)
        if count==0:
            success=False
            errors.append("did not get any SOA records")
        elif count==1:
            stats['serial']=soaserial
            success=True
        else:
            success=False
            errors.append("different SOA records returned : %s"%answers)
        
        return success,errors,stats
        