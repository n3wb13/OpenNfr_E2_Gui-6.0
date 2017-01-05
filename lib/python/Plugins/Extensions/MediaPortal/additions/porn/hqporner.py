# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2017
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
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

class hqpornerGenreScreen(MPScreen):

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

		self['title'] = Label("HQPORNER")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.filmliste.append(("--- Search ---", None))
		self.filmliste.append(("Newest", "http://hqporner.com/hdporn"))
		self.filmliste.append(("Genres", "categories"))
		self.filmliste.append(("Studios", "studios"))
		self.filmliste.append(("Actress", "actress"))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(hqpornerListScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		elif re.search('http://.*?', Link):
			self.session.open(hqpornerListScreen, Link, Name)
		else:
			self.session.open(hqpornerSubGenreScreen, Link, Name)

class hqpornerSubGenreScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("HQPORNER")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://hqporner.com/porn-" + self.Link + ".php"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw = re.findall('class="box\sfeature">\s+<a href="(.*?)".*?img\ssrc="(.*?)"[\s]?alt="(.*?)"', data, re.S)
		if raw:
			for (Url, Image, Title) in raw:
				Url = "http://hqporner.com" + Url
				Image = "http://hqporner.com/" + Image
				self.filmliste.append((decodeHtml(Title.title()), Url, Image))
			self.filmliste.sort()
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(hqpornerListScreen, Link, Name)

class hqpornerListScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("HQPORNER")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.tw_agent_hlp = TwAgentHelper(followRedirect=True)
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://hqporner.com/?s=%s&p=%s" % (self.Link, str(self.page))
		else:
			url = self.Link + "/" + str(self.page)
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if re.match('.*?NO RESULTS ON YOUR REQUEST', data, re.S|re.I):
			self.filmliste.append((_('No movies found!'), None, None, None))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
		else:
			self.getLastPage(data, 'pagination">(.*?)</ul>')
			parse = re.search('<div\sclass="box\spage-content">\s+(.*?)pagination', data, re.S)
			raw = re.findall('section\sclass="box\sfeature">\s+<a href="(.*?)".*?\ssrc="(.*?)"\salt="(.*?)".*?calendar meta-data">(.*?)<', parse.group(1), re.S)
			if raw:
				for (link, image, title, age) in raw:
					link = "http://hqporner.com" + link
					self.filmliste.append((decodeHtml(title), link, image, age))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		coverUrl = self['liste'].getCurrent()[0][2]
		age = self['liste'].getCurrent()[0][3]
		self['handlung'].setText("\n\nDate: %s" % age)
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link == None:
			return
		getPage(Link).addCallback(self.get_url).addErrback(self.dataError)

	def get_url(self, data):
		Link = re.findall('<iframe\swidth="\d+"\sheight="\d+"\ssrc="(http://(.*?)\/.*?)"', data)
		if Link and re.match('http://hqporner.com', Link[0][0]):
			getPage(Link[0][0]).addCallback(self.getVideoLink).addErrback(self.dataError)
		elif Link and re.match('http://bemywife\.cc', Link[0][0]):
			getPage(Link[0][0]).addCallback(self.bemywife).addErrback(self.dataError)
		elif Link and re.match('http://5\.79\.64\.169', Link[0][0]):
			getPage(Link[0][0]).addCallback(self.leaseweb).addErrback(self.dataError)
		elif Link and isSupportedHoster(Link[0][1].replace('www.',''), True):
			get_stream_link(self.session).check_link(Link[0][0], self.got_link)
		else:
			message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)

	def bemywife(self, data):
		stream_url = re.findall('file:\s"(.*?(\d+).mp4)"', data)
		if stream_url:
			stream_url.sort(key=lambda t : t[1], reverse=False)
			if 'http://' in stream_url[-1][0]:
				link = stream_url[-1][0]
			else:
				link = "http://bemywife.cc" + stream_url[-1][0]
			self.got_link(link)
		else:
			message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)

	def leaseweb(self, data):
		stream_url = re.findall('src="(http://[\d\.]+/runplayer/.*?)"', data)
		if stream_url:
			getPage(stream_url[0]).addCallback(self.leaseweblink).addErrback(self.dataError)
		else:
			message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)

	def leaseweblink(self, data):
		stream_url = re.findall('file":\s"(.*?mp4)"', data)
		if stream_url:
			self.got_link(stream_url[-1])
		else:
			message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)

	def getVideoLink(self, data):
		get_packedjava = re.findall("<script type=.text.javascript.>(eval.function.*?)</script>", data, re.S)
		if get_packedjava and detect(get_packedjava[0]):
			sJavascript = re.sub("\}\}\)\}\);',\d+,", "}})});',62,", get_packedjava[0])
			sUnpacked = unpack(sJavascript)
			if sUnpacked:
				videoIDs = re.findall("oid:.'(.*?).',video_id:.'(.*?).',embed_hash:.'(.*?).'", sUnpacked, re.S)
				if videoIDs:
					stream = "https://api.vk.com/method/video.getEmbed?oid=%s&video_id=%s&embed_hash=%s&callback=callbackFunc" % (videoIDs[0][0],videoIDs[0][1],videoIDs[0][2])
					get_stream_link(self.session).check_link(stream, self.got_link)

	def got_link(self, stream_url):
		Title = self['liste'].getCurrent()[0][0]
		self['name'].setText(Title)
		self.session.open(SimplePlayer, [(Title, stream_url)], showPlaylist=False, ltype='hqporner')