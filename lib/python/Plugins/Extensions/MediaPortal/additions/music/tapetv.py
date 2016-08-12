# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt
from Plugins.Extensions.MediaPortal.resources.configlistext import ConfigListScreenExt

ck = {}
config.mediaportal.tapetv_maxquali = ConfigText(default="2", fixed_size=False)
config.mediaportal.tapetv_username = ConfigText(default="tapetvUserName", fixed_size=False)
config.mediaportal.tapetv_password = ConfigPassword(default="tapetvPassword", fixed_size=False)
config.mediaportal.tapetv_autologin = ConfigYesNo(default = True)

myqualities = [['HD720p', "0"],['SD480p', "1"],['highHQ', "2"],['mediumMQ', "3"],['lowLQ', "4"],['HLS-Stream', "5"]]

BASE_URL = "https://www.tape.tv"
BASE_NAME = "Tape.tv"
EXPLORE_TOKEN = ''
LOGIN_NAME = False
GLOB_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0'

class Tapetvhelper:

	def __init__(self, session):
		self.session = session

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		idx = self['liste'].getSelectedIndex()
		mytype = self.filmliste[idx][1]
		if mytype == "videos" or mytype == "video":
			playlist = []
			for item in self.filmliste:
				if item[1] == 'videos' or item[1] == 'video':
					playlist.append(item)
			self.session.open(tapeTVListPlayer, playlist, int(idx) , True, self.CatName)
		elif mytype == 'tapes' or mytype == 'tape':
			name = "Videos in %s" % self.filmliste[idx][0]
			self.session.open(tapetvTapesVideoScreen, self.filmliste[idx], name)
		elif mytype == 'artist':
			name = 'Similar Artist Videos: %s' % self['liste'].getCurrent()[0][2]
			self.session.open(tapetvArtistSongsScreen , self.filmliste[idx], name)

	def showInfos(self):
		if self['liste'].getCurrent()[0][2] == '':
			name = "%s - %s" % (self['liste'].getCurrent()[0][6],self['liste'].getCurrent()[0][3])
		else:
			name = self['liste'].getCurrent()[0][2]
		self['name'].setText(name)
		Image = self['liste'].getCurrent()[0][9]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyQuali(self):
		if self.keyLocked:
			return
		self.session.openWithCallback(self.returnkeyQuali, ChoiceBoxExt, title=_('Videoresolution'), list=myqualities, selection=2)

	def returnkeyQuali(self, data):
		if data:
			self['F3'].setText(data[0].upper())
			config.mediaportal.tapetv_maxquali.value = data[1]
			config.mediaportal.tapetv_maxquali.save()
			configfile.save()

	def keytapetvAction(self):
		if self.keyLocked:
			return
		idx = self['liste'].getSelectedIndex()
		mytype = self.filmliste[idx][1]
		if mytype == 'videos' or mytype == 'video':
			rangelist = [['Show Similar Videos', '1'], ['Show Similar Artists', '2'], ['Show Tapes current Video','3'], ['Show Songs current Artist','4']]
			self.session.openWithCallback(self.keytapetvBackAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keytapetvBackAction(self, result):
		if result:
			listitem = self['liste'].getCurrent()
			if result[1] == '1':
				title = 'Similar Videos: %s - %s' % (self['liste'].getCurrent()[0][6],self['liste'].getCurrent()[0][3])
				self.session.open(tapetvSimilarScreen, listitem, title)
			elif result[1] == '2':
				title = 'Similar Artists: %s' % self['liste'].getCurrent()[0][6]
				self.session.open(tapetvSimilarScreen , listitem, title)
			elif result[1] == '3':
				title = 'Show Tapes current Video: %s' % self['liste'].getCurrent()[0][6]
				self.session.open(tapetvTapesScreen, listitem[0], title)
			elif result[1] == '4':
				title = 'Songs Artist: %s' % self['liste'].getCurrent()[0][6]
				self.session.open(tapetvArtistSongsScreen , listitem[0], title)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		if LOGIN_NAME:
			rangelist = [['add to Local Playlist', '1'], ['add to LoginUser Favorits', '2']]
			self.session.openWithCallback(self.keyAddBackAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)
		else:
			self.addLocalPlaylist()

	def keyAddBackAction(self, result):
		if result:
			if result[1] == '1':
				self.addLocalPlaylist()
			else:
				mytype = self['liste'].getCurrent()[0][1]
				myid = self['liste'].getCurrent()[0][4]
				if re.match('tape', mytype):
					postData = {'like':{'likeable_type': "Tape", 'likeable_id': int(myid) }}
				elif re.match('video', mytype):
					postData = {'like':{'likeable_type': mytype, 'likeable_id': int(myid) }}
				url = "%s/likes" % BASE_URL
				header = {
						'Accept': 'application/json',
						'Accept-Language': 'en-US,en;q=0.5',
						'Accept-Encoding': 'gzip, deflate',
						'Content-Type': 'application/json',
						'X-Requested-With': 'XMLHttpRequest',
						}
				jsondata = json.dumps(postData)
				getPage(url, agent=GLOB_AGENT, method='POST', postdata=jsondata, cookies=ck, headers=header).addCallback(self.addRemotePlaylist).addErrback(self.addLoginUserError).addErrback(self.dataError)

	def addLoginUserError(self, error):
		myerror = error.getErrorMessage()
		if myerror == '500 Internal Server Error':
			message = self.session.open(MessageBoxExt, _("Selection is already in the LoginUser Playlist."), MessageBoxExt.TYPE_INFO, timeout=3)
		raise error

	def addRemotePlaylist(self, data):
		if re.search('"created_at":', data):
			message = self.session.open(MessageBoxExt, _("Selection was added to the LoginUser Playlist."), MessageBoxExt.TYPE_INFO, timeout=3)

	def addLocalPlaylist(self):
		item = self['liste'].getCurrent()[0]
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist"):
			open(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist"):
			writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist","a+")
			for rawData in writePlaylist.readlines():
				if item == eval(rawData):
					message = self.session.open(MessageBoxExt, _("Selection is already in local Playlist."), MessageBoxExt.TYPE_INFO, timeout=5)
					writePlaylist.close()
					return
			writePlaylist.write('%s\n' % str(item))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the local Playlist."), MessageBoxExt.TYPE_INFO, timeout=3)

	def loadPageData(self, data):
		nowdata = json.loads(data)
		if '_links' in nowdata:
			if 'next' in nowdata["_links"]:
				if 'href' in nowdata["_links"]['next']:
					page = re.search('\?page=(\d+)', str(nowdata["_links"]['next']['href']))
					if page:
						self['page'].setText(str(self.page) + '+')
			else:
				self['page'].setText(str(self.page))
		else:
			self['page'].setText(str(self.page))
		if '_embedded' in nowdata:
			if 'videos' in nowdata["_embedded"]:
				for node in nowdata["_embedded"]["videos"]:
					try:
						myid = str(node['id']) if 'id' in node else ""
						name = str(node['name']) if 'name' in node else ""
						title = str(node['title']) if 'title' in node else ""
						url = str(node['url']) if 'url' in node else ""
						artist_name = str(node['artist_name']) if 'artist_name' in node else ""
						artist_id = str(node['artist_id']) if 'artist_id' in node else ""
						artist_image = str(node['artist_image']) if 'artist_image' in node else ""
						tile_image_url = str(node['tile_image_url']) if 'tile_image_url' in node else ""
						videos_count = str(node['videos_count']) if 'videos_count' in node else ""
						share_url = str(node['share_url']) if 'share_url' in node else ""
						path = str(node['path']) if 'path' in node else ""
						mytype = str(node['type']) if 'type' in node else "video"
						if '_embedded' in node:
							if artist_id == '' and 'artist' in node['_embedded']:
								artist_id = str(node['_embedded']['artist']['id']) if "id" in node['_embedded']['artist'] else ""
						profile_name = ''
						if 'like' in node and node['like'] != None:
							like_id = str(node['like']['id']) if 'id' in node['like'] else ""
						else:
							like_id = ''
						listname = "%s: %s - %s" % (mytype.capitalize(),artist_name, title)
						self.filmliste.append((listname, mytype, name, title, myid, url, artist_name, artist_id, artist_image, tile_image_url, path, share_url, videos_count, profile_name, like_id))
					except:
						pass
			if 'tapes' in nowdata["_embedded"]:
				for node in nowdata["_embedded"]["tapes"]:
					try:
						myid = str(node['id']) if 'id' in node else ""
						name = str(node['name']) if 'name' in node else ""
						title = str(node['title']) if 'title' in node else ""
						url = str(node['url']) if 'url' in node else ""
						artist_name = str(node['artist_name']) if 'artist_name' in node else ""
						artist_id = str(node['artist_id']) if 'artist_id' in node else ""
						artist_image = str(node['artist_image']) if 'artist_image' in node else ""
						tile_image_url = str(node['tile_image_url']) if 'tile_image_url' in node else ""
						videos_count = node['videos_count'] if 'videos_count' in node else 0
						share_url = str(node['share_url']) if 'share_url' in node else ""
						path = str(node['path']) if 'path' in node else ""
						mytype = str(node['type']) if 'type' in node else "tape"
						if videos_count == 0 and'_embedded' in node and'videos' in node['_embedded']:
							for item in node['_embedded']['videos']:
								videos_count += 1
						artist_id = str(node['artist_id']) if 'artist_id' in node else ""
						if 'profile' in node and node['profile'] != None:
							profile_name = str(node['profile']['name'])
						else:
							profile_name = ''
						if 'like' in node and node['like'] != None:
							like_id = str(node['like']['id']) if 'id' in node['like'] else ""
						else:
							like_id = ''
						listname = "%s: %s from %s - %s Videos" % (mytype.capitalize(), name, profile_name.capitalize(), str(videos_count))
						self.filmliste.append((listname, mytype, name, title, myid, url, artist_name, artist_id, artist_image, tile_image_url, path, share_url, videos_count, profile_name, like_id))
					except:
						pass

			if 'artists' in nowdata["_embedded"]:
				for node in nowdata["_embedded"]["artists"]:
					try:
						myid = str(node['id']) if 'id' in node else ""
						name = str(node['name']) if 'name' in node else ""
						title = str(node['title']) if 'title' in node else ""
						url = str(node['url']) if 'url' in node else ""
						artist_name = str(node['artist_name']) if 'artist_name' in node else ""
						artist_id = str(node['artist_id']) if 'artist_id' in node else ""
						artist_image = str(node['artist_image']) if 'artist_image' in node else ""
						tile_image_url = str(node['tile_image_url']) if 'tile_image_url' in node else ""
						videos_count = str(node['videos_count']) if 'videos_count' in node else ""
						share_url = str(node['share_url']) if 'share_url' in node else ""
						path = str(node['path']) if 'path' in node else ""
						mytype = str(node['type']) if 'type' in node else "artist"
						profile_name = ''
						if 'like' in node and node['like'] != None:
							like_id = str(node['like']['id']) if 'id' in node['like'] else ""
						else:
							like_id = ''
						name = name.title()
						listname = "%s: %s" % (mytype.capitalize(), name)
						self.filmliste.append((listname, mytype , name, title, myid, url, artist_name, artist_id, artist_image, tile_image_url, path, share_url, videos_count, profile_name, like_id))
					except:
						pass

		if len(self.filmliste) == 0:
			self.filmliste.append((_("No songs found!"),'','','','','','','','','','','','',''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self['name'].setText(self.CatName)
		self.th_ThumbsQuery(self.filmliste, 0, 10, 9, None, None, 1, 1, mode=1)
		self.showInfos()

class tapetvGenreScreen(MPScreen, Tapetvhelper):

	def __init__(self, session):
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
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"yellow" : self.keyQuali
		}, -1)

		self.username = str(config.mediaportal.tapetv_username.value)
		self.password = str(config.mediaportal.tapetv_password.value)
		self.autologin = config.mediaportal.tapetv_autologin.value
		myQuali = myqualities[int(config.mediaportal.tapetv_maxquali.value)][0].upper()
		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre:")
		self['F3'] = Label(myQuali)
		self.keyLocked = True
		self.suchString = ''
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		if self.username != "tapetvUserName" and self.password != "tapetvPassword" and self.autologin:
			self.onLayoutFinish.append(self.Login)
		else:
			self.onLayoutFinish.append(self.layoutFinished)

	def Login(self):
		getPage(BASE_URL, agent=GLOB_AGENT, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.LoginData).addErrback(self.dataError)

	def LoginData(self, data):
		token = re.search('name="csrf-token" content="(.*?)"', data, re.S)
		if token:
			loginUrl = "%s/session.json" % BASE_URL
			loginData = {'session[email]': self.username, 'session[password]': self.password}
			getPage(loginUrl, agent=GLOB_AGENT, method='POST', postdata=urlencode(loginData), cookies=ck, headers={'X-CSRF-Token': token.group(1), 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.LoginInfo).addErrback(self.LoginError).addErrback(self.dataError)

	def LoginInfo(self, data):
		username = re.search('"username":"(.*?)"', data)
		if username:
			global LOGIN_NAME
			LOGIN_NAME = username.group(1)
			self['title'].setText(BASE_NAME + "   LoginUser: " + LOGIN_NAME)
		self.layoutFinished()

	def LoginError(self, error):
		myerror = error.getErrorMessage()
		if myerror:
			self['title'].setText(BASE_NAME + "   LoginUser: Login ERROR")
		self.layoutFinished
		raise error

	def layoutFinished(self):
		self.genreliste = []
		self.genreliste.append(("--- Search ---", "callSuchen"))
		self.genreliste.append(("Local Playlist", ""))
		self.genreliste.append(("New Videos", "/videos/newest"))
		self.genreliste.append(("Popular Videos", "/videos/popular"))
		self.genreliste.append(("Editorial Videos", "/videos/editorial"))
		self.genreliste.append(("New Tapes", "/tapes/newest"))
		self.genreliste.append(("Popular Tapes", "/tapes/popular"))
		self.genreliste.append(("Editorial Tapes", "/tapes/editorial"))
		if LOGIN_NAME:
			self.genreliste.append(("LoginUser liked Videos", "%s/%s/likes/videos" % (BASE_URL,LOGIN_NAME)))
			self.genreliste.append(("LoginUser liked Tapes", "%s/%s/likes/tapes" % (BASE_URL,LOGIN_NAME)))
			self.genreliste.append(("LoginUser created Tapes", "%s/%s/tapes" % (BASE_URL,LOGIN_NAME)))
		self.genreliste.append(("--- Plugin Settings ---", ""))
		if not LOGIN_NAME:
			self.genreliste.append(("UserLogin to Tape.tv", ""))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		url = "%s/explore/new" % BASE_URL
		getPage(url, agent=GLOB_AGENT, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		raw = re.search('data.explore_token = \'(.*?)\'', data, re.S)
		if raw:
			global EXPLORE_TOKEN
			EXPLORE_TOKEN = raw.group(1)
		else:
			message = self.session.open(MessageBoxExt, _("Error!"), MessageBoxExt.TYPE_INFO, timeout=3)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		if streamGenreName == "--- Search ---":
			self.suchen()
		elif streamGenreName == "Local Playlist":
			self.session.open(tapetvWatchlist)
		elif streamGenreName == "LoginUser liked Videos" or streamGenreName == "LoginUser created Tapes" or streamGenreName == "LoginUser liked Tapes":
			self.session.open(tapetvUserLikeScreen, self['liste'].getCurrent()[0][1], streamGenreName)
		elif streamGenreName == "--- Plugin Settings ---":
			self.session.open(tapetvSetupScreen)
		elif streamGenreName == "UserLogin to Tape.tv":
			self.Login()
		else:
			streamGenreLink = "https://api.tape.tv/internal/explore%s" % self['liste'].getCurrent()[0][1]
			self.session.open(tapetvFilmScreen, streamGenreLink, streamGenreName)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '%20')
			streamGenreLink = '%s' % (self.suchString)
			selfGenreName = "--- Search ---"
			self.session.open(tapetvFilmScreen, streamGenreLink, selfGenreName)

class tapetvSetupScreen(Screen, ConfigListScreenExt):

	def __init__(self, session):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/PluginUserDefault.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/PluginUserDefault.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		self['title'] = Label(BASE_NAME + " " + _("Setup"))
		self['F4'] = Label('')
		self.setTitle(BASE_NAME + " " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		self.list.append(getConfigListEntry(_("Username:"), config.mediaportal.tapetv_username))
		self.list.append(getConfigListEntry(_("Password:"), config.mediaportal.tapetv_password))
		self.list.append(getConfigListEntry(_("Autologin:"), config.mediaportal.tapetv_autologin))

		self["config"].setList(self.list)

		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"ok":		self.saveConfig,
			"cancel":	self.exit
		}, -1)

	def saveConfig(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close()

	def exit(self):
		self.close()

class tapetvFilmScreen(Tapetvhelper, MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, CatName):
		self.CatLink = CatLink
		self.CatName = CatName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Tapetvhelper.__init__(self,session)
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyAdd,
			"yellow" : self.keyQuali,
			"blue" : self.keytapetvAction,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		myQuali = myqualities[int(config.mediaportal.tapetv_maxquali.value)][0].upper()
		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre: %s" % (self.CatName))
		self['F2'] = Label(_("Add to Playlist"))
		self['F3'] = Label(myQuali)
		self['F4'] = Label("Action")

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 999

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if 'New' in self.CatName or 'Popular' in self.CatName or 'Editorial' in self.CatName:
			self['ContentTitle'].setText("Genre: %s" % self.CatName)
			url = '%s?page=%spage_size=20padding=0&jwt=%s' % (self.CatLink, self.page, EXPLORE_TOKEN)
		elif 'LoginUser' in self.CatName:
			self['ContentTitle'].setText("Genre: %s" % self.CatName)
			url = '%s?page=%spage_size=20padding=0' % (self.CatLink, self.page)
		else:
			self['ContentTitle'].setText("Search: %s" % self.CatName)
			url = "http://search.tape.tv/betamax/query?q=%s" % (self.CatLink)
		getPage(url, agent=GLOB_AGENT, cookies=ck, headers={'Accept':'application/json, text/javascript, */*; q=0.01', 'X-Requested-With':'XMLHttpRequest'}).addCallback(self.loadPageData).addErrback(self.dataError)

class tapetvTapesScreen(Tapetvhelper, MPScreen, ThumbsHelper):

	def __init__(self, session, CatData, CatName):
		self.CatData = CatData
		self.CatName = CatName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Tapetvhelper.__init__(self,session)
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyAdd,
			"yellow" : self.keyQuali,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		myQuali = myqualities[int(config.mediaportal.tapetv_maxquali.value)][0].upper()
		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre: %s" % (self.CatName))
		self['Page'] = Label(_("Page:"))
		self['F2'] = Label(_("Add to Playlist"))
		self['F3'] = Label(myQuali)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.lastpage = 999

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['page'].setText(str(self.page))
		self.filmliste = []
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		url = 'https://api.tape.tv/internal/explore/videos/%s/tapes?page=%s&page_size=20&padding=0&jwt=%s' % (self.CatData[4], self.page, EXPLORE_TOKEN)
		getPage(url, agent=GLOB_AGENT, cookies=ck, headers={'Accept':'application/json, text/javascript, */*; q=0.01', 'X-Requested-With':'XMLHttpRequest'}).addCallback(self.loadPageData).addErrback(self.dataError)

class tapetvTapesVideoScreen(Tapetvhelper, MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, CatName):
		self.CatLink = CatLink
		self.CatName = CatName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Tapetvhelper.__init__(self,session)
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyAdd,
			"yellow" : self.keyQuali,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		myQuali = myqualities[int(config.mediaportal.tapetv_maxquali.value)][0].upper()
		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre: %s" % (self.CatName))
		self['Page'] = Label(_("Page:"))
		self['F2'] = Label(_("Add to Playlist"))
		self['F3'] = Label(myQuali)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 1

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		self['ContentTitle'].setText("Genre: %s" % self.CatName)
		if self.CatLink[11] == '':
			url = "%s%s?page=%s&page_size=20&padding=0" % (BASE_URL, self.CatLink[10],self.page)
		else:
			url = "%s?page=%s&page_size=20&padding=0" % (self.CatLink[11],self.page)
		getPage(url, agent=GLOB_AGENT, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		parse = re.search('data.tape_data\s=\s(.*?\});', data, re.S)
		if parse:
			data = '{ "_embedded": %s}' % parse.group(1)
		self.loadPageData(data)

class tapetvArtistSongsScreen(Tapetvhelper, MPScreen, ThumbsHelper):

	def __init__(self, session, CatData, CatName):
		self.CatData = CatData
		self.CatName = CatName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Tapetvhelper.__init__(self,session)
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyAdd,
			"yellow" : self.keyQuali,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label(self.CatName)

		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)

		myQuali = myqualities[int(config.mediaportal.tapetv_maxquali.value)][0].upper()
		self['F2'] = Label(_("Add to Playlist"))
		self['F3'] = Label(myQuali)
		self['liste'] = self.ml
		self['Page'] = Label(_("Page:"))

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['page'].setText(str(self.page))
		self.filmliste = []
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		link = self.CatData[10]
		if not link:
			link = self.CatData[11]
		artistlink = re.search('(//.*?|)/(.+?)($|/)', link)
		if artistlink:
			url = '%s/%s/videos?page=%s&page_size=100&padding=0' % (BASE_URL, artistlink.group(2), self.page)
			getPage(url, agent=GLOB_AGENT, cookies=ck, headers={'Accept':'application/json, text/javascript, */*; q=0.01', 'X-Requested-With':'XMLHttpRequest'}).addCallback(self.loadData).addErrback(self.dataError)
		else:
			message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)

	def loadData(self, data):
		data = '{ "videos": %s}' % data
		data = '{ "_embedded": %s}' % data
		self.loadPageData(data)

class tapetvSimilarScreen(Tapetvhelper, MPScreen, ThumbsHelper):

	def __init__(self, session, CatData, CatName):
		self.CatData = CatData
		self.CatName = CatName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Tapetvhelper.__init__(self,session)
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyAdd,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label(self.CatName)

		self.page = 1
		self.lastpage = 999
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self['Page'] = Label(_("Page:"))
		self['F2'] = Label(_("Add to Playlist"))

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		if re.match('Similar Videos', self.CatName):
			url = 'https://api.tape.tv/internal/explore/videos/%s/similar?page=%s&page_size=20&padding=0&jwt=%s' % (self.CatData[0][4], self.page, EXPLORE_TOKEN)
		else:
			url = 'https://api.tape.tv/internal/explore/artists/%s/similar?page=%s&page_size=20&padding=0&jwt=%s' % (self.CatData[0][7], self.page, EXPLORE_TOKEN)
		getPage(url, agent=GLOB_AGENT, cookies=ck, headers={'Accept':'application/json, text/javascript, */*; q=0.01', 'X-Requested-With':'XMLHttpRequest'}).addCallback(self.loadPageData).addErrback(self.dataError)

class tapetvUserLikeScreen(Tapetvhelper, MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, CatName):
		self.CatLink = CatLink
		self.CatName = CatName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Tapetvhelper.__init__(self,session)
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyDel,
			"green" : self.keyAdd,
			"yellow" : self.keyQuali,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label(self.CatName)

		self.page = 1
		self.lastpage = 999
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)

		myQuali = myqualities[int(config.mediaportal.tapetv_maxquali.value)][0].upper()
		self['F1'] = Label(_("Delete"))
		self['F2'] = Label(_("Add to Playlist"))
		self['F3'] = Label(myQuali)
		self['liste'] = self.ml
		self['Page'] = Label(_("Page:"))

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['page'].setText(str(self.page))
		self.filmliste = []
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		url = '%s?page=%s&page_size=20&padding=0' % (self.CatLink, self.page)
		getPage(url, agent=GLOB_AGENT, cookies=ck, headers={'Accept':'application/json, text/javascript, */*; q=0.01', 'X-Requested-With':'XMLHttpRequest'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if self.CatName == "LoginUser liked Videos":
			data = '{ "videos": %s}' % data
		else:
			data = '{ "tapes": %s}' % data
		data = '{ "_embedded": %s}' % data
		self.loadPageData(data)

	def keyDel(self):
		if self.keyLocked:
			return
		myid = self['liste'].getCurrent()[0][14]
		if self['liste'].getCurrent()[0][1] == 'tape' and self['liste'].getCurrent()[0][13] == LOGIN_NAME:
			message = self.session.open(MessageBoxExt, _("LoginUser created Tapes can not be delete this way!"), MessageBoxExt.TYPE_INFO, timeout=5)
			return
		url = "%s/likes/%s" % (BASE_URL, myid)
		header = {
				'Accept': 'application/json',
				'Accept-Language': 'en-US,en;q=0.5',
				'Accept-Encoding': 'gzip, deflate',
				'Content-Type': 'application/json',
				'X-Requested-With': 'XMLHttpRequest',
				}
		getPage(url, agent=GLOB_AGENT, method='DELETE', cookies=ck, headers=header).addCallback(self.delRemotePlaylist).addErrback(self.delLoginUserError).addErrback(self.dataError)

	def delLoginUserError(self, error):
		myerror = error.getErrorMessage()
		if myerror == '204 No Content':
			message = self.session.open(MessageBoxExt, _("Selection was deleted from LoginUser Playlist."), MessageBoxExt.TYPE_INFO, timeout=5)
			self.loadPage()
		else:
			message = self.session.open(MessageBoxExt, _("delete Selection ERROR in LoginUser Playlist."), MessageBoxExt.TYPE_INFO, timeout=5)
			raise error

	def delRemotePlaylist(self, data):
		pass

class tapetvWatchlist(Tapetvhelper, MPScreen, ThumbsHelper):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Tapetvhelper.__init__(self,session)
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.mykeyShowThumb,
			"up" : self.mykeyUp,
			"down" : self.mykeyDown,
			"right" : self.mykeyRight,
			"left" : self.mykeyLeft,
			"ok" : self.mykeyOK,
			"cancel": self.keyCancel,
			"red" : self.keyDel,
			"green" : self.keyMove,
			"yellow" : self.keyQuali,
			"blue" : self.mykeytapetvAction
		}, -1)

		myQuali = myqualities[int(config.mediaportal.tapetv_maxquali.value)][0].upper()
		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Local Playlist")
		self['F1'] = Label(_("Delete"))
		self['F2'] = Label(_("Move"))
		self['F3'] = Label(myQuali)
		self['F4'] = Label("Action")

		self.CatName = 'Local Playlist'
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.moveMode = False

		self.onLayoutFinish.append(self.loadPlaylist)

	def loadPlaylist(self):
		self.filmliste = []
		if fileExists(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist"):
			readStations = open(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(Title, Url, Image, Artist) = data[0]
					listname = "old Listformat: %s" % (Title)
					ArtistTitel = Title.split(" - ")
					Artist = ArtistTitel[0]
					if len(ArtistTitel) > 1:
						Title = ArtistTitel[1]
					self.filmliste.append((listname, "video" , '', Title, '', Url, Artist, '', '', Image, Url, '', '', ''))
				elif rawData:
					self.filmliste.append(eval(rawData))
			print "Load Watchlist.."
			if len(self.filmliste) == 0:
				self.filmliste.append((_("No songs found!"),'','','','','','','','','','','','',''))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			readStations.close()
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 10, 9, None, None, 1, 1, mode=1)
			self.showInfos()

	def mykeyShowThumb(self):
		if not self.moveMode:
			self.keyShowThumb()

	def mykeyUp(self):
		if self.keyLocked:
			return
		if not self.moveMode:
			self.keyUp()
		else:
			pos = self['liste'].getSelectedIndex()
			if pos > 0:
				self.filmliste = self.filmliste[:pos-1]+self.filmliste[pos:pos+1]+self.filmliste[pos-1:pos]+self.filmliste[pos+1:]
				self.ml.setList(map(self._defaultlistleft, self.filmliste))
				self['liste'].up()

	def mykeyDown(self):
		if self.keyLocked:
			return
		if not self.moveMode:
			self.keyDown()
		else:
			pos = self['liste'].getSelectedIndex()
			if pos+1 < len(self.filmliste):
				self.filmliste = self.filmliste[:pos]+self.filmliste[pos+1:pos+2]+self.filmliste[pos:pos+1]+self.filmliste[pos+2:]
				self.ml.setList(map(self._defaultlistleft, self.filmliste))
				self['liste'].down()

	def mykeyRight(self):
		if not self.moveMode:
			self.keyRight()

	def mykeyLeft(self):
		if not self.moveMode:
			self.keyLeft()

	def mykeyOK(self):
		if not self.moveMode:
			self.keyOK()
		else:
			self.keyMove()

	def keyDel(self):
		if self.keyLocked and not self.moveMode:
			return
		readpos = 0
		pos = self['liste'].getSelectedIndex()
		writeTmp = open(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist.tmp","w")
		if fileExists(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist"):
			readStations = open(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist","r")
			for rawData in readStations.readlines():
				if pos != readpos:
					writeTmp.write(rawData)
				else:
					pass
				readpos +=1
			readStations.close()
			writeTmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist.tmp", config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist")
			self.loadPlaylist()

	def keyMove(self):
		if self.keyLocked:
			return
		if not self.moveMode:
			self.moveMode = True
			self['F1'].setText('')
			self['F2'].setText(_('Finish'))
			self['F4'].setText('')
		else:
			self.moveMode = False
			self['F1'].setText(_("Delete"))
			self['F2'].setText(_("Move"))
			self['F4'].setText(_("Action"))
			writeTmp = open(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist.tmp","w")
			for rawData in self.filmliste:
				writeTmp.write('%s\n' % str(rawData))
			writeTmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist.tmp", config.mediaportal.watchlistpath.value+"mp_tapetv_watchlist")
			self.loadPlaylist()

	def mykeytapetvAction(self):
		if not self.moveMode:
			self.keytapetvAction()
			self.loadPlaylist()

class tapeTVListPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx=0, playAll=True, listTitle=None):
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=playAll, listTitle=listTitle, ltype='tapetv')

	def getVideo(self):
		title = "%s - %s" % (self.playList[self.playIdx][6],self.playList[self.playIdx][3])
		url = self.playList[self.playIdx][10]
		if not url:
			url = self.playList[self.playIdx][11]
		if not re.match('http', url):
			url = "%s%s" % (BASE_URL, url)
		imgurl = self.playList[self.playIdx][9]
		tapetvLink(self.session).getLink(self.playStream, self.dataError, title, url, imgurl)

class tapetvLink:

	def __init__(self, session):
		self.session = session
		self._callback = None

	def getLink(self, cb_play, cb_err, title, url, imgurl):
		self._callback = cb_play
		self._errback = cb_err
		self.title = title
		self.imgurl = imgurl
		getPage(url, agent=GLOB_AGENT, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self._getJSLink).addErrback(self._errback)

	def _getJSLink(self, data):
		raw = re.search('<script src="(https://www.tape.tv/assets/tape.*?)"', data, re.S)
		videoid = re.search('data\.video_data = \{"id":(.*?),',data, re.S)
		if config.mediaportal.tapetv_maxquali.value == '5' and videoid:
			if config.mediaportal.use_hls_proxy.value:
				videourl = 'https://streaming-url.tape.tv/v1/hls_playlist/%s.m3u8' % str(videoid.group(1))
				self._callback(self.title, videourl, imgurl=self.imgurl)
			else:
				message = self.session.open(MessageBoxExt, _("If you want to play this stream, you have to activate the HLS-Player in the MP-Setup"), MessageBoxExt.TYPE_INFO, timeout=5)
		elif raw and videoid:
				getPage(raw.group(1), agent=GLOB_AGENT, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self._getToken, videoid.group(1)).addErrback(self._errback)
		else:
			message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)

	def _getToken(self, data, videoid):
		raw = re.search('t\.authToken="(.*?)"', data, re.S)
		if not raw:
			raw = re.search('API_AUTH_TOKEN="(.*?)"', data, re.S)
		if raw:
			url = "http://streaming-url.tape.tv/v1/rtmp/%s" % videoid
			token = raw.group(1)
			getPage(url, agent=GLOB_AGENT, cookies=ck, headers={'Authorization': 'Token ' + token, 'Referer': BASE_URL+"/", 'Origin': 'BASE_URL'}).addCallback(self._getVideoLink).addErrback(self._errback)
		else:
			message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)

	def _getVideoLink(self, data):
		raw = re.search('"token":"(.*?)"', data, re.S)
		if raw:
			rtmp_url = "rtmpe://cp68509.edgefcs.net:1935/ondemand?ovpfv=2.1.6&auth=%s&aifp=v001" % raw.group(1)
			rtmp_app = "ondemand?ovpfv=2.1.6&auth=%s&aifp=v001" % raw.group(1)
			rtmp_swfVfy = "%s/tapePlayer.swf" % BASE_URL
			raw = re.findall('"http://video.tape.tv/play/(.*?)"', data, re.S)
			qualities = re.findall('"qualities":\["(.*?)"\],"', data, re.S)
			if raw and qualities:
				qualities = qualities[0].split('","')
				for getquality in range(int(config.mediaportal.tapetv_maxquali.value), len(myqualities)):
					for x in range(len(qualities)):
						if qualities[x] == myqualities[getquality][0]:
							break
						else:
							continue
						break
					else:
						continue
					break
				rtmp_playpath = "mp4:tapetv/play/%s" % raw[x]
				videourl = "%s app=%s swfVfy=%s playpath=%s" % (rtmp_url, rtmp_app, rtmp_swfVfy, rtmp_playpath)
				self._callback(self.title, videourl, imgurl=self.imgurl)
				return
		message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)