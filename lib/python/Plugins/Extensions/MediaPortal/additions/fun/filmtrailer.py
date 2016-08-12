# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class trailer(MPScreen, ThumbsHelper):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok"  : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("Filmtrailer.net")
		self['ContentTitle'] = Label("Trailer Auswahl")

		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.page = 1
		self.lastpage = 999
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "http://www.filmtrailer.net/page/%s" % str(self.page)
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		trailer = re.findall('<div class="entry-content">.*?<a href="(http://www.filmtrailer.net/trailer/.*?)".*?<span class="slide-title">(.*?)</span>.*?<img class="attachment-thumbnail" src="(http://www.filmtrailer.net/filmposter/.*?)"', data, re.S)
		if trailer:
			self.streamList = []
			for (url,title,image) in trailer:
				self.streamList.append((decodeHtml(title), url, image))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page, 999)
		self.showInfos()

	def showInfos(self):
		self['page'].setText("%s" % str(self.page))
		coverUrl = self['liste'].getCurrent()[0][2]
		self.filmtrailer = self['liste'].getCurrent()[0][0]
		self['name'].setText(self.filmtrailer)
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.parseID).addErrback(self.dataError)

	def parseID(self, data):
		channelID = re.findall('http://de.player-feed.filmtrailer.com/v2.0/cinema/(.*?)/', data, re.S)
		if channelID:
			print channelID
			url = "http://de.player-feed.filmtrailer.com/v2.0/cinema/" + channelID[0]
			getPage(url).addCallback(self.parseVideo).addErrback(self.dataError)

	def parseVideo(self, data):
		video = re.findall('<url>(.*?)<', data, re.S)
		if video:
			print video
			self.session.open(SimplePlayer, [(self.filmtrailer, video[-1])], showPlaylist=False, ltype='filmtrailer')