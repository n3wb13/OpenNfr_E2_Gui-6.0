# -*- coding: utf-8 -*-
#
#    Copyright (c) 2016 Billy2011, MediaPortal Team
#
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

HDSWS_Version = "HDstream.ws v0.95"
HDSWS_siteEncoding = 'utf-8'

headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
	'Cookie':'hasVsitedSite=yes',
}

class show_HDSWS_Genre(MenuHelper):

	def __init__(self, session):

		baseUrl = "http://hdstream.ws/wp/"
		MenuHelper.__init__(self, session, 0, None, baseUrl, "", self._defaultlistcenter)

		self['title'] = Label(HDSWS_Version)
		self['ContentTitle'] = Label("Genres")
		self.onLayoutFinish.append(self.mh_initMenu)
		self.param_qr = None

	def mh_initMenu(self):
		self.mh_buildMenu(self.mh_baseUrl, headers=headers)

	def mh_parseCategorys(self, data):
		print data
		menu_marker = '">Kategorien</h2'
		menu = [(0, "", "Aktuelle Filme"),
				(0, "?s=%s", "Suche..."),
			]
		menu += self.scanMenu(data,menu_marker,base_url=self.mh_baseUrl)
		self.mh_genMenu2(menu)

	def mh_callGenreListScreen(self):
		if re.search('Suche...', self.mh_genreTitle):
			self.paraQuery()
		else:
			genreurl = self.mh_genreUrl[self.mh_menuLevel].replace('&#038;','&')
			if not genreurl.startswith('http'):
				genreurl = self.mh_baseUrl+genreurl
			self.session.open(HDSWS_FilmListeScreen, genreurl, self.mh_genreTitle)

	def paraQuery(self):
		self.param_qr = ''
		self.session.openWithCallback(self.cb_paraQuery, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_qr, is_dialog=True, auto_text_init=True)

	def cb_paraQuery(self, callback = None, entry = None):
		if callback != None:
			self.param_qr = callback.strip()
			if len(self.param_qr) > 0:
				qr = self.param_qr.replace(' ','+')
				genreurl = self.mh_baseUrl + self.mh_genreUrl[0] % qr
				self.session.open(HDSWS_FilmListeScreen, genreurl, self.mh_genreTitle)

class HDSWS_FilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
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
			"0"	: self.closeAll,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self.sortOrder = 0
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label(HDSWS_Version)

		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))
		self['Page'] = Label(_("Page:"))

		self.filmQ = Queue.Queue(0)
		self.eventL = threading.Event()
		self.keyLocked = True
		self.dokusListe = []
		self.page = 0
		self.pages = 0;
		self.streamName = self.streamList = None

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		if self.page > 1:
			if '/?' in self.genreLink:
				url = self.genreLink.replace('/?', '/page/%d/?', 1)
			else:
				url = self.genreLink + "/page/%d/"
			url = url % max(self.page,1)
		else:
			url = self.genreLink

		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.pages))

		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()

	def loadPageQueued(self):
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		twAgentGetPage(url, timeout=30, headers=headers).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		printl(error,self,"E")
		if not 'TimeoutError' in str(error):
			message = self.session.open(MessageBoxExt, _("No movies / streams found!"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			message = self.session.open(MessageBoxExt, str(error), MessageBoxExt.TYPE_INFO)

	def loadPageData(self, data):
		self.dokusListe = []
		for m in re.finditer('<article id=(.*?)</article>', data, re.S):
			m2 = re.search('="post-thumbnail"\shref="(.*?)"\s.*?<img.*?src="(.*?)".*?="bookmark">(.*?)</a>.*?<p>(.*?)</p>', m.group(1), re.S)
			if m2:
				purl, img, nm, desc = m2.groups()
				i = 0
				for m2 in re.finditer('><a.*?href="(.*?)"\starget="_blank">(.*?)</a></', m.group(1)):
					url, folge = m2.groups()
					i += 1
					if i > 1: break
					folge = ' - ' + folge if folge.startswith('Folge') else ''
					entry = (decodeHtml(nm)+folge, url, img, decodeHtml(stripAllTags(desc)), None)
				if i == 0 or i > 1:
					self.dokusListe.append((decodeHtml(nm), None, img, decodeHtml(stripAllTags(desc)), purl))
				else:
					self.dokusListe.append(entry)

		if self.dokusListe:
			if not self.pages:
				ps = re.findall('class=.page-numbers. .*?>Seite\s</span>(.*?)</a>', data)
				try:
					pages = int(ps[-1].replace('.',''))
				except:
					pages = 1

				if pages > self.pages:
					self.pages = pages

			if not self.page:
				self.page = 1
			self['page'].setText("%d / %d" % (self.page,self.pages))

			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			self.th_ThumbsQuery(self.dokusListe,0,1,2,None,None, self.page, self.pages)
			self.loadPic()
		else:
			self.dokusListe.append((_("No movies found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
		if self.filmQ.empty():
			self.eventL.clear()
		else:
			self.loadPageQueued()

	def loadPic(self):
		movieName = self['liste'].getCurrent()[0][0]
		self['name'].setText(movieName)
		streamPic = self['liste'].getCurrent()[0][2]
		desc = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(desc)
		CoverHelper(self['coverArt']).getCover(streamPic)
		#self.eventL.clear()

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		streamLink = self['liste'].getCurrent()[0][1]
		self.streamName = ''
		if streamLink:
			get_stream_link(self.session).check_link(streamLink, self.gotLink)
		else:
			url = self['liste'].getCurrent()[0][4]
			twAgentGetPage(url, timeout=30, headers=headers).addCallback(self.getLink).addErrback(self.dataError)

	def getLink(self, data):
		self.streamList = []
		i = 0
		title = ''
		for m in re.finditer('<article id=(.*?)</article>', data, re.S):
			m2 = re.search('="entry-title">(.*?)</h1>', m.group(1))
			if m2:
				title = decodeHtml(m2.group(1))
				for m2 in re.finditer('><a.*?href="(.*?)"\starget="_blank">(.*?)</a></', m.group(1)):
					streamLink, folge = m2.groups()
					i += 1
					folge = folge if folge.startswith('Folge') else 'Stream %d' % i
					self.streamList.append((folge, streamLink))
				if self.streamList: break
		if len(self.streamList) == 0:
			get_stream_link(self.session).check_link('nix', self.gotLink)
		elif len(self.streamList) == 1:
			get_stream_link(self.session).check_link(self.streamList[0][1], self.gotLink)
		else:
			sel = 0
			self.session.openWithCallback(self.cb_streamChoice, ChoiceBoxExt, title=_("Stream Selection: {0}").format(title), list = self.streamList, selection=sel)

	def cb_streamChoice(self, answer):
		streamlink = answer and answer[1]
		if streamlink:
			self.streamName = answer[0]
			get_stream_link(self.session).check_link(streamlink, self.gotLink)

	def gotLink(self, stream_url):
		if stream_url:
			movieName = self['liste'].getCurrent()[0][0]
			if self.streamName.startswith('Folge'): movieName += ' - ' + self.streamName
			streamPic = self['liste'].getCurrent()[0][2]
			self.session.open(SimplePlayer, [(movieName, stream_url, streamPic)], cover=True, showPlaylist=False, ltype='hdstream.ws')

	def keyUpRepeated(self):
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		if self.keyLocked:
			return
		self.loadPic()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyPageDown(self):
		self.keyPageDownFast(1)

	def keyPageUp(self):
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