# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class autoBildGenreScreen(MPScreen):

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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Autobild.de")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Alle Videos", "videos/"))
		self.genreliste.append(("Aktionen", "videos/aktionen/"))
		self.genreliste.append(("Erlkönige", "videos/erlkoenige/"))
		self.genreliste.append(("Fahrberichte", "videos/fahrberichte/"))
		self.genreliste.append(("Klassik", "videos/klassik/"))
		self.genreliste.append(("Messen", "videos/messen/"))
		self.genreliste.append(("Motorsport", "index_3398533.html"))
		self.genreliste.append(("Neuvorstellungen", "videos/neuvorstellungen/"))
		self.genreliste.append(("Ratgeber", "videos/ratgeber/"))
		self.genreliste.append(("Tests", "videos/tests/"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		streamGenreLink = "http://www.autobild.de/" + self['liste'].getCurrent()[0][1] + "?page="
		self.session.open(autoBildFilmListeScreen, streamGenreLink, Name)

class autoBildFilmListeScreen(MPScreen, ThumbsHelper):
	def __init__(self, session, streamGenreLink, Name):
		self.streamGenreLink = streamGenreLink
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
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("Autobild.de")
		self['ContentTitle'] = Label("Spot Auswahl: %s" % self.Name)
		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.filmliste = []
		self.keckse = {}
		self.page = 1
		self.lastpage = 999
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "%s%s" % (self.streamGenreLink, str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		videos = re.findall('<div class="horizontal teaser clearfix">.*?<div class="pictureblock"><img src="(.*?)".*?<h2 class="kicker"><a href="(.*?)">(.*?)</a>.*?<p class="text">(.*?)</p>', data, re.S)
		if videos:
			self.filmliste = []
			for (image,url,title,handlung) in videos:
				self.filmliste.append((decodeHtml(title), url, image, handlung))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		streamPic = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(streamName)
		self['handlung'].setText(decodeHtml(handlung))
		self['page'].setText(str(self.page))
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		url = "%s%s" % (streamLink ,"?getjson=1")
		getPage(url).addCallback(self.findStream).addErrback(self.dataError)

	def findStream(self, data):
		self.keyLocked = False
		streamname = self['liste'].getCurrent()[0][0]
		stream_url = re.findall('"src":"http:(.*?).mp4"', data, re.S)
		urlConv = 'http:' + stream_url[0].replace('\\', '') + '.mp4'
		if stream_url:
			self.session.open(SimplePlayer, [(streamname, urlConv)], showPlaylist=False, ltype='autobild')