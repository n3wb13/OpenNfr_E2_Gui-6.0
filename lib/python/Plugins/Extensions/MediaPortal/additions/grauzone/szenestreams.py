# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

class SzeneStreamsGenreScreen(MPScreen):

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
			"0"     : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Szene-Streams.com")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.keyLocked = True
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Kinofilme", "http://szene-streams.com/publ/aktuelle_kinofilme/1-"))
		self.genreliste.append(("Last Added", "http://szene-streams.com/publ/0-"))
		self.genreliste.append(("Suche", "http://www.szene-streams.com/publ/"))
		self.genreliste.append(("720p", "http://www.szene-streams.com/publ/720p/26-"))
		self.genreliste.append(("Action", "http://www.szene-streams.com/publ/action/2-"))
		self.genreliste.append(("Abenteuer", "http://www.szene-streams.com/publ/abenteuer/3-"))
		self.genreliste.append(("Asia", "http://www.szene-streams.com/publ/asia/4-"))
		self.genreliste.append(("Bollywood", "http://www.szene-streams.com/publ/bollywood/5-"))
		self.genreliste.append(("Biografie", "http://www.szene-streams.com/publ/biografie/6-"))
		self.genreliste.append(("Drama / Romantik", "http://www.szene-streams.com/publ/drama_romantik/8-"))
		self.genreliste.append(("Doku", "http://www.szene-streams.com/publ/dokus_shows/9-"))
		self.genreliste.append(("Familie", "http://www.szene-streams.com/publ/familie/11-"))
		self.genreliste.append(("Geschichte", "http://www.szene-streams.com/publ/geschichte/12-"))
		self.genreliste.append(("HDRiP", "http://www.szene-streams.com/publ/hd/13-"))
		self.genreliste.append(("Horror", "http://www.szene-streams.com/publ/horror/14-"))
		self.genreliste.append(("History", "http://www.szene-streams.com/publ/history/15-"))
		self.genreliste.append(("Komoedie", "http://www.szene-streams.com/publ/komodie/16-"))
		self.genreliste.append(("Krieg", "http://www.szene-streams.com/publ/krieg/17-"))
		self.genreliste.append(("Klassiker", "http://www.szene-streams.com/publ/klassiker/18-"))
		self.genreliste.append(("Mystery", "http://www.szene-streams.com/publ/mystery/19-"))
		self.genreliste.append(("Musik", "http://www.szene-streams.com/publ/musik/20-"))
		self.genreliste.append(("Scifi / Fantasy", "http://www.szene-streams.com/publ/scifi_fantasy/22-"))
		self.genreliste.append(("Thriller / Crime", "http://www.szene-streams.com/publ/thriller_crime/23-"))
		self.genreliste.append(("Western", "http://www.szene-streams.com/publ/western/25-"))
		self.genreliste.append(("Zechentrick / Animation", "http://www.szene-streams.com/publ/zeichentrick_animation/24-"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		if streamGenreName == "Suche":
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True, auto_text_init=True)
		else:
			self.session.open(SzeneStreamsFilmeListeScreen, streamGenreLink, streamGenreName)

	def searchCallback(self, callbackStr):
		if callbackStr is not None:
			self.session.open(SzeneStreamsSearchScreen, callbackStr)

class SzeneStreamsFilmeListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("Szene-Streams.com")
		self['ContentTitle'] = Label(self.streamGenreName)

		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		if not self.streamGenreLink == "http://szene-streams.com/":
			url = "%s%s" % (self.streamGenreLink, str(self.page))
		else:
			url = self.streamGenreLink
		getPage(url, agent=std_headers).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.lastpage = re.findall('<span>(\d*?)</span>', data)
		if self.lastpage:
			self.lastpage = int(self.lastpage[-1])
		else:
			self.lastpage = 1

		movies = re.findall('<div class="ImgWrapNews"><a href="(.*?.[jpg|png])" class="ulightbox" target="_blank".*?alt="(.*?)".*?></a></div>.*?<a class="newstitl entryLink" <.*?href="(.*?)">.*?<div class="MessWrapsNews2" style="height:110px;">(.*?)<', data, re.S)
		if movies:
			self.filmliste = []
			for (image,title,url,h) in movies:
				if not re.match('http:', url):
					url = 'http://szene-streams.com' + url
				self.filmliste.append((decodeHtml(title), url, image, h))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste,0,1,2,None,None, self.page, self.lastpage)
			self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self.streamPic = self['liste'].getCurrent()[0][2]
		streamHandlung = self['liste'].getCurrent()[0][3]
		pagenr = "%s / %s" % (self.page, self.lastpage)
		self['page'].setText(pagenr)
		self['name'].setText(streamName)
		self['handlung'].setText(decodeHtml(streamHandlung.replace('\n','')))
		CoverHelper(self['coverArt']).getCover(self.streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(SzeneStreamsStreamListeScreen, streamLink, streamName, self.streamPic)

	def keyTMDbInfo(self):
		if TMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(TMDbMain, title)

class SzeneStreamsSearchScreen(MPScreen):

	def __init__(self, session, streamSearch):
		self.streamSearch = streamSearch
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
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyTMDbInfo
		}, -1)

		self['title'] = Label("Szene-Streams.com")
		self['ContentTitle'] = Label("Suche: %s" % self.streamSearch)

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		postString = {'a': "2", 'query': self.streamSearch}
		headers = {'User-agent': 'Mozilla/5.0'}
		getPage("http://www.szene-streams.com/publ/", method='POST', postdata=urlencode(postString), agent=headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		movies = re.findall('<div class="ImgWrapNews"><a href="(.*?)".*?(/publ/.*?)">(.*?)</a></b>.*?<div class="MessWrapsNews" align="center"> <div class="MessWrapsNews2" style="height:110px;">(.*?)<', data, re.S)
		if movies:
			self.filmliste = []
			for (image,url,title,h) in movies:
				url = 'http://szene-streams.com' + url
				self.filmliste.append((decodeHtml(title), url, image, h))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"), '', None, ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self.streamPic = self['liste'].getCurrent()[0][2]
		streamHandlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(streamName)
		self['handlung'].setText(decodeHtml(streamHandlung.replace('\n','')))
		CoverHelper(self['coverArt']).getCover(self.streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(SzeneStreamsStreamListeScreen, streamLink, streamName, self.streamPic)

	def keyTMDbInfo(self):
		if TMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(TMDbMain, title)

class SzeneStreamsStreamListeScreen(MPScreen):

	def __init__(self, session, streamFilmLink, streamName, streamPic):
		self.streamFilmLink = streamFilmLink
		self.streamName = streamName
		self.streamPic = streamPic
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0": self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Szene-Streams.com")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.streamName)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.streamPic)
		getPage(self.streamFilmLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('class="eBlock"(.*?)class="MessWrapsNews"', data, re.S|re.I)
		streams = re.findall('(http[s]?://(?!szene-streams)(?!www.szene-streams)(?!flash-moviez.ucoz)(?!www.youtube.com)(.*?)\/.*?)[\'|"|\&|<|\s]', parse.group(1), re.S)
		if streams:
			for (stream, hostername) in streams:
				if isSupportedHoster(hostername, True):
					hostername = hostername.replace('play.','').replace('www.','').replace('embed.','')
					self.filmliste.append((hostername, stream))
			# remove duplicates
			self.filmliste = list(set(self.filmliste))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		self.session.open(SimplePlayer, [(self.streamName, stream_url, self.streamPic)], showPlaylist=False, ltype='szenestreams', cover=True)