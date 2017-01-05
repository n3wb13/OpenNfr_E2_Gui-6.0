# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2017
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding execution on hardware, you are permitted to execute this plugin on VU+ hardware
#  which is licensed by satco europe GmbH, if the VTi image is used on that hardware.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
###############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

config.mediaportal.laola1_portal = ConfigText(default="int", fixed_size=False)
config.mediaportal.laola1_lang = ConfigText(default="en", fixed_size=False)

special_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36',
	'Accept': '*/*',
	'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4,id;q=0.2,ru;q=0.2,tr;q=0.2',
	'Referer': 'http://laola1.tv'
}

xip = ''

class laolaGenreScreen(MPScreen):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"green" : self.keyPortal,
			"yellow" : self.keyLang
		}, -1)

		self['title'] = Label("Laola1.tv")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.portal = config.mediaportal.laola1_portal.value
		self.lang = config.mediaportal.laola1_lang.value
		rangelist = [['DE', 'de'], ['AT', 'at'], ['INT', 'int']]
		for item in rangelist:
			if item[1] == self.portal:
				self['F2'].setText(_('Portal')+' '+item[0])
				global xip
				if item[1] == "de": xip = '146.0.32.8'
				elif item[1] == "at": xip = '91.186.152.12'
				else: xip = '85.128.141.33'
				special_headers.update({'X-Forwarded-For': xip})
		rangelist = [['DE', 'de'], ['EN', 'en'], ['RU', 'ru']]
		for item in rangelist:
			if item[1] == self.lang:
				self['F3'].setText(_('Language')+' '+item[0])
		self.genreliste = []
		url = "http://www.laola1.tv/%s-%s/home/0.html" % (self.lang, self.portal)
		getPage(url, headers=special_headers).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.parse = re.search('class="heading">(Sport\sChannels|Каналы\sпо\sвидам\sспорта)</li>(.*?)class="heading">(More|Прочее)', data, re.S)
		raw = re.findall('crane_menu_icon_toggle".*?a\shref="(.*?)">(.*?)</a>', self.parse.group(2), re.S)
		if raw:
			self.genreliste = []
			for Url, Title in raw:
				self.genreliste.append((decodeHtml(Title.strip()), Url))
		self.genreliste.insert(0,("Live", "http://www.laola1.tv/%s-%s/calendar/0.html"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyPortal(self):
		if self.keyLocked:
			return
		rangelist = [['DE', 'de'], ['AT', 'at'], ['INT', 'int']]
		self.session.openWithCallback(self.returnPortal, ChoiceBoxExt, title=_('Select Portal'), list = rangelist)

	def returnPortal(self, data):
		if data:
			self.portal = data[1]
			config.mediaportal.laola1_portal.value = self.portal
			config.mediaportal.laola1_portal.save()
			configfile.save
			self['F3'].setText(data[0])
			self.loadPage()

	def keyLang(self):
		if self.keyLocked:
			return
		rangelist = [['DE', 'de'], ['EN', 'en'], ['RU', 'ru']]
		self.session.openWithCallback(self.returnLang, ChoiceBoxExt, title=_('Select Language'), list = rangelist)

	def returnLang(self,data):
		if data:
			self.lang = data[1]
			config.mediaportal.laola1_lang.value = self.lang
			config.mediaportal.laola1_lang.save()
			configfile.save()
			self['F2'].setText(data[0])
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "Live":
			Link = Link.replace('%s-%s',self.lang+'-'+self.portal)
			self.session.open(laolaLiveScreen, Name, Link)
		else:
			self.session.open(laolaSubGenreScreen, Name, Link, self.parse.group(2))

class laolaSubGenreScreen(MPScreen):

	def __init__(self, session, Name, Link, parse):
		self.Name = Name
		self.Link = Link
		self.parse = parse
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Laola1.tv")
		self['ContentTitle'] = Label(self.Name)

		self.keyLocked = True
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.parseData)

	def parseData(self):
		parse = re.search('crane_menu_icon_toggle".*?'+self.Name+'(.*?)</ul>', self.parse, re.S)
		raw = re.findall('<a\shref="(.*?)">(.*?)</a>', parse.group(1), re.S)
		if raw:
			self.genreliste = []
			for (Url, Title) in raw:
				self.genreliste.append((decodeHtml(Title.strip()), Url))
		self.genreliste.insert(0,('Latest Videos '+self.Name, self.Link))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(laolaSelectGenreScreen, Name, Link)

class laolaLiveScreen(MPScreen):

	def __init__(self, session, Name, Link):
		self.Name = Name
		self.Link = Link
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Laola1.tv")
		self['ContentTitle'] = Label(self.Name)

		self.genreliste = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def char_gen(self, size=1, chars=string.ascii_uppercase):
		return ''.join(random.choice(chars) for x in range(size))

	def loadPage(self):
		getPage(self.Link, headers=special_headers).addCallback(self.getLiveData).addErrback(self.dataError)

	def getLiveData(self, data):
		live = re.findall('<img\swidth="80"\sheight="45"\ssrc=".*?">.*?<a\shref="(.*?)"><h2>(.*?)</h2>.*?<span\sclass="ititle">(Liga|League|Лига):</span><span\sclass="idesc\shalf">(.*?)</span>.*?<span\sclass="ititle\sfull">Streamstart:</span><span\sclass="idesc\sfull">.*?,\s(.*?)</span>.*?<span\sclass="ititle\sfull">(Verf&uuml;gbar\sin|Available in|Доступно в):</span><span\sclass="idesc\sfull"><span\sstyle="color:\#0A0;">(.*?)<', data, re.S)
		if live:
			for url,sportart,dummy,welche,time,dummy,where in live:
				sportart = sportart.replace('<div class="hdkennzeichnung"></div>','')
				title = "%s - %s - %s" % (time, sportart, welche)
				self.genreliste.append((title, url))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		self.keyLocked = True
		self.auswahl = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		getPage(url, headers=special_headers).addCallback(self.getLiveData1).addErrback(self.dataError)

	def getLiveData1(self, data):
		if 'Dieser Stream beginnt' in data:
			self.keyLocked = False
			message = self.session.open(MessageBoxExt, _("Event has not yet started."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.keyLocked = False
			match_player = re.findall('<iframe(.*?)src="(.*?)"', data, re.S)
			for iframestuff,possible_player in match_player:
				if 'class="main_tv_player"' in iframestuff:
					player = possible_player
					getPage(player, headers=special_headers).addCallback(self.getLiveData2).addErrback(self.dataError)

	def getLiveData2(self,data):
		match_streamid=re.findall('streamid:\s"(.*?)"', data, re.S)
		streamid = match_streamid[0]
		match_partnerid=re.findall('partnerid:\s"(.*?)"', data, re.S)
		partnerid = match_partnerid[0]
		match_portalid=re.findall('portalid:\s"(.*?)"', data, re.S)
		portalid = match_portalid[0]
		match_sprache=re.findall('sprache:\s"(.*?)"', data, re.S)
		sprache = match_sprache[0]
		match_auth=re.findall('auth\s=\s"(.*?)"', data, re.S)
		auth = match_auth[0]
		match_timestamp=re.findall('timestamp\s=\s"(.*?)"', data, re.S)
		timestamp = match_timestamp[0]
		url = 'http://www.laola1.tv/server/hd_video.php?play='+streamid+'&partner='+partnerid+'&portal='+portalid+'&v5ident=&lang='+sprache
		getPage(url, headers=special_headers).addCallback(self.getLiveData3,timestamp,auth).addErrback(self.dataError)

	def getLiveData3(self,data,timestamp,auth):
		match_url=re.findall('<url>(.*?)<', data, re.S)
		new_match_url = match_url[0].replace('&amp;','&').replace('l-_a-','l-L1TV_a-l1tv')+'&timestamp='+timestamp+'&auth='+auth
		getPage(new_match_url, headers=special_headers).addCallback(self.getLiveData4).addErrback(self.dataError)

	def getLiveData4(self,data):
		match_new_auth=re.findall('auth="(.*?)"', data, re.S)
		match_new_url=re.findall('url="(.*?)"', data, re.S)
		m3u8_url = match_new_url[0].replace('/z/','/i/').replace('manifest.f4m','master.m3u8')+'?hdnea='+match_new_auth[0]+'&g='+self.char_gen(12)+'&hdcore=3.2.0|X-Forwarded-For='+xip
		self.session.open(SimplePlayer, [(self.auswahl, m3u8_url)], showPlaylist=False, ltype='laola1')

class laolaSelectGenreScreen(MPScreen):

	def __init__(self, session, Name, Link):
		self.Name = Name
		self.Link = Link
		self.geo = "&geo=" + config.mediaportal.laola1_portal.value
		self.lang = "&lang=" + config.mediaportal.laola1_lang.value
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Laola1.tv")
		self['ContentTitle'] = Label(self.Name)

		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 999

		self.genreliste = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def char_gen(self, size=1, chars=string.ascii_uppercase):
		return ''.join(random.choice(chars) for x in range(size))

	def loadPage(self):
		self['page'].setText(str(self.page))
		getPage(self.Link, headers=special_headers).addCallback(self.getKey).addErrback(self.dataError)

	def getKey(self, data):
		parse = re.search('stage_frame\sactive".*?data-stageid=\s"(.*?)".*?data-call="(.*?)".*?data-page="(.*?)".*?data-filterpage="(.*?)".*?data-startvids="(.*?)".*?data-htag="(.*?)"', data, re.S).groups()
		stageid = int(parse[0])
		anzahlblock = 2+(self.page-1)*10
		filterpage = parse[3]
		startvids = parse[4]
		url = "http://www.laola1.tv/nourish.php?stageid=%s&newpage=%s&filterpage=%s&startvids=%s&anzahlblock=%s%s%s" % (stageid, self.page, filterpage, startvids, anzahlblock, self.lang, self.geo)
		getPage(url, headers=special_headers).addCallback(self.getEventData).addErrback(self.dataError)

	def getEventData(self, data):
		self.genreliste = []
		events = re.findall('<span\sclass="category">(.*?)</span>.*?<span\sclass="date">.*?,\s(.*?)</span>.*?<a\shref="/(.*?)">.*?title="(.*?)"\ssrc="(.*?)"', data, re.S)
		if events:
			for genre,time,url,desc,image in events:
				desc = desc.replace('Gepa | ','').replace('getty | ','').replace('laola1 | ','')
				title = "%s - %s" % (time, decodeHtml(desc))
				url = "http://www.laola1.tv/%s" % url
				self.genreliste.append((title, url, genre, image))
		if len(self.genreliste) == 0:
			self.genreliste.append((_('No videos found!'), None, '', None))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		self.keyLocked = True
		self.auswahl = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if url == None:
			return
		getPage(url, headers=special_headers).addCallback(self.getData).addErrback(self.dataError)

	def getData(self, data):
		self.keyLocked = False
		match_player = re.findall('<iframe(.*?)src="(.*?)"', data, re.S)
		for iframestuff,possible_player in match_player:
			if 'class="main_tv_player"' in iframestuff:
				player = possible_player
				getPage(player, headers=special_headers).addCallback(self.getData1).addErrback(self.dataError)

	def getData1(self,data):
		match_streamid=re.findall('streamid:\s"(.*?)"', data, re.S)
		streamid = match_streamid[0]
		match_partnerid=re.findall('partnerid:\s"(.*?)"', data, re.S)
		partnerid = match_partnerid[0]
		match_portalid=re.findall('portalid:\s"(.*?)"', data, re.S)
		portalid = match_portalid[0]
		match_sprache=re.findall('sprache:\s"(.*?)"', data, re.S)
		sprache = match_sprache[0]
		match_auth=re.findall('auth\s=\s"(.*?)"', data, re.S)
		auth = match_auth[0]
		match_timestamp=re.findall('timestamp\s=\s"(.*?)"', data, re.S)
		timestamp = match_timestamp[0]
		url = 'http://www.laola1.tv/server/hd_video.php?play='+streamid+'&partner='+partnerid+'&portal='+portalid+'&v5ident=&lang='+sprache
		getPage(url, headers=special_headers).addCallback(self.getData2,timestamp,auth).addErrback(self.dataError)

	def getData2(self,data,timestamp,auth):
		match_url=re.findall('<url>(.*?)<', data, re.S)
		new_match_url = match_url[0].replace('&amp;','&').replace('l-_a-','l-L1TV_a-l1tv')+'&timestamp='+timestamp+'&auth='+auth
		getPage(new_match_url, headers=special_headers).addCallback(self.getData3).addErrback(self.dataError)

	def getData3(self,data):
		match_new_auth=re.findall('auth="(.*?)"', data, re.S)
		match_new_url=re.findall('url="(.*?)"', data, re.S)
		m3u8_url = match_new_url[0].replace('/z/','/i/').replace('manifest.f4m','master.m3u8')+'?hdnea='+match_new_auth[0]+'&g='+self.char_gen(12)+'&hdcore=3.2.0|X-Forwarded-For='+xip
		self.session.open(SimplePlayer, [(self.auswahl, m3u8_url)], showPlaylist=False, ltype='laola1')

	def showInfos(self):
		self.ImageUrl = self['liste'].getCurrent()[0][3]
		CoverHelper(self['coverArt']).getCover(self.ImageUrl)