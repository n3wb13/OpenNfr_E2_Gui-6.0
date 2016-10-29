# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2016
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding execution on hardware, you are permitted to execute this plugin on VU+ hardware
#  which is licensed by satco europe GmbH, if the VTi image is used on that hardware.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
###############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class xxxArtGenreScreen(MPScreen):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path =  mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"]  = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("XXX-Art")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self['name'].setText(_('Please wait...'))
		url = "http://xxx-art.biz/"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('data-toggle="dropdown">Category(.*?)class="wide-nav-link">Top videos', data, re.S)
		if parse:
			raw = re.findall('<li\sclass=".*?"><a\shref="(.*?)1-date.html"\sclass=".*?">(.*?)</a>', parse.group(1), re.S)
			if raw:
				for (Url, Title) in raw:
					self.filmliste.append((Title, Url))
		self.filmliste.sort()
		self.filmliste.insert(0, ("New Videos", "http://xxx-art.biz/newvideos.html?&page="))
		self.filmliste.insert(0, ("Top Videos", "http://xxx-art.biz/topvideos.html?&page="))
		self.filmliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self['name'].setText('')

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = 'http://xxx-art.biz/search.php?keywords=%s&page=' % (self.suchString)
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(xxxArtListScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(xxxArtListScreen, Link, Name)

class xxxArtListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		self.plugin_path = mp_globals.pluginPath
		self.skin_path =  mp_globals.pluginPath + mp_globals.skinsPath

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

		self['title'] = Label("XXX-Art")
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
		if self.Name == "--- Search ---" or self.Name == "New Videos" or self.Name == "Top Videos":
			url = self.Link + str(self.page)
		else:
			url = self.Link + str(self.page) + "-date.html"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, 'pagination-centered">(.*?)</ul>')
		raw = re.findall('class="pm-label-duration.*?">(.*?)<.*?href="(.*?)".*?src="(.*?)".*?title="(.*?)".*?title=.*?>(.*?)<.*?<small>(.*?)\sViews', data, re.S)
		if raw:
			for (duration, link, image, title, added, views) in raw:
				self.filmliste.append((decodeHtml(title), duration, link, image, added, views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', '', None, '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 2, 3, 1, None, self.page, self.lastpage)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		runtime = self['liste'].getCurrent()[0][1]
		added = self['liste'].getCurrent()[0][4]
		views = self['liste'].getCurrent()[0][5]
		self['handlung'].setText("Runtime: %s\nAdded: %s\nViews: %s" % (runtime, added, views))
		self['name'].setText(Title)
		coverUrl = self['liste'].getCurrent()[0][3]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][2]
		Link = self['liste'].getCurrent()[0][0]
		Cover = self['liste'].getCurrent()[0][3]
		self.session.open(StreamAuswahl, Link, Title, Cover)

class StreamAuswahl(MPScreen):

	def __init__(self, session, Title, Link, Cover):
		self.Link = Link
		self.Title = Title
		self.Cover = Cover
		self.plugin_path = mp_globals.pluginPath
		self.skin_path =  mp_globals.pluginPath + mp_globals.skinsPath

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
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("XXX-Art")
		self['ContentTitle'] = Label("%s" %self.Title)

		self.filmliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.Cover)
		self.keyLocked = True
		url = self.Link
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		parse = re.search('<div id="video-wrapper">(.*?)<div class="pm-video-control">', data, re.S)
		if parse:
			streams = re.findall('\shref="(http[s]?://(.*?)\/.*?)[\'|"|\&|<]', parse.group(1), re.S|re.I)
			if streams:
				for (stream, hostername) in streams:
					if isSupportedHoster(hostername, True):
						self.filmliste.append((hostername.replace('www.',''), stream))
		if len(self.filmliste) == 0:
			embed = re.search('content="(http://www.xxx-art.biz/embed.*?)"', data, re.S|re.I)
			if embed:
				url = embed.group(1)
				getPage(url).addCallback(self.loadPageData2).addErrback(self.dataError)
			else:
				self.loadPageData2("None")
		else:
			self.ml.setList(map(self._defaultlisthoster, self.filmliste))
			self.keyLocked = False

	def loadPageData2(self, data):
		streams = re.findall('\shref="(http[s]?://(.*?)\/.*?)[\'|"|\&|<]', data, re.S|re.I)
		if streams:
			for (stream, hostername) in streams:
				if isSupportedHoster(hostername, True):
					self.filmliste.append((hostername.replace('www.',''), stream))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		title = self.Title
		self.session.open(SimplePlayer, [(self.Title, stream_url, self.Cover)], showPlaylist=False, ltype='xxxart', cover=True)