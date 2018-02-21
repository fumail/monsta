# -*- coding: UTF-8 -*-
from monsta.notification import Messenger
import smtplib
from email import utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import socket

class SMTPMessenger(Messenger):
    """Send notifications by email"""
    
    def __init__(self):
        Messenger.__init__(self)
        self.configvars['host']='127.0.0.1'
        self.configvars['port']=25
        self.configvars['helo']='${myhostname}'
        self.configvars['sender']=None
        self.configvars['username']=''
        self.configvars['password']=''
        self.configvars['starttls']='no'
        
        self.helpstrings['host']="SMTP Relay Hostname"
        self.helpstrings['port']="SMTP Port"
        self.helpstrings['helo']="The HELO string to use when connecting to the host. '${myhostname}' uses the current hostname as helo"
        self.helpstrings['sender']="Sender address for the notification email messages"
        self.helpstrings['username']="SMTP Auth Username (leave empty to send without smtp auth)"
        self.helpstrings['password']="SMTP Auth password (leave empty to send without smtp auth)"
        self.helpstrings['recipient']='alert recipient email address'
        self.helpstrings['starttls']='use starttls to encrypt the smtp traffic'
        
         
    def lint(self):
        helo=self.configvars['helo']
        if helo=='${myhostname}':
            helo=socket.gethostname()
            
        try:
            smtp=smtplib.SMTP(self.configvars['host'], int(self.configvars['port']), helo,20)
            
            if self.configvars['starttls'].lower().strip()=='yes':
                smtp.starttls()
            
            user=self.configvars['username'].strip()
            pw=self.configvars['password'].strip()
            if user!='' and pw!='':
                smtp.login(user,pw)
        except Exception as e:
            print("SMTP login failed: %s"%str(e))
            return False
        
        return True
        
       
    def send_message(self,message,subject=None):
        
        helo=self.configvars['helo']
        if helo=='${myhostname}':
            helo=socket.gethostname()
        
        smtp=smtplib.SMTP(self.configvars['host'], int(self.configvars['port']), helo,20)
        
        if self.configvars['starttls'].lower().strip()=='yes':
            smtp.starttls()
        
        user=self.configvars['username'].strip()
        pw=self.configvars['password'].strip()
        if user!='' and pw!='':
            smtp.login(user,pw)
        
        c = message.encode(u'utf8', u'replace')
        txtattach = MIMEText(c, u'plain', u'utf8')
        
        outer = MIMEMultipart(u'alternative')
        outer[u'Subject'] = Header(subject).encode()
        outer[u'To'] = self.recipient
        outer[u'From'] = self.configvars['sender']
        outer[u'auto-submitted'] = 'auto-generated'
        outer[u'Date'] = utils.formatdate(localtime=True)
        outer[u'Message-ID'] = utils.make_msgid()
        outer.attach(txtattach)
        
        smtp.sendmail(self.configvars['sender'], self.recipient, outer.as_string())

    
    