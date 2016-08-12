# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

basename = "Chefkoch.de"
baseurl ="http://www.chefkoch.de"
securl= "http://www.chefkoch.de/video/artikel/"

class chefkochGenreScreen(MPScreen):

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

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		u = "%s/videos" %(baseurl)
		getPage(u).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		raw = re.findall('class="video-categories">(.*?)</ul>', data, re.S)
		if raw:
			parse = re.findall('<li><a href="(.*?)0/Chefkoch/">(.*?)</a></li>', raw[0], re.S)
			for (url, title) in parse:
				url = baseurl + url
				self.genreliste.append((decodeHtml(title),url))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
		self['name'].setText('')

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if self.keyLocked:
			return
		self.session.open(chefvids, name, url)

class chefvids(MPScreen):

	def __init__(self, session,name,url):
		self.url = url
		self.name = name
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
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))
		self.page = 0
		self.lastpage = 0

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "%s%s/Chefkoch/" %(self.url,str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		if re.match('.*?pagination-next">.*?>.*?ansehen</span></a>', data, re.S):
			self.lastpage = self.page+1
		self['Page'].setText(_("Page:"))
		self['page'].setText("%s" % (str(self.page+1)))
		parse = re.findall('gradient\sclearfix">.*?href="/video/artikel/(.*?)".*?cktv-kat-klein.*?src="(.*?)"\salt="(.*?)".*?play-button"></span></a>', data, re.S)
		if parse:
			for (url,pic,title) in parse:
				self.filmliste.append((decodeHtml(title),url,pic))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		link = securl + self['liste'].getCurrent()[0][1]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)
		getPage(link).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self,data):
		self.desc = re.findall('itemprop="description" content="(.*?)"', data, re.S)
		self.runtime = re.findall('L.*?nge: <strong>(.*?)</strong>,', data, re.S)
		self.vid = re.findall('contentUrl" content="(.*?)">', data, re.S)
		d = "Länge: %s\n\n%s" % (self.runtime[0],(decodeHtml(self.desc[0])))
		self['handlung'].setText(d)

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 1:
			self.page -= 1
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][0]
		self.vid = self.vid[0]
		if self.vid:
			self.session.open(SimplePlayer, [(name, str(self.vid))], cover=False, showPlaylist=False, ltype='chefkoch', useResume=False)
		else:
			message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)