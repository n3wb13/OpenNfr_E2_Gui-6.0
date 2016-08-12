# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

class LiveLeakScreen(MPScreen):

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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("LiveLeak.com")
		self['ContentTitle'] = Label("Genre:")
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Featured Items", "http://www.liveleak.com/rss?featured=1&page="))
		self.genreliste.append(("Recent Items (All)", "http://www.liveleak.com/rss?selection=all&page="))
		self.genreliste.append(("Recent Items (Popular)", "http://www.liveleak.com/rss?selection=popular&page="))
		self.genreliste.append(("Top (Today)", "http://www.liveleak.com/rss?rank_by=day&page="))
		self.genreliste.append(("Top (Week)", "http://www.liveleak.com/rss?rank_by=week&page="))
		self.genreliste.append(("Top (Month)", "http://www.liveleak.com/rss?rank_by=month&page="))
		self.genreliste.append(("Top (All)", "http://www.liveleak.com/rss?rank_by=all_time&page="))
		self.genreliste.append(("Must See", "http://www.liveleak.com/rss?channel_token=9ee_1303244161&page="))
		self.genreliste.append(("Yoursay", "http://www.liveleak.com/rss?channel_token=1b3_1302956579&page="))
		self.genreliste.append(("News", "http://www.liveleak.com/rss?channel_token=04c_1302956196&page="))
		self.genreliste.append(("Entertainment", "http://www.liveleak.com/rss?channel_token=51a_1302956523&page="))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		print streamGenreLink
		self.session.open(LiveLeakClips, streamGenreLink, Name)

class LiveLeakClips(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, Name):
		self.streamGenreLink = streamGenreLink
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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self['title'] = Label("LiveLeak.com")
		self['ContentTitle'] = Label("Auswahl: %s" %self.Name)

 		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "%s%s&safe_mode=off" % (self.streamGenreLink, str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		rssfeed = re.findall('<item>.*?<title>(.*?)</title>.*?<link>(http://www.liveleak.com/view.*?)</link>.*?<description>(.*?)</description>.*?<media:thumbnail\surl="(.*?)"', data, re.S)
		if rssfeed:
			self.feedliste = []
			for (title,url,desc,image) in rssfeed:
				if not re.match('LiveLeak.com Rss Feed', title, re.S|re.I):
					self.feedliste.append((decodeHtml(title.replace('&amp;','&')),url,image,decodeHtml(desc.strip())))
			self.ml.setList(map(self._defaultlistleft, self.feedliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.feedliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		desc = self['liste'].getCurrent()[0][3]
		self['name'].setText(Title)
		self['handlung'].setText(desc)
		self['page'].setText(str(self.page))
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		title = self['liste'].getCurrent()[0][0]
		Stream = re.findall('file: "(.*?)"', data, re.S)
		if Stream:
			print Stream
			self.session.open(SimplePlayer, [(title, Stream[0])], showPlaylist=False, ltype='liveleak')
		else:
			videoPage = re.findall('"http://www.youtube.com/(v|embed)/(.*?)\?.*?"', data, re.S)
			if videoPage:
				self.session.open(YoutubePlayer,[(title, videoPage[0][1], None)],playAll= False,showPlaylist=False,showCover=False)