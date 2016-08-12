# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class sunpornoGenreScreen(MPScreen):

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
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("SunPorno.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		url = "http://www.sunporno.com/channels/"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('<div\sclass="wrap\sinternal_head6x"></div>(.*?)<div\sid="wrapBlocks"\sclass="cat-paging">', data, re.S)
		Cats = re.findall('<div\sclass="category-wrap.*?<h3><a\shref="http://www.sunporno.com/channels/(.*?)/.*?">(.*?)</a></h3>.*?<span\sclass="category-count">(.*?)</span>.*?<div\sclass="category-block">', parse.group(1), re.S)
		if Cats:
			for (Id, Title, Count) in Cats:
				Url = "http://www.sunporno.com/?area=movieAjaxListViewer&nicheId=%s&dateAddedType=5&lengthType=0-50&orderBy=id&pageId=" % Id
				self.genreliste.append((Title, Url, Count))
			self.genreliste.sort()
			self.genreliste.insert(0, ("High Definition", "http://www.sunporno.com/?area=movieAjaxListViewer&dateAddedType=5&lengthType=0-50&orderBy=hd&pageId=", 1799))
			self.genreliste.insert(0, ("Longest", "http://www.sunporno.com/?area=movieAjaxListViewer&dateAddedType=5&lengthType=0-50&orderBy=longest&pageId=", 1799))
			self.genreliste.insert(0, ("Most Favorited", "http://www.sunporno.com/?area=movieAjaxListViewer&dateAddedType=5&lengthType=0-50&orderBy=favorited&pageId=", 1799))
			self.genreliste.insert(0, ("Top Rated", "http://www.sunporno.com/?area=movieAjaxListViewer&dateAddedType=5&lengthType=0-50&orderBy=rating&pageId=", 1799))
			self.genreliste.insert(0, ("Newest", "http://www.sunporno.com/?area=movieAjaxListViewer&dateAddedType=5&lengthType=0-50&orderBy=id&pageId=", 1799))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", 1799))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
		self['name'].setText('')

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()

		else:
			Link = self['liste'].getCurrent()[0][1]
			Count = self['liste'].getCurrent()[0][2]
			self.session.open(sunpornoFilmScreen, Link, Name, Count)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			Count = self['liste'].getCurrent()[0][2]
			self.session.open(sunpornoFilmScreen, Link, Name, Count)

class sunpornoFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Count):
		self.Link = Link
		self.Name = Name
		self.Count = Count
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

		self['title'] = Label("SunPorno.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://www.sunporno.com/?area=movieAjaxListViewer&q=%s&dateAddedType=5&lengthType=0-50&orderBy=relevance&pageId=%s" % (self.Link, str(self.page))
		else:
			url = "%s%s" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.lastpage = int(round((float(self.Count) / 56) + 0.5))
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		Movies = re.findall('id":(.*?),"thumb":"(.*?)",.*?duration":"(.*?)",.*?name":\s{0,1}"(.*?)"', data, re.S)
		if Movies:
			for (Id, Image, Runtime, Title) in Movies:
				Title = Title.replace('-',' ').title()
				Url = "http://www.sunporno.com/videos/%s/" % Id
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		self['handlung'].setText("Runtime: %s" % (runtime))
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		parse = re.findall('itemprop="name">(.*?)</span>', data, re.S|re.I)
		title = decodeHtml(parse[0])
		if parse:
			title = decodeHtml(parse[0])
		else:
			title = self['liste'].getCurrent()[0][0]
		video = re.findall('video\ssrc="(.*?)"', data, re.S)
		if video:
			self.keyLocked = False
			self.session.open(SimplePlayer, [(title, video[0])], showPlaylist=False, ltype='sunporno')