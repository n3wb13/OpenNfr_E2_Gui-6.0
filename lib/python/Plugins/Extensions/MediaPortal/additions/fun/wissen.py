# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class wissenListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
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
			"up": self.keyUp,
			"down": self.keyDown,
			"right": self.keyRight,
			"left": self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Wissen.de")
		self['ContentTitle'] = Label("Videos:")
		self['Page'] = Label(_("Page:"))

		self.videoliste = []
		self.page = 0
		self.lastpage = 0

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.videoliste = []
		url = "http://www.wissen.de/medien-videos/all?page=%s" % str(self.page)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		lastlast = re.search('class="pager-last\slast".*?all\?page=(.*?)"', data, re.S)
		currentlast = re.search('pager-current\slast">(.*?)</li>', data, re.S)
		if lastlast:
			lastp = int(lastlast.group(1))
		else:
			lastp = int(currentlast.group(1))-1
		if lastp:
			lastp = lastp
			self.lastpage = lastp
		else:
			self.lastpage = 0
		self['page'].setText(str(self.page+1) + ' / ' + str(self.lastpage+1))

		preparse = re.findall('<div\sclass="views-row\sviews-row-\d+\sviews-row-(odd|even)(.*?teaser-h2.*?)</div', data, re.S)
		for (dummy, videos) in preparse:
			video = re.findall('<a\shref="(/video/.*?)">.*?background-image..url\(\'(.*?)\'.*?class="teaser-h3">Video</p>.*?<p\sclass="teaser-h2">(.*?)</p>', videos, re.S)
			if video:
				for (url, img, title) in video:
					url = "http://www.wissen.de%s" % url
					self.videoliste.append((decodeHtml(title), url, img))
		self.ml.setList(map(self._defaultlistleft, self.videoliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.videoliste, 0, 1, 2, None, None, self.page+1, self.lastpage, mode=1, pagefix=-1)
		self.showInfos()

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 1:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.keyLocked:
			return
		if self.page < self.lastpage:
			self.page += 1
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		self.wissentitle = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.get_videourl).addErrback(self.dataError)

	def get_videourl(self, data):
		videourls = re.findall('sources:\s.*?file:\s"(.*?)"', data, re.S)
		if videourls:
			self.session.open(SimplePlayer, [(self.wissentitle, videourls[-1])], showPlaylist=False, ltype='wissen')