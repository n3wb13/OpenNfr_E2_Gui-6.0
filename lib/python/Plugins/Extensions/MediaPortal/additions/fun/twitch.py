# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

headers = {'Accept': 'application/vnd.twitchtv.v2+json', 'Client-ID': '6r2dhbo9ek6mm1gab2snj0navo4sgqy'}
limit = 10

class twitchGames(MPScreen):

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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("Twitch")
		self['ContentTitle'] = Label("Games:")

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 0
		self.lastpage = 999

		self.gameList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.gameList = []
		url = "https://api.twitch.tv/kraken/games/top?limit=" + str(limit) + "&offset=" + str(self.page * limit)
		getPage(url, headers=headers).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self['page'].setText(str(self.page+1))
		topGamesJson = json.loads(data)
		for node in topGamesJson["top"]:
			self.gameList.append((str(node["game"]["name"]), str(node["game"]["box"]["large"])));
		self.ml.moveToIndex(0)
		self.ml.setList(map(self._defaultlistleft, self.gameList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][1]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked or self['liste'].getCurrent() == None:
			return
		self.session.open(twitchChannels, self['liste'].getCurrent()[0][0])

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 1:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.keyLocked:
			return
		if self.page+1 < self.lastpage:
			self.page += 1
			self.loadPage()

class twitchChannels(MPScreen):

	def __init__(self, session, gameName):
		self.gameName = gameName
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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("Twitch")
		self['ContentTitle'] = Label("Channels:")

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 0
		self.lastpage = 999

		self.channelList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.channelList = []
		url = "https://api.twitch.tv/kraken/search/streams?q=" + self.gameName.replace(" ", "%20") + "&limit=" + str(limit) + "&offset=" + str(self.page * limit)
		getPage(url, headers=headers).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self['page'].setText(str(self.page+1))
		topChannelsJson = json.loads(data)
		for node in topChannelsJson["streams"]:
			self.channelList.append((str(node["channel"]["display_name"]), str(node["channel"]["name"]), str(node["channel"]["banner"])))
		self.ml.moveToIndex(0)
		self.ml.setList(map(self._defaultlistleft, self.channelList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked or self['liste'].getCurrent() == None:
			return
		self.channelName = self['liste'].getCurrent()[0][1]
		url = "http://api.twitch.tv/api/channels/" + self.channelName + "/access_token"
		getPage(url, headers=headers).addCallback(self.parseAccessToken).addErrback(self.dataError)

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 1:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.keyLocked:
			return
		if self.page+1 < self.lastpage:
			self.page += 1
			self.loadPage()

	def parseAccessToken(self, data):
		token = json.loads(data)
		url = "http://usher.twitch.tv/api/channel/hls/{channel}.m3u8?player=twitchweb&&token={token}&sig={sig}&allow_audio_only=true&allow_source=true&type=any&p={random}'"
		url = url.replace("{random}", str(random.randint(1000000, 9999999)))
		url = url.replace("{sig}", str(token["sig"]))
		url = url.replace("{token}", str(token["token"]))
		url = url.replace("{channel}", str(self.channelName))
		getPage(url, headers={}).addCallback(self.parseM3U).addErrback(self.dataError)

	def parseM3U(self, data):
		self.session.open(twitchStreamQuality, data, self.channelName, self.gameName)

class twitchStreamQuality(MPScreen):

	def __init__(self, session, m3u8, channel, game):
		self.m3u8 = str(m3u8)
		self.channel = channel
		self.game = game
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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Twitch")
		self['ContentTitle'] = Label("Quality:")

		self.qualityList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.parseData)

	def parseData(self):
		result = re.findall('NAME="(.*?)".*?(http://.*?)\n', self.m3u8, re.S)
		for (quality, url) in result:
			if quality != "Mobile":
				self.qualityList.append((quality, url));
		self.ml.setList(map(self._defaultlistleft, self.qualityList))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked or self['liste'].getCurrent() == None:
			return
		url = self['liste'].getCurrent()[0][1]
		title = self.game + " - " + self.channel
		self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='twitch')