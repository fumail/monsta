from monsta.check import BaseCheck
import time
import random
import smtplib
from email.utils import formatdate
import imaplib
import logging
from email.mime.text import MIMEText
from email.header import Header


class SMTP2MAILBOX(BaseCheck):
    """Send a test message over SMTP and retreive it from a mailbox (round trip test)"""
    
    def __init__(self):
        BaseCheck.__init__(self)
        self.configvars['smtp_host']='localhost'
        self.configvars['smtp_port']=25
        self.configvars['smtp_timeout']=20
        self.configvars['smtp_helo']='monsta.local'
        self.configvars['smtp_username']=''
        self.configvars['smtp_password']=''
        self.configvars['smtp_starttls']='no'
        
        self.configvars['mailbox_type']='imap'
        
        self.configvars['sender']=None
        self.configvars['recipient']=None
        self.configvars['timeout']=60
        
        self.configvars['mailbox_username']=None
        self.configvars['mailbox_host']=None
        self.configvars['mailbox_password']=None
        self.configvars['mailbox_folder']='INBOX'
        self.configvars['mailbox_ssl']='no'
        
        self.helpstrings['smtp_host']="Send Mail to this host"
        self.helpstrings['smtp_port']="Send Mail to this port"
        self.helpstrings["smtp_timeout"]="SMTP Network timeout in seconds"
        self.helpstrings["smtp_helo"]="HELO string to use in the smtp dialog"
        self.helpstrings["smtp_username"]="smtp auth username (leave empty for no smtp auth)"
        self.helpstrings["smtp_password"]="smtp auth password (leave empty for no smtp auth)"
        self.helpstrings["smtp_starttls"]="encrypt smtp session with starttls"
        
        self.helpstrings["mailbox_type"]="Type of the mailbox. currently, only 'imap' is supported"
        self.helpstrings["sender"]="Sender email address of the test message"
        self.helpstrings["recipient"]="Recipient email address of the test message"
        self.helpstrings["timeout"]="Time to wait for the test message to show up in the target mailbox"
        self.helpstrings["mailbox_username"]="Login username for the target mailbox"
        self.helpstrings["mailbox_host"]="Target mailbox hostname"
        self.helpstrings["mailbox_password"]="Login password for the target mailbox"
        self.helpstrings["mailbox_folder"]="Folder in the target mailbox where the message should show up"
        
        
        self.logger=logging.getLogger('SMTP2MAILBOX')

    def performCheck(self):
        """send email message  and retreive it from the imap server
        
        """
        
        success=False
        errors=[]
        stats={}
        
        mx=self.configvars['smtp_host']            
        helo=self.configvars['smtp_helo']
        sender=self.configvars['sender']        
        recipient=self.configvars['recipient']
        smtp_port=int(self.configvars['smtp_port'])
        smtp_timeout=int(self.configvars['smtp_timeout'])
        user=self.configvars['smtp_username'].strip()
        pw=self.configvars['smtp_password'].strip()
        smtp_starttls=False
        if self.configvars['smtp_starttls'].lower().strip()=='yes':
            smtp_starttls=True

        e2eid=random.randint(10000,100000)
        
        
        body="monsta smtp check id = %s"%e2eid

        txt = MIMEText(body, u'plain')
        
        txt[u'Subject'] = Header('[monsta] smtp round trip check %s'%e2eid).encode()
        txt[u'To'] = Header(recipient)
        txt[u'From'] = Header(sender)
        txt[u'Date'] = Header(formatdate(localtime=True))
        txt[u'e2eid'] = Header(str(e2eid))

        
        
        self.logger.debug("Sending message id=%s to %s"%(e2eid,mx))
        
        try:
        
            smtpServer = smtplib.SMTP(mx, smtp_port, helo,smtp_timeout)
            if smtp_starttls:
                smtpServer.starttls()
            
            if user!='' and pw!='':
                smtpServer.login(user,pw)

            smtpServer.sendmail(sender, recipient, txt.as_string())
            smtpServer.quit()
        except Exception,e:
            success=False
            errors.append("Could not send message from %s to %s to mx %s:%s"%(sender,recipient,mx,str(e)))
            return success,errors,stats
            
            
        self.logger.debug("Message sent, tls=%s smtpauth=%s"%(smtp_starttls,(user!='' and pw!='')))
        
        timeout=int(self.configvars['timeout'])
        
        msgcontent=None
        
        try:
            if self.configvars['mailbox_type']=='imap':
                #imap
                imapserver=self.configvars['mailbox_host']        
                imapusername=self.configvars['mailbox_username']  
                imappassword=self.configvars['mailbox_password']  
                imapfolder=self.configvars['mailbox_folder']  
                imap_ssl=False
                if self.configvars['mailbox_ssl'].lower().strip()=='yes':
                    imap_ssl=True
                
                self.logger.debug("Waiting 2 secs...")
                time.sleep(2)
                self.logger.debug('Contacting imap server %s'%(imapserver))
                
                if imap_ssl:
                    imap=imaplib.IMAP4_SSL(imapserver)
                else:
                    imap=imaplib.IMAP4(imapserver)
                    
                imap.login(imapusername,imappassword)
                typ,count=imap.select(imapfolder)
                
                if typ=='NO':
                    raise Exception,"Could not select folder %s"%imapfolder
                
                killtime=time.time()+timeout
                start=time.time()
                while time.time()<killtime:
                    typ, data = imap.search(None, '(HEADER "e2eid" "%s")'%e2eid)
                    if typ=='NO':
                        raise Exception,"imap search failed"
                    msgs=data[0].split()
                    nummsgs=len(msgs)
                    if nummsgs==0:
                        time.sleep(1)
                        continue
                        
                    if nummsgs>1:
                        raise Exception,"got more than one message with id %s"%e2eid
                    
                    thetime=time.time()-start+2
                    stats['timetomailbox']="%.2f"%thetime
                    num=msgs[0]
                    typ, data = imap.fetch(num, '(RFC822)')
                    msgcontent=data[0][1]
                    imap.store(num,'+FLAGS', '\\Deleted')
                    break
                
                imap.expunge()
                imap.logout()
            else:
                raise Exception("only imap mailbox_type supported so far")
            
        except Exception,e:
            errors.append(str(e))
            success=False
        
        if msgcontent!=None:
            #print msgcontent
            success=True
        else:
            errors.append("message did not show up in target mailbox")
            success=False
            
        return success,errors,stats
    
    
class SMTPCheck(BaseCheck):
    """Run an SMTP Dialog up to the RCPT TO stage, then quit (does not actually send a message)"""
    
    def __init__(self):
        BaseCheck.__init__(self)
        self.configvars['host']=None
        self.configvars['port']=25
        self.configvars['timeout']=20
        self.configvars['helo']='monsta.local'
        
        self.configvars['sender']=None
        self.configvars['recipient']=None
        
    def performCheck(self):
        success=True
        errors=[]
        stats={}


        host=self.configvars['host']            
        helo=self.configvars['helo']
        sender=self.configvars['sender']        
        recipient=self.configvars['recipient']
        smtp_port=(self.configvars['port'])
        smtp_timeout=int(self.configvars['timeout'])
        
        smtp = smtplib.SMTP(timeout=smtp_timeout)
        
        time_start=time.time()
        try:
            code,msg=smtp.connect(host, smtp_port)
            if code<200 or code>299:
                errors.append("connection was not accepted: %s %s"%(code,msg))
                success=False
            time_banner=time.time()
            stats["banner-time"]="%.2f"%(time_banner-time_start)
        except Exception,e:
            errors.append("Error in connect:"+str(e))
            success=False
        
        
        #HELO
        if success:
            try:
                code,msg=smtp.helo(helo)

                if code<200 or code>299:
                    errors.append("HELO was not accepted: %s %s"%(code,msg))
                    success=False
            except Exception,e:
                errors.append("Error in HELO: "+str(e))
                success=False
        
        #MAIL FROM
        if success:
            try:
                code,msg=smtp.mail(sender)
                if code<200 or code>299:
                    errors.append("MAIL FROM was not accepted: %s %s"%(code,msg))
                    success=False
            except Exception,e:
                errors.append("Error in MAIL FROM: "+str(e))
                success=False

        #RCPT TO
        if success:
            try:
                code,msg=smtp.rcpt(recipient)
                if code<200 or code>299:
                    errors.append("RCPT was not accepted: %s %s"%(code,msg))
                    success=False

            except Exception,e:
                errors.append("Error in RCPT TO: "+str(e))
                success=False
        
        try:
            smtp.quit()
        except Exception,e:
            pass
        
        return success,errors,stats   
        