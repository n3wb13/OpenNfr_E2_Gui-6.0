# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class movie2kGenreScreen(MPScreen):

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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Movie2k")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [('Kinofilme',"http://www.m2k.to"),
							('Videofilme',"http://www.m2k.to")]
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		self.movie2kName = self['liste'].getCurrent()[0][0]
		movie2kUrl = self['liste'].getCurrent()[0][1]
		self.session.open(movie2kListeScreen, self.movie2kName, movie2kUrl)

class movie2kListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, movie2kName, movie2kUrl):
		self.movie2kName = movie2kName
		self.movie2kUrl = movie2kUrl
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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up": self.keyUp,
			"down": self.keyDown,
			"right": self.keyRight,
			"left": self.keyLeft,
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Movie2k")
		self['ContentTitle'] = Label(self.movie2kName)

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.movie2kUrl).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if self.movie2kName == "Kinofilme":
			self.kinofilme(data)
		elif self.movie2kName == "Videofilme":
			self.videofilme(data)

	def kinofilme(self, data):
		kino = re.findall('<div style="float:left">.*?<a href="(.*?)">.*?<img src="(.*?)".*?alt="(.*?).kostenlos".*?:</strong><br>(.*?)<', data, re.S)
		if kino:
			self.videoliste = []
			for (url, img, title, desc) in kino:
				self.videoliste.append((decodeHtml(title), url, img, desc))
			self.ml.setList(map(self._defaultlistleft, self.videoliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.videoliste, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def videofilme(self, data):
		video = re.findall('<div style="float: left;".*?<a href="(.*?)">.*?<img src="(.*?)".*?alt="(.*?)"', data, re.S)
		if video:
			self.videoliste = []
			for (url, img, title) in video:
				self.videoliste.append((decodeHtml(title), url, img))
			self.ml.setList(map(self._defaultlistleft, self.videoliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.videoliste, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(streamPic)
		self['name'].setText(title)
		if self.movie2kName == "Kinofilme":
			handlung = self['liste'].getCurrent()[0][3]
			self['handlung'].setText(decodeHtml(handlung))

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		self.session.open(movie2kStreamListeScreen, title, url, image)

class movie2kStreamListeScreen(MPScreen):

	def __init__(self, session, movie2kName, movie2kUrl, movie2kImage):
		self.movie2kName = movie2kName
		self.movie2kUrl = movie2kUrl
		self.movie2kImage = movie2kImage
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Movie2k")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.movie2kName)

		self.streamliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.movie2kUrl).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		hoster = re.findall('<tr\sid=.*?tablemoviesindex2.*?>.*?td\sheight="20"\swidth="150">.*?<a\shref.*?"(.*?.html).*?>(.*?)<img.*?/>&\#160;(.*?)</a>.*?title="Movie\squality\s(.*?)"', data, re.S)
		if hoster:
			self.streamliste = []
			for (url, date, hostername, quali) in hoster:
				if isSupportedHoster(hostername, True):
					self.streamliste.append((url, date, hostername, quali))
			if len(self.streamliste) == 0:
				self.streamliste.append((_('No supported streams found!'), None, None, None))
			self.ml.setList(map(self.movie2kStreamListEntry, self.streamliste))
			CoverHelper(self['coverArt']).getCover(self.movie2kImage)
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][0]
		if url:
			getPage(url).addCallback(self.get_hoster_link).addErrback(self.dataError)

	def get_hoster_link(self, data):
		hoster_link = re.findall('</div><br\s/>\s*<a\shref="(.*?)"\s*target="_BLANK"><img\ssrc="http://www\.m2k\.t./assets/img/click_link\.jpg"\s*border="0"\s*/></a>', data, re.S)
		if hoster_link:
			get_stream_link(self.session).check_link(hoster_link[0], self.got_link)
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def got_link(self, stream_url):
		self.session.open(SimplePlayer, [(self.movie2kName, stream_url, self.movie2kImage)], showPlaylist=False, ltype='movie2k', cover=True)