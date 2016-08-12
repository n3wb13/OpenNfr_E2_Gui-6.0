# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class n24GenreScreen(MPScreen):

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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("N24 Mediathek")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = "http://www.n24.de/n24/Mediathek/videos/"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw = re.findall('<li><a.*?data-filter_rubric="(.*?)">(.*?)</a></li>', data, re.S)
		if raw:
			for (Url, Title) in raw:
				self.filmliste.append((decodeHtml(Title), Url))
				self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		name = self['liste'].getCurrent()[0][0]
		self['name'].setText(decodeHtml(name))
	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1].replace(' ','+')
		self.session.open(n24ListScreen, Link, Name)

class n24ListScreen(MPScreen, ThumbsHelper):

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
		"0"		: self.closeAll,
		"ok"	: self.keyOK,
		"cancel": self.keyCancel,
		"5" : self.keyShowThumb,
		"up" : self.keyUp,
		"down" : self.keyDown,
		"right" : self.keyRight,
		"left" : self.keyLeft,
		"nextBouquet" : self.keyPageUp,
		"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("N24 Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))

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
		url = "http://www.n24.de/n24/Mediathek/videos/q?query=&hitsPerPage=50&pageNum=" + str(self.page) + "&recent=0&docType=CMVideo&category=" + self.Link + "&from=&to=&taxonomy=&type=&sort=new"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		lastpage = re.search('<li><span\sclass="pages">.*?\s/\s(.*?)</span></li>', data, re.S)
		if lastpage:
			self.lastpage = int(lastpage.group(1))
			self['page'].setText("%s / %s" % (str(self.page), str(self.lastpage)))
		else:
			self.lastpage = 1
			self['page'].setText("%s / 1" % str(self.page))

		parse = re.search('"search_result"(.*?)"search_paging"', data, re.S)
		if parse:
			parts = parse.group(1).split('"result_media"')
			for part in parts[1:]:
				raw = re.findall('href="(.*?)"\s+class="image".*?src=&#034;(.*?)&#034;.*?<h4>.*?href.*?>(.*?)</a>', part, re.S)
				if raw:
					for (Link, Image, Title) in raw:
						Title = Title.strip()
						self.filmliste.append((decodeHtml(Title), Link, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append(("No streams found.", "none", None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		name = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(decodeHtml(name))
		CoverHelper(self['coverArt']).getCover(coverUrl)
		link = "http://www.n24.de" + self['liste'].getCurrent()[0][1]
		getPage(link).addCallback(self.getHandlung).addErrback(self.dataError)

	def getHandlung(self, data):
		handlung = re.search('<div\sclass="text">.*?<p>(.*?)</p>.*?<div\sclass="related">', data, re.S)
		if handlung:
			self['handlung'].setText(decodeHtml(stripAllTags(handlung.group(1)).strip()))
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		if self.keyLocked:
			return
		Link = "http://www.n24.de" + self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getStreamData).addErrback(self.dataError)

	def getStreamData(self, data):
		self.title = self['liste'].getCurrent()[0][0]
		url = re.search('html5ProgressiveVideoSource\s=\s["|\'](.*?)["|\']', data, re.S)
		if url:
			self.session.open(SimplePlayer, [(self.title, url.group(1))], showPlaylist=False, ltype='n24')