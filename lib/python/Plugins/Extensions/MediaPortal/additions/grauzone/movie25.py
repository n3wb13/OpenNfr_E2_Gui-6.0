# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

baseurl = "http://tinklepad.is/"

class movie25GenreScreen(MPScreen):

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

		self.keyLocked = True
		self['title'] = Label("Movie25")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [ ('New Releases',baseurl + "new-releases/"),
		                    ('Last Added',baseurl + "latest-added/"),
		                    ('Featured Movies',baseurl + "featured-movies/"),
		                    ('Latest HQ Movies',baseurl + "latest-hd-movies/"),
		                    ('Most Popular',baseurl + "most-popular/"),
		                    ('Most Voted',baseurl + "most-voted/"),
		                    ('Popular Today',baseurl + "popular-today/"),
		                    ('Top Rated Movies',baseurl + "top-rated/"),
                            ('Action',baseurl + "action/"),
                            ('Adventure',baseurl + "adventure/"),
                            ('Animation',baseurl + "animation/"),
                            ('Biography',baseurl + "biography/"),
                            ('Comedy',baseurl + "comedy/"),
                            ('Crime',baseurl + "crime/"),
                            ('Documentary',baseurl + "documentary/"),
                            ('Drama',baseurl + "drama/"),
                            ('Family',baseurl + "family/"),
                            ('Fantasy',baseurl + "fantasy/"),
                            ('History',baseurl + "history/"),
                            ('Horror',baseurl + "horror/"),
                            ('Music',baseurl + "music/"),
                            ('Musical',baseurl + "musical/"),
                            ('Mystery',baseurl + "mystery/"),
                            ('Romance',baseurl + "romance/"),
                            ('Sci-Fi',baseurl + "sci-fi/"),
                            ('Short',baseurl + "short/"),
                            ('Sport',baseurl + "sport/"),
                            ('Thriller',baseurl + "thriller/"),
                            ('War',baseurl + "war/"),
                            ('Western',baseurl + "western/"),
                            ('Movie Title 0-9',baseurl + "0-9/"),
                            ('Movie Title A',baseurl + "a/"),
                            ('Movie Title B',baseurl + "b/"),
                            ('Movie Title C',baseurl + "c/"),
                            ('Movie Title D',baseurl + "d/"),
                            ('Movie Title E',baseurl + "e/"),
                            ('Movie Title F',baseurl + "f/"),
                            ('Movie Title G',baseurl + "g/"),
                            ('Movie Title H',baseurl + "h/"),
                            ('Movie Title I',baseurl + "i/"),
                            ('Movie Title J',baseurl + "j/"),
                            ('Movie Title K',baseurl + "k/"),
                            ('Movie Title L',baseurl + "l/"),
                            ('Movie Title M',baseurl + "m/"),
                            ('Movie Title N',baseurl + "n/"),
                            ('Movie Title O',baseurl + "o/"),
                            ('Movie Title P',baseurl + "p/"),
                            ('Movie Title Q',baseurl + "q/"),
                            ('Movie Title R',baseurl + "r/"),
                            ('Movie Title S',baseurl + "s/"),
                            ('Movie Title T',baseurl + "t/"),
                            ('Movie Title U',baseurl + "u/"),
                            ('Movie Title V',baseurl + "v/"),
                            ('Movie Title W',baseurl + "w/"),
                            ('Movie Title X',baseurl + "x/"),
                            ('Movie Title Y',baseurl + "y/"),
                            ('Movie Title Z',baseurl + "z/"),]

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		print streamGenreName, streamGenreLink

		self.session.open(movie25FilmeListeScreen, streamGenreLink, streamGenreName)

class movie25FilmeListeScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("Movie25")
		self['ContentTitle'] = Label("%s:" % self.streamGenreName)

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['Page'].setText(str(self.page)+ " of")
		url = "%s%s" % (self.streamGenreLink, str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		lastpage = re.findall('<div class="count">.*?\d/(.*\d)&nbsp', data, re.S)
		if lastpage:
			self.lastpage = lastpage[0]
			self['page'].setText(lastpage[0])
		else:
			self.lastpage = 999

		data=data.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
		movies = re.findall('<div\sclass="movie_pic"><a\shref="(.*?)".*?src="(.*?)".*?alt="(.*?)"', data, re.S)
		if movies:
			self.filmliste = []
			for (link,image,title) in movies:
				self.filmliste.append((decodeHtml(title),link,image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(movie25StreamListeScreen, streamLink, streamName)

class movie25StreamListeScreen(MPScreen):

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

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Movie25")
		self['ContentTitle'] = Label("Streams for %s:" % self.streamGenreName)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.streamGenreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		streams = re.findall('<li id="link_name">(.*?)</li>.*?<li id="playing_button"><a href="(.*?)" target', data, re.S)
		if streams:
			self.filmliste = []
			for (name, link) in streams:
				name = name.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
				if isSupportedHoster(name, True):
					self.filmliste.append((decodeHtml(name.strip()),link))
			if len(self.filmliste) == 0:
				self.filmliste.append((_('No supported streams found!'), None))
			self.ml.setList(map(self._defaultlisthoster, self.filmliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		if streamLink:
			getPage(streamLink).addCallback(self.getLink).addErrback(self.dataError)

	def getLink(self, data):
		link = re.findall('showvideo"\ssrc="(http[s]?://.*?)"', data, re.S)
		if link:
			get_stream_link(self.session).check_link(link[0], self.got_link)
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def got_link(self, stream_url):
		self.session.open(SimplePlayer, [(self.streamGenreName, stream_url)], showPlaylist=False, ltype='movie25')