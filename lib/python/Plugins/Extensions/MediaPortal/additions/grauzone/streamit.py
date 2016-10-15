# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Components.ProgressBar import ProgressBar

try:
	from Plugins.Extensions.MediaPortal.resources import cfscrape
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

if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/TMDb/plugin.pyo'):
	from Plugins.Extensions.TMDb.plugin import *
	TMDbPresent = True
elif fileExists('/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo'):
	TMDbPresent = False
	IMDbPresent = True
	from Plugins.Extensions.IMDb.plugin import *
else:
	IMDbPresent = False
	TMDbPresent = False

BASE_URL = "http://streamit.ws"
sit_cookies = CookieJar()
sit_ck = {}
sit_agent = ''

def sit_grabpage(pageurl, method='GET', postdata={}):
	if requestsModule:
		try:
			s = requests.session()
			url = urlparse.urlparse(pageurl)
			headers = {'User-Agent': sit_agent}
			if method == 'GET':
				page = s.get(url.geturl(), cookies=sit_cookies, headers=headers)
			elif method == 'POST':
				page = s.post(url.geturl(), data=postdata, cookies=sit_cookies, headers=headers)
			return page.content
		except:
			pass

class showstreamitGenre(MenuHelper):

	base_menu = [
		(0, "/kino", 'Kino'),
		(0, "", 'Filme'),
		(1, "/film", 'Neue Filme'),
		(1, "/film-hd", 'HD Filme'),
		(1, "/film-3d", '3D Filme'),
		(1, "", 'Genre'),
		(0, "", 'Serien'),
		(1, "/serie", 'Neue Serien'),
		(1, "", 'Genre'),
		(0, "/suche/?s=%s", 'Suche...')
		]

	def __init__(self, session, m_level='main', m_path='/'):
		self.m_level = m_level
		self.m_path = m_path
		MenuHelper.__init__(self, session, 0, None, BASE_URL, "", self._defaultlistcenter, cookieJar=sit_cookies)

		self['title'] = Label("STREAMIT")
		self['ContentTitle'] = Label("Genres")
		self.param_search = ''
		self.search_token = None

		self.onLayoutFinish.append(self.mh_start)

	def mh_start(self):
		thread.start_new_thread(self.get_tokens,("GetTokens",))
		self['name'].setText(_("Please wait..."))

	def get_tokens(self, threadName):
		if requestsModule and cfscrapeModule:
			printl("Calling thread: %s" % threadName,self,'A')
			global sit_ck
			global sit_agent
			if sit_ck == {} or sit_agent == '':
				sit_ck, sit_agent = cfscrape.get_tokens(BASE_URL)
				requests.cookies.cookiejar_from_dict(sit_ck, cookiejar=sit_cookies)
			else:
				s = requests.session()
				url = urlparse.urlparse(BASE_URL)
				headers = {'user-agent': sit_agent}
				page = s.get(url.geturl(), cookies=sit_cookies, headers=headers)
				if page.status_code == 503 and page.headers.get("Server") == "cloudflare-nginx":
					sit_ck, sit_agent = cfscrape.get_tokens(BASE_URL)
					requests.cookies.cookiejar_from_dict(sit_ck, cookiejar=sit_cookies)
			reactor.callFromThread(self.mh_initMenu)
		else:
			reactor.callFromThread(self.mh_errorMenu)

	def mh_errorMenu(self):
		message = self.session.open(MessageBoxExt, _("Some mandatory Python modules are missing!"), MessageBoxExt.TYPE_ERROR)
		self.keyCancel()

	def mh_initMenu(self):
		self.mh_buildMenu(self.mh_baseUrl + self.m_path, agent=sit_agent)

	def mh_parseCategorys(self, data):
		if self.m_level == 'main':
			menu = self.base_menu[:6]
			m = re.search('<a>Filme</a>.*?<a>Genre</a>.*?="sub-menu">(.*?)</ul>', data, re.S)
			if m:
				for m_entry in re.finditer('<a href="(.*?)">(.*?)</a>', m.group(1)):
					href, nm = m_entry.groups()
					menu.append((2, href, decodeHtml(nm)))

			m = re.search('>Serien</a>.*?<a>Genre</a>.*?="sub-menu">(.*?)</ul>', data, re.S)
			if m:
				menu += self.base_menu[6:9]
				for m_entry in re.finditer('<a href="(.*?)">(.*?)</a>', m.group(1)):
					href, nm = m_entry.groups()
					menu.append((2, href, decodeHtml(nm)))

			menu += self.base_menu[-1:]
		elif self.m_level == 'more-genre':
			menu = []
			m = re.search('<h1>Genre .*?="entry">(.*?)</div>', data, re.S)
			if m:
				for m_entry in re.finditer('<a href="(.*?)">(.*?)</a>', m.group(1)):
					href, nm = m_entry.groups()
					if not href.startswith('/'):
						href = '/' + href
					menu.append((0, href, decodeHtml(nm)))
		self.mh_genMenu2(menu)

	def mh_callGenreListScreen(self):
		if re.search('Suche...', self.mh_genreTitle):
			self.session.openWithCallback(self.cb_Search, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_search, is_dialog=True, auto_text_init=True)
		else:
			genreurl = self.mh_baseUrl+self.mh_genreUrl[self.mh_menuLevel]
			if "/genre-" in genreurl:
				self.session.open(showstreamitGenre, m_level='more-genre', m_path=self.mh_genreUrl[self.mh_menuLevel])
			else:
				self.session.open(streamitFilmListeScreen, genreurl, self.mh_genreTitle)

	def cb_Search(self, callback = None, entry = None):
		if callback != None:
			self.param_search = callback.strip()
			genreName = 'Videosuche: ' + self.param_search
			genreLink = self.mh_baseUrl+self.mh_genreUrl[self.mh_menuLevel] % urllib.quote_plus(self.param_search)
			self.session.open(streamitFilmListeScreen, genreLink, genreName)

class streamitFilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName, series_img=None, last_series_tag='', season_data=None):
		self.genreLink = genreLink
		self.genreName = genreName
		self.seriesImg = series_img
		self.seasonData = season_data

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		widgets_files = ('cover_widgets.xml',)
		self.skin = self.skin.replace('</screen>', '')
		for wf in widgets_files:
			path = "%s/%s/%s" % (self.skin_path, config.mediaportal.skin.value, wf)
			if not fileExists(path):
				path = self.skin_path + mp_globals.skinFallback + "/%s" % wf

			f = open(path, "r")
			for widget in f:
				self.skin += widget
			f.close()
		self.skin += '</screen>'

		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["hdpic"] = Pixmap()
		self['rating10'] = ProgressBar()
		self['rating0'] = Pixmap()
		self["hdpic"].hide()

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions", "EPGSelectActions","DirectionActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"upUp" : self.key_repeatedUp,
			"rightUp" : self.key_repeatedUp,
			"leftUp" : self.key_repeatedUp,
			"downUp" : self.key_repeatedUp,
			"upRepeated" : self.keyUpRepeated,
			"downRepeated" : self.keyDownRepeated,
			"rightRepeated" : self.keyRightRepeated,
			"leftRepeated" : self.keyLeftRepeated,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"1" : self.key_1,
			"3" : self.key_3,
			"4" : self.key_4,
			"6" : self.key_6,
			"7" : self.key_7,
			"9" : self.key_9,
			"0": self.closeAll,
			"yellow" : self.keySort,
			"red" :  self.keyTxtPageUp,
			"blue" :  self.keyTxtPageDown,
			"info" :  self.keyTMDbInfo
		}, -1)

		self.sortFuncs = None
		self.sortOrderStrGenre = ""
		self['title'] = Label("STREAMIT")

		self['Page'] = Label(_("Page:"))
		self['F1'] = Label(_("Text-"))
		self['F3'] = Label(_("Sort by..."))
		self['F4'] = Label(_("Text+"))
		self['F3'].hide()

		self.timerStart = False
		self.seekTimerRun = False
		self.eventL = threading.Event()
		self.eventH = threading.Event()
		self.eventP = threading.Event()
		self.filmQ = Queue.Queue(0)
		self.hanQ = Queue.Queue(0)
		self.picQ = Queue.Queue(0)
		self.updateP = 0
		self.keyLocked = True
		self.filmListe = []
		self.page = 0
		self.pages = 0;
		self.neueFilme = re.search('Neue Filme',self.genreName)
		self.sucheFilme = re.search('Videosuche',self.genreName)
		if 'HD Filme' in self.genreName:
			self.streamTag = 'streamhd'
		else:
			self.streamTag = 'stream'
		if '/serie/' in genreLink:
			self.seriesTag = 'Staffeln: '
		elif last_series_tag.startswith('Staf'):
			self.seriesTag = 'Episoden: '
		else:
			self.seriesTag = ''

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		if self.sortOrderStrGenre:
			sortOrder = ' (%s)' % self.sortOrderStrGenre
		else:
			sortOrder = ''

		self['ContentTitle'].setText("%s%s%s" % (self.seriesTag,self.genreName,sortOrder))

	def loadPage(self):
		if not self.sucheFilme and self.page > 1:
			page = max(1,self.page)
			link = self.genreLink
			if not '?' in link:
				link += '?'
			else:
				link += '&'
			url = "%spage=%d" % (link, page)
		else:
			url = self.genreLink

		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.pages))

		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()
		else:
			self['name'].setText(_('Please wait...'))
			self['handlung'].setText("")
			self['coverArt'].hide()

	def loadPageQueued(self):
		self['name'].setText(_('Please wait...'))
		self['handlung'].setText("")
		self['coverArt'].hide()
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		if not self.seriesTag.startswith('Epi'):
			data = sit_grabpage(url)
			self.loadPageData(data)
		else:
			self.loadPageData(self.seasonData)

	def dataError(self, error):
		self.eventL.clear()
		printl(error,self,"E")
		self.filmListe.append((_("No movies found!"),"","","", 0, False))
		self.ml.setList(map(self.streamitFilmListEntry,	self.filmListe))

	def loadPageData(self, data):
		self.getPostFuncs(data)
		self.filmListe = []
		if not self.seriesTag:
			l = len(data)
			a = 0
			while a < l:
				mg = re.search('<div id="divA">(.*?)</div>\s+</li>', data[a:], re.S)
				if mg:
					a += mg.end()
					m = re.search('<div class="voting".*?style="width:(\d*).*?<a href="(.*?)".*?title="(.*?)">.*?<img.*?src="(.*?)"', mg.group(1), re.S)
					if m:
						rating,url,name,imageurl = m.groups()
						if 'hd_icon' in mg.group(1):
							hd = True
						else:
							hd = False

						if not rating: rating = "0"
						imdb = "IMDb: %.1f / 10" % (float(rating) / 10)
						self.filmListe.append((decodeHtml(name), BASE_URL+url, BASE_URL+imageurl, imdb, rating, hd))
				else:
					a = l
		elif self.seriesTag.startswith('Staf'):
			mg = re.search('class="staffelauswahl" >(.*?)</select>', data, re.S)
			if mg:
				for m in re.finditer('<option value="(\d+)">(.*?)</option>', mg.group(1)):
					season_num, season = m.groups()
					md = re.search('(id="staffel%s".*?)</div>' % season_num, data)
					if md:
						mimdb = re.search("(var IMDB = '.*?';)", data)
						if mimdb:
							self.filmListe.append((decodeHtml(season), season_num, self.seriesImg, md.group(1)+mimdb.group(1), '', ''))
		elif self.seriesTag.startswith('Epi'):
			m = re.search("IMDB = '(.*?)';", data)
			if m:
				imdb = m.group(1)
				m = re.search('seriesName="(.*?)"', data)
				if m:
					seriesName = m.group(1)
					for m in re.finditer('<a.*?href="#(.*?)"\s{0,1}>(.*?)</a>', data):
						episode, title = m.groups()
						self.filmListe.append((decodeHtml(title), episode, self.seriesImg, imdb, decodeHtml(seriesName), ''))

		if self.filmListe:
			if not self.pages:
				m = re.search('class=\'pagination\'.*?page=(\d+)\'>Last</a', data)
				if m:
					self.pages = int(m.group(1))
				else:
					self.pages = 1

				self.page = 1
				self['page'].setText("%d / %d" % (self.page,self.pages))

			self.keyLocked = False
			if not self.seriesTag:
				self.ml.setList(map(self.streamitFilmListEntry,	self.filmListe))
				self.th_ThumbsQuery(self.filmListe, 0, 1, 2, None, None, self.page, self.pages, agent=sit_agent, cookies=sit_ck)
			else:
				self.ml.setList(map(self._defaultlistleft, self.filmListe))

			self['liste'].moveToIndex(0)
			self.loadPicQueued()
		else:
			self.filmListe.append((_("No entrys found!"),"","","", 0, False))
			self.ml.setList(map(self.streamitFilmListEntry,	self.filmListe))
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()

	def getPostFuncs(self, data):
		self.sortFuncs = []
		m = re.search('id="postFuncs">(.*?)<!-- /#postFuncs -->', data, re.S)
		if m:
			for m2 in re.finditer('href="(.*?)">(.*?)</a', m.group(1)):
				href, name = m2.groups()
				href = re.sub('&page=\d+', '', href, 1)
				href = re.sub('\?page=\d+', '?', href, 1)
				self.sortFuncs.append((decodeHtml(name), decodeHtml(href)))
		if self.sortFuncs:
			self['F3'].show()
		else:
			self['F3'].hide()

	def loadPicQueued(self):
		self.picQ.put(None)
		if not self.eventP.is_set():
			self.eventP.set()
			self.loadPic()

	def loadPic(self):
		if self.picQ.empty():
			self.eventP.clear()
			return

		if self.eventH.is_set() or self.updateP:
			print "Pict. or descr. update in progress"
			print "eventH: ",self.eventH.is_set()
			print "eventP: ",self.eventP.is_set()
			print "updateP: ",self.updateP
			return

		while not self.picQ.empty():
			self.picQ.get_nowait()

		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		streamUrl = self['liste'].getCurrent()[0][1]
		self.updateP = 1
		CoverHelper(self['coverArt'], self.showCoverExit).getCover(streamPic, agent=sit_agent, cookieJar=sit_cookies, req=True)
		if not self.seriesTag:
			rate = self['liste'].getCurrent()[0][4]
			hd = self['liste'].getCurrent()[0][5]
			if hd:
				self['hdpic'].show()
			else:
				self['hdpic'].hide()
			rating = int(rate)
			if rating > 100:
				rating = 100
			self['rating10'].setValue(rating)
		else:
			self['rating10'].setValue(0)

	def dataErrorP(self, error):
		printl(error,self,"E")
		self.ShowCoverNone()

	def showCoverExit(self):
		self.updateP = 0;
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
			self.loadPic()

	def keyOK(self):
		if self.keyLocked or self.eventL.is_set():
			return

		streamLink = self['liste'].getCurrent()[0][1]
		streamName = self['liste'].getCurrent()[0][0]
		imageLink = self['liste'].getCurrent()[0][2]
		if '/serie' in streamLink or self.seriesTag.startswith('Staf'):
			seasonData = self['liste'].getCurrent()[0][3]
			if self.seriesTag.startswith('Staf'):
				streamName = "%s %s" % (self.genreName, streamName)
			self.session.open(streamitFilmListeScreen, streamLink, streamName, series_img=imageLink, last_series_tag=self.seriesTag, season_data=seasonData+'seriesName="%s"' % self.genreName)
		elif self.seriesTag.startswith('Epi'):
			imdb = self['liste'].getCurrent()[0][3]
			seriesName = self['liste'].getCurrent()[0][4]
			postData = {'IMDB':imdb, 'val':streamLink}
			link = BASE_URL + '/lade_episode.php'
			staffel, episode = re.search('(\d+)e(\d+)', streamLink).groups()
			streamName = "%s - S%02dE%02d - %s" % (seriesName, int(staffel), int(episode), re.sub('\d+\s', '', streamName, 1))
			streamLink = BASE_URL + '/serie/' + imdb
			self.session.open(streamitStreams, streamLink, streamName, imageLink, self.streamTag, post_data=postData, post_url=link)
		else:
			self.session.open(streamitStreams, streamLink, streamName, imageLink, self.streamTag)

	def keyUpRepeated(self):
		if self.keyLocked:
			return
		self['coverArt'].hide()
		self['liste'].up()

	def keyDownRepeated(self):
		if self.keyLocked:
			return
		self['coverArt'].hide()
		self['liste'].down()

	def key_repeatedUp(self):
		if self.keyLocked:
			return
		self.loadPicQueued()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['coverArt'].hide()
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['coverArt'].hide()
		self['liste'].pageDown()

	def keyPageDown(self):
		if self.seekTimerRun:
			self.seekTimerRun = False
		self.keyPageDownFast(1)

	def keyPageUp(self):
		if self.seekTimerRun:
			self.seekTimerRun = False
		self.keyPageUpFast(1)

	def keyPageUpFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page + step) <= self.pages:
			self.page += step
		else:
			self.page = 1
		if oldpage != self.page:
			self.loadPage()

	def keyPageDownFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page - step) >= 1:
			self.page -= step
		else:
			self.page = self.pages
		if oldpage != self.page:
			self.loadPage()

	def key_1(self):
		self.keyPageDownFast(2)

	def key_4(self):
		self.keyPageDownFast(5)

	def key_7(self):
		self.keyPageDownFast(10)

	def key_3(self):
		self.keyPageUpFast(2)

	def key_6(self):
		self.keyPageUpFast(5)

	def key_9(self):
		self.keyPageUpFast(10)

	def keyTMDbInfo(self):
		if not self.keyLocked and TMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(TMDbMain, title)
		elif not self.keyLocked and IMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(IMDB, title)

	def keySort(self):
		if not self.keyLocked and self.sortFuncs:
			self.handleSort()

	def handleSort(self):
		from Screens.ChoiceBox import ChoiceBox
		self.session.openWithCallback(self.cb_handleSort, ChoiceBox, title=_("Sort Selection"), list = self.sortFuncs)

	def cb_handleSort(self, answer):
		href = answer and answer[1]
		if href:
			self.genreLink = self.genreLink.split('?')[0] + href
			self.sortOrderStrGenre = answer[0]
			self.setGenreStrTitle()
			self.loadPage()

class streamitStreams(MPScreen):

	def __init__(self, session, filmUrl, filmName, imageLink, streamTag, post_data=None, post_url=None):
		self.filmUrl = filmUrl
		self.filmName = filmName
		self.imageUrl = imageLink
		self.stream_tag = streamTag
		self.postData = post_data
		self.postUrl = post_url

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
			"red" 		: self.keyTxtPageUp,
			"blue" 		: self.keyTxtPageDown,
			"green" 	: self.keyTrailer,
			"ok"    	: self.keyOK,
			"info" 		: self.keyTMDbInfo,
			"0"			: self.closeAll,
			"cancel"	: self.keyCancel
		}, -1)

		self['title'] = Label("STREAMIT")
		self['ContentTitle'] = Label(_("Stream Selection"))

		self['name'] = Label(filmName)
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.trailerId = None
		self.streamListe = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamListe.append((_('Please wait...'),"","",""))
		self.ml.setList(map(self.streamitStreamListEntry, self.streamListe))
		seriesStreams = self.postData != None
		data = sit_grabpage(self.filmUrl)
		self.parseData(data, seriesStreams)

	def getSeriesStreams(self):
		data = sit_grabpage(self.postUrl, method='POST', postdata=self.postData)
		self.parseStreams(data)

	def parseStreams(self, data):
		self.streamListe = []
		m = re.search('id="sel_qualideutsch">(.*?)</select>', data, re.S)
		if m:
			buttons = re.findall('id="(.*?)" class="mirrorbuttonsdeutsch">(.*?)</', m.group(1))
			for id,nm in buttons:
				m2 = re.search('class="mirrorsdeutsch"\sid="\w*%s"(.*?)></div></div>' % id, data, re.S)
				if m2:
					m3 = re.search('>Ton: <b>(.*?)</b', m2.group(1))
					if m3:
						ton = ', %s' % m3.group(1)
					else:
						ton = ''
					streams = re.findall('<a href="(.*?)".*?value="(.*?)"', m2.group(1).replace('\n', ''))
					for (isUrl,isStream) in streams:
						if isSupportedHoster(isStream, True):
							streamPart = ''
							isUrl = isUrl.replace('\n','')
							isUrl = isUrl.replace('\r','')
							self.streamListe.append((isStream,isUrl,streamPart,' (%s%s)' % (nm.strip(), ton.strip())))
						else:
							print "No supported hoster:"

		if self.streamListe:
			self.keyLocked = False
		else:
			self.streamListe.append(("No streams found!","","",""))
		self.ml.setList(map(self.streamitStreamListEntry, self.streamListe))

	def parseData(self, data, seriesStreams=False):
		m = re.search('//www.youtube\.com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		if m:
			self.trailerId = m.group(2)
			self['F2'].setText('Trailer')
		else: self.trailerId = None

		desc = ''
		mdesc = re.search('<b>(Jahr:)</b>.*?">(.*?)</.*?<b>(L&auml;nge:)</b>.*?">(.*?)</', data, re.S)
		if mdesc:
			desc += mdesc.group(1) + mdesc.group(2) + '  ' + mdesc.group(3) + mdesc.group(4) + '\n\n'
		elif desc:
			desc += '\n'

		mdesc = re.search('<div id="cleaner">&nbsp;</div><div id="cleaner">&nbsp;</div>(.*?)<br><br>',data, re.S)
		if mdesc:
			desc += re.sub('<.*?>', '', mdesc.group(1).replace('\n',''), re.S).replace('&nbsp;','').strip()
		else:
			desc += "Keine weiteren Info's !"

		self['handlung'].setText(decodeHtml(desc))
		CoverHelper(self['coverArt']).getCover(self.imageUrl, agent=sit_agent, cookieJar=sit_cookies, req=True)

		if not seriesStreams:
			self.parseStreams(data)
		else:
			self.getSeriesStreams()

	def dataError(self, error):
		printl(error,self,"E")
		self.streamListe.append(("Data error!","","",""))
		self.ml.setList(map(self.streamitStreamListEntry, self.streamListe))

	def gotLink(self, stream_url):
		if stream_url:
			title = self.filmName + self['liste'].getCurrent()[0][2]
			self.session.open(SimplePlayer, [(title, stream_url, self.imageUrl)], cover=True, showPlaylist=False, ltype='streamit')

	def keyTrailer(self):
		if self.trailerId:
			self.session.open(
				YoutubePlayer,
				[(self.filmName+' - Trailer', self.trailerId, self.imageUrl)],
				playAll = False,
				showPlaylist=False,
				showCover=True
				)

	def keyTMDbInfo(self):
		if TMDbPresent:
			self.session.open(TMDbMain, self.filmName)
		elif IMDbPresent:
			self.session.open(IMDB, self.filmName)

	def keyOK(self):
		if self.keyLocked:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		data = sit_grabpage(streamLink)
		self.getUrl(data)

	def getUrl(self,data):
		try:
			link = re.search('id="download" class="cd" style="display:none"><a href="(.*?)">', data).group(1)
			us = urlparse.urlsplit(link)
			link = urlparse.urlunsplit(us[0:1]+(us[1].lower(),)+us[2:])
		except:
			link = "http://fuck.com"
		get_stream_link(self.session).check_link(link, self.gotLink)