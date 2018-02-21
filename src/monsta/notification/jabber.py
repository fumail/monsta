# -*- coding: UTF-8 -*-
from monsta.notification import Messenger
import logging
import time
import ssl
try:
    import xmpp
    XMPP_AVAILABLE = True
except ImportError:
    XMPP_AVAILABLE = False



# monkey patch broken TLS
def _startSSL(self):
    """ Immidiatedly switch socket to TLS mode. Used internally."""
    """ Here we should switch pending_data to hint mode."""
    tcpsock=self._owner.Connection
    # noinspection PyProtectedMember
    tcpsock._sslObj    = ssl.wrap_socket(tcpsock._sock, None, None)
    # noinspection PyProtectedMember
    tcpsock._sslIssuer = tcpsock._sslObj.getpeercert().get('issuer')
    # noinspection PyProtectedMember
    tcpsock._sslServer = tcpsock._sslObj.getpeercert().get('server')
    # noinspection PyProtectedMember
    tcpsock._recv = tcpsock._sslObj.read
    # noinspection PyProtectedMember
    tcpsock._send = tcpsock._sslObj.write

    tcpsock._seen_data=1
    self._tcpsock=tcpsock
    tcpsock.pending_data=self.pending_data
    # noinspection PyProtectedMember
    tcpsock._sock.setblocking(0)

    self.starttls='success'

if XMPP_AVAILABLE:
    xmpp.transports.TLS._startSSL = _startSSL



class JabberMessenger(Messenger):
    """Notifications over JABBER/XMPP/Google Talk"""
    
    def __init__(self):
        Messenger.__init__(self)
        self.configvars['jid']=None
        self.configvars['password']=None
        
        self.helpstrings['jid']='jabber id (example: yourname@jabber.org)'
        self.helpstrings['password']='jabber account password'
        self.helpstrings['recipient']='alert recipient jid'
        
    def lint(self):
        if not XMPP_AVAILABLE:
            print("You are trying to use the jabber messenger, but the python xmpp lib (xmpppy) is not installed.")
            return False
            
        jid=xmpp.protocol.JID(self.configvars['jid'])
        cl=xmpp.Client(jid.getDomain(),debug=[])
        con=cl.connect()
        if not con:
            print("XMPP Connection failed")
            return False
        
        auth=cl.auth(jid.getNode(),self.configvars['password'],resource=jid.getResource())
        if not auth:
            print("XMPP Auth failed")
            return False
        
        return True 
    
     
    def send_message(self,message,subject=None):
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
        
        