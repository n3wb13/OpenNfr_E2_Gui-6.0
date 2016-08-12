# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.simpleplayer import SimplePlayerMenu, SimplePlaylistIO

class eightiesGenreScreen(MPScreen):

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
			"cancel": self.keyCancel
		}, -1)

		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
		else:
			self.lastservice = None
		self.playing = False

		self.keyLocked = True
		self['title'] = Label("80s & 90s Music")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)
		self.onClose.append(self.stopPlay)

	def loadPage(self):
		self.genreliste = [('80s Music',"http://www.80smusicvids.com/"),
							('90s Music',"http://www.90smusicvidz.com/")]

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		eightiesName = self['liste'].getCurrent()[0][0]
		eightiesUrl = self['liste'].getCurrent()[0][1]
		self.session.open(eightiesMusicListeScreen, eightiesName, eightiesUrl)

	def keyCancel(self):
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)
		else:
			self.session.nav.stopService()
		self.playing = False
		self.close()

	def stopPlay(self):
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)
		else:
			self.session.nav.stopService()

class eightiesMusicListeScreen(MPScreen, InfoBarBase, InfoBarSeek):

	def __init__(self, session, genreName, genreLink):
		self.genreLink = genreLink
		self.genreName = genreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultPlaylistScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultPlaylistScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		if not mp_globals.isDreamOS:
			self.skin = re.sub(r'progress_pointer="(.*?):\d+,\d+" render="PositionGauge"', r'pixmap="\1" render="Progress"', self.skin)
			self.skin = re.sub(r'type="MPServicePosition">Gauge</convert>', r'type="MPServicePosition">Position</convert>', self.skin)

		MPScreen.__init__(self, session)
		InfoBarBase.__init__(self)
		InfoBarSeek.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"menu" : self.openMenu,
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.token = ''
		self.keyLocked = True
		self["title"] = Label(self.genreName)
		self["coverArt"] = Pixmap()
		self["songtitle"] = Label ("")
		self["artist"] = Label ("")
		self["album"] = Label ("%s" % self.genreName)
		self['playmode'] = Label("")

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		if re.match('.*?80smusicvids.com', self.genreLink, re.S):
			self.baseurl = "http://www.80smusicvids.com/"
			self.token = '80'
		else:
			self.baseurl = "http://www.90smusicvidz.com/"
			self.token = '90'

		getPage(self.genreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		vids = re.findall('<a target="_self" href="(.*?)">(.*?)</a><br>', data, re.S)
		if vids:
			for url,title in vids:
				url = "%s%s" % (self.baseurl, url)
				self.filmliste.append((decodeHtml(title),url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False

	def openMenu(self):
		self.session.openWithCallback(self.cb_Menu, SimplePlayerMenu, 'extern')

	def cb_Menu(self, data):
		if data != []:
			if data[0] == 2:
				playinfos = self['liste'].getCurrent()[0][0]
				if re.match('.*?-', playinfos):
					playinfos = playinfos.split(' - ')
					if playinfos:
						if len(playinfos) == 2:
							scArtist = playinfos[0]
							scTitle = playinfos[1]
							self["artist"].setText(playinfos[0])
							self["songtitle"].setText(playinfos[1])
					else:
						playinfos = playinfos.split('-')
						if playinfos:
							if len(playinfos) == 2:
								scArtist = playinfos[0]
								scTitle = playinfos[1]
								self["artist"].setText(playinfos[0])
								self["songtitle"].setText(playinfos[1])
				else:
					self["artist"].setText(playinfos)
					scArtist = ''
					scTitle = playinfos

				url = self['liste'].getCurrent()[0][1]
				ltype = 'eighties'
				token = self.token
				album = self.genreName
				entry = [scTitle, url, scArtist, album, ltype, token, '', '0']

				res = SimplePlaylistIO.addEntry(data[1], entry)
				if res == 1:
					self.session.open(MessageBoxExt, _("Added entry"), MessageBoxExt.TYPE_INFO, timeout=5)
				elif res == 0:
					self.session.open(MessageBoxExt, _("Entry already exists"), MessageBoxExt.TYPE_INFO, timeout=5)
				else:
					self.session.open(MessageBoxExt, _("Error!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def keyOK(self):
		if self.keyLocked:
			return
		eightiesName = self['liste'].getCurrent()[0][0]
		eightiesUrl = self['liste'].getCurrent()[0][1]

		playinfos = self['liste'].getCurrent()[0][0]
		if re.match('.*?-', playinfos):
			playinfos = playinfos.split(' - ')
			if playinfos:
				if len(playinfos) == 2:
					scArtist = playinfos[0]
					scTitle = playinfos[1]
					self["artist"].setText(playinfos[0])
					self["songtitle"].setText(playinfos[1])
			else:
				playinfos = playinfos.split('-')
				if playinfos:
					if len(playinfos) == 2:
						scArtist = playinfos[0]
						scTitle = playinfos[1]
						self["artist"].setText(playinfos[0])
						self["songtitle"].setText(playinfos[1])
		else:
			self["artist"].setText(playinfos)
			scArtist = ''
			scTitle = playinfos
		getPage(eightiesUrl).addCallback(self.getVid).addErrback(self.dataError)

	def getVid(self, data):
		stream_url = re.findall('(/vid/.*?.flv)', data, re.S)
		if stream_url:
			stream_url = "%s%s" % (self.baseurl, stream_url[0])
			sref = eServiceReference(0x1001, 0, stream_url)
			self.session.nav.playService(sref)
			self.playing = True

	def doEofInternal(self, playing):
		self['liste'].down()
		self.keyOK()

	def seekFwd(self):
		self['liste'].pageDown()

	def seekBack(self):
		self['liste'].pageUp()

	def lockShow(self):
		pass

	def unlockShow(self):
		pass