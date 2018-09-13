monsta
======

!! NOTE - monsta has moved to https://gitlab.com/fumail/monsta/ - This repository will no longer be updated and eventually deleted !!

A simple light-weight system and service monitoring daemon written in python

Supported Checks
----------------

Generic: 

 * check if port is available and optionally responding with a expected string on connect
 * run a script and check exit status/ouput

Mail:

 * simple SMTP : check if smtp server responds and accepts mail (tests up to the RCPT TO stage, not actually sending mail)
 * full Mailflow monitoring: sends a mail via smtp and retrieves that mail again from an IMAP box

DNS:

 * monitor DNS record availability
 * monitor DNS Synchronisation between DNS Servers (compare Zone Serial)


Supported Notification Types
----------------------------

 * Chat: Jabber/XMPP
 * SMS: Clickatell
 * E-Mail (SMTP)



Installation
------------

requirements:
for jabber/xmpp support
> easy_install xmpppy

required for dns checks:
> easy_install pydns


install monsta:
> python setup.py install


Configuration
-------------

The ini-style configuration is done in '/etc/monsta/monsta.conf' (you may use multiple config files as well by putting *.conf files
in '/etc/monsta/conf.d')


Section types:

Checks : A single check if a service is available, say "port 80 on host example.com is reachable"

Tests : Tests contain one or more checks and define what should happen if one or more checks fail.
		You need at least one test with one check. Tests also define who should be notified after how many failed attempts.
		
Notifications: Monsta supports various ways to notify a user (Email, Chat messages, SMS, ...)
Each recipient requires its own configuration section


Defining notifications:

	[Notification_somename] # must start with Notification_
	type=notificationtype  # what type of notification (jabber, email, sms,....) run monsta --help notification a list of supported types 

example:

	[Notification_smtp_bob]
	type=smtp
	recipient=bob@example.com
	sender=monsta@example.net

Defining Checks:

	[Check_checkname] #must start with Check_
	type=portconnect #type of the check. run monsta --help check to get a list of supported types
	additional fields here, based on the type



Defining Tests:


	[Test_testname] # must start with Test_
	checks=checkname1 checkname2 ... # list of checks separated by space.
	interval=300 # how often should the checks in this test be run (seconds)
	requires=all # 'all' or 'any'. All: all checks must succeed for the test to succeed. 'any': At least one check must succeed, the others may fail
	
	# notification/escalations: the number before the colon defines how many times the test must fail until the notifications happens.
	# in the example below, a smtp message and a jabber message would be sent to bob after 1 failure
	# an sms message to bob would be sent after 2 failures
	# an sms message to the boss would be sent after 5 failures
	# the counter is reset to 0 if a test succeeds
	# 0 is allowed as well, if you want a message every time a test has been performed
	notify=1:smtp_bob,jabber_bob 2:sms_bob 5:sms_boss 


Logging
-------
By default, monsta will write to syslog. You should see output in `/var/log/messages` or `/var/log/daemon.log` (depending on you distro)

You can override the logging behaviour by creating a file `/etc/monsta/logging.conf`
see http://docs.python.org/2/library/logging.config.html#logging-config-fileformat for the format this file should have.

Here is a example I use on a raspberry pi which logs to a file in the ramdisk(to preserve the sd card) and just keeps the last 3 hours of log history.


::

	[loggers]
	keys=root
	
	[handlers]
	keys=logfile
	
	[formatters]
	keys=logfileformatter
	
	[logger_root]
	level=INFO
	handlers=logfile
	
	[handler_logfile]
	class=handlers.TimedRotatingFileHandler
	level=NOTSET
	args=('/dev/shm/monsta.log','h',1,3)
	formatter=logfileformatter

