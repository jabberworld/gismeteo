#!/usr/bin/python
# -*- coding: utf-8 -*-

wz_cache = {'public':{}, 'private':{}}
cache_ttl = 600
wz_clients = {}

version = '0.1'

import os
import signal
import sys
import time
import traceback
import xmpp
import xml.dom.minidom
import sqlite3
#import urllib2

from xmpp.browser import *
from xml.parsers import expat

config=os.path.abspath(os.path.dirname(sys.argv[0]))+'/config.xml'
citydb=os.path.abspath(os.path.dirname(sys.argv[0]))+'/city.db'

con = sqlite3.connect(citydb)
cur = con.cursor()

dom = xml.dom.minidom.parse(config)

NAME =  dom.getElementsByTagName("name")[0].childNodes[0].data
HOST =  dom.getElementsByTagName("host")[0].childNodes[0].data
PORT =  dom.getElementsByTagName("port")[0].childNodes[0].data
PASSWORD = dom.getElementsByTagName("password")[0].childNodes[0].data

def get_weather_g(kod, type):

            import socks
            import socket
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 54321)
            socket.socket = socks.socksocket

            import urllib2

            kod=str(kod)
            req = urllib2.Request(u'http://informer.gismeteo.ru/xml/'+kod+u'_1.xml',headers={'User-agent': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)'})
            r = urllib2.urlopen(req)

            global embedd
            embedd=0
            global wz,period
            wz={}
            period=0

            def start_element(name, attrs):
                global embedd,wz,period
                embedd+=1
                if period not in wz:
                    wz[period]={}
                wz[period][name]=attrs

            def end_element(name):
                global embedd,period
                embedd-=1
                if name=='FORECAST':
                    period+=1
                return

            p = expat.ParserCreate()

            p.StartElementHandler = start_element
            p.EndElementHandler = end_element
            try:
                p.ParseFile(r)
            except:
                return None

            cityname=urllib2.unquote(str(wz[0][u'TOWN'][u'sname'])).decode("cp1251")

            weather = u'Погода по г. '+cityname+u' (№'+kod+u'):'
            weather_s = u'Погода по г. '+cityname+u' (№'+kod+u'):'
            weather_sms =u'№'+kod+u':'
            for period in wz:
                pr=wz[period]
#                print pr.keys()
#                print pr[u'TOWN'].keys()
#                print pr[u'TOWN'][u'sname']
                day = str(pr[u'FORECAST'][u'day'])
                mounth = pr[u'FORECAST'][u'month']
                hour = pr[u'FORECAST'][u'hour']
                week = pr[u'FORECAST'][u'weekday']
                cloud = pr[u'PHENOMENA'][u'cloudiness']
                precipitation = pr[u'PHENOMENA'][u'precipitation']
                presmax = pr[u'PRESSURE'][u'max']
                presmin = pr[u'PRESSURE'][u'min']
                tempmax = pr[u'TEMPERATURE'][u'max']
                tempmin = pr[u'TEMPERATURE'][u'min']
                heatmax = pr[u'HEAT'][u'max']
                heatmin = pr[u'HEAT'][u'min']
                windmin = pr[u'WIND'][u'min']
                windmax = pr[u'WIND'][u'max']
                winddir = pr[u'WIND'][u'direction']
                rewmax = pr[u'RELWET'][u'max']
                rewmin = pr[u'RELWET'][u'min']

                try:
                    hour=int(hour)
                    if hour in range(0,6):
                        hour=u'Ночь'
                    elif  hour in range(6,12):
                        hour=u'Утро'
                    elif  hour in range(12,18):
                        hour=u'День'
                    elif  hour in range(18,24):
                        hour=u'Вечер'
                except:
                    print 'can\'t parse'
                    pass


                months=[u'ХЗраля',u'Января',u'Февраля',u'Марта',u'Апреля',u'Мая',u'Июня',u'Июля',u'Августа',u'Сентября',u'Октября',u'Ноября',u'Декабря']
                weekdays=[u'Нулесенье 8-|',u'Воскресенье',u'Понедельник',u'Вторник',u'Среда',u'Четверг',u'Пятница',u'Суббота',u'Восьмесение О_о']
                mounth=months[int(mounth)]
                week=weekdays[int(week)]

                wind=[u'северный',u'северо-восточный',u'восточный',u'юго-восточный',u'южный',u'юго-западный',u'западный',u'северо-западный']
                sky=[u'ясно',u'малооблачно',u'облачно',u'пасмурно',u'дождь',u'ливень',u'снег',u'снег',u'гроза',u'нет данных',u'без осадков']
                skys=[u'ясн',u'малоб',u'обл',u'пасм',u'дожд',u'ливен',u'снег',u'снег',u'гроза',u'???',u'б/осад']

                winddir = wind[int(winddir)]
                clouds=skys[int(cloud)]
                cloud=sky[int(cloud)]
                precipitations=skys[int(precipitation)]
                precipitation=sky[int(precipitation)]

                weather += '\n'+hour+ u' (' +day+ ' ' +mounth+ ', '+week+u'):\n  температура воздуха от '+tempmin+ u' до '+tempmax+u' ('+heatmin+u'-'+heatmax+u')'+u';\n  '+cloud+u', '+precipitation+u';\n  атмосферное давление '+presmin+u'-'+presmax+u'мм.рт.ст.;\n  ветер '+winddir+ u', '+windmin+'-'+windmax+u'м/с;\n  влажность воздуха '+rewmin+'-'+rewmax+u'%;\n'
                weather_s += '\n'+hour+u' '+tempmin+ u'..'+tempmax+u' ('+heatmin+u'..'+heatmax+u')'+u'; '+cloud+u', '+precipitation
                weather_sms += '\n'+hour[0]+tempmin+ u'-'+tempmax+u'['+heatmin+u'-'+heatmax+u']'+u';'+clouds+u','+precipitations

            if type == 'public':
                return weather_s
            if type == 'private':
                return weather
            if type == 'sms':
                return weather_sms
            else:
                return weather

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
            wz_cache[pub][code] = time.time(), get_weather_g(code,pub)
    return wz_cache[pub][code][1]


class Transport:
    online = 1
    offlinemsg = ''
    last = time.time()
    version = '0.1'

    def __init__(self,jabber):
        self.jabber = jabber
        self.domain = NAME
        self.Features = {
                        'ids':[
                            {'category':'presence','type':'text','name':"Gismeteo Weather Service"}],
                        'features':[NS_GATEWAY, NS_DISCO_INFO, NS_VERSION, NS_LAST, NS_DISCO_ITEMS, NS_SEARCH]}
        self.online_users = {}

    def register_handlers(self):
        self.jabber.RegisterHandler('message', self.xmpp_message)
        self.jabber.RegisterHandler('presence',self.xmpp_presence)
        self.jabber.RegisterHandler('iq',      self.xmpp_iq)
        self.disco = Browser()
        self.disco.PlugIn(self.jabber)
        self.disco.setDiscoHandler(self.xmpp_base_disco,node='',jid=NAME)

    # IQ Handlers
    def xmpp_iq(self, conn, iq):
        print '======================= iq: ',[self], [conn], [iq]
        ns = iq.getQueryNS()
        typ = iq.getType()
        if ns == xmpp.NS_GATEWAY:
            self.iq_gateway_handler(iq)
#        elif ns == xmpp.NS_STATS:
#            self.iq_stats_handler(iq)
#        elif ns == xmpp.NS_TIME:
#            self.iq_time_handler(iq, 'old')
#        elif iq.getTag('time') and iq.getTag('time').getNamespace() == xmpp.NS_NEW_TIME:
#            self.iq_time_handler(iq, 'new')
        elif ns == xmpp.NS_LAST:
            self.iq_last_handler(iq)
        elif ns == xmpp.NS_SEARCH:
            self.iq_search_handler(iq)
        elif ns == xmpp.NS_VERSION:
            self.iq_version_handler(iq)
#        elif iq.getTag('vCard') and iq.getTag('vCard').getNamespace()==xmpp.NS_VCARD:
#            self.iq_vcard_handler(iq)
#        elif iq.getTag('command') and iq.getTag('command').getNamespace()==xmpp.NS_COMMANDS:
#            self.iq_command_handler(iq)
        elif ns == xmpp.NS_DISCO_INFO:
            self.iq_disco_info_handler(iq)
        elif ns == xmpp.NS_DISCO_ITEMS:
            self.iq_disco_items_handler(iq)
#        elif iq.getTag('ping') and iq.getTag('ping').getNamespace() == xmpp.NS_PING:
#            self.iq_ping_handler(iq)
#        elif ns == xmpp.NS_REGISTER:
#            self.iq_register_handler(iq)
#            print "*****self.iq_register_handler(iq) exits"
        else:
            print "***************************************",ns
            self.send_not_implemented(iq)

    def iq_version_handler(self, iq):
        name = Node('name')
        name.setData("Gismeteo.ru weather service")
        version = Node('version')
        version.setData(self.version)

        repl = iq.buildReply('result')
        query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_VERSION})
        query.addChild()
        repl.setPayload([query])
        self.jabber.send(repl)

    def iq_last_handler(self, iq):
        repl = iq.buildReply('result')
        query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_LAST, 'seconds': (int(time.time() - self.last))})
        repl.setPayload([query])
        self.jabber.send(repl)

    def iq_disco_info_handler(self, iq):
        return

    def iq_disco_items_handler(self, iq):
        repl = iq.buildReply('result')
        query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_DISCO_ITEMS})
        repl.setPayload([query])
        self.jabber.send(repl)

    def get_register_form(self):
        instr = xmpp.Node('instructions')
        instr.setData(u"Введите город для поиска")
        city = xmpp.Node('city')
        return [instr, city]

    def set_register_form(self, iq):
        iq_children = iq.getQueryChildren()
        searchField = [node.getData() for node in iq_children]
        if searchField:
            searchField='%'+searchField[0].replace("%","\\%")+'%'
        else:
            return
        if searchField=='%%' or len(searchField)<5:
            self.send_bad_request(iq)
            return
        data = cur.execute("SELECT * FROM cityindex WHERE country_en LIKE (?) OR country_ru LIKE (?) OR name_en LIKE (?) OR name_ru LIKE (?) OR keywords LIKE (?)", (searchField, searchField, searchField, searchField, searchField))
        data = cur.fetchall()

        ## HERE
        repl = iq.buildReply('result')
        query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_SEARCH})
        rprt = Node('reported', payload=[
#            DataField(label='JID'                ,name='jid'                   ,typ='jid-single'),
#            DataField(label='Index'              ,name='idx'                   ,typ='text-single'),
#            DataField(label='Country ru'         ,name='cru'                   ,typ='text-single'),
#            DataField(label='Region ru'          ,name='rru'                   ,typ='text-single'),
#            DataField(label='Country en'         ,name='cen'                   ,typ='text-single'),
#            DataField(label='Region en'          ,name='ren'                   ,typ='text-single'),
#            DataField(label='Name ru'            ,name='nru'                   ,typ='text-single'),
#            DataField(label='Name en'            ,name='nen'                   ,typ='text-single'),
#            DataField(label='Latitude'           ,name='lat'                   ,typ='text-single'),
#            DataField(label='Longtitude'         ,name='lon'                   ,typ='text-single'),
#            DataField(label='Altitude'           ,name='alt'                   ,typ='text-single'),
            DataField(label='Keywords'           ,name='kwr'                   ,typ='text-single')])
        rpl = Node('item', payload=[
            DataField(name='kwr', value="123123")])

        form = DataForm('result')
        form.addChild(node=DataField(name='FORM_TYPE',value=NS_SEARCH, typ='hidden'))
        form.addChild(node=rprt)
        form.addChild(node=rpl)


        query.addChild(node=form)
        repl.setPayload([query])
        self.jabber.send(repl)

#        for flds in data:
#            print flds[0]


    def iq_gateway_handler(self, iq):
        jid_to = iq.getTo()
        jid_to_stripped = jid_to.getStripped()
        iq_children = iq.getQueryChildren()
        typ = iq.getType()
        if (typ=='get') and (jid_to_stripped==NAME) and (not iq_children):
            repl = iq.buildReply(typ='result')
            query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_GATEWAY})
            query.setTagData('desc', u'enter city code:')
            query.setTag('prompt')
            repl.setPayload([query])
            self.jabber.send(repl)
        elif (typ=='set') and (jid_to_stripped==NAME) and iq_children:
            e_mail = [node.getData() for node in iq_children if node.getName()=='prompt']
            if len(e_mail) == 1:
                prompt = xmpp.simplexml.Node('jid')
#                prompt.setData(utils.mail2jid(e_mail[0]))
                prompt.setData(e_mail[0].replace('@', '%') + '@' + NAME)
                repl = iq.buildReply(typ='result')
                repl.setQueryPayload([prompt])
                self.jabber.send(repl)
            else:
                self.send_bad_request(iq)
        else:
            self.send_not_implemented(iq)

    def iq_search_handler(self, iq):
        typ = iq.getType()
        iq_children = iq.getQueryChildren()
        if (typ=='get') and (not iq_children):
            repl = iq.buildReply('result')
            repl.setQueryPayload(self.get_register_form())
            self.jabber.send(repl)
            raise NodeProcessed
        elif (typ=='set') and iq_children:
            self.set_register_form(iq)
            raise NodeProcessed

    def send_bad_request(self, iq):
        if iq.getType() in ['set','get']:
            self.send_error(iq,xmpp.ERR_BAD_REQUEST)

    def send_not_implemented(self, iq):
        if iq.getType() in ['set','get']:
            self.send_error(iq)

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
        if to == NAME:
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
        show = event.getShow()
        status = event.getStatus()
        to = event.getTo()
        try:
            print "pres===============", fromjid, to, type, show
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
#            print "pres===============",fromjid,to,type,show
#            try: print str(event)
#            except: pass
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
#            print 'self.online_users=',self.online_users
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
#            print 'self.online_users=',self.online_users
            return show

    def pres_exec(self, tojid, jid, type, show):

        show = self.usr_show(jid, type, show)
        jid=jid.getStripped()

        print tojid,jid,type,show
        return get_gism(tojid, short=1)

    def xmpp_message(self, con, event):

        print "message: "
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
#            m = Message(to=fromjid,frm = to, subject = event.getSubject(), body = u'you sent me "%s". WHY???'%(body))
            self.command_handler(fromjid,to,body)

    def command_handler(self,fromjid,to,body):
        print "COMMAND"
        def reply(to,body):
#            if not isinstance(body, unicode):
#                body = body.decode('utf8', 'replace')
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

        if fromjid.getStripped() != 'username@linuxoid.in':
            print fromjid.getStripped()
            return

        print 'user',[user]
        if len(user) == 2 and user[1] == '':
            user = user[0]
        else:
            reply(to,'Пшёл вон, я хз кто ты!')
            return

        if cmd == 'online':
            reply(to, str(self.online_users))
        elif cmd == 'wz':
            reply(to, str(wz_clients))
        elif cmd == 'list':
            pass
        else:
            reply(to,'...')

    def xmpp_connect(self):
        connected = None
        while not connected:
            connected = self.jabber.connect((HOST, PORT))
            time.sleep(5)
        self.register_handlers()
        connected = self.jabber.auth(NAME, PASSWORD)
        return connected

    def xmpp_disconnect(self):
        time.sleep(5)
        if not self.jabber.reconnectAndReauth():
            time.sleep(5)
            self.xmpp_connect()

def logError():
    err = '%s - %s\n'%(time.strftime('%a %d %b %Y %H:%M:%S'), version)
    sys.stderr.write(err)
    traceback.print_exc()
    sys.exc_clear()

def sigHandler(signum, frame):
    transport.offlinemsg = 'Signal handler called with signal %s'%signum
    transport.online = 0

if __name__ == '__main__':

    connection = xmpp.client.Component(NAME, PORT, debug=None, sasl=False, bind=False, route=False)
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
        except KeyboardInterrupt:
            _pendingException = sys.exc_info()
            raise _pendingException[0], _pendingException[1], _pendingException[2]
        except IOError:
            transport.xmpp_disconnect()
        except:
            logError()
        if not connection.isConnected():  transport.xmpp_disconnect()
    connection.disconnect()

