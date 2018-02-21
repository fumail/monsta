# -*- coding: UTF-8 -*-
import urllib
import logging
from monsta.notification import Messenger

class ClickatellMessenger(Messenger):
    """Send SMS over the clickatell.com HTTP API"""
    
    def __init__(self):
        Messenger.__init__(self)
        self.configvars['api_id']=None
        self.configvars['sender']=''
        self.configvars['password']=None
        self.configvars['username']=None

        self.helpstrings['api_id']="clickatell API id"
        self.helpstrings['sender']="optional number that should appear as sender(must be authorized)"
        self.helpstrings['password']="cliacktell API password"
        self.helpstrings["username"]="clickatell API username"
        self.helpstrings['recipient']='alert recipient phone number'

    def lint(self):
        url = "http://api.clickatell.com/http/auth"
        config = {}
        config['user'] = self.configvars['username']
        config['password'] = self.configvars['password']
        config['api_id'] = self.configvars['api_id']
        query = urllib.urlencode(config)
        handle = urllib.urlopen(url, query)
        output = handle.read()
        handle.close()
        if output.strip().startswith("OK"):
            return True
        else:
            print("SMS lint failed: %s"%output.strip())
            return False

    
    def send_message(self,message,subject=None):
        url = "http://api.clickatell.com/http/sendmsg"
        config = {}
        config['user'] = self.configvars['username']
        config['password'] = self.configvars['password']
        config['api_id'] = self.configvars['api_id']
        if self.configvars['sender'].strip()!='':
            config['from'] = self.configvars['sender']
        config['to'] = self.recipient
        config['text'] = message[:159]
        query = urllib.urlencode(config)
        handle = urllib.urlopen(url, query)
        output = handle.read()
        handle.close()
        
        logging.debug("SMS message sent. output=%s"%output)