

class BaseCheck(object):
    """base class for all checks"""
    def __init__(self):
        self.configvars={}
        self.section=None
        self.test=None
        self.helpstrings={}
        
    def performCheck(self):
        """perform the check and return a tuplie (status,errors,stats)
        status: boolean (check succeeded or not)
        errors: list (log/error messages why this check failed)
        stats: additional statistics (roundtrip times etc...)
        
        subclasses MUST override this
        """
        return (False,['perFormCheck() not implemented',],{})
    
    def lint(self):
        return True
    

        