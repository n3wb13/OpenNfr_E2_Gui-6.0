# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class nhlGenreScreen(MPScreen):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("NHL.com")
		self['ContentTitle'] = Label(_("Genre Selection"))
		self['name'] = Label(_("Selection:"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		lt = localtime()
		month = strftime("%m", lt)
		if month[:1] == "0":
			month = month[1:]
		url = "http://video.nhl.com/videocenter/highlights?xml=0" #% str(month)
		self.genreliste.append(("Last Highlights", url))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(nhlFilmListeScreen, Link)

class nhlFilmListeScreen(MPScreen):

	def __init__(self, session, Link):
		self.Link = Link

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
		}, -1)

		self['title'] = Label("NHL.com")
		self['ContentTitle'] = Label("Titel Auswahl")
		self['name'] = Label(_("Selection:"))
		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1 / 1")

		self.keyLocked = True
		self.filmliste = []
		self.keckse = {}
		self.page = 1
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.Link, agent=std_headers).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		videos = re.findall('<game-date>(.*?)</game-date>.*?<name>(.*?)</name>.*?<city>(.*?)</city>.*?<goals>(.*?)</goals>.*?<name>(.*?)</name>.*?<city>(.*?)</city>.*?<goals>(.*?)</goals>.*?<alt-video-clip>(.*?)</alt-video-clip>.*?<video-clip-thumbnail>(.*?)</video-clip-thumbnail>', data, re.S)
		if videos:
			self.filmliste = []
			for (date, name1, city1, score1, name2, city2, score2, stream, image) in videos:
				vs = "%s - %s %s vs. %s %s - %s:%s" % (date, name1, city1,  name2, city2, score1, score2)
				self.filmliste.append((decodeHtml(vs), stream, image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		Name = self['liste'].getCurrent()[0][0]
		self['name'].setText(Name)
		Pic = self['liste'].getCurrent()[0][2].replace('<![CDATA[','').replace(']]>','')
		CoverHelper(self['coverArt']).getCover(Pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1].replace('<![CDATA[','').replace(']]>','')
		self.session.open(SimplePlayer, [(Name, Link)], showPlaylist=False, ltype='nhl')