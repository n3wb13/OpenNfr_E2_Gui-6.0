from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

class kinokisteGenreScreen(MPScreen):

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
			"0": self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("KinoKiste")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.keyLocked = True
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Kinofilme", "http://kkiste.to/aktuelle-kinofilme/"))
		self.genreliste.append(("Serien", "http://kkiste.to/serien/"))
		self.genreliste.append(("Filme A-Z", "http://kkiste.to/film-index/"))
		self.genreliste.append(("Genres", "http://kkiste.to/genres/"))
		self.genreliste.append(("Suche", "http://kkiste.to/search/?q="))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		kkName = self['liste'].getCurrent()[0][0]
		kkUrl = self['liste'].getCurrent()[0][1]

		if kkName == "Kinofilme":
			self.session.open(kinokisteKinoScreen, kkName)
		elif kkName == "Serien":
			self.session.open(kinokisteKinoScreen, kkName)
		elif kkName == "Filme A-Z":
			self.session.open(kinokisteFilmlistenScreen)
		elif kkName == "Genres":
			self.session.open(kinokisteGenrelistenScreen)
		else:
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True, auto_text_init=True)

	def searchCallback(self, callbackStr):
		if callbackStr is not None:
			print callbackStr
			Name = callbackStr
			Link = "http://kkiste.to/search/?q=%s" % callbackStr.replace(' ','%20')
			self.session.open(kinokisteSearchScreen, Link, Name)

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)

class kinokisteKinoScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, name):
		self.Name = name
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
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("KinoKiste")
		self['ContentTitle'] = Label(self.Name)

		self['Page'] = Label(_("Page:"))

		self.toShowThumb = False
		self.page = 1
		self.lastpage = 999
		self.filmeliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmeliste = []
		if self.Name == "Kinofilme":
			url = "http://kkiste.to/aktuelle-kinofilme/?page=%s" % str(self.page)
		elif self.Name == "Serien":
			url = "http://kkiste.to/serien/?page=%s" % str(self.page)
		getPage(url).addCallback(self.filmData).addErrback(self.dataError)

	def filmData(self, data):
		self.getLastPage(data, '<div class="paginated">(.*?)<div class="clear"></div>')
		kkDaten = re.findall('<a href="(.*?)" title="Jetzt (.*?) Stream ansehen" class="image">\n<img src="(.*?)"', data)
		if kkDaten:
			for (kkUrl,kkTitle,kkImage) in kkDaten:
				kkUrl = "http://www.kkiste.to%s" % kkUrl
				kkImage = kkImage.replace('_170_120','_145_215')
				self.filmeliste.append((kkTitle, kkUrl, kkImage))
			self.ml.setList(map(self._defaultlistleft, self.filmeliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmeliste,0,1,2,None,None,self.page)
			self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		kkTitle = self['liste'].getCurrent()[0][0]
		self['name'].setText(kkTitle)
		kkUrl = self['liste'].getCurrent()[0][1]
		kkImage = self['liste'].getCurrent()[0][2]
		self.kkImageUrl = "%s" % kkImage
		CoverHelper(self['coverArt']).getCover(self.kkImageUrl)
		getPage(kkUrl).addCallback(self.getDescription).addErrback(self.dataError)

	def getDescription(self, data):
		ddDescription = re.findall('<meta name="description" content="(.*?)KKiste.to.*?"', data, re.S)
		if ddDescription:
			self['handlung'].setText(decodeHtml(ddDescription[0]))
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		if self.keyLocked:
			return
		kkName = self['liste'].getCurrent()[0][0]
		kkUrl = self['liste'].getCurrent()[0][1]
		if self.Name == "Kinofilme":
			getPage(kkUrl).addCallback(self.getParts).addErrback(self.dataError)
		elif self.Name == "Serien":
			self.session.open(kinokisteEpisodeScreen, kkName, kkUrl, self.kkImageUrl)

	def getParts(self, data):
		kkName = self['liste'].getCurrent()[0][0]
		streams = re.findall('<a href="(http://www.ecostream.tv/stream/.*?)"', data, re.S)
		if streams:
			self.session.open(kinokistePartsScreen, streams, kkName, self.kkImageUrl)

	def keyShowThumb(self):
		if self.keyLocked:
			return
		self.th_keyShowThumb(self.filmeliste, 0, 1, 2, None, None, self.page)

class kinokisteEpisodeScreen(MPScreen):

	def __init__(self, session, serienName, serienUrl, serienPic):
		self.serienName = serienName
		self.serienUrl = serienUrl
		self.serienPic = serienPic
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
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("KinoKiste")
		self['ContentTitle'] = Label(_("Episode Selection"))
		self['name'] = Label(self.serienName)

		self.page = 1
		self.kekse = {}
		self.filmeliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmeliste = []
		CoverHelper(self['coverArt']).getCover(self.serienPic)
		print self.serienUrl
		getPage(self.serienUrl).addCallback(self.seasonData).addErrback(self.dataError)

	def seasonData(self, data):
		self.urlliste = []
		jsonLink = re.findall('<select class="seasonselect" data-movie="(.*?)"', data, re.S)
		if jsonLink:
			staffeln = re.findall('<option value="(.*\d)">Staffel.*?</option>', data)
			if staffeln:
				staffeln.reverse()
				for staffel in staffeln:
					url = "http://kkiste.to/xhr/movies/episodes/%s" % jsonLink[0]
					self.urlliste.append((url, staffel))

		self.count = len(self.urlliste)
		self.counting = 0
		if len(self.urlliste) != 0:
			self.filmeliste = []
			ds = defer.DeferredSemaphore(tokens=1)
			downloads = [ds.run(self.download,url,staffel).addCallback(self.showEpisodes).addErrback(self.dataError) for url,staffel in self.urlliste]
			finished = defer.DeferredList(downloads).addErrback(self.dataError)

	def download(self, url, staffel):
		self.counting += 1
		post = {'season': staffel}
		return getPage(url, method='POST', postdata=urlencode(post), headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'})

	def showEpisodes(self, data):
		eps = re.findall('link":"(.*?)","part":"(.*?)"', data, re.S)
		if eps:
			for link, ep in eps:
				link = "http://www.ecostream.tv/stream/%s.html" % (link)
				zahl = re.findall('Season (.*\d), Episode (.*\d)', ep)
				if zahl:
					(eins, zwei) = zahl[0]
					self.filmeliste.append((ep, link, eins+zwei))

		if self.counting == self.count:
			self.filmeliste.sort(key=lambda x: int(x[2]))
			self.ml.setList(map(self._defaultlistleft, self.filmeliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		kkName = self['liste'].getCurrent()[0][0]
		self.kkUrl = self['liste'].getCurrent()[0][1]
		self.serienName2 = "%s - %s" % (self.serienName, kkName)
		print kkName, self.kkUrl
		get_stream_link(self.session).check_link(self.kkUrl, self.playfile)

	def playfile(self, stream_url):
		if stream_url != None:
			self.session.open(SimplePlayer, [(self.serienName2, stream_url, self.serienPic)], showPlaylist=False, ltype='kinokiste', cover=True)

class kinokistePartsScreen(MPScreen):

	def __init__(self, session, parts, stream_name, cover):
		self.parts = parts
		self.stream_name = stream_name
		self.cover = cover
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
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("KinoKiste")
		self['ContentTitle'] = Label("Parts Auswahl")
		self['name'] = Label(self.stream_name)

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = False
		self.kekse = {}

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		CoverHelper(self['coverArt']).getCover(self.cover)
		print self.parts
		self.parts = list(set(self.parts)) # remove dupes
		self.parts.sort() # sortieren
		self.count_disks = 0
		for part in self.parts:
			self.count_disks += 1
			partsName = "PART %s" % self.count_disks
			print partsName, part
			self.genreliste.append((partsName, part))

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		if self.keyLocked:
			return
		self.kkLink = self['liste'].getCurrent()[0][1]
		print self.kkLink
		self.keyLocked = True
		get_stream_link(self.session).check_link(self.kkLink, self.playfile)

	def playfile(self, stream_url):
		if stream_url != None:
			self.session.open(SimplePlayer, [(self.stream_name, stream_url, self.cover)], showPlaylist=False, ltype='kinokiste', cover=True)

class kinokisteFilmlistenScreen(MPScreen):

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
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("KinoKiste")
		self['ContentTitle'] = Label("FilmListen Auswahl")
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		abc = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","0","1","2","3","4","5","6","7","8","9"]
		for letter in abc:
			kkLink = "http://kkiste.to/film-index/%s/" % letter
			self.genreliste.append((letter, kkLink))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(kinokisteFilmLetterScreen, Link, Name)

class kinokisteGenrelistenScreen(MPScreen):

	def __init__(self, session):
		self.kkLink = "http://kkiste.to/genres/"
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
			"0": self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("KinoKiste")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.keyLocked = True
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Abenteuer", "http://kkiste.to/abenteuer/"))
		self.genreliste.append(("Action", "http://kkiste.to/action/"))
		self.genreliste.append(("Animation", "http://kkiste.to/animation/"))
		self.genreliste.append(("Biographie", "http://kkiste.to/biographie/"))
		self.genreliste.append(("Bollywood", "http://kkiste.to/bollywood/"))
		self.genreliste.append(("Dokumentation", "http://kkiste.to/dokumentation/"))
		self.genreliste.append(("Drama", "http://kkiste.to/drama/"))
		self.genreliste.append(("Familie", "http://kkiste.to/familie/"))
		self.genreliste.append(("Fantasy", "http://kkiste.to/fantasy/"))
		self.genreliste.append(("Geschichte", "http://kkiste.to/geschichte/"))
		self.genreliste.append(("Horror", "http://kkiste.to/horror/"))
		self.genreliste.append(("Klassiker", "http://kkiste.to/klassiker/"))
		self.genreliste.append(("Komoedie", "http://kkiste.to/komoedie/"))
		self.genreliste.append(("Kriegsfilm", "http://kkiste.to/kriegsfilm/"))
		self.genreliste.append(("Krimi", "http://kkiste.to/krimi/"))
		self.genreliste.append(("Musik", "http://kkiste.to/musik/"))
		self.genreliste.append(("Mystery", "http://kkiste.to/mystery/"))
		self.genreliste.append(("Romantik", "http://kkiste.to/romantik/"))
		self.genreliste.append(("Sci-Fi", "http://kkiste.to/sci-fi/"))
		self.genreliste.append(("Sport", "http://kkiste.to/sport/"))
		self.genreliste.append(("Thriller", "http://kkiste.to/thriller/"))
		self.genreliste.append(("Western", "http://kkiste.to/western/"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		Name= self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(kinokisteInGenreScreen, Link, Name)

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)

class kinokisteInGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("KinoKiste")
		self['ContentTitle'] = Label(self.Name)

		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.toShowThumb = False
		self.page = 1
		self.lastpage = 999

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		kkLink = "%s?page=%s" % (self.Link, str(self.page))
		getPage(kkLink).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		self.getLastPage(data, '<div class="paginated">(.*?)<div class="clear"></div>')
		kkMovies = re.findall('<div class="mbox" >.*?<a href="(.*?)" title="Jetzt (.*?) Stream ansehen".*?<img src="(.*?)"', data, re.S)
		if kkMovies:
			for (kkUrl,kkTitle,kkImage) in kkMovies:
				kkUrl = "http://kkiste.to%s" % kkUrl
				kkImage = kkImage.replace('_170_120','_145_215')
				self.genreliste.append((kkTitle, kkUrl, kkImage))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.genreliste,0,1,2,None,None,self.page)
			self.showInfos()

	def getDescription(self, data):
		ddDescription = re.findall('<meta name="description" content="(.*?)KKiste.to.*?"', data, re.S)
		if ddDescription:
			self['handlung'].setText(decodeHtml(ddDescription[0]))
		else:
			self['handlung'].setText(_("No information found."))

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		kkTitle = self['liste'].getCurrent()[0][0]
		self['name'].setText(kkTitle)
		self.ImageUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(self.ImageUrl)
		Url = self['liste'].getCurrent()[0][1]
		getPage(Url).addCallback(self.getDescription).addErrback(self.dataError)

	def keyOK(self):
		if self.keyLocked:
			return
		kkLink = self['liste'].getCurrent()[0][1]
		print kkLink
		getPage(kkLink).addCallback(self.getParts).addErrback(self.dataError)

	def getParts(self, data):
		kkName = self['liste'].getCurrent()[0][0]
		streams = re.findall('<a href="(http://www.ecostream.tv/stream/.*?)"', data, re.S)
		print streams
		if streams:
			self.session.open(kinokistePartsScreen, streams, kkName, self.ImageUrl)

	def keyShowThumb(self):
		if self.keyLocked:
			return
		self.th_keyShowThumb(self.genreliste,0,1,2,None,None,self.page)

class kinokisteFilmLetterScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("KinoKiste")
		self['ContentTitle'] = Label("Letter: %s" % self.Name)

		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.toShowThumb = False
		self.page = 1
		self.lastpage = 999

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		kkLink = "%s?page=%s" % (self.Link, str(self.page))
		getPage(kkLink).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		self.getLastPage(data, '<div class="paginated">(.*?)<div class="clear"></div>')
		kkMovies = re.findall('<li class="mbox list".*?<a href="(.*?)" title="Jetzt (.*?) Stream ansehen".*?<p class="year">(.*?)</p>\n<p class="genre">(.*?)</p>', data, re.S)
		if kkMovies:
			for (kkUrl,kkTitle,kkYear,kkGenre) in kkMovies:
				kkUrl = "http://kkiste.to%s" % kkUrl
				self.genreliste.append((kkTitle, kkYear, kkGenre, kkUrl))
			self.ml.setList(map(self.kinokisteFilmLetterListEntry, self.genreliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.genreliste,0,3,None,None,'<img src="(.*?)".*?alt=".*?>',self.page)
			self.showInfos()
		kkLink = self['liste'].getCurrent()[0][3]
		getPage(kkLink).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		ddDescription = re.findall('<meta name="description" content="(.*?)KKiste.to.*?"', data, re.S)
		kkCover = re.findall('<img src="(.*?)".*?alt=".*?>', data, re.S)
		if ddDescription:
			self['handlung'].setText(decodeHtml(ddDescription[0]))
		else:
			self['handlung'].setText(_("No information found."))
		kkImage = kkCover[0]
		self.kkImageUrl = "%s" % kkImage.replace('_170_120','_145_215')
		CoverHelper(self['coverArt']).getCover(self.kkImageUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		kkLink = self['liste'].getCurrent()[0][3]
		print kkLink
		getPage(kkLink).addCallback(self.getParts).addErrback(self.dataError)

	def keyShowThumb(self):
		if self.keyLocked:
			return
		self.th_keyShowThumb(self.genreliste, 0, 3, None, None, '<img src="(.*?)"', self.page)

	def getParts(self, data):
		kkName = self['liste'].getCurrent()[0][0]
		streams = re.findall('<a href="(http://www.ecostream.tv/stream/.*?)"', data, re.S)
		print streams
		if streams:
			self.session.open(kinokistePartsScreen, streams, kkName, self.kkImageUrl)

class kinokisteSearchScreen(MPScreen):

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
			"0": self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("KinoKiste")
		self['ContentTitle'] = Label("Suche: %s" % self.Name)

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		getPage(self.Link).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		kkMovies = re.findall('<li class="mbox list".*?<a href="(.*?)" title="Jetzt (.*?) Stream ansehen".*?<p class="year">(.*?)</p>\n<p class="genre">(.*?)</p>', data, re.S)
		if kkMovies:
			for (kkUrl,kkTitle,kkYear,kkGenre) in kkMovies:
				kkUrl = "http://kkiste.to%s" % kkUrl
				self.genreliste.append((kkTitle, kkYear, kkGenre, kkUrl))
			self.ml.setList(map(self.kinokisteFilmLetterListEntry, self.genreliste))
			self.keyLocked = False
			self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		kkLink2 = self['liste'].getCurrent()[0][3]
		print kkLink2
		getPage(kkLink2).addCallback(self.getParts).addErrback(self.dataError)

	def getParts(self, data):
		kkName = self['liste'].getCurrent()[0][0]
		streams = re.findall('<a href="(http://www.ecostream.tv/stream/.*?)"', data, re.S)
		print streams
		if streams:
			self.session.open(kinokistePartsScreen, streams, kkName, None)