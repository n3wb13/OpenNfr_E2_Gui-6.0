# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

baseurl = "http://www.bild.de"

class bildFirstScreen(MPScreen):

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
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Bild.de")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Startseite", "/video/startseite/bildchannel-home/video-home-15713248.bild.html"))
		self.genreliste.append(("News", "/video/clip/news/news-15477962.bild.html"))
		self.genreliste.append(("Politik", "/video/clip/politik/politik-15714862.bild.html"))
		self.genreliste.append(("Unterhaltung", "/video/clip/unterhaltung/unterhaltung-15478026.bild.html"))
		self.genreliste.append(("Fussball", "/video/clip/fussball/fussball-15716788.bild.html"))
		self.genreliste.append(("Sport", "/video/clip/sport/sport-15717150.bild.html"))
		self.genreliste.append(("Auto", "/video/clip/auto/auto-15711140.bild.html"))
		self.genreliste.append(("Lifestyle", "/video/clip/lifestyle/lifestyle-15716870.bild.html"))
		self.genreliste.append(("Bild-Boxx", "/video/clip/bild-boxx/bild-boxx-34731956.bild.html"))
		self.genreliste.append(("Lustige Tiervideos", "/video/clip/tiervideos/tiervideos-25998606.bild.html"))
		self.genreliste.append(("Viral", "/video/clip/virale-videos/virale-videos-36659638.bild.html"))
		self.genreliste.append(("Knops Kult Liga", "/video/clip/knops-kult-liga/knops-kult-liga-15718778.bild.html"))
		self.genreliste.append(("Bundesliga", "/video/clip/bundesliga-bei-bild/bundesliga-bei-bild-33009168.bild.html"))
		self.genreliste.append(("Leser-Reporter", "/video/clip/leserreporter/leser-reporter-15714330.bild.html"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def pincheckok(self, pincode):
		name = self['liste'].getCurrent()[0][0]
		url = baseurl + self['liste'].getCurrent()[0][1]
		if pincode:
			self.session.open(bildSecondScreen, url, name)

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = baseurl + self['liste'].getCurrent()[0][1]
		self.session.open(bildSecondScreen, url, name)

class bildSecondScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, link, name):
		self.link = link
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
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("Bild.de")
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 0
		self.lastpage = 0
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		getPage(self.link).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, '<div class="pag">(.*?)</div>')
		if self.getLastPage:
			self['page'].setText("%s / %s" % (str(self.page+1), str(self.lastpage)))

		raw = re.search('(Aktuellste|Neueste|Alle)\sVideos</h2>(.*)</section></div></div>', data, re.S).groups()
		if raw:
			seasons = re.findall('class="active">.*?data-ajax-href="(.*?)page=.*?,(.*?)"', raw[1], re.S)
			if seasons:
				vid_id1 = seasons[0][0]
				vid_id2 = seasons[0][1]
				nexturl = baseurl + vid_id1 + "page=" + str(self.page) + "," + vid_id2
				getPage(nexturl).addCallback(self.parseData2).addErrback(self.dataError)

	def parseData2(self, data):
		categorys =  re.findall('class="hentry.*?<a\shref="([^#].*?)".*?src="(.*?)".*?class="kicker">(.*?)<.*?class="headline">(.*?)</h3>', data, re.S)
		for (Url, Image, Title, handlung) in categorys:
			if not re.match('.*?bild-plus', Url):
				self.filmliste.append((decodeHtml(Title + " - " + stripAllTags(handlung.replace('</span><span>',' '))), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"),"",""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page+1, self.lastpage, mode=1, pagefix=-1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 1:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.keyLocked:
			return
		if self.page+1 < self.lastpage:
			self.page += 1
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		url = baseurl + self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.parseVideoData).addErrback(self.dataError)

	def parseVideoData(self, data):
		medialink = re.findall('data-media="(.*?)"', data, re.S)
		if medialink:
			getxml = baseurl + medialink[0]
			getPage(getxml).addCallback(self.playVideo).addErrback(self.dataError)

	def playVideo(self, data):
		streamlink = re.search('"src":"(.*?)"', data, re.S)
		if streamlink:
			title = self['liste'].getCurrent()[0][0]
			if re.match('.*?\/ondemand\/', streamlink.group(1)):
				host = streamlink.group(1).split('ondemand/')[0]
				playpath = streamlink.group(1).split('ondemand/')[1]
				final = "%sondemand/ playpath=mp4:%s swfVfy=1" % (host, playpath)
			else:
				final = streamlink.group(1)
			self.session.open(SimplePlayer, [(title, final)], showPlaylist=False, ltype='Bild.de')