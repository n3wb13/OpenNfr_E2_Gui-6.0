# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class updatetubeGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		if self.mode == "updatetube":
			self.portal = "UpdateTube.com"
			self.baseurl = "www.updatetube.com"
		if self.mode == "pinkrod":
			self.portal = "Pinkrod.com"
			self.baseurl = "www.pinkrod.com"
		if self.mode == "hotshame":
			self.portal = "hotshame.com"
			self.baseurl = "www.hotshame.com"
		if self.mode == "thenewporn":
			self.portal = "TheNewPorn.com"
			self.baseurl = "www.thenewporn.com"

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

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://%s/categories/" % self.baseurl
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="cat">(.*?)clearfix', data, re.S)
		Cats = re.findall('class="ic">.*?<a\shref="(.*?)".*?<img\ssrc="(.*?)"\salt="(.*?)"/>', parse.group(1), re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				self.genreliste.append((Title.title(), Url, Image))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Most Popular", "http://%s/most-popular/" % self.baseurl, None))
			self.genreliste.insert(0, ("Top Rated", "http://%s/top-rated/" % self.baseurl, None))
			self.genreliste.insert(0, ("Newest", "http://%s/" % self.baseurl, None))
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
			self.session.open(updatetubeFilmScreen, Link, Name, self.portal, self.baseurl)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = 'http://%s/search/?q=%s' % (self.baseurl, self.suchString)
			self.session.open(updatetubeFilmScreen, Link, Name, self.portal, self.baseurl)

class updatetubeFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal, baseurl):
		self.Link = Link
		self.portal = portal
		self.baseurl = baseurl
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

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		cat = self.Link
		search = re.search('/search/(.*)', cat, re.S)
		if search:
			url = 'http://%s/search/%s/%s' % (self.baseurl, str(self.page), str(search.group(1)))
		elif self.page == 1:
			url = "%s" % (self.Link)
		else:
			url = "%s%s/" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		lastp = re.search('class="info">.*?of\s(.*?[0-9])\sitems', data, re.S)
		if lastp:
			lastp = round((float(lastp.group(1)) / 40) + 0.5)
			self.lastpage = int(lastp)
		else:
			self.lastpage = 1
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		Movies = re.findall('class="ic">.*?<a\shref="(.*?)".*?title="(.*?)"\sclass="lnk">.*?<img\ssrc="(.*?)"', data, re.S)
		if Movies:
			for (Url, Title, Image) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('video_url:.*?\'(.*?.mp4)\/', data, re.S)
		if videoPage:
			for url in videoPage:
				self.keyLocked = False
				Title = self['liste'].getCurrent()[0][0]
				self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='updatetube')