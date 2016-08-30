# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class watchseriesGenreScreen(MPScreen):

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

		self.keyLocked = True
		self['title'] = Label("watchseries")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [('Series',"https://watchseriesfree.to/letters/"),
							('Newest Episodes Added',"https://watchseriesfree.to/latest"),
							('Popular Episodes Added This Week',"https://watchseriesfree.to/new"),
							('TV Schedule',"https://watchseriesfree.to/tvschedule/-1")]

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		if streamGenreName == "Series":
			self.session.open(watchseriesSeriesLetterScreen, streamGenreLink, streamGenreName)
		else:
			self.session.open(watchseriesNewSeriesScreen, streamGenreLink, streamGenreName)

class watchseriesNewSeriesScreen(MPScreen):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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

		self.keyLocked = True
		self['title'] = Label("watchseries")
		self['ContentTitle'] = Label("%s:" % self.streamGenreName)

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		twAgentGetPage(self.streamGenreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		eps = re.findall('class="uFollow.*?title=".*?"\shref="(/episode/.*?)"><span.*?</span>(.*?)</a></li>', data, re.S)
		if eps:
			for link,title in eps:
				title = title.replace('Seas. ','- S').replace('Ep. ','E')
				url = "https://watchseriesfree.to%s" % link
				self.genreliste.append((title, url))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.keyLocked = False

	def keyOK(self):
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(watchseriesStreamListeScreen, streamGenreLink, streamGenreName)

class watchseriesSeriesLetterScreen(MPScreen):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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

		self.keyLocked = True
		self['title'] = Label("watchseries")
		self['ContentTitle'] = Label("Letter:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		abc = ["09","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
		for letter in abc:
			url = "https://watchseriesfree.to/letters/%s" % letter
			self.genreliste.append((letter, url))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(watchseriesSeriesScreen, streamGenreLink, streamGenreName)

class watchseriesSeriesScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("watchseries")
		self['ContentTitle'] = Label("Letter - %s:" % self.streamGenreName)


		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		twAgentGetPage(self.streamGenreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		series = re.findall('<li><a title="(.*?)" href="((?:/serie)?/.*?)">.*?</li>', data, re.S)
		if series:
			self.filmliste = []
			for (title,link) in series:
				url = "https://watchseriesfree.to%s" % link
				self.filmliste.append((decodeHtml(title),url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, None, None, '<div class="show-summary".*?<img src="(.*?)".*?Description', 1, 1, maxtoken=3)
			self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		twAgentGetPage(url).addCallback(self.getDetails).addErrback(self.dataError)

	def getDetails(self, data):
		image = re.findall('<div class="show-summary".*?<img src="(.*?)".*?Description', data, re.S)
		details = re.findall('Description :</b>\s(.*?)<br>', data, re.S)
		handlung = ""
		if details:
				handlung = re.sub(r'<.*?>', '', details[0])
		if image:
				image = image[0]
		CoverHelper(self['coverArt']).getCover(image)
		self['handlung'].setText(decodeHtml(handlung))

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(watchseriesEpisodeListeScreen, streamLink, streamName)

class watchseriesEpisodeListeScreen(MPScreen):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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

		self['title'] = Label("watchseries")
		self['ContentTitle'] = Label("Episodes:")
		self['name'] = Label(self.streamGenreName)


		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		twAgentGetPage(self.streamGenreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('<ul class="listings(.*)class="sp-leader-bottom">', data, re.S)
		if parse:
			eps = re.findall('href="(/episode/.*?)">.*?>(Episode\s\d+|)(&nbsp;){0,10}(.*?)<', parse.group(1), re.S)
			if eps:
				self.filmliste = []
				for (url, dummy, dummy, title) in eps:
					epinfo = re.findall('_s(\d+)_e(\d+).html', url)
					if epinfo:
						(season, episode) = epinfo[0]
						if int(season) < 10:
							season = "S0"+str(season)
						else:
							season = "S"+str(season)
						if int(episode) < 10:
							episode = "E0"+str(episode)
						else:
							episode = "E"+str(episode)
						episode = "%s%s - %s" % (season, episode, title)
						url = "https://watchseriesfree.to%s" % url
						self.filmliste.append((decodeHtml(episode),url))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No shows found!"), ''))
		self.filmliste = list(set(self.filmliste))
		self.filmliste.sort()
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(watchseriesStreamListeScreen, streamLink, streamName)

class watchseriesStreamListeScreen(MPScreen):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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

		self['title'] = Label("watchseries")
		self['ContentTitle'] = Label("Streams:")


		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_("Please wait..."))
		twAgentGetPage(self.streamGenreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if re.match('.*?Sorry we do not have any links for this right now', data, re.S|re.I):
			self.filmliste = []
			self.filmliste.append(("There are no links available for this episode", None))
		else:
			streams = re.findall('<tr\s{0,1}><td.*?><span.*?>(.*?)<\/span><\/td><td\s{0,1}>.<a\starget="_blank"\shref="(.*?)"', data, re.S)
			if streams:
				self.filmliste = []
				for (hostername,url) in streams:
					if isSupportedHoster(hostername, True):
						url = "https://watchseriesfree.to%s" % url
						self.filmliste.append((decodeHtml(hostername),url))
				if len(self.filmliste) == 0:
					self.filmliste.append(("No supported streams found.", None))
				else:
					self.keyLocked = False
			else:
				self.filmliste.append(("Wrong parsing...", None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self['name'].setText(self.streamGenreName)

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		twAgentGetPage(streamLink).addCallback(self.getLink).addErrback(self.dataError)

	def getLink(self, data):
		link = re.findall('<a.*?class="myButton.*?href="(.*?)">Click\sHere\sto\sPlay<\/a>', data, re.S)
		if link:
			get_stream_link(self.session).check_link(link[0], self.got_link)
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def got_link(self, stream_url):
		self.session.open(SimplePlayer, [(self.streamGenreName, stream_url)], showPlaylist=False, ltype='watchseries')