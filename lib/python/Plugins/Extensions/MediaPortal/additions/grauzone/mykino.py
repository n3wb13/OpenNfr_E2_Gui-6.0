# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2017
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

class myKinoMain(MPScreen):

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

		self['title'] = Label("MyKino.to")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(("Aktuelle Kinofilme", "aktuelle-kinofilme"))
		self.streamList.append(("Neue Filme", "filme"))
		self.streamList.append(("Neue Serien (Episoden)", "neue_serien"))
		self.streamList.append(("Serien", "serien"))
		self.streamList.append(("Abenteuer", "abenteuer"))
		self.streamList.append(("Action", "action"))
		self.streamList.append(("Biographie", "biographie"))
		self.streamList.append(("Drama", "drama"))
		self.streamList.append(("Familie", "familie"))
		self.streamList.append(("Fantasy", "fantasy"))
		self.streamList.append(("Horror", "horror"))
		self.streamList.append(("Komödie", "komoedie"))
		self.streamList.append(("Krimi", "krimi"))
		self.streamList.append(("Romantik", "romantik"))
		self.streamList.append(("Sci-Fi", "sci-fi"))
		self.streamList.append(("Thriller", "thriller"))
		self.streamList.append(("Trickfilm", "trickfilm"))
		self.streamList.append(("Western", "western"))
		self.streamList.append(("Krieg", "krieg"))
		self.streamList.append(("Sport", "sport"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		if auswahl == "Neue Serien (Episoden)":
			url = 'http://mykino.to/letzte-serien-updates.html'
			self.session.open(myKinoLastSerienParsing, auswahl, url, type)
		else:
			url = 'http://mykino.to/' + self['liste'].getCurrent()[0][1] + '/page/'
			self.session.open(myKinoParsing, auswahl, url)

class myKinoParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
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

		self['title'] = Label("MyKino.to")
		self['ContentTitle'] = Label("%s" % self.genre)

		self['Page'] = Label(_("Page:"))

		self.page = 1
		self.lastpage = 1
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = self.url+str(self.page)
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, 'class="pagenavigation ">(.*?)</div>')
		movies = re.findall('<div class="boxgrid2 caption2">\n<a href="(.*?.html)">\n<img class="images3" src="(.*?)".*?<div class="boxgridtext">\n(.*?)\n</div>', data, re.S)
		if movies:
			for (Url, Image, Title) in movies:
				self.streamList.append((decodeHtml(Title), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		movie_url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		if self.genre == "Serien":
			self.session.open(mykinoSaffeln, stream_name, movie_url, cover)
		else:
			self.addGlobalWatchtlist([stream_name, cover, "mykinoStreams", stream_name, movie_url, cover])
			self.session.open(mykinoStreams, stream_name, movie_url, cover)

class myKinoLastSerienParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url, type):
		self.genre = genre
		self.url = url
		self.type = type
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
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("MyKino.to")
		self['ContentTitle'] = Label("%s" % self.genre)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		last_raw = re.findall('<div class="film_row">.*?<a href="http://mykino.to/(.*?)-.*?html#s(.*?)e(.*?)"><h3>(.*?)</h3>.*?<h4>(.*?)</h4>', data, re.S)
		if last_raw:
			for newsid,staffel,episode,serientitle,serienlabel in last_raw:
				url = "http://mykino.to/engine/ajax/a.sseries.php?news_id=%s&season=%s" % (newsid, staffel)
				title = serientitle+" "+serienlabel
				self.streamList.append((decodeHtml(title), url, serientitle, staffel, newsid))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False
			self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		apiUrl = self['liste'].getCurrent()[0][1]
		stream_name = self['liste'].getCurrent()[0][2]
		staffel = self['liste'].getCurrent()[0][3]
		newsid = self['liste'].getCurrent()[0][4]
		self.session.open(mykinoEpisoden, stream_name+" Staffel "+staffel, apiUrl, None, newsid)

class mykinoSaffeln(MPScreen):

	def __init__(self, session, stream_name, url, cover):
		self.stream_name = stream_name
		self.url = url
		self.cover = cover
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("MyKino.to")
		self['ContentTitle'] = Label(_("Season Selection"))
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
		self.streamList = []
		self.newsid = None
		self.newsid = re.findall("'news_id':(.*\d),", data)
		if self.newsid is not None:
			self.newsid = self.newsid[0]
			staffeln = re.findall('option value="(.*?)">Staffel.*?<', data, re.S)
			if staffeln:
				for staffel in staffeln:
					self.streamList.append(("Staffel "+str(staffel), str(staffel)))
				self.ml.setList(map(self._defaultlistcenter, self.streamList))
				CoverHelper(self['coverArt']).getCover(self.cover)
				self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		staffel = self['liste'].getCurrent()[0][1]
		apiUrl = "http://mykino.to/engine/ajax/a.sseries.php?news_id=%s&season=%s" % (self.newsid, staffel)
		self.session.open(mykinoEpisoden, self.stream_name+" Staffel "+staffel, apiUrl, self.cover, self.newsid)

class mykinoEpisoden(MPScreen):

	def __init__(self, session, stream_name, url, cover, newsid):
		self.stream_name = stream_name
		self.url = url
		self.cover = cover
		self.newsid = newsid
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("MyKino.to")
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
		self.streamList = []
		episoden = re.findall('option value=."(.*?).">(.*?)<', data, re.S)
		if episoden:
			for episode, episodenName in episoden:
				self.streamList.append((episodenName, episode))
			self.ml.setList(map(self._defaultlistcenter, self.streamList))
			CoverHelper(self['coverArt']).getCover(self.cover)
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		episode = self['liste'].getCurrent()[0][0]
		episodenID = self['liste'].getCurrent()[0][1]
		apiUrl = "http://mykino.to/engine/ajax/a.sseries.php?news_id=%s&series=%s" % (self.newsid, episodenID)
		self.addGlobalWatchtlist([self.stream_name+" "+episode, self.cover, "mykinoStreams", self.stream_name+" "+episode, apiUrl, self.cover])
		self.session.open(mykinoStreams, self.stream_name+" "+episode, apiUrl, self.cover)

class mykinoStreams(MPScreen):

	def __init__(self, session, stream_name, url, cover):
		self.stream_name = stream_name
		self.url = url
		self.cover = cover
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("MyKino.to")
		self['ContentTitle'] = Label(_("Stream Selection"))
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
		data = data.replace('\\"','"').replace('\\/','/')
		streamsData = re.findall('data-href="(.*?)".*?<span>(.*?)</span>', data, re.S)
		if streamsData:
			for urls,Hoster in streamsData:
				if isSupportedHoster(Hoster, True):
					Hoster = Hoster.replace('www.','')
					streams = urls.split("#,")
					if streams:
						for stream in streams:
							self.streamList.append((Hoster, stream))
			self.ml.setList(map(self._defaultlisthoster, self.streamList))
			CoverHelper(self['coverArt']).getCover(self.cover)
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamUrl = self['liste'].getCurrent()[0][1]
		get_stream_link(self.session).check_link(streamUrl, self.playfile)

	def playfile(self, stream_url):
		if stream_url != None:
			self.session.open(SimplePlayer, [(self.stream_name, stream_url, self.cover)], showPlaylist=False, ltype='mykino', cover=True)