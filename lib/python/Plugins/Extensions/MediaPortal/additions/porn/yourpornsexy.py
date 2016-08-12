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

myagent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0'

class YourPornSexyGenreScreen(MPScreen):

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

		self['title'] = Label("YourPornSexy")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://yourporn.sexy"
		getPage(url, agent=myagent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('<span>All Albums</span>(.*?)bottom', data, re.S)
		Cats = re.findall('<a\shref="(/videos/.*?)" title="(.*?)" target="_blank">', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://yourporn.sexy" + Url.replace('/0/','/%s/')
				Title = Title.lower().title()
				self.genreliste.append((Title, Url))
			self.genreliste.sort()
		self.genreliste.insert(0, ("Trends", "http://yourporn.sexy/searches/%s.html"))
		self.genreliste.insert(0, ("Orgasmic", "http://yourporn.sexy/orgasm/"))
		self.genreliste.insert(0, ("Top Viewed", "http://yourporn.sexy/popular/top-viewed.html"))
		self.genreliste.insert(0, ("Top Rated", "http://yourporn.sexy/popular/top-rated.html"))
		self.genreliste.insert(0, ("Newest", "http://yourporn.sexy/blog/all/%s.html"))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Trends":
			self.session.open(YourPornSexyTrendsScreen, Link, Name)
		else:
			self.session.open(YourPornSexyFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '-')
			Name = "--- Search ---"
			Link = self.suchString
			self.session.open(YourPornSexyFilmScreen, Link, Name)

class YourPornSexyTrendsScreen(MPScreen):

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

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("YourPornSexy")
		self['ContentTitle'] = Label("Trends:")
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.genreliste = []
		url = self.Link.replace('%s', str((self.page-1)*150))
		print url
		getPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', 'ctrl_el.*>(\d+)</div')
		Cats = re.findall('<td><a\shref=[\'|"]/(.*?).html[\'|"]\stitle=[\'|"].*?[\'|"]>(.*?)</a></td><td>(\d+)</td><td>(\d+)</td>', data , re.S)
		if Cats:
			for (Url, Title, Frequency, Results) in Cats:
				self.genreliste.append((Title, Url, Frequency, Results))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		freq = self['liste'].getCurrent()[0][2]
		results = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText("Frequency: %s\nResults: %s" % (freq, results))

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(YourPornSexyFilmScreen, Link, self.Name)

class YourPornSexyFilmScreen(MPScreen, ThumbsHelper):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("YourPornSexy")
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
		if self.Name == "Newest":
			count = 10
		else:
			count = 30
		if re.match(".*?Search", self.Name) or self.Name == "Trends":
			url = "http://yourporn.sexy/%s.html?page=%s" % (self.Link, str((self.page-1)*count))
		else:
			url = self.Link.replace('%s', str((self.page-1)*count))
		getPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', 'ctrl_el.*>(\d+)</div')
		prep = data
		if re.search("</head>(.*?)<span>Other Results</span>", data, re.S):
			preparse = re.search('</head>(.*?)<span>Other Results</span>', data, re.S)
			if preparse:
				prep = preparse.group(1)
		Movies = re.findall('itemprop="url"\shref="(.*?)"\stitle="(.*?)".*?itemprop="thumbnail".*?\ssrc="(.*?)".*?class="vid_views"><span>(\d+)</span>.*?class="vid_duration transition"><span>(.*?)</span>', prep, re.S)
		if Movies:
			for (Url, Title, Image, Views, Runtime) in Movies:
				Url = "http://yourporn.sexy" + Url
				self.filmliste.append((decodeHtml(Title), Url, Image, Views, Runtime, "-"))
		else:
			Movies = re.findall('post_share_div.*?<a\shref=[\'|"](.*?)[\'|"]\stitle=[\'|"](.*?)[\'|"].*?vid_thumb.*?\ssrc=[\'|"](.*?)[\'|"].*?post_time.*?>(.*?)[<strong|</div>].*?(\d+)\sviews', data, re.S)
			if Movies:
				for (Url, Title, Image, Added, Views) in Movies:
					Url = "http://yourporn.sexy" + Url
					self.filmliste.append((decodeHtml(Title), Url, Image, Views, "-", Added))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, '', '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()
		self.keyLocked = False

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		views = self['liste'].getCurrent()[0][3]
		runtime = self['liste'].getCurrent()[0][4]
		added = self['liste'].getCurrent()[0][5]
		self['name'].setText(title)
		self['handlung'].setText("Views: %s\nRuntime: %s\nAdded: %s" % (views, runtime, added))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link, agent=myagent).addCallback(self.getVideoUrl).addErrback(self.dataError)

	def getVideoUrl(self, data):
		videoUrl = re.findall('<source\ssrc="(.*?)"\stype="video/mp4">', data, re.S)
		if not videoUrl:
			videoUrl = re.findall('<video.*?src=[\'|"](.*?.mp4)[\'|"]\s', data, re.S)
		if videoUrl:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, videoUrl[-1])], showPlaylist=False, ltype='yourpornsexy')