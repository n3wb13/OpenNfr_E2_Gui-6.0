# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

DH_Version = "DokuHouse.de v1.01"

DH_siteEncoding = 'utf-8'

"""
Sondertastenbelegung:

Genre Auswahl:
	KeyCancel	: Menu Up / Exit
	KeyOK		: Menu Down / Select

Doku Auswahl:
	Bouquet +/-				: Seitenweise blättern in 1er Schritten Up/Down
	'1', '4', '7',
	'3', 6', '9'			: blättern in 2er, 5er, 10er Schritten Down/Up
	Rot/Blau				: Die Beschreibung Seitenweise scrollen

Stream Auswahl:
	Rot/Blau				: Die Beschreibung Seitenweise scrollen
"""

class show_DH_Genre(MenuHelper):

	def __init__(self, session):
		MenuHelper.__init__(self, session, 1, [[],[],[]], "http://www.dokuhouse.de", "/category", self._defaultlistcenter)

		self['title'] = Label(DH_Version)
		self['ContentTitle'] = Label("Genres")

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_parseData(self, data):
		print 'parseData:'
		m = re.search('<div id="sub-menu-full">(.*?)</div>', data, re.S)
		if m:
			entrys=re.findall('<li id="menu-item.*?<a href="http://www.dokuhouse.de/category(.*?)/">(.*?)</a>', m.group(1))
		else:
			entrys = None
		return entrys

	def mh_callGenreListScreen(self):
		url = self.mh_baseUrl+self.mh_genreBase+self.mh_genreUrl[0]+self.mh_genreUrl[1]
		print url
		self.session.open(DH_FilmListeScreen, url, self.mh_genreTitle)

class DH_FilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/dokuListScreen.xml"
		print path
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
			#"seekBackManual" :  self.keyPageDownMan,
			#"seekFwdManual" :  self.keyPageUpMan,
			#"seekFwd" :  self.keyPageUp,
			#"seekBack" :  self.keyPageDown
		}, -1)

		self.sortOrder = 0
		self.baseUrl = "http://www.dokuhouse.de"
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label(DH_Version)

		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))
		self['Page'] = Label(_("Page:"))

		self.timerStart = False
		self.seekTimerRun = False
		self.filmQ = Queue.Queue(0)
		self.hanQ = Queue.Queue(0)
		self.picQ = Queue.Queue(0)
		self.updateP = 0
		self.eventL = threading.Event()
		self.eventP = threading.Event()
		self.keyLocked = True
		self.dokusListe = []
		self.keckse = CookieJar()
		self.page = 0
		self.pages = 0;
		self.genreSpecials = '/specials' in genreLink

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		#print genreName
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		print "loadPage:"
		#if not self.genreSpecials:
		url = "%s/page/%d/" % (self.genreLink, self.page)
		#else:
		#	url =
		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.pages))
		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()
		print "eventL ",self.eventL.is_set()

	def loadPageQueued(self):
		print "loadPageQueued:"
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		#self.eventL.clear()
		print url
		twAgentGetPage(url, cookieJar=self.keckse, agent=None, headers=std_headers).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		print "dataError:"
		printl(error,self,"E")
		self.dokusListe.append((_("No dokus found!"),"","",""))
		self.ml.setList(map(self._defaultlistleft, self.dokusListe))

	def loadPageData(self, data):
		print "loadPageData:"
		dokus = re.findall('class="article-image darken"><a href="(.*?)".*?<img.*?src="(.*?)".*?alt="(.*?)".*?class="excerpt">(.*?)</div>', data)
		if dokus:
			print "Dokus found !"
			#print dokus
			if not self.pages:
				m = re.findall('data-paginated="(.*?)"', data)
				if m:
					self.pages = int(m[len(m)-1])
				else:
					self.pages = 1
				self.page = 1
				print "Page: %d / %d" % (self.page,self.pages)
				self['page'].setText("%d / %d" % (self.page,self.pages))
			self.dokusListe = []
			for	(url,img,name,desc) in dokus:
				#print	"Url: ", url, "Name: ", name
				self.dokusListe.append((decodeHtml(name), url, img, decodeHtml(desc.strip())))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self.loadPicQueued()
		else:
			print "No dokus found!"
			self.dokusListe.append((_("No dokus found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()

	def loadPic(self):
		print "loadPic:"
		if self.picQ.empty():
			self.eventP.clear()
			print "picQ is empty"
			return
		if self.updateP:
			print "Pict. or descr. update in progress"
			print "eventP: ",self.eventP.is_set()
			print "updateP: ",self.updateP
			return
		while not self.picQ.empty():
			self.picQ.get_nowait()
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		#streamUrl = self.baseUrl+re.sub('amp;','',self['liste'].getCurrent()[0][1])
		desc = self['liste'].getCurrent()[0][3]
		#print "streamName: ",streamName
		#print "streamPic: ",streamPic
		#print "streamUrl: ",streamUrl
		self.getHandlung(desc)
		self.updateP = 1
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def getHandlung(self, desc):
		print "getHandlung:"
		if desc == None:
			print "No Infos found !"
			self['handlung'].setText(_("No information found."))
			return
		self.setHandlung(desc)

	def setHandlung(self, data):
		print "setHandlung:"
		self['handlung'].setText(decodeHtml(data))

	def ShowCoverFileExit(self):
		print "showCoverFileExit:"
		self.updateP = 0;
		self.keyLocked	= False
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
			self.loadPic()

	def loadPicQueued(self):
		self.th_ThumbsQuery(self.dokusListe, 0, 1, 2, None, None, self.page, self.pages, mode=1)
		print "loadPicQueued:"
		self.picQ.put(None)
		if not self.eventP.is_set():
			self.eventP.set()
		self.loadPic()
		print "eventP: ",self.eventP.is_set()

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		streamLink = self['liste'].getCurrent()[0][1]
		streamName = self['liste'].getCurrent()[0][0]
		streamPic = self['liste'].getCurrent()[0][2]
		print "Open DH_Streams:"
		print "Name: ",streamName
		print "Link: ",streamLink
		self.session.open(DH_Streams, streamLink, streamName, streamPic)

	def keyUpRepeated(self):
		#print "keyUpRepeated"
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		#print "keyDownRepeated"
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		#print "key_repeatedUp"
		if self.keyLocked:
			return
		self.loadPicQueued()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyPageDown(self):
		#print "keyPageDown()"
		if self.seekTimerRun:
			self.seekTimerRun = False
		self.keyPageDownFast(1)

	def keyPageUp(self):
		#print "keyPageUp()"
		if self.seekTimerRun:
			self.seekTimerRun = False
		self.keyPageUpFast(1)

	def keyPageUpFast(self,step):
		if self.keyLocked:
			return
		#print "keyPageUpFast: ",step
		oldpage = self.page
		if (self.page + step) <= self.pages:
			self.page += step
		else:
			self.page = 1
		#print "Page %d/%d" % (self.page,self.pages)
		if oldpage != self.page:
			self.loadPage()

	def keyPageDownFast(self,step):
		if self.keyLocked:
			return
		print "keyPageDownFast: ",step
		oldpage = self.page
		if (self.page - step) >= 1:
			self.page -= step
		else:
			self.page = self.pages
		#print "Page %d/%d" % (self.page,self.pages)
		if oldpage != self.page:
			self.loadPage()

	def key_1(self):
		#print "keyPageDownFast(2)"
		self.keyPageDownFast(2)

	def key_4(self):
		#print "keyPageDownFast(5)"
		self.keyPageDownFast(5)

	def key_7(self):
		#print "keyPageDownFast(10)"
		self.keyPageDownFast(10)

	def key_3(self):
		#print "keyPageUpFast(2)"
		self.keyPageUpFast(2)

	def key_6(self):
		#print "keyPageUpFast(5)"
		self.keyPageUpFast(5)

	def key_9(self):
		#print "keyPageUpFast(10)"
		self.keyPageUpFast(10)

class DH_Streams(MPScreen):

	def __init__(self, session, dokuUrl, dokuName, dokuImg):
		self.dokuUrl = dokuUrl
		self.dokuName = dokuName
		self.dokuImg = dokuImg
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/dokuListScreen.xml"
		print path
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "EPGSelectActions", "WizardActions", "ColorActions", "NumberActions", "MenuActions", "MoviePlayerActions", "InfobarSeekActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"yellow"	: self.keyYellow,
			"red" : self.keyPageUp,
			"0"		: self.closeAll,
			"blue" : self.keyPageDown,
		}, -1)

		self['title'] = Label(DH_Version)
		self['ContentTitle'] = Label("Streams für "+dokuName)
		self['name'] = Label(self.dokuName)
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self['VideoPrio'] = Label("VidPrio")

		self.videoPrio = int(config.mediaportal.youtubeprio.value)
		self.videoPrioS = ['L','M','H']
		self.setVideoPrio()
		self.streamListe = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		print "loadPage:"
		streamUrl = self.dokuUrl
		#print "FilmUrl: %s" % self.dokuUrl
		#print "FilmName: %s" % self.dokuName
		twAgentGetPage(streamUrl).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		print "parseData:"
		desc = ''
		imgurl = self.dokuImg
		self.streamListe = []
		m2 = None
		m = re.search('class="the-content">(.*?)</div>', data, re.S)
		if m:
			ldesc = re.findall('<p>(.*?</p>)',m.group(1))
			if ldesc:
				i = 0
				for txt in ldesc:
					txt = re.sub('<span.*?</span>','',txt)
					txt = re.sub('\n','',txt)
					if i > 0:
						txt = re.sub('</p>','\n',txt)
					txt = re.sub('&nbsp;',' ',txt)
					desc = "%s%s" % (desc,re.sub('<.*?>','',txt))
					i += 1
			m2 = re.search('//www.youtube.com/(embed|v)/(.*?)("|\?)', m.group(1))
		if m2:
			print "Streams found"
			self.nParts = 0
			pstr = self.dokuName
			self.streamListe.append((pstr,m2.group(2),desc,imgurl))
			self.keyLocked	= False
		else:
			print "No dokus found!"
			desc = None
			self.streamListe.append(("No streams found!","","",""))
		self.ml.setList(map(self._defaultlistleft, self.streamListe))
		self.showInfos()

	def getHandlung(self, desc):
		print "getHandlung:"
		if desc == None:
			print "No Infos found !"
			self['handlung'].setText(_("No further information available!"))
		else:
			self.setHandlung(desc)

	def setHandlung(self, data):
		print "setHandlung:"
		self['handlung'].setText(decodeHtml(data))

	def showInfos(self):
		print "showInfos:"
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][3]
		desc = self['liste'].getCurrent()[0][2]
		print "streamName: ",streamName
		print "streamPic: ",streamPic
		self.getHandlung(desc)
		CoverHelper(self['coverArt']).getCover(streamPic)

	def dataError(self, error):
		print "dataError:"
		printl(error,self,"E")
		self.streamListe.append((_("Read error!"),"","",""))
		self.ml.setList(map(self._defaultlistleft, self.streamListe))

	def setVideoPrio(self):
		print "setVideoPrio:"
		self.videoPrio = int(config.mediaportal.youtubeprio.value)
		self['vPrio'].setText(self.videoPrioS[self.videoPrio])

	def keyOK(self):
		print "keyOK:"
		if self.keyLocked:
			return
		dhTitle = self['liste'].getCurrent()[0][0]
		dhVideoId = self['liste'].getCurrent()[0][1]
		self.session.openWithCallback(
			self.setVideoPrio,
			YoutubePlayer,
			[(dhTitle, dhVideoId, None)],
			listTitle = self.dokuName,
			showPlaylist=False
			)

	def keyPageUp(self):
		self['handlung'].pageUp()

	def keyPageDown(self):
		self['handlung'].pageDown()

	def keyYellow(self):
		self.setVideoPrio()