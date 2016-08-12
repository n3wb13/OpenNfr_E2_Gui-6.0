# -*- coding: utf-8 -*-
from ast import literal_eval
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

HTV_Version = "heiseVIDEO v1.00"

HTV_siteEncoding = 'utf-8'

class HeiseTvGenreScreen(MPScreen):

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
			"0"		: self.closeAll,
			"cancel": self.keyCancel
		}, -1)


		self['title'] = Label(HTV_Version)
		self['ContentTitle'] = Label("Genres")
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label(_("Exit"))

		self.keyLocked = True
		self.data_rubrikid="2523"
		self.baseUrl = 'http://www.heise.de'
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append((0, _('Please wait...'), '', '', ''))
		self.ml.setList(map(self.heiseTvGenreListEntry, self.genreliste))
		twAgentGetPage(self.baseUrl+'/video').addCallback(self.buildMenu).addErrback(self.dataError)

	def buildMenu(self, data):
		self.genreliste = []

		m = re.search('<ul id="teaser_reiter_nav">(.*?)</ul>', data, re.S)
		if m:
			list = re.findall('href="#(reiter.*?)">(.*?)</a></li>', m.group(1), re.S)
			if list:
				for r, n in list:
					nm = decodeHtml(n)
					m2 = re.search('<a href="(\?teaser=.*?);.*?into=%s' % r, data)
					if m2:
						self.genreliste.append((1, n, '/video/%s;offset=%%d;into=%s&hajax=1' % (m2.group(1), r), '', nm))
					else:
						self.genreliste.append((4, n, '/video', r, nm))

		list = re.findall('<section class="kasten video.*?<h3><span></span>(.*?)</h3>', data, re.S)
		if list:
			for x in list:
				if not [1 for item in self.genreliste if item[1] == x]:
					nm = decodeHtml(x)
					self.genreliste.append((3, x, '/video', '', nm))

		m = re.search('<section id="cttv_archiv">(.*?)</section>', data, re.S)
		if m:
			list = re.findall('data-jahr="(.*?)"', m.group(1), re.S)
			if list:
				for j in list:
					nm = "c't-TV Archiv %s" % j
					url = '/video/includes/cttv_archiv_json.pl?jahr=%s&rubrik=%s' % (j, self.data_rubrikid)
					self.genreliste.append((2, nm, url, '', nm, ''))

		self.ml.setList(map(self.heiseTvGenreListEntry, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return

		genreID = self['liste'].getCurrent()[0][0]
		genre = self['liste'].getCurrent()[0][4]
		raw_genre = self['liste'].getCurrent()[0][1]
		stvLink = self['liste'].getCurrent()[0][2]
		m_reiter = self['liste'].getCurrent()[0][3]
		self.session.open(HeiseTvListScreen, self.baseUrl, genreID, stvLink, genre, m_reiter, raw_genre)

class HeiseTvListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, baseUrl, genreID, stvLink, stvGenre, m_reiter, raw_genre):
		self.genreID = genreID
		self.stvLink = stvLink
		self.genreName = stvGenre
		self.baseUrl = baseUrl
		self.m_reiter = m_reiter
		self.rawGenre = raw_genre
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/dokuListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"0"		: self.closeAll,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(HTV_Version)
		self['ContentTitle'] = Label(self.genreName)
		self['Page'] = Label(_("Page:"))

		if self.genreID != 1:
			self['Page'].hide()
			self['page'].hide()

		self.items_pp = 0
		self.reiter_ofs = 0
		self.page = 0
		self.pages = 0
		self.videoPrioS = ['L','M','H']
		self.setVideoPrio()
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.getHtml()

	def getHtml(self):
		self.ml.setList(map(self._defaultlistleft, [(_('Please wait...'),'','','')]))

		self.filmliste = []
		url = self.stvLink
		if self.genreID == 1:
			url = self.baseUrl+(url % self.reiter_ofs)
		else:
			url = self.baseUrl+url

		twAgentGetPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		if self.genreID == 1:
			infos = literal_eval(data)
			stvDaten = re.findall('class=\"rahmen\">.*?<img src=\"(.*?)\".*?<h3><a href=\"(.*?)\">(.*?)</a>.*?<p>(.*?)<a href=\"', infos['actions'][1]['html'], re.S)
			if stvDaten:
				for (img,href,title,desc) in stvDaten:
					title = decodeHtml2(title)
					desc = decodeHtml2(desc)
					self.filmliste.append((title,href,self.baseUrl + img,desc))

				m = re.search('<a href=\".*?offset=(.*?);', infos['actions'][1]['html'], re.S)
				if m:
					if not self.page:
						self.items_pp = int(m.group(1))
						self.page = 1
						self.pages = 0
				else:
					self.pages = self.page

			if self.pages > 0:
				page = '%d / %d' % (self.page, self.pages)
			else:
				page = '%d' % self.page

			self['page'].setText(page)

		elif self.genreID == 2:
			infos = literal_eval(data)
			try:
				for i in range(len(infos)):
					title = decodeHtml2(infos[i]['titel'])
					desc = decodeHtml2(infos[i]['anrisstext'])
					self.filmliste.append((title,infos[i]['url'],self.baseUrl + infos[i]['anrissbild']['src'],desc))
			except KeyError, e:
				printl('Video infos key error: '+e,self,'E')

		elif self.genreID == 3:
			patt = '<section class="kasten video.*?<h3><span></span>%s</h3>(.*?)</section>' % self.rawGenre
			m = re.search(patt, data, re.S)
			if m:
				stvDaten = re.findall('<img.*?src="(.*?)".*?<h4><a href="(.*?)">(.*?)</a></h4>', m.group(1), re.S)
				if stvDaten:
					for (img,href,title) in stvDaten:
						title = decodeHtml2(title)
						self.filmliste.append((title,href,self.baseUrl + img,''))

		elif self.genreID == 4:
			m = re.search('<li id="%s">(.*?)</li>\s+</ul>' % self.m_reiter, data, re.S)
			if m:
				stvDaten = re.findall('class="rahmen">.*?<img src="(.*?)".*?<h3><a href="(.*?)">(.*?)</a>.*?<p>(.*?)<a href="', m.group(1), re.S)
				if stvDaten:
					for (img,href,title,desc) in stvDaten:
						title = decodeHtml2(title)
						desc = decodeHtml2(desc)
						self.filmliste.append((title,href,self.baseUrl + img,desc))

		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'),'','',''))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
		else:
			self.keyLocked = False
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def dataError(self, error):
		printl(error,self,'E')
		self.session.open(MessageBoxExt, "Fehler:\n%s" % error , MessageBoxExt.TYPE_INFO, timeout=5)

	def showInfos(self):
		stvTitle = self['liste'].getCurrent()[0][0]
		stvImage = self['liste'].getCurrent()[0][2]
		desc = self['liste'].getCurrent()[0][3]
		self['name'].setText(stvTitle)
		self['handlung'].setText(desc)
		CoverHelper(self['coverArt']).getCover(stvImage)

	def getVid(self, data):
		try:
			m = re.search('id="videoplayerjw-.*?data-container="(.*?)" data-sequenz="(.*?)"', data)
			url = 'http://www.heise.de/videout/feed?container=%s&sequenz=%s' % (m.group(1), m.group(2))
		except :
			self.session.open(MessageBoxExt, _("No Videodata found!"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			twAgentGetPage(url).addCallback(self.getVidInfos).addErrback(self.dataError)

	def getVidInfos(self, data):
		try:
			streams = re.findall('<jwplayer:source\s+file="(.*?)"\s+label="(.*?)"\s+type="video/mp4" />', data)
			streams.sort(key=lambda x: x[1])
			q = int(config.mediaportal.videoquali_others.value) + 1
			url = streams[min(q, len(streams) - 1)][0]
		except:
			self.session.open(MessageBoxExt, _("No Video URL found!"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			title = self['liste'].getCurrent()[0][0]
			self.session.openWithCallback(self.setVideoPrio, SimplePlayer, [(title, url)], showPlaylist=False, ltype='heisetv')

	def keyPageUp(self):
		if self.keyLocked or self.genreID != 1:
			return
		if self.pages == 0 or self.page < self.pages:
			self.page += 1
			self.reiter_ofs += self.items_pp
			self.keyLocked = True
			self.getHtml()

	def keyPageDown(self):
		if self.keyLocked or self.genreID != 1:
			return
		if self.page > 1:
			self.page -= 1
			self.reiter_ofs -= self.items_pp
			self.keyLocked = True
			self.getHtml()
	def setVideoPrio(self):
		self.videoPrio = int(config.mediaportal.videoquali_others.value)
		self['vPrio'].setText(self.videoPrioS[self.videoPrio])

	def keyYellow(self):
		self.setVideoPrio()

	def keyOK(self):
		if self.keyLocked:
			return
		url = self.baseUrl + self['liste'].getCurrent()[0][1]
		twAgentGetPage(url).addCallback(self.getVid).addErrback(self.dataError)