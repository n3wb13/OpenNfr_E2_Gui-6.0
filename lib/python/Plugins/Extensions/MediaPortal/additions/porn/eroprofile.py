# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class eroprofileGenreScreen(MPScreen):

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

		self['title'] = Label("EroProfile.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("--- Search ---", ""))
		self.genreliste.append(("Newest", "home"))
		self.genreliste.append(("Popular", "popular"))
		self.genreliste.append(("Amateur Moms/Mature", "13"))
		self.genreliste.append(("Amateur Teens", "14"))
		self.genreliste.append(("Amateurs", "12"))
		self.genreliste.append(("Asian", "19"))
		self.genreliste.append(("Ass", "27"))
		self.genreliste.append(("Big Ladies", "5"))
		self.genreliste.append(("Big Tits", "11"))
		self.genreliste.append(("Bisexual", "18"))
		self.genreliste.append(("Black / Ebony", "20"))
		self.genreliste.append(("Celeb", "23"))
		self.genreliste.append(("Facial / Cum", "24"))
		self.genreliste.append(("Fetish / Kinky", "10"))
		self.genreliste.append(("Fucking / Sucking", "26"))
		self.genreliste.append(("Hairy", "7"))
		self.genreliste.append(("Interracial", "15"))
		self.genreliste.append(("Lesbian", "6"))
		self.genreliste.append(("Lingerie / Panties", "30"))
		self.genreliste.append(("Nudist / Voyeur / Public", "16"))
		self.genreliste.append(("Other", "28"))
		self.genreliste.append(("Swingers / Gangbang", "8"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()

		else:
			streamSearchString = ""
			ID = self['liste'].getCurrent()[0][1]
			self.session.open(eroprofileFilmScreen, streamSearchString, Name, ID)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			Name = self['liste'].getCurrent()[0][0]
			self.suchString = callback.replace(' ', '+')
			streamSearchString = self.suchString
			streamGenreID = ""
			self.session.open(eroprofileFilmScreen, streamSearchString, Name, streamGenreID)

class eroprofileFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, SearchString, Name, ID):
		self.SearchString = SearchString
		self.ID = ID
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

		self['title'] = Label("EroProfile.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if self.ID == "":
			url = 'http://www.eroprofile.com/m/videos/home?text=%s&pnum=%s' % (self.SearchString, str(self.page))
		elif self.ID == "home":
			url = 'http://www.eroprofile.com/m/videos/home?text=%s&pnum=%s' % (self.SearchString, str(self.page))
		elif self.ID == "popular":
			url = 'http://www.eroprofile.com/m/videos/popular/month?text=%s&pnum=%s' % (self.SearchString, str(self.page))
		else:
			url = 'http://www.eroprofile.com/m/videos/niche/%s/?text=%s&pnum=%s' % (self.ID, self.SearchString, str(self.page))
		getPage(url, headers={'Cookie': 'hideNiches=9%2C2%2C3%2C1%2C29%2C31%2C4%2C21%2C22%2C25', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		lastp = re.search('class="maxW"><tr><td><b>(.*?)</b>\sresults</td>', data, re.S)
		if lastp:
			lastp = round((float(lastp.group(1)) / 12) + 0.5)
			self.lastpage = int(lastp)
		else:
			self.lastpage = 1
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		Movies = re.findall('class="video">.*?img\ssrc="(.*?)".*?class="title"><a\shref="(.*?)">(.*?)</a.*?class="duration">(.*?)</div>', data, re.S)
		if Movies:
			for (Image, Url, Title, Runtime) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image.replace('amp;',''), Runtime))
			if self.page == 1:
				self.filmliste.insert(0, ("--- Search ---", None, None, None))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s" % (runtime))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		if Title == "--- Search ---":
			self.suchen()
		else:
			url = self['liste'].getCurrent()[0][1]
			self.keyLocked = True
			url = 'http://www.eroprofile.com' + url
			getPage(url).addCallback(self.getVideoPage).addErrback(self.dataError)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			self.SearchString = self.suchString
			self.loadPage()

	def getVideoPage(self, data):
		videoPage = re.findall('file:\'(.*?)\'', data, re.S)
		if videoPage:
			for url in videoPage:
				self.keyLocked = False
				Title = self['liste'].getCurrent()[0][0]
				self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='eroprofile')