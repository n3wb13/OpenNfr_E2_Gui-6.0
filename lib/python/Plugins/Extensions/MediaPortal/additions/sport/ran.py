# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class ranLinkMain(MPScreen):

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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("ran.de")
		self['ContentTitle'] = Label("Genre:")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		url = "http://www.ran.de/videos"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		categorys = re.findall('<h2><a class="trackable_teaser".*?" >(.*?)</a></h2>.*?<section\sid="block_(.*?)".*?\(offset\)\/(\d+)', data, re.S)
		for (Title, Section, offset) in categorys:
			Url = "http://www.ran.de/psdflow/ajaxblock/(block)/" + Section + "/(offset)/"
			self.streamList.append((decodeHtml(Title), Url, int(offset)))
			self.streamList.sort(key=lambda t : t[0].lower())
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self['name'].setText("")

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		offset = self['liste'].getCurrent()[0][2]
		self.session.open(ranLinkStreamScreen, url, title, offset)

class ranLinkStreamScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, offset):
		self.Link = Link
		self.Name = Name
		self.offset = offset
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

		self['title'] = Label("ran.de")
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
		url = self.Link + str((self.page - 1) * self.offset)
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'ajax_pager">(.*?)</ul>', '.*>\s+(\d+)\s+<')
		streams = re.findall('teaser-image lazy">\s*<a href="(.*?)".*?"teaser-figure" data-src="(.*?)".*?<h3><span>(.*?)</span></h3>', data, re.S)
		if streams:
			for (Link, Pic, Title) in streams:
				Pic = "http://www.ran.de" + Pic
				self.filmliste.append((decodeHtml(Title).strip(), Link, Pic))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.getIDData).addErrback(self.dataError)

	def getIDData(self, data):
		raw = re.search('"clip_id":\s*"(.*?)"', data, re.S)
		url = "http://vas.sim-technik.de/video/video.jsonp?clipid=" + raw.group(1)
		getPage(url).addCallback(self.getStreamData).addErrback(self.dataError)

	def getStreamData(self, data):
		title = self['liste'].getCurrent()[0][0]
		raw = re.search('"VideoURL":"(.*?)"', data, re.S)
		if raw:
			self.session.open(SimplePlayer, [(title, raw.group(1).replace('\/','/'))], showPlaylist=False, ltype='ran')
		else:
			message = self.session.open(MessageBoxExt, _("No video found."), MessageBoxExt.TYPE_INFO, timeout=3)