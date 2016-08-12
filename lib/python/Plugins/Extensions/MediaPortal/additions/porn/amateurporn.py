# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class amateurpornGenreScreen(MPScreen):

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

		self['title'] = Label("AmateurPorn.net")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.amateurporn.net/channels/"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cat = re.findall('<h1>Channels<div\sid="plusone"><g:plusone></g:plusone></div></h1>(.*?)</div>', data, re.S)
		if Cat:
			for Data in Cat:
				Cats = re.findall('<a href="(.*?)"\stitle=".*?">(.*?)</a>', Data, re.S)
		if Cats:
			for (Url, Title) in Cats:
				self.genreliste.append((decodeHtml(Title), Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Top Rated", "/top-rated/", None))
			self.genreliste.insert(0, ("Most Popular", "/most-viewed/", None))
			self.genreliste.insert(0, ("Newest", "", None))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()

		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(amateurpornFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '%20')
			Name = self['liste'].getCurrent()[0][0]
			Link = '/search/%s/' % (self.suchString)
			self.session.open(amateurpornFilmScreen, Link, Name)

class amateurpornFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("AmateurPorn.net")
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
		url = "http://www.amateurporn.net%s/page%s.html" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'id="pagination">(.*?)</div>')
		Movie = re.findall('class="video">.*?<a\shref="(.*?)".*?<img src="(.*?)"\salt="(.*?)".*?margin-top:2px;">(.*?)\sviews</span>.*?text-align:right;\'>(.*?)<br\s/>', data, re.S)
		if Movie:
			for (Url, Pic, Title, Views, Runtime) in Movie:
				Pic = Pic.replace(' ','%20')
				self.filmliste.append((decodeHtml(Title), Url, Pic, Runtime, Views))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste,0,1,2,3,None,self.page,self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		runtime = runtime.replace('\t','').replace('\n','').replace('\r','').replace(' ','')
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nViews: %s" % (runtime, views))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(url).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('<param\sname="flashvars"\svalue="file=(.*?)&provider=', data, re.S)
		if videoPage:
			for url in videoPage:
				self.keyLocked = False
				title = self['liste'].getCurrent()[0][0]
				self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='amateurporn')