MONSTA_VERSION="0.0.1-13-g1f55d6b"


from monsta.check.mailflow import *
from monsta.check.port import *
from monsta.check.mailflow import *
from monsta.check.dns import *
from monsta.check.script import ScriptCheck

from monsta.notification import LogMessenger
from monsta.notification.smtp import SMTPMessenger
from monsta.notification.jabber import JabberMessenger
from monsta.notification.sms import ClickatellMessenger

from monsta.funkyconsole import FunkyConsole

import logging
import thread
import random
import time
import sys

class MonstaTest(object):
    """one testset"""
    
    REQUIRES_ANY=1
    REQUIRES_ALL=2
    
    def __init__(self):
        self.failcount=0
        self.interval=300
        self.notifications={}
        self.checks=[]
        self.requires=MonstaTest.REQUIRES_ALL
        self.section=None
        
class TestRunner(object):
    def __init__(self,test):
        self.test=test
        self.stayalive=True
        self.name=None
        
    def notify(self,results):
        failcount=self.test.failcount
        notifications=self.test.notifications
        if failcount in notifications:
            notifiers=notifications[failcount]
            logging.info("failcount=%s, notifiying : %s"%(self.test.failcount,notifiers))
            
            #build message
            message="[%s]"%self.test.section
            for result in results:
                checksection,boolstatus,errors,stats=result
                if boolstatus:
                    status="OK"
                else:
                    status="FAIL"
                message=message+"\n%s: status=%s errors=%s"%(checksection,status,errors)
            subject="[%s]"%self.test.section
            
            for notifier in notifiers:
                try:
                    notifier.send_message(message,subject=subject)    
                except Exception,e:
                    import traceback
                    trace=traceback.format_exc()
                    logging.error("[%s] Unhandled exception while sending message to %s : %s, traceback=%s"%(notifier.__class__.__name__,notifier.recipient,str(e),trace))
        
        else:
            logging.debug("No one to notify in failcount %s"%failcount)
    
    def _run_check(self,check):
        logging.info("Starting  %s in %s"%(check.section,self.name))
        try:
            (success,errors,stats)=check.performCheck()
        except Exception,e:
            import traceback
            trace=traceback.format_exc()
            logging.error("Unhandled exception %s in check %s of %s : %s"%(str(e),check.section,self.name,trace))
            success=False
            errors=[trace,]
            stats={}
        logging.info("%s in %s completed. success=%s errors=%s stats=%s"%(check.section,self.name,success,errors,stats))
        return (success,errors,stats)
    
    def run(self):
        myname=self.test.section
        self.name=myname
        #make sure not all tests run at the same time at startup
        backofftime=random.randint(0,3)
        logging.debug("Test %s will run in %s seconds"%(myname,backofftime))
        time.sleep(backofftime)
        
        while self.stayalive:
            logging.info("Running test %s"%myname)
            
            allresults=[]
            #perform checks
            for check in self.test.checks:
                success,errors,stats=self._run_check(check)
                allresults.append((check.section,success,errors,stats))
            
            #evaluate results
            happy=True
            for result in allresults:
                success=result[1]
                if success and self.test.requires==MonstaTest.REQUIRES_ANY:
                    happy=True
                    break
            
                if not success:
                    happy=False
                    
                
            if happy:
                logging.info("%s: required test conditions fulfilled."%myname)
                self.test.failcount=0
            else:
                self.test.failcount+=1
                logging.info("%s: not all test conditions fullfilled. failcount is now %s"%(myname,self.test.failcount))
            
            #TODO: do something with stats?
            
            self.notify(allresults)
            
            logging.info("Test %s completed. Next run in %s seconds"%(myname,self.test.interval))
            time.sleep(self.test.interval)
            
        logging.info("Test %s shut down"%myname)


class MonstaHelp(object):
    def __init__(self,config):
        self.config=config
        self.controller=MainController(config)
        self.fc=FunkyConsole()
        
    def command(self,args):
        """console command"""
        
            
        if len(args)==0:
            options=[
                ("--lint","lint config"),
                ("--version","show version"),  
                ("--help check","list available checks"), 
                ("--help check [type]","show help for checktype [type]"), 
                ("--help notification","list available notification types"), 
                ("--help notification [type]","show help for notificationtype"), 
                ("--run [sectionname]","run a Test/Check/notification once"), 
               
            ]
            for k,v in options:
                print self.fc.strcolor(k, [self.fc.MODE["bold"],]),
                print "\t",
                print v
            sys.exit(0)
        
        classtype=args[0]
        
        typedict=self.controller.supportedchecktypes
        notificationdict=self.controller.supportednotifications
        
        if classtype=="check":
            if len(args)==1: # list checks
                self._help_index("check", typedict)
                
            if len(args)==2:
                ctype=args[1]
                self._help_details("check", typedict, ctype)
                
        elif classtype=="notification":
            if len(args)==1: # list checks
                self._help_index("notification",notificationdict)
                
                
            if len(args)==2:
                ctype=args[1]
                self._help_details("notification", notificationdict, ctype)
        else:
            print "unknown help topic: %s"%args
            sys.exit(1)
            
    def _help_index(self,typename,thedict):
        print self.fc.strcolor("Available %s types:"%typename,"yellow")
        for key in sorted(thedict.keys()):
            cls=thedict[key]
            docstr=cls.__doc__
            if docstr==None:
                docstr="(no description available)"
            else:
                docstr=self.fc.strcolor(docstr, [self.fc.MODE["bold"],])
            colorkey=self.fc.strcolor(key,"magenta")
            print "%s : %s"%(colorkey,docstr)
        print
        sys.exit(0)
    
    def _help_details(self,typename,thedict,value):
        if value not in thedict:
            print "No such %s type. run 'monsta --help %s' for a list"%(typename,typename)
            sys.exit(1)
        cls=thedict[value]
        info=self.help_string(cls)
        print info
        print
        sys.exit(0)

    
    def help_string(self,monstaclass):
        docstr=monstaclass.__doc__
        if docstr==None:
            docstr="(no description)"
        else:
            docstr=self.fc.strcolor(docstr, [self.fc.MODE["bold"],])
        instance=monstaclass()
        vardict=instance.configvars
        varnames=sorted(vardict.keys())
        
        helpstring="%s\nConfiguration:"%docstr
        for var in varnames:
            default=vardict[var]
            if default==None:
                default=self.fc.strcolor("REQUIRED","red")
            elif default=='':
                default="(default empty)"
            else:
                default="(default "+self.fc.strcolor(default, [self.fc.MODE["bold"],])+" )"
                
            description="(undocumented)"
            if var in instance.helpstrings:
                description=instance.helpstrings[var]
                
            helpline="%s %s :: %s"%(self.fc.strcolor(var,'magenta'),default,description)
            helpstring=helpstring+"\n%s"%helpline
        return helpstring

class RunOnce(object):
    
    def __init__(self,config):
        self.config=config
        self.controller=MainController(config)
        self.notifyclasses=self.controller.supportednotifications
        self.checkclasses=self.controller.supportedchecktypes
        self.fc=FunkyConsole()
        
    def run(self,section):
        if section not in self.config.sections():
            print "section not found in config: %s"%section
            print "available sections are:"
            l=sorted(self.config.sections())
            l=[x for x in l if x.startswith("Check_") or x.startswith("Test_") or x.startswith("Notification_")]
            print "\n".join(l)
            sys.exit(1)
            
        if section.startswith("Notification_"):
            self.run_notify(section)
            sys.exit(0)
            
        if section.startswith("Check_"):
            self.run_check(section)
            sys.exit(0)
        
        if section.startswith("Test_"):
            self.run_test(section)
            sys.exit(0)
        
    
    def run_notify(self,section):
        
        ntype=self.config.get(section,"type")
        if ntype not in self.notifyclasses:
            print "unsupported type: %s"%ntype
            sys.exit(1)
            
        cls=self.notifyclasses[ntype]
        instance=cls()
        
        
        instance.section=section
        instance.recipient=self.config.get(section,'recipient').strip()
    
        defaultconfig=instance.configvars
        actualconfig={}
        
        for key,defaultvalue in defaultconfig.iteritems():
            defaultvalue=self.controller._get_value(self.config,"%s_default"%ntype,key,defaultvalue)
                                          
            if self.config.has_option(section,key):
                actualconfig[key]=self.config.get(section,key)
            else:
                if defaultvalue==None:
                    print "not all required variables configured. please run --lint"
                    sys.exit(1)
                else:
                    actualconfig[key]=defaultvalue
        instance.configvars=actualconfig
        
        print "Running notification test: %s (type %s)"%(section,ntype)
        instance.send_message("Monsta Notification Test",subject="[monsta] Notification test")
    
    
    def run_check(self,section):
        ctype=self.config.get(section,"type")
        if ctype not in self.checkclasses:
            print "unsupported type: %s"%ctype
            sys.exit(1)
            
        cls=self.checkclasses[ctype]
        instance=cls()


        defaultconfig=instance.configvars
        actualconfig={}
        for key,defaultvalue in defaultconfig.iteritems():
            defaultvalue=self.controller._get_value(self.config,"%s_default"%ctype,key,defaultvalue)

            if self.config.has_option(section,key):
                actualconfig[key]=self.config.get(section,key)
            else:
                if defaultvalue==None:
                    print "not all required variables configured. please run --lint"
                    sys.exit(1)
                else:
                    actualconfig[key]=defaultvalue
        instance.configvars=actualconfig
        
        print "Running check %s (type %s)"%(section,ctype)
        result=instance.performCheck()
        success,errors,stats=result
        if success:
            print self.fc.strcolor("CHECK OK", "green")
        else:
            print self.fc.strcolor("CHECK FAILED","red")
        
        if len(errors)>0:
            print "Errors:"
            print "\n".join(errors)
        
        if len(stats)>0:
            print "Statistics:"
            print "\n".join(["%s : %s"%(k,v) for k,v in stats.items()])
            

    def run_test(self,section):
        checks=self.config.get(section,"checks").split()
        print "Running all checks in %s "%section
        for check in checks:
            self.run_check("Check_%s"%check)
            print ""
    
class MainController(object):
    def __init__(self,config):
        self.stayalive=True
        self.config=config
        self.tests=[]
        self.supportedchecktypes={
            'portconnect':SimplePortCheck,
            'mailbox':SMTP2MAILBOX,
            'dnslookup':DNSLookup,
            'dnsserial':DNSSerialCompare,
            'smtp':SMTPCheck,
            'script':ScriptCheck,
        }
        self.supportednotifications={
            #'log':LogMessenger,  #enable for debugging
            'smtp':SMTPMessenger,
            'xmpp':JabberMessenger,
            'sms_clickatell':ClickatellMessenger,
        }
    
    def startup(self):
        logging.debug("reading config...")
        self.initFromConfig(self.config)
        
        #start checker threads
        logging.info("starting checker threads...")
        
        for test in self.tests:
            logging.info("starting test %s"%test.section)
            runner=TestRunner(test)
            thread.start_new_thread(runner.run, ())
            
        #let the mainthread sleep
        while self.stayalive:
            time.sleep(1)
    
    def lint(self):
        checks,notifications=self.initFromConfig(self.config)
        for sec in self.config.sections():
            if sec.startswith("Check_") and sec not in checks.keys():
                print "%s is not used in any tests and will never be run"%sec
                
            if sec.startswith("Notification_") and sec not in notifications.keys():
                print "Unused notification: %s"%sec
            
        for key,instance in notifications.items():
            print "Linting notification %s"%key
            result=instance.lint()
            if result:
                print "=> %s OK"%key
            else:
                print "=> %s FAILED"%key
            
    
    def configfail(self,section,option,message):
        import sys
        msg="Invalid config .. section=[%s] option=%s problem: %s"%(section,option,message)
        logging.error(msg)
        print msg
        sys.exit()
       
    def _get_value(self,config,section,option,defaultvalue=None):
        """get value from section, None if section or option not available and default is None"""
        if config.has_option(section,option):
            return config.get(section,option)
        else:
            return defaultvalue 
        
    def initFromConfig(self,config):
        self.tests=[]
        
        #lint result
        usedchecksections={}
        usednotificationsections={}
        
        #find all tests
        for sec in config.sections():
            #logging.debug("section:"+sec)
            
            if not sec.startswith('Test_'):
                continue
            
            test=MonstaTest()
            test.section=sec

            if config.has_option(sec,'requires'):
                req=config.get(sec,'requires').strip().lower()
                if req=='any':
                    test.requires=MonstaTest.REQUIRES_ANY
                elif req=='all' or req=='':
                    test.requires=MonstaTest.REQUIRES_ALL
                else:
                    self.configfail(sec, 'requires', "Unknown value %s. allowed: any or all"%req)
                    return
        
            if config.has_option(sec,'interval'):
                intv=config.getint(sec,'interval')
                test.interval=intv
            
            
            #loop through checks
            if not config.has_option(sec,'checks'):
                self.configfail(sec,'checks', "missing")
                return
            
            
            checknames=self.config.get(sec,'checks').strip().split()
            for checkname in checknames:
                
                
                checksection='Check_%s'%checkname
                if not config.has_section(checksection):
                    self.configfail(checksection,'(n/a)',"missing config section for this check")
                    return
                
                
                if not config.has_option(checksection,'type'):
                    self.configfail(checksection,'type',"missing")
                    return
                    
                checktype=config.get(checksection,'type')
                
                if checktype not in self.supportedchecktypes:
                    self.configfail(checksection, 'type', "Unsupported checktype: %s"%checktype)
                    return
                
                checkclass=self.supportedchecktypes[checktype]
                checkinstance=checkclass()
                checkinstance.section=checksection
                
                usedchecksections[checksection]=checkinstance
                
                #get all configs
                defaultconfig=checkinstance.configvars
                actualconfig={}
                for key,defaultvalue in defaultconfig.iteritems():
                    defaultvalue=self._get_value(self.config,"%s_default"%checktype,key,defaultvalue)
                    
                    if config.has_option(checksection,key):
                        actualconfig[key]=config.get(checksection,key)
                    else:
                        if defaultvalue==None:
                            self.configfail(checksection, key, "missing option and no default available")
                        else:
                            actualconfig[key]=defaultvalue
                checkinstance.configvars=actualconfig
                
                #couple checks and test
                test.checks.append(checkinstance)
                checkinstance.test=test
            
            
            #loop through notifications
            if self.config.has_option(sec,'notify'):
                notify=self.config.get(sec,'notify').strip().split()
            else:
                logging.warning("Section %s has no notify option - this group will only be available for statistics"%sec)
                notify=[]
       
            for nblock in notify:
                all_notifications=[]
                try:
                    (level,anblock)=nblock.split(':',1)
                    level=int(level)
                    all_notifications=anblock.split(',')
                except:
                    self.configfail(sec, 'notify', "could not parse")
                
                test.notifications[level]=[]
                
                for notification in all_notifications:
                    checksection='Notification_%s'%notification
                    if not config.has_section(checksection):
                        self.configfail(checksection,'(n/a)',"missing config section for this notification")
                        return
                    
                    
                    if not config.has_option(checksection,'type'):
                        self.configfail(checksection,'type',"missing")
                        return
                        
                    if not config.has_option(checksection,'recipient'):
                        self.configfail(checksection,'recipient',"missing")
                        return
                    
                    recipient=config.get(checksection,'recipient').strip()
                    checktype=config.get(checksection,'type').strip()
                    
                    if checktype not in self.supportednotifications:
                        self.configfail(checksection, 'type', "Unsupported notification type: %s"%checktype)
                        return
                    
                    notifyclass=self.supportednotifications[checktype]
                    notifyinstance=notifyclass()
                    notifyinstance.section=checksection
                    notifyinstance.recipient=recipient
                    usednotificationsections[checksection]=notifyinstance
      
                    defaultconfig=notifyinstance.configvars
                    actualconfig={}
                    for key,defaultvalue in defaultconfig.iteritems():
                        defaultvalue=self._get_value(self.config,"%s_default"%checktype,key,defaultvalue)
                                                    
                        if config.has_option(checksection,key):
                            actualconfig[key]=config.get(checksection,key)
                        else:
                            if defaultvalue==None:
                                self.configfail(checksection, key, "missing option and no default available")
                            else:
                                actualconfig[key]=defaultvalue
                    notifyinstance.configvars=actualconfig
                
                
                    test.notifications[level].append(notifyinstance)
            
            #all config done    
            self.tests.append(test)
        
        return usedchecksections,usednotificationsections
