# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class redtubeGenreScreen(MPScreen):

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

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("RedTube.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.redtube.com/channels"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('class="video">.*?<a\shref="(.*?)"\stitle="(.*?)">.*?data-src="(.*?)"', data, re.S)
		if Cats:
			for (Url, Title, Image) in Cats:
				Url = "http://www.redtube.com" + Url + '?page='
				self.genreliste.append((Title, Url, Image))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Most Favored", "http://www.redtube.com/mostfavored?period=alltime&page=", None))
			self.genreliste.insert(0, ("Most Viewed", "http://www.redtube.com/mostviewed?period=alltime&page=", None))
			self.genreliste.insert(0, ("Top Rated", "http://www.redtube.com/top?period=alltime&page=", None))
			self.genreliste.insert(0, ("Newest", "http://www.redtube.com/?page=", None))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()

		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(redtubeFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = 'http://www.redtube.com/?search=%s&page=' % (self.suchString)
			self.session.open(redtubeFilmScreen, Link, Name)

class redtubeFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
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

		self['title'] = Label("RedTube.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s%s" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		lastp = re.search('<h1>.*?\s\((.*?)\)</h1>', data, re.S)
		if lastp:
			lastp = lastp.group(1).replace(',','')
			cat = self.Link
			search = re.search('/?search=(.*)', cat, re.S)
			if search:
				lastp = round((float(lastp) / 20) + 0.5)
			else:
				lastp = round((float(lastp) / 24) + 0.5)
			self.lastpage = int(lastp)
		else:
			self.lastpage = 1230
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		Movies = re.findall('"video-duration"\sonclick="window.location.href\s=\'(.*?)\'">(.*?)<.*?data-src="(.*?)".*?alt="(.*?)"\s/>.*?views">(.*?)</span>', data, re.S)
		if Movies:
			for (Url, Runtime, Image, Title, Views) in Movies:
				if Image.startswith('//'):
					Image = 'http:' + Image
				Views = Views.replace(',','').replace(' views','')
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nViews: %s" % (runtime, views))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = 'http://www.redtube.com' + self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('<source\ssrc="(.*?)"\stype="video/mp4">', data, re.S)
		if videoPage:
			url = videoPage[-1]
			url = url.replace('\/','/')
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='redtube')