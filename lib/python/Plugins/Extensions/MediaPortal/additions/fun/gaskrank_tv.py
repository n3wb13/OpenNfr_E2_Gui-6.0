# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

GKTV_Version = "GasKrank.tv v0.91"

GKTV_siteEncoding = 'utf-8'

"""
Sondertastenbelegung:

Genre Auswahl:
	KeyCancel		: Menu Up / Exit
	KeyOK			: Menu Down / Select

Doku Auswahl:
	Bouquet +/-				: Seitenweise blättern in 1er Schritten Up/Down
	'1', '4', '7',
	'3', 6', '9'			: blättern in 2er, 5er, 10er Schritten Down/Up
	Rot/Blau				: Die Beschreibung Seitenweise scrollen

Stream Auswahl:
	Rot/Blau				: Die Beschreibung Seitenweise scrollen
"""

class show_GKTV_Genre(MenuHelper):

	def __init__(self, session):

		MenuHelper.__init__(self, session, 2, [[],[],[]], "http://www.gaskrank.tv", "/tv", self._defaultlistcenter)

		self['title'] = Label(GKTV_Version)
		self['ContentTitle'] = Label("Genres")

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_initMenu(self):
		self.mh_buildMenu(self.mh_baseUrl + '/tv')

	def mh_parseData(self, data):
		print 'parseData:'
		entrys = entrys2 = []
		entrys.append(('/motorrad-videos','Die neuesten Filme'))
		entrys.append(('/top-videos','Am meisten gesehen'))
		entrys.append(('/user-voted','Am besten bewertet'))
		entrys.append(('/charts','Charts'))

		a = data.find('<h3>Video Kategorien</h3>')
		if a >= 0:
			b = data.find('<h3>Medien</h3>')
			if b >= 0:
				entrys2 = re.findall('<li>.*?<a href="/tv(.*?)/">(.*?)</a>', data[a:b], re.S)

		return entrys+entrys2

	def mh_callGenreListScreen(self):
		genreurl = self.mh_baseUrl+self.mh_genreBase+self.mh_genreUrl[0]+self.mh_genreUrl[1]
		print 'GenreURL:',genreurl
		self.session.open(GKTV_FilmListeScreen, genreurl, self.mh_genreTitle)

class GKTV_FilmListeScreen(MPScreen, ThumbsHelper):

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
		}, -1)

		self.sortOrder = 0
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label(GKTV_Version)

		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))
		self['Page'] = Label(_("Page:"))

		self.filmQ = Queue.Queue(0)
		self.hanQ = Queue.Queue(0)
		self.picQ = Queue.Queue(0)
		self.updateP = 0
		self.eventL = threading.Event()
		self.eventP = threading.Event()
		self.keyLocked = True
		self.dokusListe = []
		self.page = 0
		self.pages = 0;
		self.baseUrl = 'http://www.gaskrank.tv'

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
		if self.page:
			url = "%s/filme-%d.htm" % (self.genreLink, (self.page - 1)*15)
		else:
			url = self.genreLink
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
		print url
		twAgentGetPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		print "dataError:"
		printl(error,self,"E")
		self.dokusListe.append((_("No videos found!"),"","",""))
		self.ml.setList(map(self._defaultlistleft, self.dokusListe))

	def loadPageData(self, data):
		print "loadPageData:",len(data)
		self.dokusListe = []
		dokus = re.findall('"gkVidImg">.*?<img.*?src="(.*?)".*?href="(.*?)">(.*?)</a>', data, re.S)
		if dokus:
			print "videos found !"
			if not self.pages:
				m = re.search('<a href="/tv.*?filme-(\d+).htm"><i class="icon-forward">', data)
				try:
					pages = int(m.group(1)) / 15 + 1
				except:
					pages = 1
				if pages > self.pages:
					self.pages = min(pages,999)
			if not self.page:
				self.page = 1
			print "Page: %d / %d" % (self.page,self.pages)
			self['page'].setText("%d / %d" % (self.page,self.pages))
			for	(img,url,name) in dokus:
				#print	"Url: ", url, "Name: ", name
				self.dokusListe.append((decodeHtml(name), self.baseUrl+url, img))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self.th_ThumbsQuery(self.dokusListe, 0, 1, 2, None, None, self.page, self.pages, mode=1)
			self.loadPicQueued()
		else:
			print "No videos found !"
			print data
			self.dokusListe.append((_("No videos found!"),"","",""))
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
		desc = None
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
			self['handlung'].setText(_("No further information available!"))
			return
		self.setHandlung(desc)

	def setHandlung(self, data):
		print "setHandlung:"
		self['handlung'].setText(decodeHtml(data))

	def ShowCoverFileExit(self):
		print "showCoverExitFile:"
		self.updateP = 0;
		self.keyLocked	= False
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
			self.loadPic()

	def loadPicQueued(self):
		print "loadPicQueued:"
		self.picQ.put(None)
		if not self.eventP.is_set():
			self.eventP.set()
		self.loadPic()
		print "eventP: ",self.eventP.is_set()

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		self.session.open(
			GKTVPlayer,
			self.dokusListe,
			playIdx = self['liste'].getSelectedIndex()
			)

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
		self.keyPageDownFast(1)

	def keyPageUp(self):
		#print "keyPageUp()"
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

class GKTVPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx):
		print "GKTVPlayer:"

		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=True, listTitle="GasKrank.tv", ltype='gaskrank.tv')

	def getVideo(self):
		url = self.playList[self.playIdx][1]
		twAgentGetPage(url).addCallback(self.parseStream).addErrback(self.dataError)

	def parseStream(self, data):
		print "parseStream:"
		m2 = re.search('0: {src:"(.*?)"', data)
		if m2:
			print "Streams found"
			url = m2.group(1)
			title = self.playList[self.playIdx][0]
			img = self.playList[self.playIdx][2]
			self.playStream(title, url, imgurl=img)
		else:
			print "No stream found"
			self.dataError("Kein Videostream gefunden!")