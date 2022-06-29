#!/usr/bin/python
# -*- coding: utf-8 -*-

import pogoda_g_plugin

wz_cache = {'public':{}, 'private':{}}
cache_ttl = 600
wz_clients = {}

version = 'unknown'

import sha
#import email, os, signal, smtplib, sys, time, traceback, xmpp
import os, signal, sys, time, traceback, xmpp, md5
from xmpp.browser import *
#from email.MIMEText import MIMEText
#from email.Header import decode_header
import config, xmlconfig
import threading


def get_gism(node, short):
	pub = 'public' if short else 'private'
	try:
		code = int(unicode(node).split('@')[0])
	except:
		print "can't get code for node",[node]
		return None
	if (code in wz_cache[pub]) and (time.time() - wz_cache[pub][code][0] < cache_ttl):
			wz = wz_cache[pub][code][1]
	else:
			wz_cache[pub][code] = time.time(),pogoda_g_plugin.get_weather_g(code,pub)
	return wz_cache[pub][code][1]


class Transport:

	online = 1
	restart = 0
	offlinemsg = ''

	def __init__(self,jabber):
		self.jabber = jabber
		self.watchdir = config.watchDir
		self.domain = config.mainServerJID
		self.usercfg_load()
		self.msglock = threading.Lock()
		if '~' in self.watchdir:
			self.watchdir = self.watchdir.replace('~', os.environ['HOME'])
		# A list of two element lists, 1st is xmpp domain, 2nd is email domain
		#self.mappings = [mapping.split('=') for mapping in config.domains]
		#email.Charset.add_charset( 'utf-8', email.Charset.SHORTEST, None, None )
		self.Features = {
						'ids':[
							{'category':'presence','type':'text','name':config.discoName}],
						'features':[NS_VERSION,NS_COMMANDS,NS_GATEWAY,NS_REGISTER,NS_DISCO_INFO]}
		self.online_users = {}

	def register_handlers(self):
		self.jabber.RegisterHandler('message', self.xmpp_message)
		self.jabber.RegisterHandler('presence',self.xmpp_presence)
		self.jabber.RegisterHandler('iq',      self.xmpp_iq)
		self.disco = Browser()
		self.disco.PlugIn(self.jabber)
		self.disco.setDiscoHandler(self.xmpp_base_disco,node='',jid=config.jid)
		
	# IQ Handlers
	def xmpp_iq(self, conn, iq):
		print '======================= iq: ',[self], [conn], [iq]
		ns = iq.getQueryNS()
		typ = iq.getType()
		if ns == xmpp.NS_GATEWAY:
			self.iq_gateway_handler(iq)
#		elif ns == xmpp.NS_STATS:
#			self.iq_stats_handler(iq)
#		elif ns == xmpp.NS_TIME:
#			self.iq_time_handler(iq, 'old')
#		elif iq.getTag('time') and iq.getTag('time').getNamespace() == xmpp.NS_NEW_TIME:
#			self.iq_time_handler(iq, 'new')
#		elif ns == xmpp.NS_LAST:
#			self.iq_last_handler(iq)
#		elif ns == xmpp.NS_SEARCH:
#			self.iq_search_handler(iq)
#		elif ns == xmpp.NS_VERSION:
#			self.iq_version_handler(iq)
#		elif iq.getTag('vCard') and iq.getTag('vCard').getNamespace()==xmpp.NS_VCARD:
#			self.iq_vcard_handler(iq)
#		elif iq.getTag('command') and iq.getTag('command').getNamespace()==xmpp.NS_COMMANDS:
#			self.iq_command_handler(iq)
		elif ns == xmpp.NS_DISCO_INFO:
			print 'executing',xmpp.NS_DISCO_INFO
			pass
			#print 'executing',xmpp.NS_DISCO_INFO
			#self.iq_disco_info_handler(iq)
#		elif ns == xmpp.NS_DISCO_ITEMS:
#			self.iq_disco_items_handler(iq)
#		elif iq.getTag('ping') and iq.getTag('ping').getNamespace() == xmpp.NS_PING:
#			self.iq_ping_handler(iq)
		elif ns == xmpp.NS_REGISTER:
			self.iq_register_handler(iq)
			print "*****self.iq_register_handler(iq) exits"
		else:
			print "***************************************",ns
			self.send_not_implemented(iq)
		
	def iq_disco_info_handler(self, iq):
		jid_from = iq.getFrom()
		jid_from_stripped = jid_from.getStripped()
		jid_to = iq.getTo()
		jid_to_stripped = jid_to.getStripped()
		typ = iq.getType()
		_id = iq.getAttr('id')
		node = iq.getTagAttr('query','node')
		print "INFO",jid_from, jid_to, typ, _id, node
		if jid_to_stripped==config.jid and typ=='get' and ((not node) or (node == '#'.join((utils.NODE, utils.SERVER_CAPS)))):
			#If node is empty or equal NODE#SERVER_CAPS then returm disco
			reply = iq.buildReply(typ='result')
			reply.setQueryPayload(self.Features)
			self.jabber.send(reply)
		print "INFO2",jid_from, jid_to, typ, _id, node
		
	def iq_register_handler(self, iq):
		jid_from = iq.getFrom()
		jid_from_stripped = jid_from.getStripped()
		jid_to = iq.getTo()
		jid_to_stripped = jid_to.getStripped()
		typ = iq.getType()
		iq_children = iq.getQueryChildren()
		print "REGISTER ",jid_from, jid_to, typ, iq_children
		if (typ=='get') and (jid_to_stripped==config.jid) and (not iq_children):
			repl = iq.buildReply(typ='result')
			repl.setQueryPayload(self.get_register_form(jid_from_stripped))
			self.jabber.send(repl)
			raise NodeProcessed
		#elif typ == 'set' and (jid_to_stripped==config.jid) and iq_children:
		elif typ == 'set' and (jid_to_stripped==config.jid): #to additional commands use ^^^
			query_tag = iq.getTag('query')
			#if 1:#query_tag.getTag('email') and query_tag.getTag('password'):
			if query_tag.getTag('nick'):
				'''user = query_tag.getTagData('email')
				password = query_tag.getTagData('password')
				error = xmpp.ERR_BAD_REQUEST
				if not user:
					text = i18n.NULL_EMAIL
					self.send_error(iq,error,text)
					return
				if not password:
					text = i18n.NULL_PASSWORD
					self.send_error(iq,error,text)
					return
				if not utils.is_valid_email(user):
					text = i18n.UNACCEPTABLE_EMAIL
					self.send_error(iq,error,text)
					return
				if not utils.is_valid_password(password):
					text = i18n.UNACCEPTABLE_PASSWORD
					self.send_error(iq,error,text)
					return
				mmp_conn = pool.get(jid_from)
				if mmp_conn:
					mmp_conn.exit()
				self.mrim_connection_start(jid_from, iq_register=iq)
				'''
				repl = iq.buildReply(typ='result')
				self.jabber.send(repl)
				sub = xmpp.Presence(to=jid_from_stripped,frm=config.jid)
				sub.setType('subscribe')
				self.jabber.send(sub)
				print "REGISTERED with",jid_from_stripped
				
				md = md5.md5(jid_from.getStripped()).hexdigest()
				m = Message(to=jid_from,frm = jid_to, body = 'Registration successful. Use JIDs like NUMBER@gismeteo.jabbercity.ru, where number is gismeteo city code, for example, 34731')
				self.jabber.send(m)
				
				raise NodeProcessed
	
			elif query_tag.getTag('remove'):
				#account = spool.Profile(jid_from_stripped)
				if 1:#account.remove():
					#spool.Options(jid_from).remove()
					ok_iq = iq.buildReply(typ='result')
					ok_iq.setPayload([],add=0)
					self.jabber.send(ok_iq)
					unsub = xmpp.Presence(to=jid_from_stripped,frm=config.jid)
					unsub.setType('unsubscribe')
					self.jabber.send(unsub)
					unsub.setType('unsubscribed')
					self.jabber.send(unsub)
					
					print "RAISE!!!"
					raise NodeProcessed
				else:
					pass

					
	def get_register_form(self, jid):
		user = ''#'spool.Profile(jid).getUsername()'
		instr = xmpp.Node('instructions')
		instr.setData(u"webpresence registration. Ник не заполнять, ибо костыль.")
		#email = xmpp.Node('email')
		nick = xmpp.Node('nick')
		passwd = xmpp.Node('password')
		if user:
			reg = xmpp.Node('registered')
			email.setData(user)
			return [instr,reg,email,passwd]
		else:
			#email.setData('fake')
			return [instr,nick]
			return [instr,email]
		
	def iq_gateway_handler(self, iq):
		jid_to = iq.getTo()
		jid_to_stripped = jid_to.getStripped()
		iq_children = iq.getQueryChildren()
		typ = iq.getType()
		if (typ=='get') and (jid_to_stripped==config.jid) and (not iq_children):
			repl = iq.buildReply(typ='result')
			query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_GATEWAY})
#			query.setTagData('desc', i18n.ENTER_EMAIL)
			query.setTagData('desc', u'enter e-mail')
			query.setTag('prompt')
			repl.setPayload([query])
			self.jabber.send(repl)
		elif (typ=='set') and (jid_to_stripped==config.jid) and iq_children:
			e_mail = [node.getData() for node in iq_children if node.getName()=='prompt']
			if len(e_mail) == 1:
				prompt = xmpp.simplexml.Node('jid')
#				prompt.setData(utils.mail2jid(e_mail[0]))
				prompt.setData(e_mail[0].replace('@', '%') + '@' + config.jid)
				repl = iq.buildReply(typ='result')
				repl.setQueryPayload([prompt])
				self.jabber.send(repl)
			else:
				self.jabber.send_bad_request(iq)
		else:
			self.jabber.send_not_implemented(iq)
			
	def send_not_implemented(self, iq):
		if iq.getType() in ['set','get']:
			self.send_error(iq)

	def send_bad_request(self, iq):
		if iq.getType() in ['set','get']:
			self.send_error(iq,xmpp.ERR_BAD_REQUEST)

	def send_error(self, stanza, error=xmpp.ERR_FEATURE_NOT_IMPLEMENTED, text='', reply=1):
		e = xmpp.Error(stanza,error,reply)
		if text:
			e.getTag('error').setTagData('text', text)
			e.getTag('error').getTag('text').setAttr('xml:lang','ru-RU')
		else:
			e.getTag('error').delChild('text')
		self.jabber.send(e)


	# Disco Handlers
	def xmpp_base_disco(self, con, event, type):
		fromjid = event.getFrom().__str__()
		to = event.getTo()
		node = event.getQuerynode();
		#Type is either 'info' or 'items'
		if to == config.jid:
			if node == None:
				if type == 'info':
					return self.Features
				if type == 'items':
					return []
			else:
				self.jabber.send(Error(event,ERR_ITEM_NOT_FOUND))
				raise NodeProcessed
		else:
			self.jabber.send(Error(event,MALFORMED_JID))
			raise NodeProcessed

	#XMPP Handlers
	def xmpp_presence(self, con, event):
		# Add ACL support
		fromjid = event.getFrom()
		type = event.getType()
#		print dir(type),type
		show = event.getShow()
		status = event.getStatus()
#		print dir(event)
		to = event.getTo()
		try:
			print "pres===============",fromjid,to,type,show
		except:
			print "pres===============XRENNNN"
		if type == 'subscribe':
			self.jabber.send(Presence(to=fromjid, frm = to, typ = 'subscribe'))
		elif type == 'subscribed':
			self.jabber.send(Presence(to=fromjid, frm = to, typ = 'subscribed'))
		elif type == 'unsubscribe':
			self.jabber.send(Presence(to=fromjid, frm = to, typ = 'unsubscribe'))
		elif type == 'unsubscribed':
			self.jabber.send(Presence(to=fromjid, frm = to, typ = 'unsubscribed'))
		elif type == 'probe':
			print "PROBE",self.usr_show(fromjid, type, show)
			self.jabber.send(Presence(to=fromjid, frm = to))
		elif type == 'unavailable':
			self.pres_exec(to, fromjid, type, show)
			self.jabber.send(Presence(to=fromjid, frm = to, typ = 'unavailable'))
		elif type == 'error':
			return
		else:
			if not fromjid.getStripped() in wz_clients: wz_clients[fromjid.getStripped()]=[]
			if not to.getStripped() in wz_clients[fromjid.getStripped()]: 
				if '@' in to.getStripped():
					wz_clients[fromjid.getStripped()].append(to.getStripped())
			
			wz = self.pres_exec(to, fromjid, type, show)
			if wz: status=wz
#			print "pres===============",fromjid,to,type,show
#			try: print str(event)
#			except: pass
			self.jabber.send(Presence(to=fromjid, frm = to, typ = type, show=show, status=status))

	def usr_show(self, jid, type, show):
		res = jid.getResource()
		jid = jid.getStripped()
		prio= 0
		
		unavail = 0
		if type == 'unavailable':
			show = 'unavailable'
			unavail = 1
		elif not type and not show:
			show = 'available'
		#return show
		
		# self.online_users = {}
		# self.online_users[jid] = {}
		# self.online_users[jid][res] = {}
		# self.online_users[jid][res]['prio'] = prio
		# self.online_users[jid][res]['show'] = show
		
		if unavail:
			if self.online_users.has_key(jid):
				if self.online_users[jid].has_key(res):
					del self.online_users[jid][res]
				if not len(self.online_users[jid]):
					del self.online_users[jid]
#			print 'self.online_users=',self.online_users
			return show
		else:
			if not self.online_users.has_key(jid):
				self.online_users[jid] = {res:{'prio':prio, 'show':show}}
			else:
				self.online_users[jid][res] = {'prio': prio, 'show': show}
				
			maxprio = -100
			for res in self.online_users[jid]:
				pr = self.online_users[jid][res]['prio']
				if pr > maxprio:
					maxprio = prio
					show = self.online_users[jid][res]['show']
#			print 'self.online_users=',self.online_users
			return show
				
	def pres_exec(self, tojid, jid, type, show):
			
		show = self.usr_show(jid, type, show)
		jid=jid.getStripped()

		print tojid,jid,type,show
		return get_gism(tojid, short=1)

	def xmpp_message(self, con, event):
		
		print "mess==============="
		mtype = event.getType()
		fromjid = event.getFrom()
		fromstripped = fromjid.getStripped()
		to = event.getTo()
		try:
			if event.getSubject.strip() == '':
				event.setSubject(None)
		except AttributeError:
			pass
		if event.getBody() == None:
			return

		if to.getNode() != '':
			wz = get_gism(to, short=0)
			m = Message(to=fromjid,frm = to, body = wz)
			self.jabber.send(m)
		else:
			body = event.getBody()
#			m = Message(to=fromjid,frm = to, subject = event.getSubject(), body = u'you sent me "%s". WHY???'%(body))
			self.command_handler(fromjid,to,body)

	def command_handler(self,fromjid,to,body):
		def reply(to,body):
#			if not isinstance(body, unicode):
#				body = body.decode('utf8', 'replace')
			m = Message(to=fromjid,frm = to, body = body)
			self.jabber.send(m)
		def onoff(arg):
			if arg:return 'on'
			else:return 'off'

		body = body.split(' ',1)
		if len(body) == 1:
			body.append('')
		elif len(body) > 2 or len(body) < 1:
			reply(to,'хз чо за косяк')
			return
		cmd,params = body
					
		cmd = cmd.lower().strip()
		params = params.lower().strip().split()
		user = fromjid.getStripped().split('@'+self.domain)
		
		if fromjid.getStripped() != 'adminko@server.tld':
			print fromjid.getStripped()
			return

		print 'user',[user]
		if len(user) == 2 and user[1] == '':
			user = user[0]
		else:
			reply(to,'Пшёл вон, я хз кто ты!')
			return
		help = {}
		help['config'] = 'examples:\n config enabled on\n config enabled off\n config autoremove on\n config autoremove off\n config singlecontact on\n config singlecontact off'
		
		if cmd == 'online':
			reply(to, str(self.online_users))
		elif cmd == 'wz':
			reply(to, str(wz_clients))
		elif cmd == 'config':
			if len(params)==0:
					rep='current config:\n'
					for x in ['enabled','autoremove','singlecontact']:
						rep+='- %s: %s\n'%(x,onoff(self.usercfg_get(user,x)))
					reply(to,rep)
			elif len(params)==2:
				if params[0] == 'enabled':
					if params[1] == 'on':
						self.usercfg_set(user,'enabled',1)
						reply(to,'ok, %s is ON'%user)
					elif params[1] == 'off':
						self.usercfg_set(user,'enabled',0)
						reply(to,'ok, %s is OFF'%user)
					else:
						reply(to,'wrong params. %s'%help[cmd])
				elif params[0] == 'autoremove':
					if params[1] == 'on':
						self.usercfg_set(user,'autoremove',1)
						reply(to,'ok, %s autoremove is ON'%user)
					elif params[1] == 'off':
						self.usercfg_set(user,'autoremove',0)
						reply(to,'ok, %s autoremove is OFF'%user)
					else:
						reply(to,'wrong params. %s'%help[cmd])
				elif params[0] == 'singlecontact':
					if params[1] == 'on':
						self.usercfg_set(user,'singlecontact',1)
						reply(to,'ok, %s singlecontact mode is ON'%user)
					elif params[1] == 'off':
						self.usercfg_set(user,'singlecontact',0)
						reply(to,'ok, %s singlecontact mode is OFF'%user)
					else:
						reply(to,'wrong params. %s'%help[cmd])
				else:
					reply(to,'%s'%help[cmd])
			else:
				reply(to,help[cmd])
		elif cmd == 'list':
			pass
		else:
			reply(to,'...')
			
	def oldmails_load(self,user):
		userpath=self.watchdir+self.domain+'/'+user+'/'
		try:
			state=read_file(userpath+'oldmails.py')
		except:
			state={}
		return state
		
	def oldmails_save(self,user,state):
		try:
			userpath=self.watchdir+self.domain+'/'+user+'/'
			write_file(userpath+'oldmails.py',state)
		except:
			logError()
			
	def usercfg_load(self):
		try:
			self.usercfg=read_file('usercfg.py')
		except:
			self.usercfg={}
			
	def usercfg_save(self):
		try:
			write_file('usercfg.py',self.usercfg)
		except:
			logError()

	def usercfg_set(self,user,parm,value):
		if not self.usercfg.has_key(user):
			self.usercfg[user]={}
		self.usercfg[user][parm]=value
		self.usercfg_save()
			
	def usercfg_get(self,user,parm):
		if not self.usercfg.has_key(user):
			self.usercfg[user]={}
		if not self.usercfg[user].has_key(parm):
			if parm=='enabled':
				return 1
			if parm=='autoremove':
				return 1
			if parm=='singlecontact':
				return 0
			else:
				logError()
				raise AttributeError
		else:
			return self.usercfg[user][parm]
			
	def mail_check(self):
		if time.time()<transport.lastcheck: return
		transport.lastcheck = time.time() + cache_ttl

		print "check.........."
		# self.online_users = {}
		# self.online_users[jid] = {}
		# self.online_users[jid][res] = {}
		# self.online_users[jid][res]['prio'] = prio
		# self.online_users[jid][res]['show'] = show
		for jid in self.online_users:
			for res in self.online_users[jid]:
				if jid in wz_clients:
					for node in wz_clients[jid]:
						wz = get_gism(node, short=1)
						if wz: status=wz
						else: status='<???>'
						self.jabber.send(Presence(to=jid, frm = node, show='chat', status=status))

		print "checked."

	def xmpp_connect(self):
		connected = self.jabber.connect((config.mainServer,config.port))
		if config.dumpProtocol: print "connected:",connected
		while not connected:
			time.sleep(5)
			connected = self.jabber.connect((config.mainServer,config.port))
			if config.dumpProtocol: print "connected:",connected
		self.register_handlers()
		if config.dumpProtocol: print "trying auth"
		connected = self.jabber.auth(config.saslUsername,config.secret)
		if config.dumpProtocol: print "auth return:",connected
		return connected

	def xmpp_disconnect(self):
		time.sleep(5)
		if not self.jabber.reconnectAndReauth():
			time.sleep(5)
			self.xmpp_connect()

def loadConfig():
	configOptions = {}
	for configFile in config.configFiles:
		if os.path.isfile(configFile):
			xmlconfig.reloadConfig(configFile, configOptions)
			config.configFile = configFile
			return
	print "Configuration file not found. You need to create a config file and put it in one of these locations:\n	" + "\n	".join(config.configFiles)
	sys.exit(1)

def logError():
	err = '%s - %s\n'%(time.strftime('%a %d %b %Y %H:%M:%S'),version)
	if logfile != None:
		logfile.write(err)
		traceback.print_exc(file=logfile)
		logfile.flush()
	sys.stderr.write(err)
	traceback.print_exc()
	sys.exc_clear()

def sigHandler(signum, frame):
	transport.offlinemsg = 'Signal handler called with signal %s'%signum
	if config.dumpProtocol: print 'Signal handler called with signal %s'%signum
	transport.online = 0

if __name__ == '__main__':
	if 'PID' in os.environ:
		config.pid = os.environ['PID']
	loadConfig()
	if config.pid:
		pidfile = open(config.pid,'w')
		pidfile.write(`os.getpid()`)
		pidfile.close()

	if config.saslUsername:
		sasl = 1
	else:
		config.saslUsername = config.jid
		sasl = 0

	logfile = None
	if config.debugFile:
		logfile = open(config.debugFile,'a')

	if config.dumpProtocol:
		debug=['always', 'nodebuilder']
	else:
		debug=[]
	connection = xmpp.client.Component(config.jid,config.port,debug=debug,sasl=sasl,bind=config.useComponentBinding,route=config.useRouteWrap)
	transport = Transport(connection)
	if not transport.xmpp_connect():
		print "Could not connect to server, or password mismatch!"
		sys.exit(1)
	# Set the signal handlers
	signal.signal(signal.SIGINT, sigHandler)
	signal.signal(signal.SIGTERM, sigHandler)
	transport.lastcheck = time.time() + 10
	while transport.online:
		try:
			connection.Process(1)
			transport.mail_check()
		except KeyboardInterrupt:
			_pendingException = sys.exc_info()
			raise _pendingException[0], _pendingException[1], _pendingException[2]
		except IOError:
			transport.xmpp_disconnect()
		except:
			logError()
		if not connection.isConnected():  transport.xmpp_disconnect()
	connection.disconnect()
	if config.pid:
		os.unlink(config.pid)
	if logfile:
		logfile.close()
	if transport.restart:
		args=[sys.executable]+sys.argv
		if os.name == 'nt': args = ["\"%s\"" % a for a in args]
		if config.dumpProtocol: print sys.executable, args
		os.execv(sys.executable, args)




