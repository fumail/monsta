from monsta.notification import Messenger
import logging
import time

class JabberMessenger(Messenger):
    """Notifications over JABBER/XMPP/Google Talk"""
    
    def __init__(self):
        Messenger.__init__(self)
        self.configvars['jid']=None
        self.configvars['password']=None
        
        self.helpstrings['jid']='jabber id (example: yourname@jabber.org)'
        self.helpstrings['password']='jabber account password'
        
    def lint(self):
        try:
            import xmpp
        except ImportError:
            print "You are trying to use the jabber messenger, but the python xmpp lib (xmpppy) is not installed."
            return False
            
        jid=xmpp.protocol.JID(self.configvars['jid'])
        cl=xmpp.Client(jid.getDomain(),debug=[])
        con=cl.connect()
        if not con:
            print "XMPP Connection failed"
            return False
        
        auth=cl.auth(jid.getNode(),self.configvars['password'],resource=jid.getResource())
        if not auth:
            print "XMPP Auth failed"
            return False
        
        return True 
    
     
    def send_message(self,message,subject=None):
        import xmpp
        
        jid=xmpp.protocol.JID(self.configvars['jid'])
        cl=xmpp.Client(jid.getDomain(),debug=[])
        con=cl.connect()
        if not con:
            raise Exception("XMPP connection failed")
        
        auth=cl.auth(jid.getNode(),self.configvars['password'],resource=jid.getResource())
        if not auth:
            raise Exception("XMPP authentication failed")
        
        id=cl.send(xmpp.protocol.Message(self.recipient,message))
        
        logging.debug("XMPP message sent. ID=%s"%id)
        
        time.sleep(1)
        cl.disconnect()
        
        