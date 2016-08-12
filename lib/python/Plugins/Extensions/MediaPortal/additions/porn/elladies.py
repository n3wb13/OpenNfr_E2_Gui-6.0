# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

BASE_URL = 'http://search.el-ladies.com'

class elladiesGenreScreen(MPScreen):

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

		self['title'] = Label("El-Ladies.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		getPage(BASE_URL).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('<select id="selSearchNiche"(.*?)</select>', data, re.S)
		if parse:
			genre = re.findall('<option value="(\d{0,2})">(.*?)<', parse.group(1), re.S)
			if genre:
				for genrenr, genrename in genre:
					if not re.match('(Bizarre|Gay|Men|Piss|Scat)', genrename):
						self.genreliste.append((genrename.replace('&amp;', '&'), genrenr))
		self.genreliste.insert(0, ("--- Search ---", None))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		if streamGenreName == "--- Search ---":
			self.suchen()
		else:
			streamSearchString = ""
			streamGenreID = self['liste'].getCurrent()[0][1]
			self.session.open(elladiesFilmScreen, streamSearchString, streamGenreName, streamGenreID)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			streamGenreName = self['liste'].getCurrent()[0][0]
			self.suchString = callback.replace(' ', '+')
			streamSearchString = self.suchString
			streamGenreID = ""
			self.session.open(elladiesFilmScreen, streamSearchString, streamGenreName, streamGenreID)

class elladiesFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, SearchString, streamGenreName, CatID):
		self.SearchString = SearchString
		self.CatID = CatID
		self.Name = streamGenreName
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
			"yellow" : self.keyHD,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("El-Ladies.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label("HD")

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.suchString = ''
		self.HD = 0
		self.HDText = ['Off','On']
		self['title'].setText('El-Ladies.com (HD: ' + self.HDText[self.HD] + ')')

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = '%s/?search=%s&fun=0&niche=%s&pnum=%s&hd=%s' % (BASE_URL, self.SearchString, self.CatID, str(self.page), self.HD)
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pageNav">(.*?)</div>')
		Movies = re.findall('<a\shref="http://just.eroprofile.com/play/(.*?)".*?<img\ssrc="(.*?)".*?<div>(.*?)</div>', data, re.S)
		if Movies:
			for (ID, Image, Cat) in Movies:
				Title = decodeHtml(Cat) + ' - ' + ID
				Image = Image.replace('&amp;','&')
				self.filmliste.append((Title, ID, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)
		url = self['liste'].getCurrent()[0][1]
		url = 'http://just.eroprofile.com/play/' + url
		getPage(url).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		title = re.search('<title>(.*?)</title>', data, re.S)
		self['name'].setText(decodeHtml(title.group(1)))
		handlung = re.search('name="description"\scontent="(.*?)"\s/>', data, re.S)
		self['handlung'].setText(decodeHtml(handlung.group(1)))

	def keyHD(self):
		if self.HD == 1:
			self.HD = 0
		else:
			self.HD = 1
		self['title'].setText('El-Ladies.com (HD: ' + self.HDText[self.HD] + ')')
		self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		if Title == "--- Search ---":
			self.suchen()
		else:
			url = self['liste'].getCurrent()[0][1]
			self.keyLocked = True
			url = 'http://just.eroprofile.com/play/' + url
			getPage(url).addCallback(self.getVideoPage).addErrback(self.dataError)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			self.SearchString = self.suchString
			self.loadPage()

	def getVideoPage(self, data):
		videoPage = re.findall(',file:\'(.*?)\'', data, re.S)
		if videoPage:
			for url in videoPage:
				self.keyLocked = False
				Title = self['liste'].getCurrent()[0][0]
				self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='elladies')