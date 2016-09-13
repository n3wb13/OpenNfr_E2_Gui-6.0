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

try:
	import cfscrape
except:
	cfscrapeModule = False
else:
	cfscrapeModule = True

try:
	import requests
except:
	requestsModule = False
else:
	requestsModule = True

import urlparse
import thread

BASE_URL = "http://serienstream.to"
ss_cookies = CookieJar()
ss_ck = {}
ss_agent = ''

class ssMain(MPScreen):

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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Serienstream.to")
		self['ContentTitle'] = Label(_("Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		thread.start_new_thread(self.get_tokens,("GetTokens",))
		self.streamList.append(("Neue Episoden","neue"))
		self.streamList.append(("Serien von A-Z","serien"))
		self.streamList.append(("Watchlist","watchlist"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self['name'].setText(_("Please wait..."))

	def get_tokens(self, threadName):
		if requestsModule and cfscrapeModule:
			printl("Calling thread: %s" % threadName,self,'A')
			global ss_ck
			global ss_agent
			if ss_ck == {} or ss_agent == '':
				ss_ck, ss_agent = cfscrape.get_tokens(BASE_URL)
				requests.cookies.cookiejar_from_dict(ss_ck, cookiejar=ss_cookies)
			else:
				s = requests.session()
				url = urlparse.urlparse(BASE_URL)
				headers = {'user-agent': ss_agent}
				page = s.get(url.geturl(), cookies=ss_cookies, headers=headers)
				if page.status_code == 503 and page.headers.get("Server") == "cloudflare-nginx":
					ss_ck, ss_agent = cfscrape.get_tokens(BASE_URL)
					requests.cookies.cookiejar_from_dict(ss_ck, cookiejar=ss_cookies)
			self.keyLocked = False
			reactor.callFromThread(self.showInfos)
		else:
			reactor.callFromThread(self.ss_error)

	def ss_error(self):
		message = self.session.open(MessageBoxExt, _("Some mandatory Python modules are missing!"), MessageBoxExt.TYPE_ERROR)
		self.keyCancel()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][1]
		if auswahl == "serien":
			self.session.open(ssSerien)
		elif auswahl == "watchlist":
			self.session.open(ssWatchlist)
		elif auswahl == "neue":
			self.session.open(ssNeueEpisoden)

class ssSerien(MPScreen, SearchHelper):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		self.skin = self.skin.replace('</screen>', '')
		path = "%s/%s/search_widgets.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/search_widgets.xml"
		with open(path, "r") as f:
			self.skin += f.read()
			f.close()
		self.skin += '</screen>'

		MPScreen.__init__(self, session)
		SearchHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"green" : self.keyAdd,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Serienstream.to")
		self['ContentTitle'] = Label("Serien A-Z")
		self['F2'] = Label(_("Add to Watchlist"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.cover = None

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def goToLetter(self, num):
		self.keyNumberGlobal(num, self.streamList)
		self.showSearchkey(num)

	def loadPage(self):
		url = BASE_URL + "/serien"
		getPage(url, agent=ss_agent, cookies=ss_ck).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		serien = re.findall('<li>.*?<a href="http://serienstream.to/serie/stream/(.*?)".*?title=".*?Stream anschauen">(.*?)</a>.*?</li>', data, re.S)
		if serien:
			for (id, serie) in serien:
				url = BASE_URL + "/serie/stream/%s" % id
				self.streamList.append((decodeHtml(serie), url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No shows found!'), None))
		else:
			self.keyLocked = False
			self.streamList.sort(key=lambda t : t[0].lower())
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		self.getCover()

	def getCover(self):
		url = self['liste'].getCurrent()[0][1]
		getPage(url, agent=ss_agent, cookies=ss_ck).addCallback(self.setCoverUrl).addErrback(self.dataError)

	def setCoverUrl(self, data):
		cover = re.findall('<div class=".*?picture">.*?<img src="(http://serienstream.to/public/img/cover/.*?)"', data, re.S)
		if cover:
			self.cover = cover[0]
			CoverHelper(self['coverArt']).getCover(self.cover, agent=ss_agent, cookieJar=ss_cookies)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Title = self['liste'].getCurrent()[0][0]
		Url = self['liste'].getCurrent()[0][1]
		self.session.open(ssStaffeln, Title, Url, self.cover)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		muTitle = self['liste'].getCurrent()[0][0]
		muID = self['liste'].getCurrent()[0][1]
		fn = config.mediaportal.watchlistpath.value+"mp_ss_watchlist"
		if not fileExists(fn):
			open(fn,"w").close()
		try:
			writePlaylist = open(fn, "a")
			writePlaylist.write('"%s" "%s"\n' % (muTitle, muID))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)
		except:
			pass

class ssNeueEpisoden(MPScreen):

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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Serienstream.to")
		self['ContentTitle'] = Label("Neue Episoden")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.cover = None

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = BASE_URL
		getPage(url, agent=ss_agent, cookies=ss_ck).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		neue = re.findall('<td><a\shref="(/serie/stream/.*?)">(.*?)</a>.{0,1}</td>', data)
		if neue:
			for url, episodenName in neue:
				if re.search('S\d+\sE\d+', episodenName):
					title = re.sub('S\d+\sE\d+.*?', '', episodenName)
					get = re.findall('S(\d+)\sE(\d+)', episodenName)
					if get:
						(staffel, episode) = get[0]
						if int(staffel) < 10:
							staffel = "S0"+str(staffel)
						else:
							staffel = "S"+str(staffel)
						if int(episode) < 10:
							episode = "E0"+str(episode)
						else:
							episode = "E"+str(episode)
						title = "%s - %s%s" % (title, staffel, episode)
				else:
					title = episodenName
				url = BASE_URL + url
				self.streamList.append((title, url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No episodes found!'), None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		episodenName = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.openWithCallback(self.reloadList, ssStreams, episodenName, episodenName, url, self.cover)

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		episodenName = self['liste'].getCurrent()[0][0]
		self['name'].setText(episodenName)
		self.getCover()

	def getCover(self):
		url = self['liste'].getCurrent()[0][1]
		getPage(url, agent=ss_agent, cookies=ss_ck).addCallback(self.setCoverUrl).addErrback(self.dataError)

	def setCoverUrl(self, data):
		cover = re.findall('<div class=".*?picture">.*?<img src="(http://serienstream.to/public/img/cover/.*?)"', data, re.S)
		if cover:
			self.cover = cover[0]
			CoverHelper(self['coverArt']).getCover(self.cover, agent=ss_agent, cookieJar=ss_cookies)

	def reloadList(self):
		self.keyLocked = True
		self.loadPage()

class ssWatchlist(MPScreen):

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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"red" : self.keyDel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Serienstream.to")
		self['ContentTitle'] = Label("Watchlist")
		self['F1'] = Label(_("Delete"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.cover = None

		self.keyLocked = True
		self.cove = None
		self.onLayoutFinish.append(self.loadPlaylist)

	def loadPlaylist(self):
		self.keyLocked = True
		self.streamList = []
		self.wl_path = config.mediaportal.watchlistpath.value+"mp_ss_watchlist"
		try:
			readStations = open(self.wl_path,"r")
			rawData = readStations.read()
			readStations.close()
			for m in re.finditer('"(.*?)" "(.*?)"', rawData):
				(stationName, stationLink) = m.groups()
				self.streamList.append((stationName, stationLink))
		except:
			pass
		if len(self.streamList) == 0:
			self.streamList.append((_('Watchlist is currently empty'), None))
		else:
			self.streamList.sort()
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		self.getCover()

	def getCover(self):
		url = self['liste'].getCurrent()[0][1]
		getPage(url, agent=ss_agent, cookies=ss_ck).addCallback(self.setCoverUrl).addErrback(self.dataError)

	def setCoverUrl(self, data):
		cover = re.findall('<div class=".*?picture">.*?<img src="(http://serienstream.to/public/img/cover/.*?)"', data, re.S)
		if cover:
			self.cover = cover[0]
			CoverHelper(self['coverArt']).getCover(self.cover, agent=ss_agent, cookieJar=ss_cookies)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		serienTitle = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(ssStaffeln, serienTitle, url, self.cover)

	def keyDel(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		i = self['liste'].getSelectedIndex()
		c = j = 0
		l = len(self.streamList)
		try:
			f1 = open(self.wl_path, 'w')
			while j < l:
				if j != i:
					(stationName, stationLink) = self.streamList[j]
					f1.write('"%s" "%s"\n' % (stationName, stationLink))
				j += 1
			f1.close()
			self.loadPlaylist()
		except:
			pass

class ssStaffeln(MPScreen):

	def __init__(self, session, Title, Url, Cover):
		self.Url = Url
		self.Title = Title
		self.cover = Cover
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Serienstream.to")
		self['ContentTitle'] = Label(_("Season Selection"))
		self['name'] = Label(self.Title)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.Url, agent=ss_agent, cookies=ss_ck).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('class="hosterSiteDirectNav">(.*?)</div>', data, re.S)
		staffeln = re.findall('<a\s.*?href="(/serie/stream/.*?/staffel-(\d+))"', parse.group(1), re.S)
		if staffeln:
			for url, staffel in staffeln:
				url = BASE_URL + url
				self.streamList.append((_("Season")+" "+staffel, url, staffel))
		if len(self.streamList) == 0:
			self.streamList.append((_('No seasons found!'), None))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		CoverHelper(self['coverArt']).getCover(self.cover, agent=ss_agent, cookieJar=ss_cookies)
		self['name'].setText(self.Title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		staffel = self['liste'].getCurrent()[0][2]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(ssEpisoden, url, staffel, self.Title, self.cover)

class ssEpisoden(MPScreen):

	def __init__(self, session, Url, Staffel, Title, Cover):
		self.Url = Url
		self.Staffel = Staffel
		self.Title = Title
		self.cover = Cover
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Serienstream.to")
		self['ContentTitle'] = Label(_("Episode Selection"))
		self['name'] = Label(self.Title)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.Url, agent=ss_agent, cookies=ss_ck).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.watched_liste = []
		self.mark_last_watched = []
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_bs_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_bs_watched","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_bs_watched"):
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_bs_watched")
			if not leer == 0:
				self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_bs_watched" , "r")
				for lines in sorted(self.updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						self.watched_liste.append("%s" % (line[0]))
				self.updates_read.close()
		parse = re.search('class="pageTitle">(.*?)id="footer">', data, re.S)
		episoden = re.findall('Folge\s(\d+).*?class="seasonEpisodeTitle">.*?href="(.*?)".*?<strong>(.*?)</strong>.*?<span>(.*?)</span>', parse.group(1), re.S)
		if episoden:
			for episode, url, title_de, title_en in episoden:
				if int(self.Staffel) < 10:
					staffel = "S0"+str(self.Staffel)
				else:
					staffel = "S"+str(self.Staffel)
				if int(episode) < 10:
					episode = "E0"+str(episode)
				else:
					episode = "E"+str(episode)
				if title_de == "":
					title = title_en.strip()
					Flag = "EN"
					check = (decodeHtml(self.Title)) + " - " + staffel + episode + " - " + (decodeHtml(title_en.strip()))
				else:
					title = title_de.strip()
					Flag = "DE"
					check = (decodeHtml(self.Title)) + " - " + staffel + episode + " - " + (decodeHtml(title_de.strip()))
				episodenName = staffel + episode + " - " + title
				checkname = check
				checkname2 = check.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('Ä','Ae').replace('Ö','Oe').replace('Ü','Ue')
				url = BASE_URL + url
				if (checkname in self.watched_liste) or (checkname2 in self.watched_liste):
					self.streamList.append((decodeHtml(episodenName), url, True, Flag))
				else:
					self.streamList.append((decodeHtml(episodenName), url, False, Flag))
		if len(self.streamList) == 0:
			self.streamList.append((_('No episodes found!'), None, False, None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleftmarked, self.streamList))
		CoverHelper(self['coverArt']).getCover(self.cover, agent=ss_agent, cookieJar=ss_cookies)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		episodenName = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.openWithCallback(self.reloadList, ssStreams, self.Title, episodenName, url, self.cover)

	def reloadList(self):
		self.keyLocked = True
		self.loadPage()

class ssStreams(MPScreen):

	def __init__(self, session, title, episode, url, cover):
		self.serienUrl = url
		self.cover = cover
		self.Title = title
		self.episode = episode
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Serienstream.to")
		self['leftContentTitle'] = Label(_("Stream Selection"))
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.Title)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.serienUrl, agent=ss_agent, cookies=ss_ck).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		streams = re.findall('episodeLink\d+"\sdata-lang-key="(.*?)">.*?"(.*?)".*?class="icon\s(.*?)"', data, re.S)
		if streams:
			for (language, url, hoster) in streams:
				if isSupportedHoster(hoster, True):
					if language == "1":
						Flag = "DE"
					elif language == "2":
						Flag = "EN"
					else:
						Flag = "DEUS"
					self.streamList.append((hoster, url, False, Flag))
		if len(self.streamList) == 0:
			self.streamList.append((_('No supported streams found!'), None, False, ""))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleftmarked, self.streamList))
		CoverHelper(self['coverArt']).getCover(self.cover, agent=ss_agent, cookieJar=ss_cookies)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			get_stream_link(self.session).check_link(url, self.playfile)

	def playfile(self, stream_url):
		if not re.search('\S[0-9][0-9]E[0-9][0-9]', self.Title, re.I):
			self.streamname = self.Title + " - " + self.episode
		else:
			self.streamname = self.Title
		if re.search('\sS[0-9][0-9]E[0-9][0-9]', self.streamname) and not re.search('-\sS[0-9][0-9]E[0-9][0-9]', self.streamname):
			new_title = ""
			splits = re.split('(S[0-9][0-9]E[0-9][0-9])', self.streamname, re.I)
			count = 0
			for split in splits:
				if count == 1:
					new_title += "- "
				new_title += split
				count += 1
			self.streamname = new_title
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_bs_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_bs_watched","w").close()
		self.update_liste = []
		leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_bs_watched")
		if not leer == 0:
			self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_bs_watched" , "r")
			for lines in sorted(self.updates_read.readlines()):
				line = re.findall('"(.*?)"', lines)
				if line:
					self.update_liste.append("%s" % (line[0]))
			self.updates_read.close()
			updates_read2 = open(config.mediaportal.watchlistpath.value+"mp_bs_watched" , "a")
			check = ("%s" % self.streamname)
			if not check in self.update_liste:
				print "update add: %s" % (self.streamname)
				updates_read2.write('"%s"\n' % (self.streamname))
				updates_read2.close()
			else:
				print "dupe %s" % (self.streamname)
		else:
			updates_read3 = open(config.mediaportal.watchlistpath.value+"mp_bs_watched" , "a")
			print "update add: %s" % (self.streamname)
			updates_read3.write('"%s"\n' % (self.streamname))
			updates_read3.close()
		self.session.open(SimplePlayer, [(self.streamname, stream_url, self.cover)], showPlaylist=False, ltype='serienstream', cover=True)