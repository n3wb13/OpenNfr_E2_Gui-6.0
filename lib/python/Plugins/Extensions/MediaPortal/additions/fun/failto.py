# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

class failScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
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
			"left" : self.keyLeft,
			"right" : self.keyRight,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Fail.to")
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "http://www.fail.to/genre/1-videos/p-%s" % str(self.page)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.getLastPage(data, '', 'class="pagination">.*?<strong>(.*?)</strong>')
		parse = re.search('<body>(.*?)class="pagination">', data, re.S)
		Videos = re.findall('class="entry">.*?</span><a href="(.*?)" title=".*?">(.*?)</a></h3>.*?class="preview".*?<img src="(.*?)"', parse.group(1), re.S)
		if Videos:
			self.filmliste = []
			for (Url, Title, Image) in Videos:
				Url = "http://www.fail.to" + Url
				Image = "http://www.fail.to" + Image
				self.filmliste.append((Title, Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		PicLink = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(PicLink)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		Title = self['liste'].getCurrent()[0][0]
		Stream = re.findall("'file': '(.*?)'", data)
		if Stream:
			Stream = "http://www.fail.to" + Stream[0]
			self.session.open(SimplePlayer, [(Title, Stream)], showPlaylist=False, ltype='failto')
		else:
			videoPage = re.findall('www.youtube.com/(v|embed)/(.*?)"', data, re.S)
			if videoPage:
				self.session.open(YoutubePlayer,[(Title, videoPage[0][1], None)],playAll= False,showPlaylist=False,showCover=False)