# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

config.mediaportal.itunestrailersquality = ConfigText(default="720p", fixed_size=False)

if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/TMDb/plugin.pyo'):
	from Plugins.Extensions.TMDb.plugin import *
	TMDbPresent = True
elif fileExists('/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo'):
	TMDbPresent = False
	IMDbPresent = True
	from Plugins.Extensions.IMDb.plugin import *
else:
	IMDbPresent = False
	TMDbPresent = False

class itunestrailersGenreScreen(MPScreen):

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
			"left" : self.keyLeft,
			"yellow": self.keyQuality
		}, -1)

		self.quality = config.mediaportal.itunestrailersquality.value

		self['title'] = Label("iTunes Movie Trailers")
		self['ContentTitle'] = Label(_("Selection:"))
		self['F3'] = Label(self.quality)

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste = []
		self.genreliste.append(("Top Trailers", "https://trailers.apple.com/appletv/us/index.xml"))
		self.genreliste.append(("Calendar", "https://trailers.apple.com/appletv/us/calendar.xml"))
		self.genreliste.append(("Genres", "https://trailers.apple.com/appletv/us/browse.xml"))
		self.genreliste.append(("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = 'https://trailers.apple.com/trailers/global/atv/search.php?q=%s' % self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(itunestrailersFilmScreen, Link, Name, "Search")

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		if Name == "Genres" or Name == "Top Trailers" or Name == "Calendar":
			self.session.open(itunestrailersSubGenreScreen, Link, Name)

	def keyQuality(self):
		if self.keyLocked:
			return
		self.keyLocked = True
		if self.quality == "720p":
			self.quality = "1080p"
			config.mediaportal.itunestrailersquality.value = "1080p"
		elif self.quality == "1080p":
			self.quality = "480p"
			config.mediaportal.itunestrailersquality.value = "480p"
		elif self.quality == "480p":
			self.quality = "720p"
			config.mediaportal.itunestrailersquality.value = "720p"

		config.mediaportal.itunestrailersquality.save()
		configfile.save()
		self['F3'].setText(self.quality)
		self.layoutFinished()

class itunestrailersSubGenreScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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

		self['title'] = Label("iTunes Movie Trailers")
		self['ContentTitle'] = Label(self.Name+":")
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		getPage(self.Link).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if self.Name == "Genres":
			raw = re.findall('<label>(.*?)</label>.*?<link>(.*?)</link>', data, re.S)
			if raw:
				for (Title, Url) in raw:
					self.genreliste.append((Title, Url, "Genres"))
		else:
			raw = re.findall('<collectionDivider.*?accessibilityLabel="(.*?)">', data, re.S)
			if raw:
				for Label in raw:
					self.genreliste.append((Label, self.Link, self.Name))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Cat = self['liste'].getCurrent()[0][2]
		self.session.open(itunestrailersFilmScreen, Link, Name, Cat)

class itunestrailersFilmScreen(MPScreen):

	def __init__(self, session, Link, Name, Cat):
		self.Link = Link
		self.Name = Name
		self.Cat = Cat
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp,
			"info" :  self.keyTMDbInfo
		}, -1)

		self['title'] = Label("iTunes Movie Trailers")
		self['ContentTitle'] = Label(_("Movie Selection"))
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = self.Link
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if self.Cat == "Search":
			Movies = re.findall('MenuItem.*?loadURL\(\'(.*?)\'\).*?<label>(.*?)</label>.*?<image>(.*?)</image>', data, re.S|re.I)
		elif self.Cat == "Genres":
			Movies = re.findall('loadTrailerDetailPage\(\'(.*?)\'\);.*?<title>(.*?)</title>.*?<image>(.*?)</image>', data, re.S)
		elif self.Cat == "Top Trailers" or self.Cat == "Calendar":
			parse = re.search('<title>%s</title>(.*?)</shelf>' % self.Name, data, re.S)
			Movies = re.findall('loadTrailerDetailPage\(\'(.*?)\'\);.*?<title>(.*?)</title>.*?<image>(.*?)</image>', parse.group(1), re.S)
		if Movies:
			for (Url, Title, Image) in Movies:
				self.filmliste.append((decodeHtml(Title).replace('&amp;','&'), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(coverUrl)
		getPage(url).addCallback(self.getDescription).addErrback(self.dataError)

	def getDescription(self, data):
		description = re.search('<summary>(.*?)</summary>', data, re.S)
		if description:
			self['handlung'].setText(decodeHtml(description.group(1)))

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Cover = self['liste'].getCurrent()[0][2]
		self.session.open(itunestrailersSubFilmScreen, Link, Title, Cover)

	def keyTMDbInfo(self):
		if not self.keyLocked and TMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(TMDbMain, title)
		elif not self.keyLocked and IMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(IMDB, title)

class itunestrailersSubFilmScreen(MPScreen):

	def __init__(self, session, Link, Name, Cover):
		self.Link = Link
		self.Name = Name
		self.Cover = Cover
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label("iTunes Movie Trailers")
		self['ContentTitle'] = Label(self.Name)
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = self.Link
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if re.search('id="more"', data):
			url = re.search('id="more".onSelect="atv.loadURL\(\'(.*?)\'\)', data, re.S|re.I)
			getPage(url.group(1)).addCallback(self.loadData2).addErrback(self.dataError)
		else:
			url = re.search('id="play".onSelect="atv.loadURL\(\'(.*?)\'\)', data, re.S|re.I)
			self.filmliste.append(("Trailer", url.group(1), self.Cover))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.showInfos()

	def loadData2(self, data):
		Movies = re.findall('MenuItem.*?loadURL\(\'(.*?)\'\).*?<label>(.*?)</label>.*?<image>(.*?)</image>', data, re.S|re.I)
		if Movies:
			for (Url, Title, Image) in Movies:
				if Title != "Related":
					self.filmliste.append((decodeHtml(Title).replace('&amp;','&'), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(coverUrl)
		getPage(url).addCallback(self.getDescription).addErrback(self.dataError)

	def getDescription(self, data):
		description = re.search('<description>(.*?)</description>', data, re.S)
		if description:
			self['handlung'].setText(decodeHtml(description.group(1)))

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getVideo).addErrback(self.dataError)

	def getVideo(self, data):
		video = re.search('<mediaURL>(.*?)</mediaURL>', data, re.S)
		Link = video.group(1)
		if config.mediaportal.itunestrailersquality.value == "720p":
			Link = Link.replace('a720p.m4v','h720p.mov')
		elif config.mediaportal.itunestrailersquality.value == "1080p":
			Link = Link.replace('a720p.m4v','h1080p.mov')
			Link = Link.replace('h720p.mov','h1080p.mov')
		elif config.mediaportal.itunestrailersquality.value == "480p":
			Link = Link.replace('a720p.m4v','h480p.mov')
			Link = Link.replace('h720p.mov','h480p.mov')
		Title = self['liste'].getCurrent()[0][0]
		mp_globals.player_agent = "QuickTime/7.6.2 (qtver=7.6.2;os=Windows NT 5.1Service Pack 3)"
		self.session.open(SimplePlayer, [(self.Name + " - " + Title, Link, self.Cover)], showPlaylist=False, ltype='itunestrailers', cover=True)