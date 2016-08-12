# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class pornoidGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		if self.mode == "pornoid":
			self.portal = "Pornoid.com"
			self.baseurl = "www.pornoid.com"
		if self.mode == "befuck":
			self.portal = "BeFuck.com"
			self.baseurl = "www.befuck.com"

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "http://%s/categories/" % self.baseurl
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw = re.findall('class="ic">.*?<a\shref="(.*?)".*?src="(.*?)">.*?<figcaption>(.*?)</figcaption>.*?</span><b>', data, re.S)
		if raw:
			for (Url, Image, Title) in raw:
				Title = Title.strip().title()
				self.filmliste.append((decodeHtml(Title), Url, Image))
			self.filmliste.sort()
			self.filmliste.insert(0, ("Most Popular", "http://%s/most-popular/" % self.baseurl, None))
			self.filmliste.insert(0, ("Top Rated", "http://%s/" % self.baseurl, None))
			self.filmliste.insert(0, ("Newest", "http://%s/" % self.baseurl, None))
			self.filmliste.insert(0, ("--- Search ---", "callSuchen", None))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False
			self.showInfos()
		self['name'].setText('')

	def showInfos(self):
		ImageUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(ImageUrl)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = '?q=%s' % self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(pornoidListScreen, Link, Name, self.portal, self.baseurl)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornoidListScreen, Link, Name, self.portal, self.baseurl)

class pornoidListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal, baseurl):
		self.Link = Link
		self.Name = Name
		self.portal = portal
		self.baseurl = baseurl
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.lastpage = 1

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		if re.match('.*?Search', self.Name):
			url = 'http://%s/searchpages/%s' % (self.baseurl, self.Link)
		else:
			url = self.Link + str(self.page) + "/"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		data = re.sub(r'<[<!--].*<a href="http://www.pornoid.com/login.php..*-->', "", data)
		self.getLastPage(data, '<nav\sid="pgn">(.*?)</nav>')
		raw = re.findall('<div\sclass="ic">.*?href="(http://\D+/videos/.*?)"\s(class=".*?title=|title=)"(.*?)">.*?src="(.*?)".*?<span>(.*?)</span>', data, re.S)
		if raw:
			for (Link, x, Title, Image, Length) in raw:
				if not re.match(".*?pornsharia.com", Link, re.S):
					Title = Title.strip()
					self.filmliste.append((decodeHtml(Title), Link, Image, Length))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		runtime = self['liste'].getCurrent()[0][3]
		self['handlung'].setText("Runtime: %s" % runtime)
		self['name'].setText(title)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getStreamData).addErrback(self.dataError)

	def getStreamData(self, data):
		title = self['liste'].getCurrent()[0][0]
		videoLink = re.search("video_url:\s'(.*?)'", data, re.S)
		if videoLink:
			self.session.open(SimplePlayer, [(title, videoLink.group(1))], showPlaylist=False, ltype='pornoid')