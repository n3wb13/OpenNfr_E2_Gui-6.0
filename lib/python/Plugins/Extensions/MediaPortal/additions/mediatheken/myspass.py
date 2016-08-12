# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class myspassGenreScreen(MPScreen):

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
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("MySpass.de")
		self['ContentTitle'] = Label("Sendungen A-Z:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://www.myspass.de/myspass/ganze-folgen/"
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('FormatGruppe:\sABC(.*?)</div>', data, re.S)
		ganze = re.findall('<a\shref="(/myspass/shows/.*?)"\sclass="showsAZName">(.*?)</a>', parse.group(1), re.S)
		if ganze:
			self.genreliste = []
			for (link, name) in ganze:
				link = "http://www.myspass.de%s" % link
				self.genreliste.append((decodeHtml(name), link))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		myspassName = self['liste'].getCurrent()[0][0]
		myspassUrl = self['liste'].getCurrent()[0][1]
		print myspassName, myspassUrl
		self.session.open(myspassStaffelListeScreen, myspassName, myspassUrl)

class myspassStaffelListeScreen(MPScreen):

	def __init__(self, session, myspassName, myspassUrl):
		self.myspassName = myspassName
		self.myspassUrl = myspassUrl
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
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("MySpass.de")
		self['ContentTitle'] = Label("Staffeln:")

		self.staffelliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		print "hole daten"
		getPage(self.myspassUrl).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('\/\sGanze\sFolgen.*?class="episodeListSeasonList(.*?)</ul>', data, re.S)
		staffeln = re.findall('data-target=(.*?)data-query="(.*?season=.*?)">.*?\);">.\t{0,5}\s{0,15}(.*?)</a></span>', parse.group(1), re.S)
		if staffeln:
			self.staffelliste = []
			for (pages, link, name) in staffeln:
				page = re.search('data-maxpages="(.*?)"', pages, re.S)
				if page:
					pages = page.group(1)
				else:
					pages = 0
				link = "http://www.myspass.de/myspass/includes/php/ajax.php?v=2&ajax=true&action=%s&pageNumber=" % (link.replace('&amp;','&'))
				self.staffelliste.append((decodeHtml(name), link, pages))
			self.ml.setList(map(self._defaultlistleft, self.staffelliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		myname = self['liste'].getCurrent()[0][0]
		myid = self['liste'].getCurrent()[0][1]
		mypages = self['liste'].getCurrent()[0][2]

		print myid, myname, mypages
		self.session.open(myspassFolgenListeScreen, myname, myid, mypages)

class myspassFolgenListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, myspassName, myspassUrl, myspassPages):
		self.myspassName = myspassName
		self.myspassUrl = myspassUrl
		self.myspassPages = myspassPages
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
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label("MySpass.de")
		self['ContentTitle'] = Label("Folgen:")
		self['Page'] = Label(_("Page:"))

		self.page = 0
		self.lastpage = 0

		self.folgenliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.folgenliste = []
		url = "%s%s" % (self.myspassUrl, str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.lastpage = int(self.myspassPages)
		self['page'].setText(str(self.page+1) + ' / ' + str(self.lastpage+1))
		folgen = re.findall('class="episodeListInformation">.*?location.href=.*?--\/(.*?)\/.*?img\ssrc="(.*?)"\salt="(.*?)".*?\/h5>.*?"spacer5"></div>(.*?)<div', data, re.S|re.I)
		if folgen:
			for (id, image, title, description) in folgen:
				link = "http://www.myspass.de/myspass/includes/apps/video/getvideometadataxml.php?id=%s" % (id)
				image = "http:" + image
				description = description.replace('\t','').replace('\n','')
				self.folgenliste.append((decodeHtml(title), link, image, description))
			self.ml.setList(map(self._defaultlistleft, self.folgenliste))
			self.keyLocked = False
			self.showInfos()
			self.th_ThumbsQuery(self.folgenliste, 0, 1, 2, None, None, self.page+1, self.lastpage+1, mode=1, pagefix=-1)

	def showInfos(self):
		streamTitle = self['liste'].getCurrent()[0][0]
		streamPic = self['liste'].getCurrent()[0][2]
		streamHandlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(streamTitle)
		self['handlung'].setText(streamHandlung)
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		self.myname = self['liste'].getCurrent()[0][0]
		self.mylink = self['liste'].getCurrent()[0][1]
		getPage(self.mylink).addCallback(self.get_link).addErrback(self.dataError)

	def get_link(self, data):
		stream_url = re.search('<url_flv><.*?CDATA\[(.*?)\]\]></url_flv>', data, re.S)
		if stream_url:
			print stream_url.group(1)
			self.session.open(SimplePlayer, [(self.myname, stream_url.group(1))], showPlaylist=False, ltype='myspass')

	def keyPageDown(self):
		print "PageDown"
		if self.keyLocked:
			return
		if not self.page < 1:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		print "PageUP"
		if self.keyLocked:
			return
		if self.page < self.lastpage:
			self.page += 1
			self.loadPage()