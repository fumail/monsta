from monsta.notification import Messenger
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header


class SMTPMessenger(Messenger):
    """Send notifications by email"""
    
    def __init__(self):
        Messenger.__init__(self)
        self.configvars['host']='127.0.0.1'
        self.configvars['port']=25
        self.configvars['helo']='monsta.local'
        self.configvars['sender']=None
        self.configvars['username']=''
        self.configvars['password']=''
        self.configvars['starttls']='no'
        
        self.helpstrings['host']="SMTP Relay Hostname"
        self.helpstrings['port']="SMTP Port"
        self.helpstrings['helo']="The HELO string to use when connecting to the host"
        self.helpstrings['sender']="Sender address for the notification email messages"
        self.helpstrings['username']="SMTP Auth Username (leave empty to send without smtp auth)"
        self.helpstrings['password']="SMTP Auth password (leave empty to send without smtp auth)"
        self.helpstrings['recipient']='alert recipient email address'
        self.helpstrings['starttls']='use starttls to encrypt the smtp traffic'
        
         
    def lint(self):
        try:
            smtp=smtplib.SMTP(self.configvars['host'], int(self.configvars['port']), self.configvars['helo'],20)
            
            if self.configvars['starttls'].lower().strip()=='yes':
                smtp.starttls()
            
            user=self.configvars['username'].strip()
            pw=self.configvars['password'].strip()
            if user!='' and pw!='':
                smtp.login(user,pw)
        except Exception,e:
            print "SMTP Send failed: %s"%str(e)
            return False
        
        return True
        
       
    def send_message(self,message,subject=None):
        smtp=smtplib.SMTP(self.configvars['host'], int(self.configvars['port']), self.configvars['helo'],20)
        
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
        outer.attach(txtattach)
        
        smtp.sendmail(self.configvars['sender'], self.recipient, outer.as_string())

    
    