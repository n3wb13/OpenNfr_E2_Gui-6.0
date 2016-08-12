# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.api import VuBox4PlayersApi, NetworkError, SYSTEMS

api = VuBox4PlayersApi()

class forPlayersGenreScreen(MPScreen):

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

		self['title'] = Label("4Players")
		self['ContentTitle'] = Label(_("Selection:"))
		self.selectionListe = []
		self.searchTxt = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.selectionListe.append(("Aktuelle Videos", "1"))
		self.selectionListe.append(("Meistgesehene Videos", "2"))
		self.selectionListe.append(("Letzte Reviews", "3"))
		self.selectionListe.append(("Videos nach Spiel suchen", "4"))
		self.ml.setList(map(self._defaultlistcenter, self.selectionListe))

	def keyOK(self):
		self.selectionLink = self['liste'].getCurrent()[0][1]
		print 'SelektionLink: ', self.selectionLink
		if self.selectionLink == "4":
			self.searchTxt = []
			limit = int(150)
			api.set_systems(SYSTEMS)
			self.session.openWithCallback(self.mySearch, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True, auto_text_init=False)
		else:
			self.session.open(forPlayersVideoScreen, self.selectionLink, '')

	def mySearch(self, callback = None):
		if callback != None:
			self.searchTxt = callback
			self.session.open(forPlayersVideoScreen, self.selectionLink, self.searchTxt)

class forPlayersVideoScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, selectionLink, searchData):
		self.selectionLink = selectionLink
		self.searchData = searchData
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
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"info"  : self.keyInfo,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.page = 1
		self.lastpage = 999
		self.keyLocked = True
		self['title'] = Label("4Players")

 		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")
		self.juengstTS = ''
		self.videosListe = []
		self.videosQueue = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadVideos)

	def loadVideos(self):
		if self.selectionLink == '1':
			try:
				limit = int(50)
				api.set_systems(SYSTEMS)
				videos = api.get_latest_videos(limit)
				self.videosQueue.append((self.page, videos))
				self.juengstTS = min((v['ts'] for v in videos))
				self.showData(videos)
			except NetworkError:
				self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
				self.ml.setList(map(self._defaultlistleft, self.videosListe))
		elif self.selectionLink == '2':
			try:
				limit = int(150)
				api.set_systems(SYSTEMS)
				videos = api.get_popular_videos(limit)
				self.showData(videos)
			except NetworkError:
				self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
				self.ml.setList(map(self._defaultlistleft, self.videosListe))
		elif self.selectionLink == '3':
			try:
				limit = int(150)
				api.set_systems(SYSTEMS)
				videos = api.get_latest_reviews(older_than=0)
				self.showData(videos)
			except NetworkError:
				self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
				self.ml.setList(map(self._defaultlistleft, self.videosListe))
		elif self.selectionLink == "4":
			videos = []
			try:
				searchStr = str(self.searchData)
				try:
					videos = api.get_games(searchStr)
					if videos == None:
						self.videosListe.append(('Keine Videos gefunden....', "", "", ""))
						self.ml.setList(map(self._defaultlistleft, self.videosListe))
					else:
						self.showSearchData(videos)
				except NetworkError:
					self.videosListe.append(('Keine Videos gefunden....', "", "", ""))
			except NetworkError:
				self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
				self.ml.setList(map(self._defaultlistleft, self.videosListe))

	def showSearchData(self, videos):
		for video in videos:
			gameTitel = video['title'].encode('utf-8')
			gameID = video['id']
			videoPic = video['thumb']
			gameStudio = video['studio']
			self.videosListe.append((gameTitel, "empty", str(videoPic), gameTitel, gameID, gameStudio, 2))
		self.ml.setList(map(self._defaultlistleft, self.videosListe))
		self.keyLocked = False

	def showData(self, videos):
		for video in videos:
			gameTitle = video['game']['title'].encode('utf-8')
			videoTitle = video['video_title'].encode('utf-8')
			videoStreamUrl = video['streams']['hq']['url'].encode('utf-8')
			videoDate = video['date']
			videoPic = video['thumb']
			gameId = video['game']['id']
			gameStudio = video['game']['studio']
			videoTitleConv = gameTitle + ' - ' + videoTitle + ' ' + '(' + videoDate + ')'
			self.videosListe.append((videoTitleConv, videoStreamUrl, str(videoPic), videoTitle, gameId, gameStudio, gameTitle))
		self.ml.setList(map(self._defaultlistleft, self.videosListe))
		self.keyLocked = False
		self.th_ThumbsQuery(self.videosListe, 0, 1, 2, None, None, self.page, 999, mode=1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(str(Title))
		self['page'].setText(str(self.page))
		CoverHelper(self['coverArt']).getCover(Image)

	def loadPage(self):
		if self.selectionLink == '1':
			self.videosListe = []
			self.queuedVideoList = []
			for queuedEntry in self.videosQueue:
				if queuedEntry[0] == self.page:
					self.queuedVideoList = queuedEntry[1]
			if self.queuedVideoList:
				self.showData(self.queuedVideoList)
			else:
				try:
						api.set_systems(SYSTEMS)
						videos = api.get_latest_videos(older_than=self.juengstTS)
						self.juengstTS = min((v['ts'] for v in videos))
						self.videosQueue.append((self.page, videos))
						self.showData(videos)
				except NetworkError:
						self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
						self.ml.setList(map(self._defaultlistleft, self.videosListe))

	def keyInfo(self):
		text = []
		gameStudio = self['liste'].getCurrent()[0][5]
		gameId = self['liste'].getCurrent()[0][4]
		gameTitle = self['liste'].getCurrent()[0][6]
		gameInfoCol = api._get_game_info(gameId)
		text.append('Titel: ' + str(gameTitle))
		text.append('\n')
		text.append('Studion: ' + str(gameStudio))
		text.append('\n')
		for info in gameInfoCol:
			gamePub = info['publisher']
			text.append('Publisher: ' + str(gamePub))
			text.append('\n')
			for system in info['systeme']:
				gameSys = system['system']
				text.append('Plattform: ' + str(gameSys))
				text.append('\n')
				text.append('Release: ' + str(system['releasetag']) + '.' + str(system['releasemonat']) + '.' + str(system['releasejahr']))
				text.append('\n')
				text.append('USK: ' + str(system['usk']))
				text.append('\n')
		sText = ''.join(text)
		self.session.open(MessageBoxExt,_(sText), MessageBoxExt.TYPE_INFO)

	def keyOK(self):
		playersUrl = self['liste'].getCurrent()[0][1]
		if playersUrl == "empty":
			game_id = self['liste'].getCurrent()[0][4]
			game_id_int = int(game_id)
			searchVideos = api.get_videos_by_game(older_than=0, game_id=game_id)
			self.session.open(forPlayersSearchListScreen, searchVideos)
		else:
			streamUrl = str(playersUrl)
			playersTitle = self['liste'].getCurrent()[0][3]
			playersTitleStr = str(playersTitle)
			if playersUrl:
				self.session.open(SimplePlayer, [(playersTitleStr, streamUrl)], showPlaylist=False, ltype='4players')

class forPlayersSearchListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, videosListe):
		self.searchVideoListe = videosListe
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
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"info"  : self.keyInfo,
		}, -1)

		self.page = 1
		self.lastpage = 999
		self.keyLocked = True
		self['title'] = Label("4Players")

 		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")
		self.juengstTS = ''
		self.videosListe = []
		self.videosQueue = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadSearchVideos)

	def loadSearchVideos(self):
		videos = self.searchVideoListe
		for video in videos:
			gameTitle = video['game']['title'].encode('utf-8')
			videoTitle = video['video_title'].encode('utf-8')
			videoStreamUrl = video['streams']['hq']['url'].encode('utf-8')
			videoDate = video['date']
			videoPic = video['thumb']
			gameId = video['game']['id']
			gameStudio = video['game']['studio']
			videoTitleConv = gameTitle + ' - ' + videoTitle + ' ' + '(' + videoDate + ')'
			self.videosListe.append((videoTitleConv, videoStreamUrl, str(videoPic), videoTitle, gameId, gameStudio, gameTitle))
		self.ml.setList(map(self._defaultlistleft, self.videosListe))
		self.keyLocked = False
		self.th_ThumbsQuery(self.videosListe, 0, 1, 2, None, None, self.page, 999, mode=1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(str(Title))
		self['page'].setText(str(self.page))
		CoverHelper(self['coverArt']).getCover(Image)

	def keyInfo(self):
		text = []
		gameStudio = self['liste'].getCurrent()[0][5]
		gameId = self['liste'].getCurrent()[0][4]
		gameTitle = self['liste'].getCurrent()[0][6]
		gameInfoCol = api._get_game_info(gameId)
		text.append('Titel: ' + str(gameTitle))
		text.append('\n')
		text.append('Studion: ' + str(gameStudio))
		text.append('\n')
		for info in gameInfoCol:
			gamePub = info['publisher']
			text.append('Publisher: ' + str(gamePub))
			text.append('\n')
			for system in info['systeme']:
				gameSys = system['system']
				text.append('Plattform: ' + str(gameSys))
				text.append('\n')
				text.append('Release: ' + str(system['releasetag']) + '.' + str(system['releasemonat']) + '.' + str(system['releasejahr']))
				text.append('\n')
				text.append('USK: ' + str(system['usk']))
				text.append('\n')
		sText = ''.join(text)
		self.session.open(MessageBoxExt,_(sText), MessageBoxExt.TYPE_INFO)

	def keyOK(self):
		playersUrl = self['liste'].getCurrent()[0][1]
		streamUrl = str(playersUrl)
		playersTitle = self['liste'].getCurrent()[0][3]
		playersTitleStr = str(playersTitle)
		if playersUrl:
			self.session.open(SimplePlayer, [(playersTitleStr, streamUrl)], showPlaylist=False, ltype='4players')