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
from Plugins.Extensions.MediaPortal.resources.configlistext import ConfigListScreenExt
from Plugins.Extensions.MediaPortal.resources.imports import *

glob_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0'
premium = False
keckse = {}
BASE_URL = 'http://seriesever.net'

config.mediaportal.seriesever_userName = ConfigText(default="USERNAME", fixed_size=False)
config.mediaportal.seriesever_userPass = ConfigPassword(default="PASSWORD", fixed_size=False)

class serieseverMain(MPScreen):

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
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue" : self.loginSetup
		}, -1)

		self['title'] = Label("SeriesEver")
		self['ContentTitle'] = Label(_("Genre Selection"))
		self['F4'] = Label(_("Setup"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(("New Added", BASE_URL))
		self.streamList.append(("Alle Serien", BASE_URL))
		self.streamList.append(("Watchlist", None))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()
		self.login(False)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		if auswahl == "Watchlist":
			self.session.open(serieseverWatchlist)
		else:
			url = self['liste'].getCurrent()[0][1]
			self.session.open(serieseverParsing, auswahl, url)

	def login(self, msg=False):
		self.username = config.mediaportal.seriesever_userName.value
		self.password = config.mediaportal.seriesever_userPass.value
		if not self.username == "USERNAME" and not self.password == "PASSWORD":
			loginUrl = BASE_URL + '/service/login'
			loginData = {'username': self.username, 'password': self.password}
			getPage(loginUrl, method='POST', agent=glob_agent, postdata=urlencode(loginData), cookies=keckse, headers={'Referer': BASE_URL, 'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.loginCheck, msg).addErrback(self.dataError)
		else:
			self.setPremium(False)

	def loginCheck(self, data, msg):
		if re.search(self.username, data, re.S|re.I):
			url = BASE_URL + "/premium.html"
			getPage(url, cookies=keckse, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.checkPremium, msg).addErrback(self.dataError)
		else:
			self.setPremium(False)
			if msg:
				message = self.session.open(MessageBoxExt, _("Login failed!"), MessageBoxExt.TYPE_INFO, timeout=3)

	def checkPremium(self, data, msg):
		if re.search('<strong>Status.*?</strong>.*?Premium</p>', data, re.S|re.I):
			self.setPremium(True)
		else:
			self.setPremium(False)
			if msg:
				message = self.session.open(MessageBoxExt, _("You are not a Premium User!"), MessageBoxExt.TYPE_INFO, timeout=3)

	def setPremium(self, status):
		global premium
		premium = status
		if premium:
			self['title'].setText("SeriesEver - Premium (1080p)")
		else:
			self['title'].setText("SeriesEver")

	def loginSetup(self):
		if mp_globals.isDreamOS:
			self.session.openWithCallback(self.callBackSetup, serieseverSetupScreen, is_dialog=True)
		else:
			self.session.openWithCallback(self.callBackSetup, serieseverSetupScreen)

	def callBackSetup(self, answer):
		if answer:
			self.login(True)

	def keyCancel(self):
		url = BASE_URL + "/service/logout.html"
		getPage(url, cookies=keckse, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'})
		self.close()

class serieseverParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green"	: self.keyAdd
		}, -1)

		self['title'] = Label("SeriesEver")
		self['ContentTitle'] = Label("%s" % self.genre)
		self['F2'] = Label(_("Add"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self.streamList.append(('Loading...', None))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.streamList = []
		getPage(self.url, agent=glob_agent).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if self.genre == "Alle Serien":
			m = re.search('="collapse" href="#mc-seriens">(.*?)</ul>\s*</li>\s*</ul>\s*</li>\s*<li>', data, re.S)
			if m:
				for serie in re.finditer('<a data-toggle="collapse" href="#sc-.*?">(.*?)</a>.*?<li><a href="(.*?)staffel-', m.group(1), re.S):
					Title,Url = serie.groups()
					self.streamList.append((decodeHtml(Title), Url))

			if len(self.streamList) == 0:
				self.streamList.append(('Parsing Fehler !', None))

			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.ml.moveToIndex(0)
			self.keyLocked = False
		else:
			for serie in re.finditer('<div class="box-content">.*?a href="(http://seriesever.*?)" class="play" title="(.*?)"><span class="i-play">.*?<img class="img" src="(http://seriesever.net.*?)".*?<div class="box-title">.*?<a href="(http://seriesever.net/.*?)"', data, re.S):
				UrlEpisode,Title,Image,UrlSerie = serie.groups()
				Image = Image.replace('thumb/','')
				self.streamList.append((decodeHtml(Title), UrlEpisode, Image, UrlSerie))

			if len(self.streamList) == 0:
				self.streamList.append((_('Parsing error!'), None))
				self.keyLocked = True
			else:
				self.keyLocked = False
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.ml.moveToIndex(0)
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		movie_url = self['liste'].getCurrent()[0][1]
		if self.genre == "Alle Serien":
			self.session.open(showStaffeln, stream_name, movie_url)
		else:
			self.session.open(showStreams, stream_name, movie_url)

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		if self.genre == "New Added":
			coverUrl = self['liste'].getCurrent()[0][2]
			CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		if self.genre == "Alle Serien":
			movie_url = self['liste'].getCurrent()[0][1]
		else:
			movie_url = self['liste'].getCurrent()[0][3]
		stream_name = self['liste'].getCurrent()[0][0]
		fn = config.mediaportal.watchlistpath.value+"mp_se_watchlist"
		if not fileExists(fn):
			open(fn,"w").close()
		try:
			writePlaylist = open(fn, "a")
			writePlaylist.write('"%s" "%s"\n' % (stream_name, movie_url))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)
		except:
			pass

class serieseverWatchlist(MPScreen, ThumbsHelper):

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
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyDel
		}, -1)

		self['title'] = Label("SeriesEver")
		self['ContentTitle'] = Label("Watchlist")
		self['F1'] = Label(_("Delete"))

		self.watchList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.readWatchlist)

	def readWatchlist(self):
		self.keyLocked = True
		self.watchList = []
		self.wl_path = config.mediaportal.watchlistpath.value+"mp_se_watchlist"
		try:
			readStations = open(self.wl_path,"r")
			rawData = readStations.read()
			readStations.close()
			for m in re.finditer('"(.*?)" "(.*?)"', rawData):
				(sName, sUrl) = m.groups()
				self.watchList.append((decodeHtml(sName), sUrl))
		except:
			pass
		if len(self.watchList) == 0:
			self.watchList.append((_('Watchlist is currently empty'), None))
		else:
			self.watchList.sort()
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.watchList))
		self.ml.moveToIndex(0)
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		movie_url = self['liste'].getCurrent()[0][1]
		self.session.open(showStaffeln, stream_name, movie_url)

	def keyDel(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		i = self['liste'].getSelectedIndex()
		c = j = 0
		l = len(self.watchList)
		try:
			f1 = open(self.wl_path, 'w')
			while j < l:
				if j != i:
					(sName, sUrl) = self.watchList[j]
					f1.write('"%s" "%s"\n' % (sName, sUrl))
				j += 1
			f1.close()
			self.readWatchlist()
		except:
			pass

class showStaffeln(MPScreen):

	def __init__(self, session, stream_name, url):
		self.stream_name = stream_name
		self.url = url
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("SeriesEver")
		self['ContentTitle'] = Label("Staffeln / Episode")
		self['name'] = Label(self.stream_name)

		self.staffeln = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.coverUrl = None
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.staffeln = []
		self.staffeln.append((_('Please wait...'), None))
		self.ml.setList(map(self._defaultlistcenter, self.staffeln))
		self.staffeln = []
		getPage(self.url, agent=glob_agent).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		cover = re.findall('<a class="cover" href=".*?" title=".*?"><img src="(http://seriesever.net/uploads/posters/.*?)"', data, re.S)
		if cover:
			self.coverUrl = cover[0].replace('thumb/','')
			CoverHelper(self['coverArt']).getCover(self.coverUrl)

		staffeln_raw = re.findall('<meta itemprop="numberOfEpisodes" content=".*?"/>.*?<a class="seep" href="(.*?)" title="(.*?)\sStaffel\s(\d+)\sEpisode.(\d+)" itemprop="url"><span itemprop="name">', data, re.S)
		if staffeln_raw:
			for Url,Title,Staffel,Episode in staffeln_raw:
				if int(Staffel) < 10:
					Staffel = "S0%s" % str(Staffel)
				else:
					Staffel = "S%s" % str(Staffel)
				if int(Episode) < 10:
					Episode = "E0%s" % str(Episode)
				else:
					Episode = "E%s" % str(Episode)
				Title = "%s%s" % (Staffel,Episode)
				self.staffeln.append((Title, Url))
			if len(self.staffeln) == 0:
				self.staffeln.append((_('Parsing error!'), None))
			self.ml.setList(map(self._defaultlistcenter, self.staffeln))
			self.ml.moveToIndex(0)
			self.keyLocked = False
		else:
			self.staffeln.append(('Für diese Serie wurde noch keine Episoden veröffentlicht.', None))
			self.ml.setList(map(self._defaultlistcenter, self.staffeln))
			self.ml.moveToIndex(0)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		staffel_auswahl = self['liste'].getCurrent()[0][0]
		staffel_url = self['liste'].getCurrent()[0][1]
		self.session.open(showStreams, self.stream_name+" - "+staffel_auswahl, staffel_url)

class showStreams(MPScreen):

	def __init__(self, session, stream_name, url):
		self.stream_name = stream_name
		self.url = url
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("SeriesEver")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.stream_name)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.coverUrl = None
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.coverUrl)
		self.streamList = []
		self.streamList.append(('Loading...', None))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.streamList = []
		getPage(self.url, agent=glob_agent).addCallback(self.getVideoID).addErrback(self.dataError)

	def getVideoID(self, data):
		cover = re.findall('<link rel="image_src" href="(.*?)"', data, re.S)
		if cover:
			self.coverUrl = cover[0]
			CoverHelper(self['coverArt']).getCover(self.coverUrl)
		url = BASE_URL + "/service/get_video_part"
		videoID = re.findall('var\svideo_id\s{0,2}=\s"(.*?)"', data)
		videoReso = re.findall('<li><a href="#" class="changePart" data-part="(.*?)">', data, re.S)
		if videoID:
			self.videoID = videoID[0]
			self.videoReso = videoReso[0]
			if "720p" in self.videoReso:
				post_data = urllib.urlencode({'page': '0', 'part_name': '720p', 'video_id': self.videoID})
				getPage(url, method='POST', postdata=post_data, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.parseData, "720p").addErrback(self.dataError)
			if "1080p" in self.videoReso:
				post_data = urllib.urlencode({'page': '0', 'part_name': '1080p', 'video_id': self.videoID})
				if premium:
					getPage(url, method='POST', cookies=keckse, postdata=post_data, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.parseData, "1080p").addErrback(self.dataError)
				else:
					getPage(url, method='POST', postdata=post_data, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.parseData, "1080p").addErrback(self.dataError)
			if "en-sub" in self.videoReso:
				post_data = urllib.urlencode({'page': '0', 'part_name': 'en-sub', 'video_id': self.videoID})
				getPage(url, method='POST', postdata=post_data, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.parseData, "en-sub").addErrback(self.dataError)
			if "de-sub" in self.videoReso:
				post_data = urllib.urlencode({'page': '0', 'part_name': 'de-sub', 'video_id': self.videoID})
				getPage(url, method='POST', postdata=post_data, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.parseData, "de-sub").addErrback(self.dataError)
		else:
			self.streamList.append(('No VideoID found.', None))
			self.ml.setList(map(self._defaultlistcenter, self.streamList))

	def parseData(self, data, video_reso):
		parts = re.findall('"part_count":(\d+),"', data)
		if parts:
			parts = parts[0]
			if parts > 0:
				for i in range(0,int(parts)):
					self.streamList.append(('Stream '+str(i+1)+' - '+video_reso, str(i)))
			else:
				self.streamList.append(('Keine Streams in '+video_reso+'vorhanden !', None))
			self.ml.setList(map(self._defaultlistcenter, self.streamList))
			self.ml.moveToIndex(0)
			self.keyLocked = False
		else:
			self.streamList.append(('Fehler auf der Webseite !', None))
			self.ml.setList(map(self._defaultlistcenter, self.streamList))
			self.ml.moveToIndex(0)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamID = self['liste'].getCurrent()[0][1]
		url = BASE_URL + "/service/get_video_part"
		if re.search('en-sub', streamName):
			post_data = urllib.urlencode({'page': streamID, 'part_name': 'en-sub', 'video_id': self.videoID})
			getPage(url, method='POST', agent=glob_agent, postdata=post_data, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.getStreamData).addErrback(self.dataError)
		if re.search('de-sub', streamName):
			post_data = urllib.urlencode({'page': streamID, 'part_name': 'de-sub', 'video_id': self.videoID})
			getPage(url, method='POST', agent=glob_agent, postdata=post_data, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.getStreamData).addErrback(self.dataError)
		if premium:
			post_data = urllib.urlencode({'page': streamID, 'part_name': '1080p', 'video_id': self.videoID})
			getPage(url, method='POST', agent=glob_agent, postdata=post_data, cookies=keckse, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.getStreamData).addErrback(self.dataError)
		else:
			post_data = urllib.urlencode({'page': streamID, 'part_name': '720p', 'video_id': self.videoID})
			getPage(url, method='POST', agent=glob_agent, postdata=post_data, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.getStreamData).addErrback(self.dataError)

	def getStreamData(self, data):
		try:
			data = json.loads(data)
			code = data['part']['code'].replace("!BeF","R").replace("@jkp","Ax")
			if 'http' in code:
				print code
				url = re.findall('src="(.*?)"', code)
				if url:
					print url
					if 'openload' in url[0]:
						get_stream_link(self.session).check_link(str(url[0]), self.got_link)
					elif 'everplay.watchpass.net' in url[0]:
						getPage(str(url[0]), agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseStream).addErrback(self.dataError)
					else:
						self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)
				else:
					self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)
			else:
				import base64
				stream_url = base64.b64decode(code)
				print stream_url
				get_stream_link(self.session).check_link(stream_url, self.got_link)
		except:
			self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)

	def parseStream(self, data):
		print data
		stream_url = re.findall('file:\s"(.*?)"', data)
		if stream_url:
			self.got_link(stream_url[0])
		else:
			self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)

	def got_link(self, stream_url):
		mp_globals.player_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0"
		self.session.open(SimplePlayer, [(self.stream_name, stream_url, self.coverUrl)], cover=True, showPlaylist=False, ltype='seriesever')

class serieseverSetupScreen(Screen, ConfigListScreenExt):

	def __init__(self, session):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/PluginUserDefault.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/PluginUserDefault.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		self['title'] = Label("SeriesEver " + _("Setup"))
		self['F4'] = Label('')
		self.setTitle("SeriesEver " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		self.list.append(getConfigListEntry(_("Username:"), config.mediaportal.seriesever_userName))
		self.list.append(getConfigListEntry(_("Password:"), config.mediaportal.seriesever_userPass))
		self["config"].setList(self.list)

		self["setupActions"] = ActionMap(["MP_Actions"],
		{
			"ok":		self.saveConfig,
			"cancel":	self.exit
		}, -1)

	def saveConfig(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close(True)

	def exit(self):
		self.close(False)