import logging

class Messenger(object):
    def __init__(self):
        self.recipient=None
        self.section=None
        self.configvars={
            'recipient':None,
        }
        self.helpstrings={
            'recipient':'Recipient of the alert',
        }
        
    def send_message(self,message):
        logging.debug("Unimplemented sendmessage()! recipient=%s message=%s"%(self.recipient,message))
       
    def lint(self):
        return True
     
    def __repr__(self):
        return str(self.recipient)
        
class LogMessenger(Messenger):
    """Send notifications to local logging framework (mainly for debugging)"""
    
    def __init__(self):
        Messenger.__init__(self)
        
    def send_message(self,message,subject=None):
        func=logging.info
        
        if self.recipient=='error':
            func=logging.error
            
        if self.recipient=='debug':
            func=logging.debug
            
        func(message)
    
    
