# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

wn = "wrestlingnetwork.tv"

class wrestlingnetworkGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		if self.mode == "watchwrestling":
			self.portal = "watchwrestling.in"
			self.baseurl = "http://watchwrestling.in"
		if self.mode == "wrestlingnetwork":
			self.portal = "wrestlingnetwork.tv"
			self.baseurl = "http://wrestlingnetwork.tv/"

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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		url = self.baseurl
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if self.portal == wn:
			raw = re.findall('Home</a></li>(.*?)</ul></div>	', data, re.S)
		else:
			raw = re.findall('id="main-nav">(.*?)</ul>', data, re.S)
		if raw:
			parse = re.findall('<li.*?href="(.*?)">(.*?)</a>', raw[0], re.S)
			for (url, title) in parse:
				self.genreliste.append((decodeHtml(title), url))
			self.genreliste.sort()
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False
			self.showInfos()
		self['name'].setText('')

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Url = self['liste'].getCurrent()[0][1]
		self.session.open(wrestlingnetworkListeScreen, Name, Url, self.portal)

class wrestlingnetworkListeScreen(MPScreen):

	def __init__(self, session, Name,Link, portal):
		self.Link = Link
		self.Name = Name
		self.portal = portal
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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)

		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		if self.portal == wn:
			url = "%s/page/%s" % (self.Link ,str(self.page))
		else:
			url = "%spage/%s" % (self.Link ,str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if self.portal == wn:
			self.getLastPage(data, 'class=\'pagination\'>(.*?)</div>')
			raw = re.findall('id="main"(.*?)id="sidebar"', data, re.S)
			shows = re.findall('class="solar-featured-content".*?src="(.*?)".*?\shref="(.*?)">\s+(.*?)<', raw[0], re.S)
			if shows:
				self.filmliste = []
				for (image, url, title) in shows:
					title = title.strip()
					self.filmliste.append((decodeHtml(title),url,image))
		else:
			if re.search('<link rel="next"', data):
				self.lastpage = self.page + 1
				self['page'].setText(str(self.page) + ' + ')
			else:
				self['page'].setText(str(self.page))
			raw = re.findall('id="main">(.*?)id="sidebar"', data, re.S)
			shows = re.findall('clip-link.*?title="(.*?)" href="(.*?)".*?src="(.*?)"', raw[0], re.S)
			if shows:
				self.filmliste = []
				for (title,url,image) in shows:
					self.filmliste.append((decodeHtml(title),url,image))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Url = self['liste'].getCurrent()[0][1]
		self.session.open(wrestlingnetworkPlayer, Name, Url, self.portal)

class wrestlingnetworkPlayer(MPScreen):

	def __init__(self, session, Name, Url, portal):
		self.Name = Name
		self.Url = Url
		self.portal = portal
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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Videos: %s" %self.Name)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.getVideo)

	def getVideo(self):
		url = self.Url
		getPage(url).addCallback(self.getData).addErrback(self.dataError)

	def getData(self, data):
		if self.portal == wn:
			url = re.findall('href="(http://(www.|)wrestlingnetwork.(net|tv)/dailymotion-embed/.*?)">(.*?)</a>', data, re.S)
			if url:
				self.filmliste = []
				for (url,dump,dump1,title) in url:
					self.filmliste.append((decodeHtml(title),url))
			else:
				self.filmliste.append((_("Video deleted or there has been an error!"), None))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
		else:
			if re.match('.*?Link will added in Few Hours', data, re.S):
				self.filmliste.append((_("Link will added in few Hours!"), None))
				self.keyLocked = True
			else:
				url = re.findall('href="(http[s]?://[^<>]*?)"\sclass="su-button.*?webkit-text-shadow:none">(.*?)</span>', data, re.S)
				if url:
					self.filmliste = []
					for (url,title) in url:
						self.filmliste.append((decodeHtml(title),url))
						self.keyLocked = False
				else:
					self.filmliste.append((_("Video deleted or there has been an error!"), None))
					self.keyLocked = False
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.ml.moveToIndex(0)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			getPage(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml','Referer': self.Url}).addCallback(self.getExtraData).addErrback(self.dataError)

	def getExtraData(self, data):
		url = re.findall('<iframe.*?src="(http://www.dailymotion.com/embed/video/.*?)"', data, re.S)
		if url:
			getPage(url[0]).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		data = data.replace("\\/", "/")
		if self.portal == wn:
			title = self['liste'].getCurrent()[0][0]
		else:
			title = self['liste'].getCurrent()[0][0]
		streamname = self.Name + " - " + title
		stream_url = re.findall('"(240|380|480)".*?url":"(http://www.dailymotion.com/cdn/.*?)"', data, re.S)
		if stream_url:
			self.session.open(SimplePlayer, [(streamname, stream_url[-1][1])], showPlaylist=False, ltype='wrestling')
		else:
			message = self.session.open(MessageBoxExt, _("Video deleted or has an error!"), MessageBoxExt.TYPE_INFO, timeout=3)