# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

baseurl = "http://anime-world24.net/"

class animeWorldMAin(MPScreen, ThumbsHelper):

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
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("anime-world24.net")
		self['ContentTitle'] = Label("Animeliste A-Z:")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = baseurl + "animeliste/letter/Alle/site/%s" % str(self.page)
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		movies = re.findall('<div class="cover"><a href="(.*?)"><img class="img-sbordered rounded-x" src="(.*?)" alt="(.*?)"/></a></div>', data, re.S)
		if movies:
			for (Url, Cover, Title) in movies:
				Cover = baseurl + Cover.replace('sizex=50&sizey=50','sizex=250&sizey=250')
				self.streamList.append((decodeHtml(Title), Url, Cover))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, None, None, 'id="animedescriptionimg">.*?<img src="(.*?)"', 1, 1, coverlink=baseurl)
			self.showInfos()

	def showInfos(self):
		Name = self['liste'].getCurrent()[0][0]
		Url = self['liste'].getCurrent()[0][1]
		self.cover = self['liste'].getCurrent()[0][2]
		self['name'].setText(Name)
		CoverHelper(self['coverArt']).getCover(self.cover)
		getPage(Url).addCallback(self.getmore).addErrback(self.dataError)

	def getmore(self, data):
		desc = re.findall('<div class="description">(.*?)</div>', data, re.S)
		if desc:
			self['handlung'].setText(decodeHtml(desc[0]))
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		movie_url = self['liste'].getCurrent()[0][1]
		self.session.open(animeWorldFolgen, stream_name, movie_url, self.cover)

class animeWorldFolgen(MPScreen):

	def __init__(self, session, stream_name, url, cover):
		self.stream_name = stream_name
		self.url = url
		self.cover = cover
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("anime-world24.net")
		self['ContentTitle'] = Label("Folgen:")
		self['name'] = Label("%s" % self.stream_name)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.streamList = []
		folgen = re.findall('<td class="text-center">(.*?)</td>.*?<a href="(.*?)">(.*?)</a>', data, re.S)
		if folgen:
			for (sFolge, sUrl, sTitle) in folgen:
				url = sUrl.replace('" class="cmc','')
				sUrl = "http://anime-world24.net/"+url
				self.streamList.append((sFolge, decodeHtml(sTitle), sUrl))
			self.ml.setList(map(self.awListEntry3, self.streamList))
			CoverHelper(self['coverArt']).getCover(self.cover)
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		self.sFolge = self['liste'].getCurrent()[0][0]
		self.sTitle = self['liste'].getCurrent()[0][1]
		sUrl = self['liste'].getCurrent()[0][2]
		print self.sFolge, self.sTitle, sUrl
		getPage(sUrl).addCallback(self.streamData).addErrback(self.dataError)

	def streamData(self, data):
		string = 'file: "(.*?)".*?title: "Folge %s"' % self.sFolge
		stream_url = re.findall(string, data, re.S)
		if stream_url:
			stream_url = stream_url[0]
			self.session.open(SimplePlayer, [(self.sFolge+" "+self.sTitle, stream_url, self.cover)], showPlaylist=False, ltype='animeworld', cover=True)