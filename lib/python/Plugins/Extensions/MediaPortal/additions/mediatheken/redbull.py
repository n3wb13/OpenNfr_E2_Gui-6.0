# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

basename = "Red Bull TV"
baseurl ="https://api.redbull.tv/v1/"

class RBtvGenreScreen(MPScreen):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Search", baseurl+"channels/sports/episodes?search="))
		self.genreliste.append(("Shows", baseurl+"/shows/series?limit=100"))
		self.genreliste.append(("Adventure", baseurl+"channels/sports/adventure/shows?limit=100"))
		self.genreliste.append(("Aerial", baseurl+"channels/sports/aerial/shows?limit=100"))
		self.genreliste.append(("Arts & Lifestyle", baseurl+"channels/artsandlifestyle/shows?limit=100"))
		self.genreliste.append(("Compilation", baseurl+"channels/sports/compilation/shows?limit=100"))
		self.genreliste.append(("More Sports", baseurl+"channels/sports/other/shows?limit=100"))
		self.genreliste.append(("Motorsports", baseurl+"channels/sports/motorsports/shows?limit=100"))
		self.genreliste.append(("Music", baseurl+"channels/music/shows?limit=100"))
		self.genreliste.append(("Skateboarding", baseurl+"channels/sports/skateboarding/shows?limit=100"))
		self.genreliste.append(("Watersports", baseurl+"channels/sports/watersports/shows?limit=100"))
		self.genreliste.append(("Winter Sports", baseurl+"channels/sports/wintersports/shows?limit=100"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if name == "Search":
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True)
		else:
			self.session.open(rbtvshows, name, url)

	def searchCallback(self, callbackStr):
		if callbackStr is not None:
			name = "Search"
			url = self['liste'].getCurrent()[0][1]
			url = url + "%s" % callbackStr.replace(' ','+')
			self.session.open(rbtvshows, name, url)

class rbtvshows(MPScreen):

	def __init__(self, session,name,url):
		self.url = url
		self.name = name
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self.keyLocked = True
		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "%s" % (self.url)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if re.match('.*?total_results":0', data):
			self.filmliste.append((_('No shows found!'), None, None, None))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		else:
			shows = re.findall('"title":"(.*?)",.*?"short_description":"(.*?)",.*?"images".*?"uri":"(.*?)".*?"episodes":"(.*?)"', data, re.S)
			if shows:
				for (title,desc,pic,url) in shows:
					self.filmliste.append((decodeHtml(title),url,decodeHtml(desc).replace('\\"','"'),pic))
				self.ml.setList(map(self._defaultlistcenter, self.filmliste))
				self.ml.moveToIndex(0)
				self.keyLocked = False
				self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		desc = self['liste'].getCurrent()[0][2]
		pic = self['liste'].getCurrent()[0][3]
		pic = pic + "/width=125"
		self['handlung'].setText(desc)
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(rbtvepisodes, name, url)

class rbtvepisodes(MPScreen):

	def __init__(self, session,name,url):
		self.url = url
		self.name = name
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self.keyLocked = True
		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "%s" % (self.url) + "?limit=100"
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if re.match('.*?total_results":0', data):
			self.filmliste.append((_('No episodes found!'), None, None, None))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		else:
			shows = re.findall('{"id":"(.*?)".*?type":"(.*?)".*?title":"(.*?)",.*?subtitle":"(.*?)".*?vin":"(.*?)".*?long_description":"(.*?)",.*?duration":"(.*?)".*?published_on":"(.*?)".*?"images".*?uri":"(.*?)".*?"show":{', data, re.S)
			if shows:
				for (id,type,title,subtitle,vin,longdesc,duration,publicated,pic) in shows:
					title = title + " - " + subtitle
					self.filmliste.append((decodeHtml(title),decodeHtml(longdesc).replace('\\"','"'),duration,publicated,pic,id,vin,type))
				self.ml.setList(map(self._defaultlistleft, self.filmliste))
				self.ml.moveToIndex(0)
				self.keyLocked = False
				self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		longdescr = self['liste'].getCurrent()[0][1]
		duration = self['liste'].getCurrent()[0][2]
		published = self['liste'].getCurrent()[0][3]
		pic = self['liste'].getCurrent()[0][4] + "/width=125"
		descr = "Published: %s     Runtime: %s\n%s" % (published,duration,longdescr)
		self['handlung'].setText(descr)
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][5]
		vin = self['liste'].getCurrent()[0][6]
		type = self['liste'].getCurrent()[0][7]
		url = "https://api.redbull.tv/v1/videos/" + url +"?type="+type+"?vin="+vin
		getPage(url).addCallback(self.loadm3u8).addErrback(self.dataError)

	def loadm3u8(self, data):
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		url = re.findall('"uri":"(https://api.redbull.tv/v1/playlists/.*?\.m3u8.*?)",', data, re.S)[0]
		getPage(url).addCallback(self.loadplaylist).addErrback(self.dataError)

	def loadplaylist(self, data):
		videoPrio = int(config.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			bw = 8000000
		elif videoPrio == 1:
			bw = 3000000
		else:
			bw = 1500000
		title = self['liste'].getCurrent()[0][0]
		self.bandwith_list = []
		match_sec_m3u8=re.findall('BANDWIDTH=(.*?),.*?RESOLUTION=(.*?),.*?(http://.*?m3u8)', data, re.S)
		for each in match_sec_m3u8:
			bandwith,resolution,url = each
			self.bandwith_list.append((int(bandwith),url))
		_, best = min((abs(int(x[0]) - bw), x) for x in self.bandwith_list)
		self['name'].setText(title)
		self.keyLocked = False
		self.session.open(SimplePlayer, [(title, best[1])], showPlaylist=False, ltype='redbulltv')