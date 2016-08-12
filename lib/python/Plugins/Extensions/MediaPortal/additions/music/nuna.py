# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class nunaGenreScreen(MPScreen):

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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("nuna.tv")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [('Musikrichtung',"Musikrichtung"),
							('Kuenstler',"nstler")]

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		nunaName = self['liste'].getCurrent()[0][0]
		nunaUrl = self['liste'].getCurrent()[0][1]

		print nunaName, nunaUrl
		self.session.open(nunaArtistListeScreen, nunaName, nunaUrl)

class nunaArtistListeScreen(MPScreen):

	def __init__(self, session, genreName, genreLink):
		self.genreLink = genreLink
		self.genreName = genreName
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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("nuna.tv")
		self['ContentTitle'] = Label("Genre: %s" % self.genreName)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "http://www.nuna.tv/"

		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		print "drin"
		if re.match('.*?Musikrichtung', self.genreLink, re.S):
			parse = "Musikrichtung"
		else:
			parse = "nstler"

		raw = re.search('<select\sdata-placeholder=".*?'+parse+'"\sclass="chzn-select">(.*)</select>', data, re.S)
		if raw:
			self.filmliste = []
			genre = re.findall('<option\svalue="(/videos.js.*?)"\s{0,2}>(.*?)</option', raw.group(1), re.S|re.I)
			if genre:
				for link,title in genre:
					url = "http://www.nuna.tv%s" % link
					self.filmliste.append((decodeHtml(title),url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		nunaName = self['liste'].getCurrent()[0][0]
		nunaUrl = self['liste'].getCurrent()[0][1]

		print nunaName, nunaUrl
		self.session.open(nunaMusicListeScreen, nunaName, nunaUrl)

class nunaMusicListeScreen(MPScreen):

	def __init__(self, session, genreName, genreLink):
		self.genreLink = genreLink
		self.genreName = genreName
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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("nuna.tv")
		self['ContentTitle'] = Label("Genre: %s" % self.genreName)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		print self.genreLink
		getPage(self.genreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		print "drin"

		vids = re.findall('li\s{0,1}>\s{0,1}<a\shref="(.*?)".*?<img\salt="(.*?)"\ssrc="(.*?)"\s/>', data, re.S)
		if vids:
			self.filmliste = []
			for (link,title,image) in vids:
				url = "http://www.nuna.tv%s" % link
				self.filmliste.append((decodeHtml(title),url,image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		self.nunaName = self['liste'].getCurrent()[0][0]
		nunaUrl = self['liste'].getCurrent()[0][1]
		nunaImage = self['liste'].getCurrent()[0][2]
		idx = self['liste'].getSelectedIndex()

		print idx, self.nunaName, nunaUrl, nunaImage
		self.session.open(NunaPlayer, self.filmliste, int(idx) , True, None)

class NunaPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx=0, playAll=True, listTitle=None):
		print "NunaPlayer:"

		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=playAll, listTitle=listTitle)

	def getVideo(self):
		self.nunaName = self.playList[self.playIdx][0]
		nunaUrl = self.playList[self.playIdx][1]
		print self.nunaName, nunaUrl
		getPage(nunaUrl).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		stream_url = re.findall('data-src="(.*?)"\sdata-title', data)
		if stream_url:
			print stream_url
			self.playStream(self.nunaName, stream_url[0])