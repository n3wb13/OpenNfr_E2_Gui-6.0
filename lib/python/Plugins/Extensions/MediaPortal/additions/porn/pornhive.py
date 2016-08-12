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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import TwAgentHelper

BASE_URL = "http://www.pornhive.tv"
BASE_NAME = "PornHive.tv"

class pornhiveGenreScreen(MPScreen):

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
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		getPage(BASE_URL).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('All\sTitles(.*?)</ul>', data, re.S)
		if parse:
			Cat = re.findall('<a\shref="(.*?)">(.*?)</a', parse.group(1), re.S)
			if Cat:
				for (Url, Title) in Cat:
					Url = "%s/all" % Url
					self.genreliste.append((Title, Url))
		parse = re.search('"dropdown">Categories(.*?)</ul>', data, re.S)
		if parse:
			Cat = re.findall('<a\shref="(.*?)"\stitle=".*?">(.*?)</a', parse.group(1), re.S)
			if Cat:
				for (Url, Title) in Cat:
					self.genreliste.append((Title, Url))
		self.genreliste.insert(0, ('Newest', '%s/en/page' % BASE_URL))
		self.genreliste.insert(0, ('--- Search ---', 'callSuchen'))
		self.genreliste.append(('StreamCloud', '%s/en/hoster/streamcloud.eu' % BASE_URL))
		self.genreliste.append(('FlashX', '%s/en/hoster/flashx.tv' % BASE_URL))
		self.genreliste.append(('NowVideo', '%s/en/hoster/nowvideo.sx' % BASE_URL))
		self.genreliste.append(('SockShare', '%s/en/hoster/sockshare.tv' % BASE_URL))
		self.genreliste.append(('Openload', '%s/en/hoster/openload.co' % BASE_URL))
		self.genreliste.append(('Vidxden', '%s/en/hoster/vidxden.com' % BASE_URL))
		self.genreliste.append(('Videomega', '%s/en/hoster/videomega.tv' % BASE_URL))
		self.genreliste.append(('Videowood', '%s/en/hoster/videowood.tv' % BASE_URL))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(pornhiveFilmScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		else:
			self.session.open(pornhiveFilmScreen, Link, Name)

class pornhiveFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = None

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "%s/en/search/%s?title=%s" % (BASE_URL, str(self.page*20-20), self.Link)
		else:
			url = self.Link + "/" + str(self.page*20-20)
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if not self.lastpage:
			self.getLastPage(data, 'class="pagination"(.*?)</div>', '.*"(\d+)(">\d+|">Last|\?)')
			if self.lastpage < 41:
				self.getLastPage(data, 'class="pagination"(.*?)</div>')
			else:
				self.lastpage = self.lastpage/20 + 1
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		Movies = re.findall('<div\sclass="vid-panel-img">.*?<a\shref="(.*?)"><img data-src="(.*?)".*?"vid-title vid-marquee">(.*?)<', data, re.S)
		if Movies:
			for (Url, Image, Title) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Image = self['liste'].getCurrent()[0][2]
		if Link == None:
			return
		self.session.open(pornhiveStreamListeScreen, Link, Title, Image)

class pornhiveStreamListeScreen(MPScreen):

	def __init__(self, session, streamFilmLink, streamName, streamImage):
		self.streamFilmLink = streamFilmLink
		self.streamName = streamName
		self.streamImage = streamImage
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
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Streams:")
		self['name'] = Label(_("Please wait..."))

		self.captchainfo = {}
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.streamImage)
		self.keyLocked = True
		self.filmliste = []
		getPage(self.streamFilmLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		streams = re.findall('data-id="(.*?)".*?Watch\sit\son\s+(.*?)"', data, re.S)
		if streams:
			for (streamid, hostername) in streams:
				if isSupportedHoster(hostername, True):
					self.filmliste.append((hostername, streamid))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No supported streams found!"), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False
		self['name'].setText(self.streamName)

	def keyOK(self):
		if self.keyLocked:
			return
		streamid = self['liste'].getCurrent()[0][1]
		if streamid == None:
			return
		url = "%s/en/out/%s" % (BASE_URL, streamid)
		self.tw_agent_hlp = TwAgentHelper()
		self.tw_agent_hlp.getRedirectedUrl(url).addCallback(self.test_streamLink).addErrback(self.dataError)

	def test_streamLink(self, url):
		if re.match(BASE_URL, url):
			getPage(url).addCallback(self.get_streamLink).addErrback(self.dataError)
		else:
			get_stream_link(self.session).check_link(url, self.got_link)

	def get_streamLink(self, data):
		streams = re.search('<iframe\ssrc="(.*?)"', data, re.S|re.I)
		if streams:
			get_stream_link(self.session).check_link(streams.group(1), self.got_link)
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def got_link(self, stream_url):
		self.session.open(SimplePlayer, [(self.streamName, stream_url, self.streamImage)], showPlaylist=False, ltype='pornhive', cover=True)