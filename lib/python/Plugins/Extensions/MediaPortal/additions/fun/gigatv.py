# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class gigatvGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("GIGA.de")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Alle Videos", "http://www.giga.de/tv/alle-videos/", None))
		self.genreliste.append(("G-Log","http://www.giga.de/games/videos/g-log/", "http://media2.giga.de/2012/12/g-log2-150x95.jpg"))
		self.genreliste.append(("GIGA Android/Apple","http://www.giga.de/android/videos-podcasts/", None))
		self.genreliste.append(("GIGA Failplays","http://www.giga.de/games/channel/giga-failplays/", "http://media2.giga.de/2013/04/failplay-teaser-150x95.jpg"))
		self.genreliste.append(("GIGA Gameplay","http://www.giga.de/games/videos/giga-gameplay/", "http://media2.giga.de/2012/12/gameplay2-150x95.jpg"))
		self.genreliste.append(("GIGA Live","http://www.giga.de/games/videos/giga-live/", "http://media2.giga.de/2012/12/gigatvlive-teaser-150x95.jpg"))
		self.genreliste.append(("GIGA Top Montag","http://www.giga.de/mac/channel/giga-top-montag/", "http://media2.giga.de/2013/04/topmontag-teaser-150x95.jpg"))
		self.genreliste.append(("Jonas liest","http://www.giga.de/games/videos/jonas-liest/", "http://media2.giga.de/2012/12/jonasliest-teaser-150x95.jpg"))
		self.genreliste.append(("NostalGIGA","http://www.giga.de/games/videos/nostalgiga/", "http://media2.giga.de/2012/12/nostalgiga-150x95.jpg"))
		#self.genreliste.append(("Radio GIGA","http://www.giga.de/games/videos/radio-giga/", "http://media2.giga.de/2012/12/radiogiga-150x95.jpg"))
		self.genreliste.append(("Specials","http://www.giga.de/games/videos/specials/", None))
		self.genreliste.append(("Top 100 Filme","http://www.giga.de/games/videos/top-100-filme/", "http://media2.giga.de/2012/12/top100filme-teaser-150x95.jpg"))
		self.genreliste.append(("Top 100 Games","http://www.giga.de/games/videos/top-100-games/", "http://media2.giga.de/2012/12/top100spiele-teaser-150x95.jpg"))
		self.genreliste.append(("Top 100 Momente","http://www.giga.de/android/channel/top-100-spielemomente/", "http://media2.giga.de/2013/04/top100spielemomente-teaser-150x95.jpg"))
		#self.genreliste.append(("Top 100 Serien","http://www.giga.de/games/videos/top-100-tv-serien/", "http://media2.giga.de/2012/12/top100serien-teaser-150x95.jpg"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.genreliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(gigatvFilmScreen, streamGenreLink, Name)

class gigatvFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, Name):
		self.CatLink = CatLink
		self.Name = Name
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("GIGA.de")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self['title'].setText('GIGA.de')

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if self.page > 1:
			url = "%s%s/" % (self.CatLink, str(self.page))
		else:
			url = "%s" % (self.CatLink)
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '<ul\sclass="sequences\shlist">(.*?)</ul>')
		Movies = re.findall('embed\/(\d+).*?<article\sclass=.*?smallimg">.*?hgroup>.*?<a\shref=".*?>(.*?)</a>.*?src="(http://www.giga.de/.*?)"\salt=', data, re.S|re.I)
		if Movies:
			for (ID, Title, Image) in Movies:
				Title = Title.replace('<b>','').replace('</b>','')
				self.filmliste.append((decodeHtml(Title), Image, ID))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][1]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		ID = self['liste'].getCurrent()[0][2]
		url = "http://videos.giga.de/embed/%s" % ID
		self.keyLocked = True
		getPage(url).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('file:\s"(http://lx\d+.spieletips.de/\d+/\d+p.mp4)"', data, re.S)
		if videoPage:
			url = videoPage[0]
			self.play(url)
		else:
			message = self.session.open(MessageBoxExt, _("This video is not available."), MessageBoxExt.TYPE_INFO, timeout=5)
		self.keyLocked = False

	def play(self,file):
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Title, file)], showPlaylist=False, ltype='giga')