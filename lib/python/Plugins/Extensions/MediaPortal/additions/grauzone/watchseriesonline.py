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

wso_url = "watchseries-online.se"

class wsoMain(MPScreen):

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

		self['title'] = Label("watchseries-online")
		self['ContentTitle'] = Label(_("Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)
		self.keyLocked = False

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(('A-Z',"index"))
		self.streamList.append(('Last 350 Episodes',"new"))
		self.streamList.append(("Watchlist","watchlist"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		current = self['liste'].getCurrent()
		if self.keyLocked or current == None:
			return
		selection = current[0][1]
		if selection == "index":
			self.session.open(wsoIndex)
		elif selection == "new":
			self.session.open(wsoNewEpisodes)
		elif selection == "watchlist":
			self.session.open(wsoWatchlist)

class wsoIndex(MPScreen, SearchHelper):

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

		self['title'] = Label("watchseries-online")
		self['ContentTitle'] = Label(_("A-Z"))
		self['F2'] = Label(_("Add to Watchlist"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def goToLetter(self, num):
		self.keyNumberGlobal(num, self.streamList)
		self.showSearchkey(num)

	def loadPage(self):
		url = "http://%s/index" % wso_url
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('<div class="ddmcc"><ul>\s<p class="sep" id="goto\_\#">((.|\s)*?)<div style="clear:both;"><!-- --></div>', data, re.S)
		if parse:
			series = re.findall('<li><a\shref="(http://%s/category/.*?)">(.*?)</a></li>' % wso_url, parse.group(1), re.S)
			if series:
				for (url, serie) in series:
					self.streamList.append((decodeHtml(serie), url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No shows found!'), None))
		else:
			self.streamList.sort(key=lambda t : t[0].lower())
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		current = self['liste'].getCurrent()
		if self.keyLocked or current == None:
			return
		Title = current[0][0]
		Url = current[0][1]
		self.session.open(wsoEpisodes, Url, Title)

	def keyAdd(self):
		current = self['liste'].getCurrent()
		if self.keyLocked or current == None:
			return
		muTitle = current[0][0]
		muID = current[0][1]
		fn = config.mediaportal.watchlistpath.value+"mp_wso_watchlist"
		if not fileExists(fn):
			open(fn,"w").close()
		try:
			writePlaylist = open(fn, "a")
			writePlaylist.write('"%s" "%s"\n' % (muTitle, muID))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)
		except:
			pass

class wsoNewEpisodes(MPScreen):

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

		self['title'] = Label("watchseries-online")
		self['ContentTitle'] = Label("New Episodes")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = "http://%s/last-350-episodes" % wso_url
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		newEpisodes = re.findall('href="(http://%s/episode/.*?)".*?</span>(.*?)</a>\s</li>' % wso_url, data)
		if newEpisodes:
			for url, episodeName in newEpisodes:
				self.streamList.append((decodeHtml(episodeName), url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No episodes found!'), None))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		currentEpisode = self['liste'].getCurrent()
		if self.keyLocked or currentEpisode == None:
			return
		episodeName = currentEpisode[0][0]
		url = currentEpisode[0][1]
		self.session.openWithCallback(self.reloadList, wsoStreams, episodeName, episodeName, url)

	def reloadList(self):
		self.keyLocked = True
		self.loadPage()

class wsoWatchlist(MPScreen):

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

		self['title'] = Label("watchseries-online")
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
		self.wl_path = config.mediaportal.watchlistpath.value+"mp_wso_watchlist"
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
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		current = self['liste'].getCurrent()
		if self.keyLocked or current == None:
			return
		title = current[0][0]
		self['name'].setText(title)

	def keyOK(self):
		current = self['liste'].getCurrent()
		if self.keyLocked or current == None:
			return
		serieTitle = current[0][0]
		url = current[0][1]
		self.session.open(wsoEpisodes, url, serieTitle)

	def keyDel(self):
		current = self['liste'].getCurrent()
		if self.keyLocked or current == None:
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

class wsoEpisodes(MPScreen):

	def __init__(self, session, Url, Title):
		self.Url = Url
		self.Title = Title
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

		self['title'] = Label("watchseries-online")
		self['ContentTitle'] = Label(_("Episode Selection"))
		self['name'] = Label(self.Title)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.Url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.watched_list = []
		self.mark_last_watched = []
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_wso_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_wso_watched","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_wso_watched"):
			empty = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_wso_watched")
			if not empty == 0:
				self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_wso_watched" , "r")
				for lines in sorted(self.updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						self.watched_list.append("%s" % (line[0]))
				self.updates_read.close()
		parse = re.search('<div id="episode-list">((.|\s)*?)</div> <!-- \.post_wrapper -->', data, re.S)
		#parse = re.search('class="container Sheet-body"(.*?)<script type=', data, re.S)
		if parse:
			episodes = re.findall("<a\shref='(http://%s/.*?)'.*?</span>(.*?)</a>" % wso_url, parse.group(1), re.S)
			if episodes:
				for url, title in episodes:
					title=title.strip()
					checkname = (decodeHtml(self.Title)) + " - " + (decodeHtml(title.strip()))
					checkname2 = checkname.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('Ä','Ae').replace('Ö','Oe').replace('Ü','Ue')
					if (checkname in self.watched_list) or (checkname2 in self.watched_list):
						self.streamList.append((decodeHtml(title), url, True, None))
					else:
						self.streamList.append((decodeHtml(title), url, False, None))
		if len(self.streamList) == 0:
			self.streamList.append((_('No episodes found!'), None, False, None))
		self.ml.setList(map(self._defaultlistleftmarked, self.streamList))
		self.keyLocked = False

	def keyOK(self):
		currentEpisode = self['liste'].getCurrent()
		if self.keyLocked or currentEpisode == None:
			return
		episodeName = currentEpisode[0][0]
		url = currentEpisode[0][1]
		self.session.openWithCallback(self.reloadList, wsoStreams, self.Title, episodeName, url)

	def reloadList(self):
		self.keyLocked = True
		self.loadPage()

class wsoStreams(MPScreen):

	def __init__(self, session, title, episode, url):
		self.serieUrl = url
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

		self['title'] = Label("watchseries-online")
		self['leftContentTitle'] = Label(_("Stream Selection"))
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.Title)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)
		self.tw_agent_hlp = TwAgentHelper()

	def loadPage(self):
		getPage(self.serieUrl).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		streams = re.findall('<a\starget="_blank"\srel="nofollow"\shref="(.*?)">(.*?)</a>', data, re.S)
		if streams:
			for (url, hoster) in streams:
				if isSupportedHoster(hoster, True):
					self.streamList.append((hoster, url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.streamList))
		self.keyLocked = False

	def keyOK(self):
		current = self['liste'].getCurrent()
		if self.keyLocked or current == None:
			return
		url = current[0][1]
		if url:
			self.tw_agent_hlp.getRedirectedUrl(url).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, url):
		get_stream_link(self.session).check_link(url, self.playfile)

	def playfile(self, stream_url):
		if not re.search('\S[0-9][0-9]E[0-9][0-9]', self.Title, re.I):
			self.streamname = self.Title + " - " + self.episode
		else:
			self.streamname = self.Title
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_wso_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_wso_watched","w").close()
		self.update_list = []
		empty = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_wso_watched")
		if not empty == 0:
			self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_wso_watched" , "r")
			for lines in sorted(self.updates_read.readlines()):
				line = re.findall('"(.*?)"', lines)
				if line:
					self.update_list.append("%s" % (line[0]))
			self.updates_read.close()
			updates_read2 = open(config.mediaportal.watchlistpath.value+"mp_wso_watched" , "a")
			check = ("%s" % self.streamname)
			if not check in self.update_list:
				print "update add: %s" % (self.streamname)
				updates_read2.write('"%s"\n' % (self.streamname))
				updates_read2.close()
			else:
				print "dupe %s" % (self.streamname)
		else:
			updates_read3 = open(config.mediaportal.watchlistpath.value+"mp_wso_watched" , "a")
			print "update add: %s" % (self.streamname)
			updates_read3.write('"%s"\n' % (self.streamname))
			updates_read3.close()
		self.session.open(SimplePlayer, [(self.streamname, stream_url)], showPlaylist=False, ltype='watchseriesonline')