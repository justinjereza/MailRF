from mailrfd import lists, MailRfReceiver, MailRfFactory
from twisted.trial import unittest
from twisted.test import proto_helpers

class MailRfFactoryTestCase(unittest.TestCase):
	def setUp(self):
		factory = MailRfFactory()
		self.proto = factory.buildProtocol(('127.0.0.1', 0))
		self.tr = proto_helpers.StringTransport()
		self.proto.makeConnection(self.tr)
		
	def testDebugReceived(self):
		self.proto.dataReceived('DEBUG: ACK ACK ACK\r\n')

	def testLineReceived(self):
		'''
				msg = \
		ENVFROM: trent@example.net
		ENVRCPT: alice@example.com
		ENVRCPT: bob@example.com
		ENVRCPT: charlie@example.com
		ENVRCPT: eve@example.com
		ENVRCPT: oscar@example.com
		TO: alice@example.com
		CC: bob@example.com, charlie@example.com
		FROM: trent@example.com
		PROCESS
		'''
		self.proto.dataReceived('ENVFROM: trent@example.net\r\n')
		self.proto.dataReceived('ENVRCPT: alice@example.com\r\n')
		self.proto.dataReceived('ENVRCPT: bob@example.com\r\n')
		self.proto.dataReceived('ENVRCPT: charlie@example.com\r\n')
		self.proto.dataReceived('ENVRCPT: eve@example.com\r\n')
		self.proto.dataReceived('ENVRCPT: oscar@example.com\r\n')
		self.proto.dataReceived('TO: alice@example.com\r\n')
		self.proto.dataReceived('CC: bob@example.com, charlie@example.com\r\n')
		self.proto.dataReceived('FROM: trent@example.com\r\n')
		self.proto.dataReceived('PROCESS\r\n')
		print '\n\nRESPONSE'
		print '========'
		print self.tr.value() + '========'

class MailRfReceiverTestCase(unittest.TestCase):
	def _testListStructure(self):
		v = MailRfReceiver.lists

		self.assertTrue(v)
		self.assertIsInstance(v, dict)
		for i in v:
			self.assertIsInstance(i, str)
			d = v[i]
			self.assertIsInstance(d, dict)
			for j in d:
				self.assertIsInstance(j, str)
				self.assertIsInstance(d[j], list)

	def _testListLengths(self):
		v = MailRfReceiver.lists['secure']
		for i in v:
			self.assertEqual(len(v[i]), 2)
		v = MailRfReceiver.lists['restrict']
		for i in v:
			self.assertEqual(len(v[i]), 3)

	def testInit(self):
		MailRfReceiver.init(lists)
		self._testListStructure()
		self._testListLengths()

	def testInitLists(self):
		MailRfReceiver.initLists()
		self._testListStructure()
		self._testListLengths()

	def testLogLists(self):
		MailRfReceiver.logLists()