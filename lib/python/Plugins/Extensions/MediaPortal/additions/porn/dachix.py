# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class dachixGenreScreen(MPScreen):

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

		self['title'] = Label("Dachix.com")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.suchString = ''

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "http://www.dachix.com/categories"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw = re.findall('class="listing-categories">.*?<a\shref="(.*?)".*?class="title">(.*?)</b>.*?src="(.*?)"', data, re.S)
		if raw:
			for (Url, Title, Image) in raw:
				Url = "http://www.dachix.com" + Url + "/videos"
				self.filmliste.append((decodeHtml(Title), Url, Image))
			self.filmliste.sort()
			self.filmliste.insert(0, ("Longest", "http://www.dachix.com/videos?sort=longest", None))
			self.filmliste.insert(0, ("Most Popular", "http://www.dachix.com/videos?sort=popular", None))
			self.filmliste.insert(0, ("Most Viewed", "http://www.dachix.com/videos?sort=viewed", None))
			self.filmliste.insert(0, ("Top Rated", "http://www.dachix.com/videos?sort=rated", None))
			self.filmliste.insert(0, ("Most Recent", "http://www.dachix.com/videos", None))
			self.filmliste.insert(0, ("--- Search ---", "callSuchen", None))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False
			self.showInfos()
		self['name'].setText('')

	def showInfos(self):
		pic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(pic)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '-')
			Link = 'http://www.dachix.com/s/%s' % (self.suchString)
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(dachixListScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(dachixListScreen, Link, Name)

class dachixListScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("Dachix.com")
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
		if re.match('.*?\?sort', self.Link, re.S):
			url = self.Link + "&p=" + str(self.page)
		else:
			url = self.Link + "?p=" + str(self.page)
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, 'class="main-sectionpaging">(.*?)</div>', '.*p=(\d+)"')
		raw = re.findall('itemprop="video".*?title="(.*?)".*?content="(.*?)".*?src="(.*?)".*?duration"\scontent=".*?">(.*?)\s-', data, re.S)
		if raw:
			for (Title, Link , Image, Duration) in raw:
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
		self['name'].setText(title)
		pic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = "http://" + self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getStreamData).addErrback(self.dataError)

	def getStreamData(self, data):
		self.title = self['liste'].getCurrent()[0][0]
		url = re.search('file":"(.*?)"', data, re.S)
		url = unquote(url.group(1))
		if url:
			self.session.open(SimplePlayer, [(self.title, url)], showPlaylist=False, ltype='dachix')