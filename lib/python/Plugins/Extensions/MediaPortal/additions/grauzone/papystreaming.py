# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2016
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding execution on hardware, you are permitted to execute this plugin on VU+ hardware
#  which is licensed by satco europe GmbH, if the VTi image is used on that hardware.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
###############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

BASE_URL_EN = "http://babystreaming.com"
BASE_URL_FR = "http://papystreaming.com/fr"
BASE_URL_XXX = "http://papyporn.com/fr"

BASE_URL = "http://papystreaming.com/fr"
BASE_NAME = ""

class papystreamingGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.UrlMode = mode
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		global BASE_NAME
		if self.UrlMode == 'EN':
			self.baseUrl = BASE_URL_EN
			BASE_NAME = "Babystreaming"
		elif self.UrlMode == 'FR':
			self.baseUrl = BASE_URL_FR
			BASE_NAME = "Papystreaming (FR)"
		else:
			self.baseUrl = BASE_URL_XXX
			BASE_NAME = "PapyPorn"

		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		getPage(self.baseUrl).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		if self.UrlMode == 'EN':
			self.genreliste.append(('Movies Latest', '%s/movies/?porder=latest' % self.baseUrl))
			self.genreliste.append(('Movies Popular', '%s/movies/?porder=pop' % self.baseUrl))
			self.genreliste.append(("Movie A-Z","%s/movies/movies-a-z-list/" % self.baseUrl))
			self.genreliste.append(('Movies Rating Metacritic', '%s/movies/?porder=rating1' % self.baseUrl))
			self.genreliste.append(('Movies Rating IMDB', '%s/movies/?porder=rating' % self.baseUrl))
			self.genreliste.append(('Series Latest', '%s/tv-series/?porder=latest' % self.baseUrl))
			self.genreliste.append(('Series Popular', '%s/tv-series/?porder=pop' % self.baseUrl))
			self.genreliste.append(('Series A-Z', '%s/tv-series/tv-series-a-z-list' % self.baseUrl))
			self.genreliste.append(('Series Rating IMDB', '%s/tv-series/?porder=rating' % self.baseUrl))
		elif self.UrlMode == 'FR':
			self.genreliste.append(('Movies Latest', '%s/films/?porder=latest' % self.baseUrl))
			self.genreliste.append(('Movies Popular', '%s/films/?porder=pop' % self.baseUrl))
			self.genreliste.append(("Movies A-Z","%s/films/films-de-a-a-z" % self.baseUrl))
			self.genreliste.append(('Movies Rating Metacritic', '%s/films/?porder=rating1' % self.baseUrl))
			self.genreliste.append(('Movies Rating IMDB', '%s/films/?porder=rating' % self.baseUrl))
			self.genreliste.append(('Series Latest', '%s/series-tv/?porder=latest' % self.baseUrl))
			self.genreliste.append(('Series Popular', '%s/series-tv/?porder=pop' % self.baseUrl))
			self.genreliste.append(('Series A-Z', '%s/series-tv/series-tv-liste-de-a-a-z' % self.baseUrl))
			self.genreliste.append(('Series Rating IMDB', '%s/series-tv/?porder=rating' % self.baseUrl))
		else:
			self.genreliste.append(("Videos A-Z","%s/videos/liste-de-a-a-z" % self.baseUrl))
			self.genreliste.append(('Movies Popular', '%s/?porder=pop' % self.baseUrl))
			self.genreliste.append(('Movies Latest', '%s/?porder=latest' % self.baseUrl))

		Cat = re.findall('u-item-type-taxonomy.*?<a\shref="(.*?)">(.*?)<', data, re.S)
		if Cat:
			for (Url, Title) in Cat:
				self.genreliste.append((Title, Url))
		parse = re.search('"dropdown">Categories(.*?)</ul>', data, re.S)
		if parse:
			Cat = re.findall('<a\shref="(.*?)"\stitle=".*?">(.*?)</a', parse.group(1), re.S)
			if Cat:
				for (Url, Title) in Cat:
					self.genreliste.append((Title, Url))
		self.genreliste.insert(0, ('--- Search ---', 'callSuchen'))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = '%s/?s=%s' % (self.baseUrl,self.suchString)
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(papystreamingFilmScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		elif re.match(".*?A-Z", Name):
			self.session.open(papystreamingLetterScreen, Link, Name)
		else:
			self.session.open(papystreamingFilmScreen, Link, Name)

class papystreamingLetterScreen(MPScreen, SearchHelper):

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
		self.skin = self.skin.replace('</screen>', '')
		path = "%s/%s/search_widgets.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/search_widgets.xml"
		with open(path, "r") as f:
			self.skin += f.read()
			f.close()
		self.skin += '</screen>'

		MPScreen.__init__(self, session)
		SearchHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("A-Z")
		self['name'] = Label(_("Please wait..."))
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.streamList = []

		self.onLayoutFinish.append(self.loadPage)

	def goToLetter(self, num):
		self.keyNumberGlobal(num, self.streamList)
		self.showSearchkey(num)

	def loadPage(self):
		getPage(self.Link).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('<div class="glossaryheader".*?</div>(.*?)$', data, re.S)
		raw = re.findall('<a href="(.*?)">(.*?)<', parse.group(1), re.S)
		if raw:
			for (Url, Title) in raw:
				self.streamList.append((decodeHtml(Title), Url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if re.match("Series", self.Name):
			self.session.open(papystreamingSeriesScreen, Link, Title, None)
		else:
			self.session.open(papystreamingPlayMovieScreen, Link, Title, None)

class papystreamingFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = None

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?/category/", self.Link):
			url = self.Link
		else:
			url = "%s&gpage=%s" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if not self.lastpage:
			self.getLastPage(data, '', '<div class="pagination">.*?[of|sur]\s(.*?)</span>')
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		Movies = re.findall('<article id=.*?src="(.*?)".*?<a href="(.*?)">(.*?)<', data, re.S)
		if Movies:
			for (Image, Url, Title) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Image = self['liste'].getCurrent()[0][2]
		if Link == None:
			return
		if re.match("Series", self.Name):
			self.session.open(papystreamingSeriesScreen, Link, Title, Image)
		else:
			self.session.open(papystreamingPlayMovieScreen, Link, Title, Image)

class papystreamingSeriesScreen(MPScreen):

	def __init__(self, session, streamFilmLink, streamName, streamImage):
		self.streamFilmLink = streamFilmLink
		self.streamName = streamName
		self.streamImage = streamImage
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Series: %s" % self.streamName)
		self['name'] = Label(_("Please wait..."))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.streamImage)
		self.keyLocked = True
		getPage(self.streamFilmLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('<div class="videolinks">(.*?)<div class="clear">', data, re.S)
		if parse:
			saisonnr = re.findall('<li>(S..son.*?)<ul>(.*?)</li></ul>', parse.group(1), re.S)
			if saisonnr:
				for (saison, saisondata) in saisonnr:
					self.filmliste.append((saison, saisondata))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No supported streams found!"), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False
		self['name'].setText(self.streamName)

	def keyOK(self):
		if self.keyLocked:
			return
		series = self['liste'].getCurrent()[0][0]
		data = self['liste'].getCurrent()[0][1]
		seriename = "%s - %s" % (self.streamName, series)
		self.session.open(papystreamingStaffelnScreen, seriename, data, self.streamImage)

class papystreamingStaffelnScreen(MPScreen):

	def __init__(self, session, series, data, streamImage):
		self.streamName = series
		self.streamData = data
		self.streamImage = streamImage
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Series: %s " % self.streamName)
		self['name'] = Label(_("Please wait..."))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPageData)

	def loadPageData(self):
		CoverHelper(self['coverArt']).getCover(self.streamImage)
		streams = re.findall('mainboxtext">(\d+)<.*?&quot;http.*?\\\&quot;', self.streamData, re.S)
		if not streams:
			streams = re.findall('title="play video (\d+)".*?&quot;http.*?\\\&quot;', self.streamData, re.S)
		if streams:
			for nr in streams:
				self.filmliste.append(('Episode ' + str(nr),str(nr)))
		cacao = re.findall('mainboxtext">(\d+)<.*?http://127.0.0.1:4001/.*?&', self.streamData, re.S)
		if not cacao:
			cacao = re.findall('title="play video (\d+)".*?http://127.0.0.1:4001/.*?&', self.streamData, re.S)
		if cacao:
			for nr in cacao:
				self.filmliste.append(('Episode ' + str(nr), str(nr)))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No supported streams found!"), None))
		self.filmliste = list(set(self.filmliste))
		self.filmliste.sort()
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False
		self['name'].setText(self.streamName)

	def keyOK(self):
		if self.keyLocked:
			return
		episode = self['liste'].getCurrent()[0][1]
		self.session.open(papystreamingPlayEpisodenScreen, episode, self.streamData, self.streamName, self.streamImage)

class papystreamingPlayEpisodenScreen(MPScreen):

	def __init__(self, session, episode, data, title, streamImage):
		self.streamName = episode
		self.streamData = data
		self.streamTitle = title
		self.streamImage = streamImage
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Series: %s - %s " % (self.streamTitle,self.streamName))
		self['name'] = Label(_("Please wait..."))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPageData)

	def loadPageData(self):
		CoverHelper(self['coverArt']).getCover(self.streamImage)
		streams = re.findall('mainboxtext">'+self.streamName+'<.*?&quot;(http[s]?://(.*?)\/.*?)\\\&quot;', self.streamData, re.S)
		if not streams:
			streams = re.findall('title="play video '+self.streamName+'".*?&quot;(http[s]?://(.*?)\/.*?)\\\&quot;', self.streamData, re.S)
		if streams:
			for (streamurl, hostername) in streams:
				hostername = hostername.replace('embed.','')
				if isSupportedHoster(hostername, True):
					self.filmliste.append((hostername, streamurl))
		cacao = re.findall('mainboxtext">'+self.streamName+'<.*?http://127.0.0.1:4001/(.*?)&', self.streamData, re.S)
		if not cacao:
			cacao = re.findall('title="play video '+self.streamName+'".*?http://127.0.0.1:4001/(.*?)&', self.streamData, re.S)
		if cacao:
			for (streamurl) in cacao:
				self.filmliste.append(('yujitube', 'http://s%s.yujitube.com:8080/%s' % (str(random.randint(101,899)), streamurl)))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No supported streams found!"), None))
		self.filmliste.sort()
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False
		self['name'].setText("%s - %s" % (self.streamTitle,self.streamName))

	def keyOK(self):
		if self.keyLocked:
			return
		streamHoster = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		if streamHoster == 'yujitube':
			self.got_link(streamLink)
		else:
			get_stream_link(self.session).check_link(streamLink, self.got_link)

	def got_link(self, stream_url):
		self.session.open(SimplePlayer, [(self.streamTitle + " - " + self.streamName, stream_url, self.streamImage)], showPlaylist=False, ltype='papystreaming', cover=True)

class papystreamingPlayMovieScreen(MPScreen):

	def __init__(self, session, streamFilmLink, streamName, streamImage):
		self.streamFilmLink = streamFilmLink
		self.streamName = streamName
		self.streamImage = streamImage
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Streams:")
		self['name'] = Label(_("Please wait..."))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.streamImage)
		self.keyLocked = True
		getPage(self.streamFilmLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('<div class="videolinks">(.*?)<div class="clear">', data, re.S)
		if parse:
			streams = re.findall('&quot;(http[s]?://(.*?)\/.*?)\\\&quot;', parse.group(1), re.S)
			if streams:
				for (streamurl, hostername) in streams:
					hostername = hostername.replace('embed.','')
					if isSupportedHoster(hostername, True):
						self.filmliste.append((hostername, streamurl))
			cacao = re.findall('http://127.0.0.1:4001/(.*?)&', parse.group(1), re.S)
			if cacao:
				for stream in cacao:
					self.filmliste.append(('yujitube', 'http://s%s.yujitube.com:8080/%s' % (str(random.randint(101,899)), stream)))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No supported streams found!"), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False
		self['name'].setText(self.streamName)

	def keyOK(self):
		if self.keyLocked:
			return
		hoster = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if url:
			if hoster == 'yujitube':
				self.got_link(url)
			else:
				get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		self.session.open(SimplePlayer, [(self.streamName, stream_url, self.streamImage)], showPlaylist=False, ltype='papystreaming', cover=True)