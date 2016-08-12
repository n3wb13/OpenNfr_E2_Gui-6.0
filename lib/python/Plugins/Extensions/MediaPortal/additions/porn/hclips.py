# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

class hclipsGenreScreen(MPScreen):

	def __init__(self, session):
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("HClips.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.hclips.com/categories/"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="thumb_holder(.*?)class="cat-text">', data, re.S)
		Cats = re.findall('<a\shref="(http://www.hclips.com/categories/.*?)".*?class="img"\ssrc="(.*?)".*?class="title">(.*?)</strong', parse.group(1), re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				self.genreliste.append((Title, Url, Image))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Longest", "http://www.hclips.com/longest/", None))
			self.genreliste.insert(0, ("Most Popular", "http://www.hclips.com/most-popular/", None))
			self.genreliste.insert(0, ("Top Rated", "http://www.hclips.com/top-rated/", None))
			self.genreliste.insert(0, ("Most Recent", "http://www.hclips.com/latest-updates/", None))
			self.genreliste.insert(0, ("--- Search ---", "", None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if re.search('--- Search', Name):
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True)
		else:
			self.session.open(hclipsFilmScreen, Link, Name)

	def searchCallback(self, callbackStr):
		Name = self['liste'].getCurrent()[0][0]
		if callbackStr is not None:
			self.session.open(hclipsFilmScreen, callbackStr, Name)

class hclipsFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("HClips.com")
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
		if not re.search('Search', self.Name):
			url = "%s%s/" % (self.Link, str(self.page))
		else:
			key = "AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY"
			start = (self.page-1)*20
			cx = "007041593788150376897:8pvxilcjx8e"
			q = "%s%s" % (self.Link,"%20inurl%3A%2F")
			url = "https://www.googleapis.com/customsearch/v1element?key=%s&num=20&hl=en&prettyPrint=false&cx=%s&q=%s&filter=0&start=%s"%(key,cx,q,start)
		twAgentGetPage(url, gzip_decoding=True).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if not re.search('Search', self.Name):
			self.getLastPage(data, 'class="pagination(.*?)</div>')
			parse = re.search('class="thumb_holder">(.*?)class="heading"', data, re.S)
			Movies = re.findall('<a\shref="(http://www.hclips.com/videos/.*?)"\sclass="thumb">.*?<img\ssrc="(.*?)".*?class="dur">(.*?)</span>.*?class="title">(.*?)</strong>.*?small_views">Views:\s(\d+)</span>.*?small_added-date">Added:\s(.*?)</span>', parse.group(1), re.S)
			if Movies:
				for (Url, Image, Runtime, Title, Views, Added) in Movies:
					self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views, Added))
		else:
			if ('results' in data):
				data = json.loads(data)
				try: self.lastpage = data['cursor']['pages'][-1]['label']
				except KeyError: lastpage = 1
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
				for e in data['results']:
					Url = e['unescapedUrl'].encode('utf-8')
					Title = e['titleNoFormatting'].split("|")[0].encode('utf-8')
					Content = e.get('contentNoFormatting','None').encode('utf-8').replace("\\n","").replace("\n","")
					try: Image = e['richSnippet']['cseImage']['src'].encode('utf-8')
					except KeyError: Image = None
					items = re.findall('Duration: (.*?)\sViews: (\d+)\s+Added:\s(.*?\s\w+\sago)', Content, re.S)
					if items:
						Runtime, Views, Added = items[0]
					else:
						Runtime, Views, Added = "", "", ""
					self.filmliste.append((Title, Url, Image, Runtime, Views, Added))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None, None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Url = self['liste'].getCurrent()[0][1]
		if Url == None:
			return
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		added = self['liste'].getCurrent()[0][5]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nViews: %s\nAdded: %s" % (runtime, views, added))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link == None:
			return
		self.keyLocked = True
		getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('video_url:\s\'(.*?)\'', data, re.S)
		if videoPage:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, videoPage[0])], showPlaylist=False, ltype='hclips')