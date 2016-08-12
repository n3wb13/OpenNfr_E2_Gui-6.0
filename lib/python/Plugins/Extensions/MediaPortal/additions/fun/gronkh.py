# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

class gronkhGenreScreen(MPScreen, ThumbsHelper):

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
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("gronkh.de")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://gronkh.de/lets-player"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('Play-Team</h4></div>(.*?)</div>', data, re.S)
		Cats = re.findall('<a\stitle="(.*?)"\shref="(.*?)">.*?<img\salt.*?src=\'(.*?)\'', parse.group(1), re.S)
		if Cats:
			for (Title, Url, Image) in Cats:
				Url = "http://gronkh.de" + Url + '/page/'
				self.genreliste.append((Title, Url, Image))
			self.genreliste.insert(0, ("Angezockt", "http://gronkh.de/testet/page/", None))
			self.genreliste.insert(0, ("Aktuelle Folgen", "http://gronkh.de/page/", None))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.genreliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(gronkhFilmScreen, streamGenreLink, Name)

class gronkhFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, Name):
		self.CatLink = CatLink
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

		self['title'] = Label("gronkh.de")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self['title'].setText('gronkh.de')

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s%s" % (self.CatLink, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '<ol\sclass="wp-paginate">(.*?)</ol>')
		if re.search('http://gronkh.de/testet/page/', self.CatLink):
			Movies = re.findall('letsplay.*?id=".*?">.*?thumb"\shref="(.*?)".*?img\ssrc="(.*?)".*?title="(.*?)"', data, re.S)
			if Movies:
				for (Url, Image, Title) in Movies:
					self.filmliste.append((decodeHtml(Title), Url, Image))
		else:
			Movies = re.findall('letsplay.*?id=".*?">.*?thumb"\shref="(.*?)".*?img\ssrc="(.*?)".*?<h1>.*?title="(.*?)".*?<h2>.*?title=".*?".*?>(.*?)</a>', data, re.S)
			if Movies:
				for (Url, Image, Title1, Title2) in Movies:
					Title = Title1 + ' - ' + Title2
					self.filmliste.append((decodeHtml(Title), Url, Image))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('"http://www.youtube.com/(v|embed)/(.*?)\?.*?"', data, re.S)
		if videoPage:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(YoutubePlayer,[(title, videoPage[0][1], None)],playAll= False,showPlaylist=False,showCover=False)
		else:
			message = self.session.open(MessageBoxExt, _("This video is not available."), MessageBoxExt.TYPE_INFO, timeout=5)
		self.keyLocked = False