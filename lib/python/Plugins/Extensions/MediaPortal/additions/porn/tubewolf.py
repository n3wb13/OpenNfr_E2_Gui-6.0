# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class tubewolfGenreScreen(MPScreen):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Tubewolf.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self['name'].setText(_('Please wait...'))
		url = "http://www.tubewolf.com/categories/"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('class="categories-list"(.*?)middle-box', data, re.S)
		cat = re.findall('a\shref="(.*?)".*?alt="(.*?)"', parse.group(1), re.S)
		if cat:
			for (Url, Title) in cat:
				self.filmliste.append((decodeHtml(Title), Url))
			self.filmliste.sort()
			self.filmliste.insert(0, ("Top Rated", "http://www.tubewolf.com/top-rated"))
			self.filmliste.insert(0, ("Most Popular", "http://www.tubewolf.com/most-popular"))
			self.filmliste.insert(0, ("Newest", "http://www.tubewolf.com/latest-updates"))
			self.filmliste.insert(0, ("--- Search ---", "callSuchen", ""))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False
		self['name'].setText('')

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = '?q=%s' % (self.suchString)
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(tubewolfListScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(tubewolfListScreen, Link, Name)

class tubewolfListScreen(MPScreen, ThumbsHelper):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("Tubewolf.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.lastpage = 1
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://www.tubewolf.com/search/%s/%s" % (self.page, self.Link)
		else:
			url = self.Link + "/" + str(self.page) + "/"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data,'<li\sclass="active"(.*?)Next')
		parse = re.search('class="video-list">(.*?)class="pagination">', data, re.S)
		streams = parse.group(1).split('</div>')
		if streams:
			for item in streams:
				Date = re.search('date">(.*?)</span>', item)
				if Date:
					Date = Date.group(1)
				else:
					Date = ''
				raw = re.findall('itemprop.*?href="(http://www.tubewolf.com/movies.*?)".*?title="(.*?)".*?class="th.*?src="(.*?)".*?class="duration">\s{0,2}(.*?)</span>', item, re.S)
				if raw:
					for (Link, Title, Image, Duration) in raw:
						self.filmliste.append((decodeHtml(Title), Link, Image, Duration, Date))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', '', '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		runtime = self['liste'].getCurrent()[0][3]
		added = self['liste'].getCurrent()[0][4]
		self['handlung'].setText("Runtime: %s\nAdded: %s" % (runtime, added))
		self['name'].setText(Title)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getStreamData).addErrback(self.dataError)

	def getStreamData(self, data):
		title = self['liste'].getCurrent()[0][0]
		raw = re.findall("video_url:\s'(.*?)',", data, re.S)
		if raw:
			self.session.open(SimplePlayer, [(title, raw[0])], showPlaylist=False, ltype='tubewolf')