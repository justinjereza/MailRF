#!/usr/bin/env python

# Pass -O to python for __debug__ == False. This will run the script as a daemon
# accepting connections on working_dir/socket and logging to the syslog mail
# facility. If __debug__ == True, the daemon will listen on localhost port 8027
# and log to sys.stderr.

import os, sys, pwd, grp, platform

from logging import INFO
from syslog import LOG_MAIL, LOG_PID
from signal import signal, SIGHUP, SIGUSR1
from email.utils import parseaddr, getaddresses
from twisted.python import log, syslog
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory

if __debug__:
    from twisted.internet.endpoints import TCP4ServerEndpoint
else:
    from twisted.internet.endpoints import UNIXServerEndpoint

system = platform.system()
if system == 'Linux':
    pw = pwd.getpwnam('mail')
    uid = pw[2]
    gid = pw[3]
elif system == 'Darwin':
    uid = pwd.getpwnam('root')[2]
    gid = grp.getgrnam('mail')[2]

if __debug__:
    working_dir = os.path.dirname(__file__)
else:
    working_dir = '/var/mailrf'
    os.mkdir(working_dir)

lists = {
    'secure': working_dir + '/secure.txt',
    'restrict': working_dir + '/restrict.txt'
}

class MailField(object):
    def __init__(self, s):
        self.value = s

    def __str__(self):
        return self.value

class MultiMailField(object):
    def __init__(self, s):
        self.value = [ s ]

    def __str__(self):
        return str(self.value)

    def __iter__(self):
        return self.value.__iter__()

    def append(self, s):
        self.value.append(s)

class HeaderMailField(MailField):
    def __init__(self, s):
        super(HeaderMailField, self).__init__(parseaddr(s)[1])

class HeaderMultiMailField(MultiMailField):
    def __init__(self, s):
        for i in getaddresses([ s ]):
            if hasattr(self, 'value'):
                super(HeaderMultiMailField, self).append(i[1])
            else:
                super(HeaderMultiMailField, self).__init__(i[1])

class EnvFrom(MailField):
    pass

class EnvRcpt(MultiMailField):
    pass

class HeaderTo(HeaderMultiMailField):
    pass

class HeaderCC(HeaderMultiMailField):
    pass

class HeaderFrom(HeaderMailField):
    pass

class MailRfReceiver(LineReceiver):
    @classmethod
    def init(cls, d):
        cls.lists = v = dict()

        for i in d:
            v[i] = {
                d[i]: list()
            }
        cls.initLists()

    @classmethod
    def initLists(cls, *args):
        v = cls.lists

        for i in v:
            for j in v[i]:
                v[i][j] = cls._readList(j)
        log.msg('Lists initialized.', logLevel=INFO)

    @classmethod
    def logLists(cls, *args):
        v = cls.lists
        for i in v:
            u = [ v[i][j] for j in v[i] ][0]
            log.msg('%s LIST: %s' % (i.upper(), u), logLevel=INFO)

    def connectionMade(self):
        self.num = self.factory.spawn
        self.factory.spawn = self.factory.spawn + 1
        log.msg('*[%08X] *** CONNECTION MADE ***' % self.num, logLevel=INFO)

    def connectionLost(self, reason):
        log.msg('*[%08X] *** CONNECTION LOST *** %s' % (self.num, reason), logLevel=INFO)

    def lineReceived(self, line):
        if line == 'PROCESS':
            v = self.lists['secure']
            secure_list = [ v[i] for i in v ][0]
            v = self.lists['restrict']
            restrict_list = [ v[i] for i in v ][0]

            secure = False
            env_remove = list()
            log.msg('*[%08X] *** PROCESSING ***' % self.num, logLevel=INFO)
            if hasattr(self, 'envFrom'):
                log.msg('*[%08X] ENV FROM    : %s' % (self.num, self.envFrom), logLevel=INFO)
            if hasattr(self, 'envRcpt'):
                log.msg('*[%08X] ENV RCPT    : %s' % (self.num, self.envRcpt), logLevel=INFO)
            if hasattr(self, 'headerTo'):
                log.msg('*[%08X] HEADER TO   : %s' % (self.num, self.headerTo), logLevel=INFO)
            if hasattr(self, 'headerCC'):
                log.msg('*[%08X] HEADER CC   : %s' % (self.num, self.headerCC), logLevel=INFO)
            if hasattr(self, 'headerFrom'):
                log.msg('*[%08X] HEADER FROM : %s' % (self.num, self.headerFrom), logLevel=INFO)

            if hasattr(self, 'headerTo'):
                for i in self.headerTo:
                    if i in secure_list:
                        secure = True

            if hasattr(self, 'headerCC'):
                for i in self.headerCC:
                    if i in secure_list:
                        secure = True

            if hasattr(self, 'headerFrom'):
                # str() is used to force string interpretation
                if str(self.headerFrom) in secure_list:
                    secure = True

            log.msg('*[%08X] SECURE      : %s' % (self.num, secure), logLevel=INFO)

            if secure:
                for i in self.envRcpt:
                    if i in restrict_list and i not in self.headerTo:
                        env_remove.append(i)

                for i in env_remove:
                    self.sendLine(i)
            self.sendLine('EOF')

            log.msg('*[%08X] ENV REMOVE  : %s' % (self.num, env_remove), logLevel=INFO)
        elif line.startswith('ENVFROM: '):
            self.envFrom = EnvFrom(line[9:len(line)])
        elif line.startswith('ENVRCPT: '):
            rcpt = line[9:len(line)]
            if hasattr(self, 'envRcpt'):
                if rcpt not in self.envRcpt:
                    self.envRcpt.append(rcpt)
            else:
                self.envRcpt = EnvRcpt(rcpt)
        elif line.startswith('TO: '):
            if not hasattr(self, 'headerTo'):
                self.headerTo = HeaderTo(line[4:len(line)])
        elif line.startswith('CC: '):
            if not hasattr(self, 'headerCC'):
                self.headerCC = HeaderCC(line[4:len(line)])
        elif line.startswith('FROM: '):
            if not hasattr(self, 'headerFrom'):
                self.headerFrom = HeaderFrom(line[6:len(line)])
        elif line.startswith('DEBUG'):
            log.msg(line, logLevel=INFO)
        else:
            self.transport.loseConnection()

    @classmethod
    def _readList(cls, filename):
        v = list()

        with open(filename) as f:
            for i in f:
                v.append(i.strip())
        return v

class MailRfFactory(Factory):
    protocol = MailRfReceiver

    def __init__(self):
        self.spawn = 1

        MailRfReceiver.init(lists)
        signal(SIGHUP, MailRfReceiver.initLists)
        signal(SIGUSR1, MailRfReceiver.logLists)

if __name__ == '__main__':
    if not __debug__:
        os.setgid(gid)
        os.setuid(uid)

        # Initial fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit()
        except OSError, e:
            print e
            sys.exit(1)

        # Give process it's own session under init
        os.setsid()

        # Final fork
        try:
            pid = os.fork()
            if pid > 0:
                pid_file = open(working_dir + '/mailrfd.pid', 'w')
                pid_file.write(str(pid))
                pid_file.close()
                sys.exit()
        except OSError, e:
            print e
            sys.exit(1)

    if __debug__:
        log.startLogging(sys.stderr)
    else:
        syslog.startLogging(prefix='mailrfd', options=LOG_PID, facility=LOG_MAIL)

    if __debug__:
        endpoint = TCP4ServerEndpoint(reactor, 8027, interface='localhost')
    else:
        endpoint = UNIXServerEndpoint(reactor, working_dir + '/socket')

    endpoint.listen(MailRfFactory())
    reactor.run()
