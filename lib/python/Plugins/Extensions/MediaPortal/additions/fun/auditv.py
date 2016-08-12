# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class auditvGenreScreen(MPScreen):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Audi.tv")
		self['ContentTitle'] = Label("Kanal Auswahl")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Deutsch", "http://tv.audi.de/rss/feed/podcast_de.xml"))
		self.genreliste.append(("English", "http://tv.audi.de/rss/feed/podcast_en.xml"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(auditvFilmScreen, streamGenreLink, streamGenreName)

class auditvFilmScreen(MPScreen):

	def __init__(self, session, phCatLink, catName):
		self.phCatLink = phCatLink
		self.catName = catName
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Titel Auswahl")
		self['ContentTitle'] = Label("Genre: %s" % self.catName)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(self.catName)
		self.filmliste = []
		url = self.phCatLink
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		phMovies = re.findall('<item>.*?<title>(.*?)</title>.*?<link>.*?video/(.*?)</link>.*?<description>(.*?)</description>.*?</item>', data, re.S)
		if phMovies:
			for (Title, Id, Desc) in phMovies:
				if Desc != "":
					title = Title + " - " + Desc
				else:
					title = Title
				self.filmliste.append((decodeHtml(title), Id))
		else:
			self.filmliste.append(('Audi.tv is currently not available.', None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Id = self['liste'].getCurrent()[0][1]
		url = 'http://tv.audi.com/binaries/asset/videodownload/%s/asset/0' % Id
		title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='auditv')