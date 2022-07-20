#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#               Python based Jabber Weather transport.
# Copyright:	Initial version - based on code of mail transport (https://github.com/xmpppy/mail-transport) + pogoda_plugin.py from Talisman bot
#               2022 rain from JabberWorld. JID: rain@jabberworld.info
# Licence:      GPL v2
# Requirements:
#               python-xmpppy - https://github.com/xmpppy/xmpppy
#               python-feedparser - https://github.com/kurtmckee/feedparser (for Meteonova)

import os
import signal
import sys
import time
import traceback
import xmpp
import xml.dom.minidom
import sqlite3
import re

from xmpp.browser import *
from xml.parsers import expat

wz_cache = {'public':{}, 'private':{}}
version = '1.1'

weatherlogo = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAADAFBMVEUAAAAXlP4Uiv8UkP4Uh/8Uhv8Ujv4LzP4MzP4M0/4Lyv8J5P4Lz/8Lzv8Vjf4Vi/4Vif4Vif4Ujf4Ui/4Uiv4Uj/4Ujf4Uk/4UkP4Tk/4Tkf4TlP4Tlv4Nwv4Nxf4Mxf4MyP4Mxv4LzP4Lyv4Lzf4MzP4L0P4Lz/4Lzv4K1P4K0v4K0f4K0P4ViP4ViP8Uiv8UjP8TjP8Uj/8Tkf8Tk/8Tlv8SmP4SmP8Smv8Rmv8Pmv8RnP8SnP8PnP8dn/E4pNY6pNQgn+4PnP4Rn/8Sn/1WrbnBw0/qyyfsyybJxUdksKoTn/kPnv8Rof8Oof9VsLzq0C7/1Rj/1Rv/1Bvw1kCKyMxoxP9ev/81r/8Tov8Qof8Qo/8apvW9zF7/2yD/2iT/2iP/2iX/5GH/8azy8cvD5/m85f+u4P9qxf8Ypv8Oov8Oo/8Rpv8Opf8zrt/m2j//4Cr/4Cv/517/9b7/9sf79cjM6vK95v+/5/9sx/8zsv8cqv8Ppf8Qpv8QqP8Op/8zsd/n4Eb/5jL/5jP/5zv/9Kj/+dL/+M/8+NHT7fPG6v/H6v/D6f+85v+75v+f3P9Mvv8RqP8Pqv8brfXA22v/7Tf/6zf/7lT/+cv/+9n/+9j2+N7U7/vP7v/Q7v/T7/9Mv/8Nqv8Qrf8NrP9ZwcHt6kr/8Vv/96n/+97//OD9++Ho9fLZ8f/c8v+m4P8ZsP8PrP8Pr/8Pr/xxy8X199D9/Ov9/On6++vu+PTi9P7i9P/j9f/O7v8vuf8Nrv8Osf8Psf8LsP9pzv/s+P3v+fvv+frq+P7q+P/r+P/s+P/V8f8vvP8Msf8PtP8Lsv971f/1+//x+v+05/8Yt/8Os/8Otv8Ltf9Fxv/j9v/2+//z+//0+//3/P/g9f9Qyv8Mtf8OuP8NuP8Quf9o0//P8P/k9v/l9//f9f+46v9QzP8Ouv8Nuv8lwf86x/87x/8zxf8Zvv8Luv8Nvf8MvP8LvP8Nv/4Nv/8Mwf8MxP8Mxv8LyP8My/8Lzf8Kz/4Kz//////VbIFxAAAALXRSTlMAAAAAAAAAAAAAAAAAABdxyPI4vvs42Re9cfrH8fHHx3H6F7042Ti++xdxyPJYUQVDAAABtElEQVR42nzGAxLDUBQAwBeOYydHqG2ljmve/xi18Xe0ABjOsBwfT3yI8xzL4BgAQQqilPxJEgWKAFpWUuk/UopMg6plEDQVdCOLYOhg5pBMsPJIFhSKSAUo3ZUrlXLpG1QvatV6o9lqd075APZVt9cfDEdjx3Vd+w14F34QRpNpNJsvlqv1xnsB24vd/qi4+ITEpOSU1LT0jMys7Gg4YMgBgdy8/ILCgqLiktKy8oryyqqq6praHAhgqAOB+obGpuYWAFPykMAAEAMAMC/vqbZt27aNrfWYItliriMSS6QyuUKhVKk1Wp2AgB4ZjCazxWqzO5wu95tH6fXRgB8FgqFwJBqLJ5JcKp3J4kCO5AvFUrlSrdW5RrPVxoAO6vb6g+FoMJ5MJ2Q2XyxxYEXWG7b9x3b7AwYcyel8ud6+7s++5OGAoSiKAuBZxekg+Hzuv5nYtm3jznayuXzhGihelcqVaq1+12i2iqVroH3T6XR7/bvBcNRpX2H8MJk+jR8wm5NmSC5ISaSWpDQse0WwLTjumuA6CHr+5i/fCyEcYVxsfxKcRcJANCaVNrv9h53RSsajOAJEXzIn7jGAuwAAAABJRU5ErkJggg=='

config = os.path.abspath(os.path.dirname(sys.argv[0]))+'/config.xml'
citydb = os.path.abspath(os.path.dirname(sys.argv[0]))+'/city.db'

con = sqlite3.connect(citydb)
cur = con.cursor()

dom = xml.dom.minidom.parse(config)

NAME      = dom.getElementsByTagName("name")[0].childNodes[0].data
HOST      = dom.getElementsByTagName("host")[0].childNodes[0].data
PORT      = dom.getElementsByTagName("port")[0].childNodes[0].data
PASSWORD  = dom.getElementsByTagName("password")[0].childNodes[0].data

cache_ttl = int(dom.getElementsByTagName("cache_ttl")[0].childNodes[0].data)
useproxy  = int(dom.getElementsByTagName("useproxy")[0].childNodes[0].data)
proxyaddr = str(dom.getElementsByTagName("proxyaddr")[0].childNodes[0].data)
proxyport = int(dom.getElementsByTagName("proxyport")[0].childNodes[0].data)
datasrc   = str(dom.getElementsByTagName("datasrc")[0].childNodes[0].data)

if useproxy:
    import socks
    import socket
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxyaddr, proxyport)
    socket.socket = socks.socksocket
import urllib2

if datasrc == 'meteonova':
    import feedparser
    def get_weather_g(kod, typ):
        kod=str(kod)
        req = urllib2.Request(u'https://www.meteonova.ru/rss/'+kod+u'.xml')
        try:
            r = urllib2.urlopen(req, timeout=10)
        except:
            r = None

        d = feedparser.parse(r)
        bozo = d["bozo"]

        weather = ''
        weather_s = ''

        if bozo == 0:
            for i in d["items"]:
                title = i["title"]
                city = title[:title.rfind(":")]
                title = title[title.rfind(":")+2:]
                ttle = title.split()
                state = i["description"].split(", ")
                temp = state[2].split()
                wind = state[4].split()
                wind = wind[1].split("-")
                if len(wind) > 1:
                    wind = wind[0][:1]+"-"+wind[1][:1]
                else:
                    wind = wind[0][:1]

                weather += "\n"+title+"\n"+state[2]+"\n"+state[0]+", "+state[1]+"\n"+state[3]+"\n"+state[4]+", "+state[5]+"\n"

                if state[0] == u'облачно':
                    state[0] = u'обл.'
                elif state[0] == u'малооблачно':
                    state[0] = u'м.обл.'
                elif state[0] == u'пасмурно':
                    state[0] = u'пасм.'

                if state[1] == u'без осадков':
                    state[1] = u'б/о'
                elif state[1] == u'временами ливни':
                    state[1] = u'врем. ливн.'

                weather_s += "\n"+ttle[0]+": "+temp[1]+", "+state[0]+", "+state[1]+", "+wind+" ("+state[5]+")"

        else:
            return 'Fetching weather error'

        weather = u'Погода по г. '+city+u' (№'+kod+u'):'+weather
        weather_s = u'Погода по г. '+city+u' (№'+kod+u'):'+weather_s

        if typ == 'public':
            return weather_s
        if typ == 'private':
            return weather
        else:
            return weather

elif datasrc == 'gismeteo':
    def get_weather_g(kod, typ):

        kod=str(kod)
        req = urllib2.Request(u'http://informer.gismeteo.ru/xml/'+kod+u'_1.xml',headers={'User-agent': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)'})
        try:
            r = urllib2.urlopen(req, timeout=10)
        except:
            r = None

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
    #         print pr.keys()
    #         print pr[u'TOWN'].keys()
    #         print pr[u'TOWN'][u'sname']
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

        if typ == 'public':
            return weather_s
        if typ == 'private':
            return weather
        if typ == 'sms': # not used
            return weather_sms
        else:
            return weather
else:
    pass

def get_gism(node, short):
    pub = 'public' if short else 'private'
    try:
        code = int(unicode(node).split('@')[0])
    except:
        print "can't get code for node", unicode(node)
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
    version = version
    weatherlogo = weatherlogo

    def __init__(self,jabber):
        self.jabber = jabber
        self.domain = NAME
        self.Features = {
                        'ids':[
                            {
                                'category':'headline',
                                'type':'weather',
                                'name':"Jabber Weather Service (from "+datasrc+")"
                                }],
                        'features':[
                        NS_GATEWAY,
                        NS_DISCO_INFO,
                        NS_VERSION,
                        NS_LAST,
                        NS_DISCO_ITEMS,
                        NS_SEARCH,
                        NS_VCARD,
                        'urn:xmpp:ping',
                        'urn:xmpp:time'
                        ]}

    def register_handlers(self):
        self.jabber.RegisterHandler('message', self.xmpp_message)
        self.jabber.RegisterHandler('presence',self.xmpp_presence)
        self.jabber.RegisterHandler('iq',      self.xmpp_iq)
        self.disco = Browser()
        self.disco.PlugIn(self.jabber)
        self.disco.setDiscoHandler(self.xmpp_base_disco,node='',jid=NAME)

    # IQ Handlers
    def xmpp_iq(self, conn, iq):
        ns = iq.getQueryNS()
        print 'IQ REQUEST: ', ns
        if ns == xmpp.NS_GATEWAY: # to allow add bots via "Add contact"
            self.iq_gateway_handler(iq)
        elif ns == xmpp.NS_LAST: # to get uptime
            self.iq_last_handler(iq)
        elif ns == xmpp.NS_SEARCH: # to allow search
            self.iq_search_handler(iq)
        elif ns == xmpp.NS_VERSION: # to get version
            self.iq_version_handler(iq)
        elif iq.getTag('vCard') and iq.getTag('vCard').getNamespace()==xmpp.NS_VCARD: # to get vcards for transport and bots
            self.iq_vcard_handler(iq)
        elif ns == xmpp.NS_DISCO_INFO: # to prevent error when you click on transport in service browser and allow clients to discover transport functions
            self.iq_disco_info_handler(iq)
        elif ns == xmpp.NS_DISCO_ITEMS: # to prevent error when you expand transport's tree in service browser
            self.iq_disco_items_handler(iq)
        elif iq.getTag('ping') and iq.getTag('ping').getNamespace() == 'urn:xmpp:ping':
            self.iq_ping_handler(iq)
        elif iq.getTag('time') and iq.getTag('time').getNamespace() == 'urn:xmpp:time':
            self.iq_time_handler(iq, 'new')
#        elif ns == xmpp.NS_TIME:
#            self.iq_time_handler(iq, 'old')
#        elif ns == xmpp.NS_STATS:
#            self.iq_stats_handler(iq)
#        elif iq.getTag('command') and iq.getTag('command').getNamespace()==xmpp.NS_COMMANDS:
#            self.iq_command_handler(iq)
#        elif ns == xmpp.NS_REGISTER:
#            self.iq_register_handler(iq)
#            print "*****self.iq_register_handler(iq) exits"
        else:
            print "Not implemented namespace: ", ns
            self.send_not_implemented(iq)

    def iq_time_handler(self, iq, typ):
        repl = iq.buildReply('result')
        query = Node('time')
        query.setTagData(tag='tzo',    val="+02:00")
        query.setTagData(tag='utc',    val=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
        repl.setPayload([query])
        self.jabber.send(repl)
        raise NodeProcessed

    def iq_ping_handler(self, iq):
        repl = iq.buildReply('result')
        self.jabber.send(repl)
        raise NodeProcessed

    def iq_vcard_handler(self, iq):
        repl = iq.buildReply('result')
        query = xmpp.Node('vCard', attrs={'xmlns':xmpp.NS_VCARD})

        if str(iq.getTo()) == self.domain:
            query.setTagData(tag='NICKNAME', val='Weather')
            query.setTagData(tag='FN',       val='Jabber Weather Transport')
            query.setTagData(tag='BDAY',     val='2022-07-22')
            query.setTagData(tag='DESC',     val='gismeteo.ru and meteonova.ru weather service')
            query.setTagData(tag='ROLE',     val='Создаю ботов для получения погоды с '+datasrc)
            query.setTagData(tag='URL',      val='https://github.com/jabberworld/gismeteo')

            transav = query.addChild('PHOTO')
            transav.setTagData(tag='BINVAL', val=self.weatherlogo)
            transav.setTagData(tag='TYPE',   val='image/png')

        else:
            idx = str(iq.getTo().node)
            if re.match(r"^[0-9]{1,5}$", idx):
                data = cur.execute("SELECT * FROM cityindex WHERE idx = (?) LIMIT 1", (idx, ))
                data = cur.fetchone()
                if data:
                    query.setTagData(tag='NICKNAME', val=data[6])

                    tel = query.addChild('TEL')
                    tel.setTagData(tag='NUMBER',     val=data[0])

                    addrru = query.addChild('ADR')
                    addrru.setTagData(tag='CTRY',    val=data[1]+" ("+data[3]+")")
                    addrru.setTagData(tag='REGION',  val=data[2]+" ("+data[4]+")")
                    addrru.setTagData(tag='LOCALITY',val=data[6]+" ("+data[5]+")")

                    query.setTagData(tag='FN',       val=data[6]+", "+data[2]+", "+data[1])
                    query.setTagData(tag='DESC',     val="Lat.: "+data[7]+", Long.: "+data[8]+", Alt.: "+data[9]+"\n"+data[10])
                else:
                    query.setTagData(tag='FN',       val="Город не найден")

                query.setTagData(tag='URL',      val='https://github.com/jabberworld/gismeteo')
                query.setTagData(tag='BDAY',     val='2022-07-22')

                botav = query.addChild('PHOTO')
                botav.setTagData(tag='BINVAL',   val=self.weatherlogo)
                botav.setTagData(tag='TYPE',     val='image/png')

        repl.setPayload([query])
        self.jabber.send(repl)
        raise NodeProcessed

    def iq_version_handler(self, iq):
        name = Node('name')
        name.setData("Jabber Weather Service")
        version = Node('version')
        version.setData(self.version)

        repl = iq.buildReply('result')
        query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_VERSION})
        query.addChild(node=name)
        query.addChild(node=version)
        repl.setPayload([query])
        self.jabber.send(repl)
        raise NodeProcessed

    def iq_last_handler(self, iq):
        repl = iq.buildReply('result')
        query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_LAST, 'seconds': (int(time.time() - self.last))})
        repl.setPayload([query])
        self.jabber.send(repl)
        raise NodeProcessed

    def iq_disco_info_handler(self, iq):
        return

    def iq_disco_items_handler(self, iq):
        repl = iq.buildReply('result')
        query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_DISCO_ITEMS})
        repl.setPayload([query])
        self.jabber.send(repl)
        raise NodeProcessed

    def get_register_form(self):
        ft = DataForm('form')
#        instr = xmpp.Node('instructions')
#        instr.setData(u"Введите город для поиска")
        ft.addChild(node=DataField(name='FORM_TYPE',value=NS_SEARCH, typ='hidden'))
        ft.addChild(node=DataField(name='city', label='Город', typ='text-single'))
        return [ft]
#        return [instr, ft]

    def set_register_form(self, iq):
        iq_children = iq.getQueryChildren()
        for nod in iq_children:
            for k in nod.getChildren():
                if k.getAttr('var') == 'city':
                    for j in k.getChildren():
                        searchField = j.getData()
        if searchField:
            searchField='%'+searchField.replace("%","\\%")+'%'
        else:
            return
        if searchField=='%%' or len(searchField)<4:
            self.send_bad_request(iq)
            return
        data = cur.execute("SELECT * FROM cityindex WHERE idx LIKE (?) OR country_en LIKE (?) OR country_ru LIKE (?) OR name_en LIKE (?) OR name_ru LIKE (?) OR keywords LIKE (?) LIMIT 100", (searchField, searchField, searchField, searchField, searchField, searchField))
        data = cur.fetchall()
        print data

        repl = iq.buildReply('result')
        query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_SEARCH})
        rprt = Node('reported', payload=[
            DataField(label='JID'       ,name='jid'  ,typ='jid-single'),
            DataField(label='Index'     ,name='idx'  ,typ='text-single'),
            DataField(label='Страна'    ,name='cru'  ,typ='text-single'),
            DataField(label='Регион'    ,name='rru'  ,typ='text-single'),
            DataField(label='Город'     ,name='nru'  ,typ='text-single'),
            DataField(label='Country'   ,name='cen'  ,typ='text-single'),
            DataField(label='Region'    ,name='ren'  ,typ='text-single'),
            DataField(label='City'      ,name='nen'  ,typ='text-single'),
            DataField(label='Lat.'      ,name='lat'  ,typ='text-single'),
            DataField(label='Long.'     ,name='lon'  ,typ='text-single'),
            DataField(label='Alt.'      ,name='alt'  ,typ='text-single'),
            DataField(label='Keywords'  ,name='kwr'  ,typ='text-single')])

        form = DataForm('result')
        form.addChild(node=DataField(name='FORM_TYPE', value=NS_SEARCH, typ='hidden'))
        form.addChild(node=rprt)

        for flds in data:
            rpl = Node('item', payload=[
                DataField(name='jid', value=JID(node=unicode(str(flds[0]), "utf-8"), domain=self.domain)),
                DataField(name='idx', value=flds[0]),
                DataField(name='cru', value=flds[1]),
                DataField(name='rru', value=flds[2]),
                DataField(name='cen', value=flds[3]),
                DataField(name='ren', value=flds[4]),
                DataField(name='nru', value=flds[6]),
                DataField(name='nen', value=flds[5]),
                DataField(name='lat', value=flds[7]),
                DataField(name='lon', value=flds[8]),
                DataField(name='alt', value=flds[9]),
                DataField(name='kwr', value=flds[10])])
            form.addChild(node=rpl)

        query.addChild(node=form)
        repl.setPayload([query])
        self.jabber.send(repl)

    def iq_gateway_handler(self, iq):
        jid_to = iq.getTo()
        jid_to_stripped = jid_to.getStripped()
        iq_children = iq.getQueryChildren()
        typ = iq.getType()
        if (typ=='get') and (jid_to_stripped==NAME) and (not iq_children):
            repl = iq.buildReply(typ='result')
            query = xmpp.Node('query', attrs={'xmlns':xmpp.NS_GATEWAY})
            query.setTagData('desc', u'Enter city code:')
            query.setTag('prompt')
            repl.setPayload([query])
            self.jabber.send(repl)
            raise NodeProcessed
        elif (typ=='set') and (jid_to_stripped==NAME) and iq_children:
            code = [node.getData() for node in iq_children if node.getName()=='prompt']
            code = str(code[0])
            if re.match(r"^[0-9]{1,5}$", code):
                prompt = xmpp.simplexml.Node('jid')
                prompt.setData(code + '@' + NAME)
                repl = iq.buildReply(typ='result')
                repl.setQueryPayload([prompt])
                self.jabber.send(repl)
                raise NodeProcessed
            else:
                self.send_bad_request(iq)
                raise NodeProcessed
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
    def xmpp_base_disco(self, con, event, typ):
        fromjid = event.getFrom().__str__()
        to = event.getTo()
        node = event.getQuerynode();
        #Type is either 'info' or 'items'
        if to == NAME:
            if node == None:
                if typ == 'info':
                    return self.Features
                if typ == 'items':
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
        typ = event.getType()
        show = event.getShow()
        status = event.getStatus()
        to = event.getTo()
        if re.match(r"^[0-9]{1,5}$", str(to.node.encode("utf-8"))):
            try:
                print "PRESENCE: ", fromjid, "->", to, typ, show
            except:
                print "PRESENCE: ERROR"
            if typ == 'subscribe':
                self.jabber.send(Presence(to=fromjid, frm = to, typ = 'subscribe'))
            elif typ == 'subscribed':
                self.jabber.send(Presence(to=fromjid, frm = to, typ = 'subscribed'))
            elif typ == 'unsubscribe':
                self.jabber.send(Presence(to=fromjid, frm = to, typ = 'unsubscribe'))
            elif typ == 'unsubscribed':
                self.jabber.send(Presence(to=fromjid, frm = to, typ = 'unsubscribed'))
            elif typ == 'probe':
                print "PROBE", self.usr_show(fromjid, typ, show)
                self.jabber.send(Presence(to=fromjid, frm = to))
            elif typ == 'unavailable':
                self.jabber.send(Presence(to=fromjid, frm = to, typ = 'unavailable'))
            elif typ == 'error':
                return
            else:
                to = JID(str(to)+"/"+datasrc)
                wz = self.pres_exec(to, fromjid, typ, show)
                if wz: status=wz
                self.jabber.send(Presence(to=fromjid, frm = to, typ = typ, show=show, status=status))

    def usr_show(self, jid, typ, show):
        if not typ and not show:
            show = 'available'
        return show

    def pres_exec(self, tojid, jid, typ, show):
        show = self.usr_show(jid, typ, show)
        print "PRES EXEC:",
        print tojid, "->", jid, typ, show
        return get_gism(tojid, short=1)

    def xmpp_message(self, con, event):
        fromjid = event.getFrom()
        to = event.getTo()
        print "GOT MSG FROM:", fromjid

        if to.getNode() != '':
            wz = get_gism(to, short=0)
            m = Message(to=fromjid, frm = to, body = wz)
            self.jabber.send(m)
        else:
            pass # this variant is for commands to transport directly

    def xmpp_connect(self):
        connected = None
        while not connected:
            print "Connecting..."
            connected = self.jabber.connect((HOST, PORT))
            time.sleep(1)
        self.register_handlers()
        connected = self.jabber.auth(NAME, PASSWORD)
        print "Connected"
        return connected

    def xmpp_disconnect(self):
        print "Disconnected"
        time.sleep(5)
        if not self.jabber.reconnectAndReauth():
            print "Reconnect in 60 seconds"
            time.sleep(60)
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

