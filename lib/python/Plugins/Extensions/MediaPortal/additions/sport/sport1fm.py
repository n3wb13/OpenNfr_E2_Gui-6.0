# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class sport1fmGenreScreen(MPScreen):

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
		self['title'] = Label("Sport1.fm")
		self['ContentTitle'] = Label("Sendungen:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://www.sport1.fm/data/live.json"
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		info = re.findall('"resource":"(.*?)".*?"adcode":".*?".*?"resourceid":.*?."type":"stream"."tstamp":.*?."stream.start":(.*?)."stream.end":(.*?).".*?game.home.name":"(.*?)"."game.guest.iconid":.*?"game.guest.name":"(.*?)"."game.status":"(.*?)"."game.minute":(.*?)."game.scores.half":".*?"."game.scores.current":"(.*?)"', data, re.S)
		if info:
			self.genreliste = []
			for (stream, start, end, teamA, teamB, status, running, score) in info:
				match = "%s - %s" % (teamA, teamB)
				status = "%s: %s" % (status, running)
				self.genreliste.append((decodeHtml(match), stream, status, score))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False
		else:
			self.genreliste.append((_("Currently no streams available"), None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		if self.keyLocked:
			return
		sport1fmName = self['liste'].getCurrent()[0][0]
		sport1fmUrl = self['liste'].getCurrent()[0][1]
		self.session.open(sport1fmListeScreen, sport1fmName, sport1fmUrl)

class sport1fmListeScreen(MPScreen):

	def __init__(self, session, sport1fmName, sport1fmUrl):
		self.sport1fmName = sport1fmName
		self.sport1fmUrl = sport1fmUrl

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

		self.keyLocked = True
		self['title'] = Label("Sport1.fm")
		self['ContentTitle'] = Label("Streams:")

		self.streamliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://playerservices.streamtheworld.com/api/livestream?version=1.5&mount=%sAAC" % self.sport1fmUrl
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.streamliste = []
		streams = re.findall('<ip>(.*?)</ip>', data, re.S)
		mount = re.findall('<mount>(.*?)</mount>', data, re.S)
		if streams and mount:
			for stream in streams:
				stream = "http://%s/%s" % (stream, mount[0])
				self.streamliste.append((stream, None))
			self.ml.setList(map(self._defaultlistleft, self.streamliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		stream_url = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(self.sport1fmName, stream_url)], showPlaylist=False, ltype='sport1fm')