# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

class kxMain(MPScreen):

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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		lt = localtime()
		self.currentdatum = strftime("%d.%m.%Y", lt)
		self.neueste_kino = "Frisches aus dem Kino vom %s" % self.currentdatum
		self.neueste_online = "Neue Filme online vom %s" % self.currentdatum
		self.keyLocked = True
		date = datetime.datetime.now().strftime('%Y-%m-%d')
		self.streamList.append((self.neueste_kino, "http://kinox.nu"))
		self.streamList.append((self.neueste_online, "http://kinox.nu"))
		self.streamList.append(("Kinofilme", "http://kinox.to/Cine-Films.html"))
		self.streamList.append(("Suche", "dump"))
		self.streamList.append(("Filme A-Z", "dump"))
		self.streamList.append(("Serien A-Z","dump"))
		self.streamList.append(("Neueste Serien", "http://kinox.to/Latest-Series.html"))
		self.streamList.append(("Dokumentationen A-Z","dump"))
		self.streamList.append(("Neueste Dokumentationen", "http://kinox.to/Latest-Documentations.html"))
		self.streamList.append(("Watchlist","dump"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if auswahl == "Kinofilme":
			self.session.open(kxKino, url)
		elif auswahl == self.neueste_kino:
			self.session.open(kxNeuesteKino, url)
		elif auswahl == self.neueste_online:
			self.session.open(kxNeuesteOnline, url)
		elif auswahl == "Suche":
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True, auto_text_init=True)
		elif auswahl == "Filme A-Z":
			self.session.open(kxABC, url, auswahl)
		elif auswahl == "Serien A-Z":
			self.session.open(kxABC, url, auswahl)
		elif auswahl == "Neueste Serien":
			self.session.open(kxNeuesteSerien, url, auswahl)
		elif auswahl == "Dokumentationen A-Z":
			self.session.open(kxABC, url, auswahl)
		elif auswahl == "Neueste Dokumentationen":
			self.session.open(kxNeuesteSerien, url, auswahl)
		elif auswahl == "Watchlist":
			self.session.open(kxWatchlist)

	def searchCallback(self, callbackStr):
		if callbackStr is not None:
			self.searchStr = callbackStr
			url = "http://kinox.to/Search.html?q="
			self.searchData = self.searchStr
			self.session.open(kxSucheAlleFilmeListeScreen, url, self.searchData)

class kxKino(MPScreen, ThumbsHelper):

	def __init__(self, session, kxGotLink):
		self.kxGotLink = kxGotLink
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
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label("KinoFilme")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.kxGotLink).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		kxMovies = re.findall('<div class="Opt leftOpt Headlne"><a title=".*?" href="(.*?)"><h1>(.*?)</h1></a></div>.*?<div class="Thumb"><img style="width: 70px; height: 100px" src="(.*?)"/></div>.*?<div class="Descriptor">(.*?)</div>.*?src="/gr/sys/lng/(.*?).png"', data, re.S)
		if kxMovies:
			for (kxUrl,kxTitle,kxImage,kxHandlung,kxLang) in kxMovies:
				kxUrl = "http://kinox.to" + kxUrl
				kxImage = "http://kinox.to"+ kxImage
				self.streamList.append((decodeHtml(kxTitle),kxUrl,kxImage,kxLang,kxHandlung))
			self.ml.setList(map(self.kinoxlistleftflagged, self.streamList))
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		coverUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][4]
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(kxStreams, auswahl, stream_name, cover)

class kxNeuesteKino(MPScreen, ThumbsHelper):

	def __init__(self, session, kxGotLink):
		self.kxGotLink = kxGotLink
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
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Kinox.to")
		lt = localtime()
		self.currentdatum = strftime("%d.%m.%Y", lt)
		self['ContentTitle'] = Label("Frisches aus dem Kino vom %s" % self.currentdatum)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.kxGotLink).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw_m = re.findall('<div class="Opt leftOpt Headlne"><h1>Frisches aus dem Kino(.*?)</table>', data, re.S)
		if raw_m:
			movies = re.findall('td class="Title img_preview" rel="(.*?)"><a href="(/Stream/.*?)" title=".*?" class="OverlayLabel">(.*?)</a></td>', raw_m[0], re.S)
			if movies:
				for (kxImage,kxUrl,kxTitle) in movies:
					kxUrl = "http://kinox.to" + kxUrl
					kxImage = "http://kinox.to"+ kxImage
					self.streamList.append((decodeHtml(kxTitle),kxUrl,kxImage))
				self.ml.setList(map(self._defaultlistleft, self.streamList))
				self.keyLocked = False
				self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
				self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(image)

	def getDetails(self, data):
		details = re.findall('<div class="Grahpics">.*?<img src="(.*?)".*?<div class="Descriptore">(.*?)</div>', data, re.S)
		if details:
			for (image, handlung) in details:
				self['handlung'].setText(decodeHtml(handlung))
				CoverHelper(self['stationIcon']).getCover(image)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(kxStreams, auswahl, stream_name, cover)

class kxNeuesteOnline(MPScreen, ThumbsHelper):

	def __init__(self, session, kxGotLink):
		self.kxGotLink = kxGotLink
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
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Kinox.to")
		lt = localtime()
		self.currentdatum = strftime("%d.%m.%Y", lt)
		self['ContentTitle'] = Label("Neue Filme online vom %s" % self.currentdatum)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.kxGotLink).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		neueste = re.findall('div class="Opt leftOpt Headlne"><h1>Neue Filme online vom(.*?)</table>', data, re.S)
		if neueste:
			movies = re.findall('td class="Title img_preview" rel="(.*?)"><a href="(/Stream/.*?)" title=".*?" class="OverlayLabel">(.*?)</a></td>', neueste[0], re.S)
			if movies:
				for (kxImage,kxUrl,kxTitle) in movies:
					kxUrl = "http://kinox.to" + kxUrl
					kxImage = "http://kinox.to"+ kxImage
					self.streamList.append((decodeHtml(kxTitle),kxUrl,kxImage))
					self.ml.setList(map(self._defaultlistleft, self.streamList))
				self.keyLocked = False
				self.th_ThumbsQuery(self.streamList, 0, 1, None, None, '<div class="Grahpics">.*?<img src="(.*?)"', 1, 1)
				self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(image)
		getPage(url).addCallback(self.getDetails).addErrback(self.dataError)

	def getDetails(self, data):
		details = re.findall('<div class="Grahpics">.*?<img src="(.*?)".*?<div class="Descriptore">(.*?)</div>', data, re.S)
		if details:
			for (image, handlung) in details:
				image = "http://kinox.to"+ image
				self['handlung'].setText(decodeHtml(handlung))
				#CoverHelper(self['coverArt']).getCover(image)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		self.session.open(kxStreams, auswahl, stream_name, 'no_cover')

class kxABC(MPScreen):

	def __init__(self, session, kxGotLink, name):
		self.kxGotLink = kxGotLink
		self.Name = name
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label(self.Name)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		abc = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","0","1","2","3","4","5","6","7","8","9"]
		for letter in abc:
			self.streamList.append((letter, ''))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		if self.Name == "Serien A-Z":
			self.session.open(kxSerienABCpage, auswahl)
		elif self.Name == "Dokumentationen A-Z":
			self.session.open(kxDokuABCpage, auswahl)
		else:
			self.session.open(kxABCpage, auswahl)

class kxABCpage(MPScreen, ThumbsHelper):

	def __init__(self, session, letter):
		self.letter = letter
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
			"0": self.closeAll,
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

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label("Movies %s" % self.letter)
		self['F2'] = Label(_("Add to Watchlist"))

		self['Page'] = Label(_("Page:"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = "http://kinox.to/aGET/List/Page="+str(self.page)+"&Per_Page=25&url=%2FaGET%2FList%2F&dir=desc&sort=title&per_page=25&ListMode=cover&additional=%7B%22fType%22%3A%22movie%22%2C%22fLetter%22%3A%22"+self.letter+"%22%7D&iDisplayStart=0&iDisplayLength=25"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		data = data.replace('\\/','/').replace('\\"','"')
		print data
		kxMovies = re.findall('title="(.*?)"\shref="(.*?)".*?<img.*?src="(.*?)".*?<div\sclass="Descriptor">(.*?)</div>.*?src=".*?lng.*?/(.*?).pn.*?"\salt="language">', data, re.S)
		if kxMovies:
			for (kxTitle,kxUrl,kxImage,kxHandlung,kxLang) in kxMovies:
				kxUrl = "http://kinox.to" + kxUrl
				kxImage = "http://kinox.to"+ kxImage
				kxTitle = kxTitle
				self.streamList.append((decodeHtml(kxTitle),kxUrl,kxImage,kxLang,kxHandlung))
				self.ml.setList(map(self.kinoxlistleftflagged, self.streamList))
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page)
			self.showInfos()
		else:
			self['page'].setText("END")

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		self['page'].setText(str(self.page))
		coverUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][4]
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(kxStreams, auswahl, stream_name, cover)

class kxNeuesteSerien(MPScreen, ThumbsHelper):

	def __init__(self, session, kxGotLink, name):
		self.kxGotLink = kxGotLink
		self.Name = name
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"green" : self.keyAdd
		}, -1)

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label(self.Name)
		self['name'] = Label(_("Selection:"))
		self['F2'] = Label(_("Add to Watchlist"))

		self.keckse = {}
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.kxGotLink, cookies=self.keckse).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		kxMovies = re.findall('<td class="Icon"><img width="16" height="11" src="/gr/sys/lng/(.*?).png" alt="language"></td>.*?<td class="Title"><a href="(.*?)" onclick="return false;">(.*?)</a>', data, re.S)
		if kxMovies:
			for (kxLang,kxUrl,kxTitle) in kxMovies:
				kxUrl = "http://kinox.to" + kxUrl
				self.streamList.append((decodeHtml(kxTitle),kxUrl,'',kxLang))
				self.ml.setList(map(self.kinoxlistleftflagged, self.streamList))
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, None, 2, '<div class="Grahpics">.*?<img src="(.*?)"', 1, 1)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		if self.Name == "Neueste Serien":
			self.session.open(kxEpisoden, auswahl, stream_name)
		elif self.Name == "Neueste Dokumentationen":
			self.session.open(kxStreams, auswahl, stream_name, 'no_cover')

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		muTitle = self['liste'].getCurrent()[0][0]
		muID = self['liste'].getCurrent()[0][1]
		muLang = self['liste'].getCurrent()[0][3]

		if not fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watchlist"):
			open(config.mediaportal.watchlistpath.value+"mp_kx_watchlist","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watchlist"):
			writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_kx_watchlist","a")
			writePlaylist.write('"%s" "%s" "%s" "0"\n' % (muTitle, muID, muLang))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)

class kxDokuABCpage(MPScreen, ThumbsHelper):

	def __init__(self, session, letter):
		self.letter = letter
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
			"0": self.closeAll,
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

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label("Dokumetation %s" % self.letter)

		self['Page'] = Label(_("Page:"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self.filmtype = "documentation"
		url = "http://kinox.to/aGET/List/Page="+str(self.page)+"&Per_Page=25&url=%2FaGET%2FList%2F&dir=desc&sort=title&per_page=25&ListMode=cover&additional=%7B%22fType%22%3A%22"+self.filmtype+"%22%2C%22fLetter%22%3A%22"+self.letter+"%22%7D&iDisplayStart=0&iDisplayLength=25"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		data = data.replace('\\/','/').replace('\\"','"')
		print data
		kxMovies = re.findall('title="(.*?)"\shref="(.*?)".*?<img.*?src="(.*?)".*?<div\sclass="Descriptor">(.*?)</div>.*?src=".*?lng.*?/(.*?).pn.*?"\salt="language">', data, re.S)
		if kxMovies:
			for (kxTitle,kxUrl,kxImage,kxHandlung,kxLang) in kxMovies:
				kxUrl = "http://kinox.to" + kxUrl
				kxImage = "http://kinox.to"+ kxImage
				kxTitle = kxTitle
				self.streamList.append((decodeHtml(kxTitle),kxUrl,kxImage,kxLang,kxHandlung))
				self.ml.setList(map(self.kinoxlistleftflagged, self.streamList))
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page)
			self.showInfos()
		else:
			self['page'].setText("END")

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		self['page'].setText(str(self.page))
		coverUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][4]
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(kxStreams, auswahl, stream_name, cover)

class kxSerienABCpage(MPScreen, ThumbsHelper):

	def __init__(self, session, letter):
		self.letter = letter
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
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyAdd
		}, -1)

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label("Serien %s" % self.letter)
		self['F2'] = Label(_("Add to Watchlist"))

		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = "http://kinox.to/aGET/List/?ListMode=cover&Page="+str(self.page)+"&Per_Page=25&additional=%7B%22fType%22%3A%22series%22%2C%22fLetter%22%3A%22"+self.letter+"%22%7D&dir=desc&iDisplayLength=25&iDisplayStart=0&per_page=25&sort=title&url=%2FaGET%2FList%2F"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		data = data.replace('\\/','/').replace('\\"','"')
		print data
		kxMovies = re.findall('title="(.*?)"\shref="(.*?)".*?<img.*?src="(.*?)".*?<div\sclass="Descriptor">(.*?)</div>.*?src=".*?lng.*?/(.*?).pn.*?"\salt="language">', data, re.S)
		if kxMovies:
			for (kxTitle,kxUrl,kxImage,kxHandlung,kxLang) in kxMovies:
				kxUrl = "http://kinox.to" + kxUrl
				kxImage = "http://kinox.to"+ kxImage
				kxTitle = kxTitle
				self.streamList.append((decodeHtml(kxTitle),kxUrl,kxImage,kxLang,kxHandlung))
				self.ml.setList(map(self.kinoxlistleftflagged, self.streamList))
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page)
			self.showInfos()
		else:
			self['page'].setText("END")

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		self['page'].setText(str(self.page))
		coverUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][4]
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		self.session.open(kxEpisoden, auswahl, stream_name)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		muTitle = self['liste'].getCurrent()[0][0]
		muID = self['liste'].getCurrent()[0][1]
		muLang = self['liste'].getCurrent()[0][3]
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watchlist"):
			open(config.mediaportal.watchlistpath.value+"mp_kx_watchlist","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watchlist"):
			writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_kx_watchlist","a")
			writePlaylist.write('"%s" "%s" "%s" "0"\n' % (muTitle, muID, muLang))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)

class kxEpisoden(MPScreen):

	def __init__(self, session, url, stream_name):
		self.url = url
		self.stream_name = stream_name
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label(_("Episode Selection"))
		self['name'] = Label(self.stream_name)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.watched_liste = []
		self.mark_last_watched = []
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_kx_watched","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watched"):
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_kx_watched")
			if not leer == 0:
				self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_kx_watched" , "r")
				for lines in sorted(self.updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						self.watched_liste.append("%s" % (line[0]))
				self.updates_read.close()
		MirrorByEpisode = "http://kinox.to/aGET/MirrorByEpisode/"
		if re.match('.*rel="\?Addr=', data, re.S):
			id = re.findall('rel="(\?Addr=.*?)"', data, re.S)
			if id:
				staffeln2 = re.findall('<option value="(.*\d+)" rel="(.*\d+)"', data, re.M)
				if staffeln2:
					for each in staffeln2:
						(staffel, epsall) = each
						eps = re.findall('(\d+)', epsall, re.S)
						for episode in eps:
							url_to_streams = "%s%s&Season=%s&Episode=%s" % (MirrorByEpisode, id[0], staffel, episode)
							if int(staffel) < 10:
								staffel3 = "S0"+str(staffel)
							else:
								staffel3 = "S"+str(staffel)
							if int(episode) < 10:
								episode3 = "E0"+str(episode)
							else:
								episode3 = "E"+str(episode)
							self.staffel_episode = "%s%s" % (staffel3, episode3)
							if self.staffel_episode:
								streamname = "%s - %s" % (self.stream_name, self.staffel_episode)
								#check = ("%s %s" % (self.stream_name, streamname))
								if streamname in self.watched_liste:
									self.streamList.append((streamname,url_to_streams,True))
									self.mark_last_watched.append(streamname)
								else:
									self.streamList.append((streamname,url_to_streams,False))
						self.ml.setList(map(self._defaultlistleftmarked, self.streamList))
						if len(self.mark_last_watched) != 0:
							counting_watched = 0
							for (name,url,watched) in self.streamList:
								counting_watched += 1
								if self.mark_last_watched[-1] == name:
									counting_watched = int(counting_watched) - 1
									print "[kinox] last watched episode: %s" % counting_watched
									break
							self["liste"].moveToIndex(int(counting_watched))
							self.keyLocked = False
						else:
							if len(self.streamList) != 0:
								jump_last = len(self.streamList) -1
							else:
								jump_last = 0
							print "[kinox] last episode: %s" % jump_last
							self["liste"].moveToIndex(int(jump_last))
							self.keyLocked = False
		details = re.findall('<div class="Grahpics">.*?<img src="(.*?)".*?<div class="Descriptore">(.*?)</div>', data, re.S)
		if details:
			for (image, handlung) in details:
				image = "http://kinox.to"+ image
				self['handlung'].setText(decodeHtml(handlung))
				CoverHelper(self['coverArt']).getCover(image)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		episode = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		streamname = "%s" % episode
		self.session.open(kxStreams, auswahl, streamname, 'no_cover')

class kxWatchlist(MPScreen):

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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"red" : self.keyDel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("kinox.to")
		self['ContentTitle'] = Label("Watchlist")
		self['F1'] = Label(_("Delete"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPlaylist)

	def loadPlaylist(self):
		self.streamList = []
		if fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watchlist"):
			readStations = open(config.mediaportal.watchlistpath.value+"mp_kx_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(stationName, stationLink, stationLang, stationTotaleps) = data[0]
					self.streamList.append((stationName, stationLink, '', stationLang))
			self.streamList.sort()
			self.ml.setList(map(self.kinoxlistleftflagged, self.streamList))
			readStations.close()
			self.keyLocked = False
			self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		self.session.open(kxEpisoden, auswahl, stream_name)

	def keyDel(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		selectedName = self['liste'].getCurrent()[0][0]
		writeTmp = open(config.mediaportal.watchlistpath.value+"mp_kx_watchlist.tmp","w")
		if fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watchlist"):
			readStations = open(config.mediaportal.watchlistpath.value+"mp_kx_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(stationName, stationLink, stationLang, stationTotaleps) = data[0]
					if stationName != selectedName:
						writeTmp.write('"%s" "%s" "%s" "%s"\n' % (stationName, stationLink, stationLang, stationTotaleps))
			readStations.close()
			writeTmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_kx_watchlist.tmp", config.mediaportal.watchlistpath.value+"mp_kx_watchlist")
			self.loadPlaylist()

class kxStreams(MPScreen):

	def __init__(self, session, kxGotLink, stream_name, cover='no_cover'):
		self.kxGotLink = kxGotLink
		self.stream_name = stream_name
		self.cover = cover
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.stream_name)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.kxGotLink).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		hosterdump = re.findall('<li id="Hoster(.*?)/li>', data, re.S)
		if hosterdump:
			self.streamList = []
			self.streamList.append(("Hoster", "nix", "Mirror", "Hits", "Date"))
			for each in hosterdump:
				if re.search('Mirror', each, re.I):
					hosters = re.findall('rel="(.*?)".*?<div class="Named">(.*?)</div>.*?<div class="Data"><b>Mirror</b>\:.(.*?)<br.*?><b>Vom</b>\:.(.*\d+)</div>',each, re.S|re.I)
					if hosters:
						(get_stream_url, hostername, mirror, date)= hosters[0]
						mirrors = re.findall('[0-9]/([0-9])', mirror)
						if mirrors:
							print "total", mirrors[0]
							get_stream_url_m = ''
							for i in range(1,int(mirrors[0])+1):
								if re.search('Season=', get_stream_url, re.S):
									details = re.findall('(.*?)&amp;Hoster=(.*?)&amp;Mirror=(.*?)&amp;Season=(.*?)&amp;Episode=(\d+)', get_stream_url, re.S)
									if details:
										(dname, dhoster, dmirror, dseason, depisode) = details[0]
										get_stream_url_m = "http://kinox.to/aGET/Mirror/%s&Hoster=%s&Mirror=%s&Season=%s&Episode=%s" %  (dname, dhoster, str(i), dseason, depisode)
									else:
										details = re.findall('(.*?)&amp;Hoster=(.*?)&amp;Season=(.*?)&amp;Episode=(\d+)', get_stream_url, re.S)
										(dname, dhoster, dseason, depisode) = details[0]
										get_stream_url_m = "http://kinox.to/aGET/Mirror/%s&Hoster=%s&Season=%s&Episode=%s" %  (dname, dhoster, dseason, depisode)
								else:
									details = re.findall('(.*?)&amp;Hoster=(.*?)&amp;Mirror=(\d+)', get_stream_url, re.S)
									if details:
										(dname, dhoster, dmirror) = details[0]
										get_stream_url_m = "http://kinox.to/aGET/Mirror/%s&Hoster=%s&Mirror=%s" %  (dname, dhoster, str(i))
									else:
										details = re.findall('(.*?)&amp;Hoster=(\d+)', get_stream_url, re.S)
										if details:
											(dname, dhoster) = details[0]
											get_stream_url_m = "http://kinox.to/aGET/Mirror/%s&Hoster=%s" %  (dname, dhoster)
								if isSupportedHoster(hostername, True):
									self.streamList.append((hostername, get_stream_url_m, str(i)+"/"+mirrors[0], '', date))
				else:
					hosters = re.findall('rel="(.*?)".*?<div class="Named">(.*?)</div>.*?<div class="Data"><b>Vom</b>\:.(.*\d+)</div>',each, re.S)
					if hosters:
						(get_stream_url, hostername, date)= hosters[0]
						get_stream_url = "http://kinox.to/aGET/Mirror/%s" % get_stream_url.replace('&amp;','&')
						if isSupportedHoster(hostername, True):
							self.streamList.append((hostername, get_stream_url, "1", '', date))
			if len(self.streamList) == 0:
				self.streamList.append((_('No supported streams found!'), None, None, None, None))
			self.ml.setList(map(self.kxStreamListEntry, self.streamList))
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.parseStream, url).addErrback(self.dataError)

	def parseStream(self, data, url):
		if re.match('.*?Part', data, re.S):
			print "more parts.."
			urls = []
			urls.append(("Part 1", url+"&Part=1"))
			urls.append(("Part 2", url+"&Part=2"))
			self.session.open(kxParts, urls, self.stream_name)
		else:
			print "one parts only.."
			stream = None
			extern_stream_url = re.findall('<a href=.".*?(http.*?)"', data)
			if extern_stream_url:
				stream = extern_stream_url[0].replace('\\','')
				if stream:
					get_stream_link(self.session).check_link(stream, self.playfile)
			if not stream:
				self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def playfile(self, stream_url):
		if stream_url != None:
			if not fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watched"):
				open(config.mediaportal.watchlistpath.value+"mp_kx_watched","w").close()

			self.update_liste = []
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_kx_watched")
			if not leer == 0:
				self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_kx_watched" , "r")
				for lines in sorted(self.updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						self.update_liste.append("%s" % (line[0]))
				self.updates_read.close()

				updates_read2 = open(config.mediaportal.watchlistpath.value+"mp_kx_watched" , "a")
				check = ("%s" % self.stream_name)
				if not check in self.update_liste:
					print "[kinox] update add: %s" % (self.stream_name)
					updates_read2.write('"%s"\n' % (self.stream_name))
					updates_read2.close()
				else:
					print "[kinox] dupe %s" % (self.stream_name)
			else:
				updates_read3 = open(config.mediaportal.watchlistpath.value+"mp_kx_watched" , "a")
				print "[kinox] update add: %s" % (self.stream_name)
				updates_read3.write('"%s"\n' % (self.stream_name))
				updates_read3.close()

			if re.search('no_cover', self.cover):
				cover = None
			else:
				cover = self.cover
			self.session.open(SimplePlayer, [(self.stream_name, stream_url, cover)], showPlaylist=False, ltype='kinox.to', cover=True)

class kxParts(MPScreen):

	def __init__(self, session, parts, stream_name):
		self.parts = parts
		self.stream_name = stream_name
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label(_("Parts Selection"))
		self['name'] = Label(self.stream_name)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		for (partName, partUrl) in self.parts:
			self.streamList.append((partName, partUrl))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		extern_stream_url = re.findall('<a href=."(.*?)"', data, re.S)
		stream = None
		if extern_stream_url:
			stream = extern_stream_url[0].replace('\\','')
			if stream:
				get_stream_link(self.session).check_link(stream, self.playfile)
		if not stream:
			self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def playfile(self, stream_url):
		if stream_url != None:
			part = self['liste'].getCurrent()[0][0]
			streamname = "%s - %s" % (self.stream_name ,part)
			self.session.open(SimplePlayer, [(streamname, stream_url)], showPlaylist=False, ltype='kinox.to', cover=False)

class kxSucheAlleFilmeListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, searchURL, searchData):
		self.kxGotLink = searchURL + searchData
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
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyAdd
		}, -1)

		self['title'] = Label("Kinox.to")
		self['ContentTitle'] = Label("Suche nach Filmen")
		self['F2'] = Label(_("Add to Watchlist"))

		self.keckse = {}
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.kxGotLink, cookies=self.keckse).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		movies = re.findall('<td\sclass="Icon"><img\swidth="16"\sheight="11"\ssrc="/gr/sys/lng/(.*?).png"\salt="language"></td>.*?title="(.*?)".*?<td\sclass="Title">(.*?)>(.*?)</a>', data, re.S)
		if movies:
			for (kxLang,kxArt,kxUrl,kxTitle) in movies:
				kxUrl = re.search('href="(.*?)"', kxUrl, re.S).group(1)
				if kxUrl != '':
					kxUrl = "http://kinox.to" + kxUrl
					if kxArt == 'documentation':
						kxArt = 'doku'
					self.streamList.append((decodeHtml(kxTitle),kxUrl, kxLang, kxArt.capitalize()))
			self.ml.setList(map(self.kxListSearchEntry, self.streamList))
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, None, 2, '<div class="Grahpics">.*?<img src="(.*?)"', 1, 1)
			self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.getDetails).addErrback(self.dataError)

	def getDetails(self, data):
		details = re.findall('<div class="Grahpics">.*?<img src="(.*?)".*?<div class="Descriptore">(.*?)</div>', data, re.S)
		if details:
			for (image, handlung) in details:
				image = "http://kinox.to"+ image
				self['handlung'].setText(decodeHtml(handlung))
				CoverHelper(self['coverArt']).getCover(image)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		auswahl = self['liste'].getCurrent()[0][1]
		art = self['liste'].getCurrent()[0][3]
		if art == 'Series':
			self.session.open(kxEpisoden, auswahl, stream_name)
		else:
			self.session.open(kxStreams, auswahl, stream_name, 'no_cover')

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		art = self['liste'].getCurrent()[0][3]
		if art == 'Series':
			if not fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watchlist"):
				open(config.mediaportal.watchlistpath.value+"mp_kx_watchlist","w").close()
			if fileExists(config.mediaportal.watchlistpath.value+"mp_kx_watchlist"):
				writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_kx_watchlist","a")
				writePlaylist.write('"%s" "%s" "%s" "0"\n' % (stream_name, url, "1")) # default German language
				writePlaylist.close()
				message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)