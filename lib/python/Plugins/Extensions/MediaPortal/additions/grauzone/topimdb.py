# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

from kinoxto import *
from movie4k import *
from kinokiste import *
from ddl_me import DDLME_FilmListeScreen

class timdbGenreScreen(MPScreen):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"

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
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"red" : self.kkisteSearch,
			"green" : self.kinoxSearch,
			"yellow" : self.movie4kSearch,
			"blue" : self.ddlmeSearch
		}, -1)

		self['title'] = Label("Top IMDb")
		self['ContentTitle'] = Label(_("Selection:"))
		self['F1'] = Label("kkiste")
		self['F2'] = Label("Kinox")
		self['F3'] = Label("Movie4k")
		self['F4'] = Label("ddl.me")

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.filmliste = []
		self.page = 1
		self.lastpage = 20

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		self.start = 1
		self.start = (self.page * 50) - 49

		url = "http://www.imdb.de/search/title?groups=top_1000&sort=user_rating,desc&start=%s" % str(self.start)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded', 'User-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0', 'Accept-Language':'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		movies = re.findall('class="lister-item.*?<img\salt="(.*?)".*?loadlate="(.*?\.jpg)".*?class="lister-item-index.*?>(.*?)\.</span>.*?class="lister-item-year.*?>\((\d+)\)</span.*?title="Users rated this (.*?\/10)', data, re.S)
		if movies:
			for title,image,place,year,rates in movies:
				image_raw = image.split('._V1_')
				image = "%s._V1_SX214_.jpg" % image_raw[0]
				self.filmliste.append((place, decodeHtml(title), year, rates, image))
				self.ml.setList(map(self.timdbEntry, self.filmliste))
			self.showInfos()
			self.keyLocked = False

	def showInfos(self):
		coverUrl = self['liste'].getCurrent()[0][4]
		self['page'].setText("%s / 20" % str(self.page))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		self.searchTitle = self['liste'].getCurrent()[0][1]

	def kinoxSearch(self):
		self.searchTitle = self['liste'].getCurrent()[0][1]
		self.session.openWithCallback(self.searchKinoxCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.searchTitle, is_dialog=True, auto_text_init=True)

	def searchKinoxCallback(self, callbackStr):
		if callbackStr is not None:
			url = "http://kinox.to/Search.html?q="
			self.session.open(kxSucheAlleFilmeListeScreen, url, callbackStr)

	def movie4kSearch(self):
		self.searchTitle = self['liste'].getCurrent()[0][1]
		self.session.openWithCallback(self.searchMovie4kCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.searchTitle, is_dialog=True, auto_text_init=True)

	def searchMovie4kCallback(self, callbackStr):
		if callbackStr is not None:
			url = "http://www.movie4k.tv/movies.php?list=search&search=%s" %(callbackStr)
			name = "Suche: %s" %(callbackStr)
			self.session.open(m4kFilme, url, name)

	def kkisteSearch(self):
		self.searchTitle = self['liste'].getCurrent()[0][1]
		self.session.openWithCallback(self.searchkkisteCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.searchTitle, is_dialog=True, auto_text_init=True)

	def searchkkisteCallback(self, callbackStr):
		if callbackStr is not None:
			url = "http://kkiste.to/search/?q=%s" % callbackStr.replace(' ','%20')
			self.session.open(kinokisteSearchScreen, url, callbackStr)

	def ddlmeSearch(self):
		self.searchTitle = self['liste'].getCurrent()[0][1]
		self.session.openWithCallback(self.searchDdlmeCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.searchTitle, is_dialog=True, auto_text_init=True)

	def searchDdlmeCallback(self, callbackStr):
		if callbackStr is not None:
			url = "http://de.ddl.me/search_99/?q=%s" % urllib.quote(callbackStr.strip())
			self.session.open(DDLME_FilmListeScreen, url, "Suche...")