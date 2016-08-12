# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class amateurslustGenreScreen(MPScreen):

	def __init__(self, session):
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

		self['title'] = Label("AmateursLust.com")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.suchString = ''

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "http://www.amateurslust.com/categories.html"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('<h1>Porn\sCategories</h1>(.*?)id="right-banners-main', data, re.S)
		raw = re.findall('<a\shref="(.*?)".*?<h3>(.*?)</h3>.*?src="(.*?)"\s/>', parse.group(1), re.S)
		if raw:
			for (Url, Title, Image) in raw:
				Url = "http://www.amateurslust.com" + Url + "page"
				self.filmliste.append((decodeHtml(Title), Url, Image))
			self.filmliste.sort()
			self.filmliste.insert(0, ("Top Rated", "http://www.amateurslust.com/page", None))
			self.filmliste.insert(0, ("Newest", "http://www.amateurslust.com/page", None))
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
			self.suchString = callback.replace(' ', '-')
			Link = 'http://www.amateurslust.com/search/%s/page' % (self.suchString)
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(amateurslustListScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(amateurslustListScreen, Link, Name)

class amateurslustListScreen(MPScreen, ThumbsHelper):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("AmateursLust.com")
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
		if self.Name == "Top Rated":
			url = self.Link + str(self.page) + "/?sort=rating"
		else:
			url = self.Link + str(self.page) + "/"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, '<ul\sclass="paging">(.*?)<div\sclass="banners-horizontal">')
		parse = re.search('class="content">(.*?)id="right-banners-main', data, re.S)
		raw = re.findall('<a\shref="(.*?)".*?<h3>(.*?)</h3>.*?src="(.*?)"\s/>.*?<span>(.*?)</span>', parse.group(1), re.S)
		if raw:
			for (Link, Title, Image, Duration) in raw:
				self.filmliste.append((decodeHtml(Title), Link, Image, Duration))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		runtime = self['liste'].getCurrent()[0][3]
		self['handlung'].setText("Runtime: %s" % runtime)
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = "http://www.amateurslust.com" + self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getStreamData).addErrback(self.dataError)

	def getStreamData(self, data):
		title = self['liste'].getCurrent()[0][0]
		url = re.search("'video'.*?:.*?'(.*?)'", data, re.S)
		if url:
			self.session.open(SimplePlayer, [(title, url.group(1))], showPlaylist=False, ltype='amateurslust')