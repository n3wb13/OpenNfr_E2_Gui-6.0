# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

IPhone5Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3'
MyHeaders= {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
			'Accept-Language':'en-US,en;q=0.5'}

config.mediaportal.beeg_apikey = ConfigText(default="1764", fixed_size=False)
config.mediaportal.beeg_salt = ConfigText(default="Q3A5Bc6oJ934nAXedx3nyM", fixed_size=False)

class beegGenreScreen(MPScreen):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("beeg.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''
		self.tags = 'popular'
		self.looplock = False

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://api2.beeg.com/api/v6/%s/index/main/0/mobile" % config.mediaportal.beeg_apikey.value
		twAgentGetPage(url, agent=IPhone5Agent, headers=MyHeaders).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('"%s":\[(.*?)\]' % self.tags, data, re.S)
		if parse:
			Cats = re.findall('"(.*?)"', parse.group(1), re.S)
			if Cats:
				for Title in Cats:
					Url = 'http://api2.beeg.com/api/v6/%s/index/tag/$PAGE$/mobile?tag=%s' % (config.mediaportal.beeg_apikey.value, Title)
					Title = Title.title()
					self.genreliste.append((Title, Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Longest", "http://api2.beeg.com/api/v6/%s/index/tag/$PAGE$/mobile?tag=long%svideos" % (config.mediaportal.beeg_apikey.value, "%20")))
			self.genreliste.insert(0, ("Newest", "http://api2.beeg.com/api/v6/%s/index/main/$PAGE$/mobile" % config.mediaportal.beeg_apikey.value))
			if self.tags == 'popular':
				self.genreliste.insert(0, ("- Show all Tags -", ""))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False
		else:
			if not self.looplock:
				self.getkeys()
			else:
				self.keyLocked = False
				message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def getkeys(self):
		self.looplock = True
		url = "http://beeg.com"
		twAgentGetPage(url, agent=IPhone5Agent, headers=MyHeaders).addCallback(self.getkeysData).addErrback(self.dataError)

	def getkeysData(self, data):
		parse = re.search('cpl/(\d+)\.js', data, re.S)
		if parse and config.mediaportal.beeg_apikey.value != parse.group(1):
			config.mediaportal.beeg_apikey.value = parse.group(1)
			config.mediaportal.beeg_apikey.save()
		url = "http://static.beeg.com/cpl/%s.js" % config.mediaportal.beeg_apikey.value
		twAgentGetPage(url, agent=IPhone5Agent, headers=MyHeaders).addCallback(self.getsaltData).addErrback(self.dataError)

	def getsaltData(self, data):
		parse = re.search('beeg_salt="(.*?)"', data, re.S)
		if parse:
			config.mediaportal.beeg_salt.value = parse.group(1)
			config.mediaportal.beeg_salt.save()
			self.layoutFinished()
		else:
			self.keyLocked = False
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "- Show all Tags -":
			self.tags = 'nonpopular'
			self.genreliste = []
			self.layoutFinished()
		elif Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(beegFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = 'http://api2.beeg.com/api/v6/%s/index/search/$PAGE$/mobile?query=%s' % (config.mediaportal.beeg_apikey.value, self.suchString)
			Name = "--- Search ---"
			self.session.open(beegFilmScreen, Link, Name)

class beegFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("beeg.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = self.Link.replace('$PAGE$', '%s' % str(self.page-1))
		twAgentGetPage(url, agent=IPhone5Agent, headers=MyHeaders).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', '"pages":(.*?),')
		Videos = re.findall('\{"title":"(.*?)","id":"(.*?)"', data, re.S)
		if Videos:
			for (Title, VideoId) in Videos:
				Url = 'http://api2.beeg.com/api/v6/%s/video/%s' % (config.mediaportal.beeg_apikey.value, VideoId)
				Image = 'http://img.beeg.com/236x177/%s.jpg' % VideoId
				self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		twAgentGetPage(url, agent=IPhone5Agent, headers=MyHeaders).addCallback(self.getVideoPage).addErrback(self.dataError)
		
	def getVideoPage(self, data):
		streamlinks = re.findall('\d{3}p":"(.*?)"', data , re.S)
		if streamlinks:
			streamlink = streamlinks[-1].replace('{DATA_MARKERS}','data=pc.DE')
			linkid = re.search('^(.*?key=)(.*?)(%2C.*?)$', streamlink)
			if linkid:
				a = config.mediaportal.beeg_salt.value
				e = urllib2.unquote(linkid.group(2)).decode('utf-8')
				t = len(a)
				o = ''
				for n in range(len(e)):
					r = ord(e[n])
					i = n % t
					s = ord(a[i]) % 21
					o += chr(r - s)
				ofinal = ''
				while len(o) > 3:
					oPart = o[-3:]
					o = o[:-3]
					ofinal = ofinal+oPart
				ofinal = ofinal+o
				Url = "http:" + linkid.group(1) + ofinal + linkid.group(3)
				Title = self['liste'].getCurrent()[0][0]
				Cover = self['liste'].getCurrent()[0][2]
				mp_globals.player_agent = IPhone5Agent
				self.session.open(SimplePlayer, [(Title, Url, Cover)], showPlaylist=False, ltype='beeg', cover=True)
				return
		message = self.session.open(MessageBoxExt, _("Stream not found"), MessageBoxExt.TYPE_INFO, timeout=3)