# -*- coding: utf-8 -*-

#  Talisman plugin
#  pogoda_plugin.py  v1.1

# Coded by: Avinar  (avinar@xmpp.ru)

# licence show in another plugins ;)

import urllib2

def get_weather_g(kod, type):
			kod=str(kod)
			req = urllib2.Request(u'http://informer.gismeteo.ru/xml/'+kod+u'_1.xml',headers={'User-agent': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)'})
#			req = urllib2.Request(u'http://localhost/xml/'+kod+u'_1.xml')
			r = urllib2.urlopen(req)
			
			
			from xml.parsers import expat
			
			global embedd
			embedd=0
			global wz,period
			wz={}
			period=0
			
			def start_element(name, attrs):
				global embedd,wz,period
#				prefix=''
#				for x in range(embedd):
#					prefix+='\t'
#				print 'start_element:',prefix, name, attrs
				embedd+=1
				if period not in wz:
					wz[period]={}
				wz[period][name]=attrs
			def end_element(name):
				global embedd,period
				embedd-=1
				if name=='FORECAST':
#					print 'fore'#,period
					period+=1
				return
#				prefix=''
#				for x in range(embedd):
#					prefix+='\t'
#				print 'end_element:',prefix, name
#			def char_data(data):
#				print 'char_data:', repr(data)

			p = expat.ParserCreate()
			
			p.StartElementHandler = start_element
			p.EndElementHandler = end_element
#			p.CharacterDataHandler = char_data
			try:
				p.ParseFile(r)	
			except:
#			reply(type ,source, u'Нет данных...')
				return None
			
			cityname=urllib2.unquote(str(wz[0][u'TOWN'][u'sname'])).decode("cp1251")
			
#			return
			weather = u'Погода по г. '+cityname+u' (№'+kod+u'):'
			weather_s = u'Погода по г. '+cityname+u' (№'+kod+u'):'
			weather_sms =u'№'+kod+u':'
			for period in wz:
				pr=wz[period]
#				try:
				if 1:
#					print pr.keys()
#					print pr[u'TOWN'].keys()
#					print pr[u'TOWN'][u'sname']
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
#				except:
#					print 'can\'t parse'
				
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


def handler_weather_pogoda(type, source, parameters):
	if parameters == '':
		reply(type ,source, u'И что ты от меня хочешь?')
		return
	else:
		## Вычисление города
		import urllib2
		parameters = parameters.lower().replace('\n','')
		kod = ''
		try:
			code=int(parameters)
			kod=parameters.strip()
		except:
			wez_file = 'static/weather_g.txt'
			fp = file(wez_file)
			lines = fp.readlines()
			for line in lines:
				line = line.split(' ')
				if unicode(line[1],"utf-8").replace('\n','')==parameters:
					kod = line[0]
					break
		if not kod:
			found=[]
			for line in lines:
				line = line.split(' ')
				if unicode(line[1],"utf-8").replace('\n','').lower().find(parameters.lower())>=0:
					found.append(unicode(line[1],"utf-8").replace('\n','').capitalize())
					#break
			if not len(found):
				reply(type ,source, u'Город "'+parameters.capitalize()+u'" не найден. Может неправильно написали? И даже ничего похожего тоже нет.')
			else:
				if len(found)>20:
					found=u', '.join(found[:20])+u' <всего найдено %d, показаны первые 20>'%len(found)
				else:
					found=u', '.join(found)
				reply(type ,source, u'Город "'+parameters.capitalize()+u'" не найден. Может неправильно написали? Может имелся ввиду один из следующих? \n%s'%(found))
		else:
		
			try:
				weather = get_weather_g(kod, type)
				
			except urllib2.HTTPError:
				print 'exception!!!!!!!\n',sys.exc_info()[1]
				reply(type ,source, u'Не могу получить инфу по городу с кодом '+kod)
				return
			except:
				print 'exception!!!!!!!\n',sys.exc_info()[1]
				reply(type ,source, u'хз чё случилось :-(')
				return
		
			if type=='private':
				reply(type ,source, weather+u'\nПогода предоставлена www.gismeteo.ru')
			else:
				reply(type,source,u'%s \n (подробно смотри в привате)'%weather)
		
		

