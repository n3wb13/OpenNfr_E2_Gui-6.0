# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class retrotvFilmListeScreen(MPScreen, ThumbsHelper):

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
			"ok"    : self.keyOK,
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

		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self['title'] = Label("retro-tv.de")
		self['ContentTitle'] = Label("Episoden")
		self['name'] = Label("Film Auswahl")
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		url = "http://www.retro-tv.de/archiv:%s" % str(self.page)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.getLastPage(data, 'Gehe zu Seite:(.*?)</div>')
		movies = re.findall('title="(Folge.*?)".*?href="(.*?)"><img\ssrc=".*?".*?<img\ssrc=".*?videos%2F(.*?)".*?td_description', data, re.S)
		if movies:
			self.filmliste = []
			for (title,url,image) in movies:
				image = 'http://www.retro-tv.de/image_resizer.php?width=320&height=240&image=gfx%2Fvideos%2F' + image
				url = 'http://www.retro-tv.de/' + url
				self.filmliste.append((decodeHtml(title),url,image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		streamTitle = self['liste'].getCurrent()[0][0]
		streamUrl = self['liste'].getCurrent()[0][1]
		streamPic = self['liste'].getCurrent()[0][2]
		self['name'].setText(streamTitle)
		CoverHelper(self['coverArt']).getCover(streamPic)
		getPage(streamUrl).addCallback(self.getDescription).addErrback(self.dataError)

	def getDescription(self, data):
		ddDescription = re.search('name="description"\scontent=".*?Heute:\s{0,2}(.*?)"', data, re.S)
		if ddDescription:
			self['handlung'].setText(decodeHtml(ddDescription.group(1)))
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		if self.keyLocked:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		if streamLink == None:
			return
		url = streamLink
		getPage(streamLink).addCallback(self.getlink).addErrback(self.dataError)

	def getlink(self, data):
		parse = re.findall('id=video-html5-source\ssrc="(.*?)"', data, re.S)
		if parse:
			url = parse[-1]
			title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='retrotv')