# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubelink import YoutubeLink
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

LSDE_Version = "LACHSCHON.DE v0.91"

LSDE_siteEncoding = 'utf-8'

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

class show_LSDE_Genre(MenuHelper):

	def __init__(self, session):

		baseUrl = "http://www.lachschon.de"
		MenuHelper.__init__(self, session, 0, None, baseUrl, "", self._defaultlistcenter)

		self['title'] = Label(LSDE_Version)
		self['ContentTitle'] = Label("Genres")

		self.onLayoutFinish.append(self.parseCats)

	def parseCats(self):
		self.mh_parseCategorys(None)

	def mh_parseCategorys(self, data):
		print 'mh_parseCategorys:'
		menu = []
		menu.append((0, '', 'KATEGORIEN'))
		menu.append((1, '/gallery/trend/?', 'Trend'))
		menu.append((1, '/gallery/new/?', 'Neue'))
		menu.append((1, '/gallery/all/?', 'Alles'))
		menu.append((1, '/gallery/toprecent/?', 'Top'))
		menu.append((1, '/gallery/floprecent/?', 'Flop'))
		menu.append((0, '', 'TOP & FLOP'))
		menu.append((1, '/gallery/premium/?', 'Premium-Lachse'))
#		menu.append((1, '/gallery/trash/?', 'Müllhalde'))
		menu.append((1, '/gallery/top/?', 'Hall of Fame'))
		menu.append((1, '/gallery/flop/?', 'Hall of Shame'))
		menu.append((1, '/gallery/mostvoted/?', 'Stimmen'))
		menu.append((1, '/gallery/mostfavs/?', 'Favs'))
		menu.append((0, '/gallery/search_item/?q=%s&x=0&y=0&', 'Suche...'))
		self.mh_genMenu2(menu)

	def mh_callGenreListScreen(self):
		if re.search('Suche...', self.mh_genreTitle):
			self.paraQuery()
		else:
			genreurl = self.mh_baseUrl+self.mh_genreUrl[self.mh_menuLevel]+'set_gallery_type=video'
			#print 'GenreURL:',genreurl
			self.session.open(LSDE_FilmListeScreen, genreurl, self.mh_genreTitle)

	def paraQuery(self):
		self.param_qr = ''
		self.session.openWithCallback(self.cb_paraQuery, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_qr, is_dialog=True)

	def cb_paraQuery(self, callback = None, entry = None):
		if callback != None:
			self.param_qr = callback.strip()
			if len(self.param_qr) > 0:
				qr = self.param_qr.replace(' ','+')
				genreurl = self.mh_baseUrl+(self.mh_genreUrl[self.mh_menuLevel] % qr)+'set_gallery_type=video'
				self.session.open(LSDE_FilmListeScreen, genreurl, self.mh_genreTitle)

class LSDE_FilmListeScreen(MPScreen, ThumbsHelper):

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
		self['title'] = Label(LSDE_Version)

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
		self.pages = 0

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
		url = "%s&page=%d" % (self.genreLink, max(self.page,1))

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
		self.dokusListe = []
		self.dokusListe.append(("Keine Videos / Streams gefunden!","","",""))
		self.ml.setList(map(self._defaultlistleft, self.dokusListe))

	def loadPageData(self, content):
		print "loadPageData:",len(content)
		m = re.search('="pageselection(.*?)</div>', content, re.S)
		self.dokusListe = []
		content = content[content.find('<ul id="itemlist">'):content.find('<p class="advert-notice">')]
		spl=content.split('<li>')
		for i in range(1,len(spl),1):
			entry=spl[i]
			match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
			if match:
				url=match[0]
			else:
				continue
			match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
			if match:
				thumb=match[0]
			else:
				thumb = None
			match=re.compile('<span class="rating">(.+?)</span>', re.DOTALL).findall(entry)
			rating=-1
			if match:
				rating=match[0]
			match=re.compile('class="title" href="(.+?)"(.+?)title="(.+?)">(.+?)\n', re.DOTALL).findall(entry)
			title=match[0][3]
			title=decodeHtml(title).strip()
			if rating!=-1:
				title=title+(" (%.1f / 10)" % float(rating))
			self.dokusListe.append((title, "http://www.lachschon.de"+url, thumb, None))

		if self.dokusListe:
			print "Videos found !"
			if not self.pages:
				try:
					pgs = re.findall('"\?page=.*?">(\d+)</a', m.group(1), re.S)
					pages = min(int(pgs[-1]), 999)
				except:
					pages = 1

				if pages > self.pages:
					self.pages = pages

			if not self.page:
				self.page = 1
			print "Page: %d / %d" % (self.page,self.pages)
			self['page'].setText("%d / %d" % (self.page,self.pages))

			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			self.th_ThumbsQuery(self.dokusListe,0,1,2,None,None, self.page, self.pages)
			self.loadPicQueued()
		else:
			print "No Videos found !"
			self.dokusListe.append(("Keine Videos gefunden!","","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
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
		#print "streamName: ",streamName
		#print "streamPic: ",streamPic
		#print "streamUrl: ",streamUrl
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
		self['handlung'].setText(data)

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
		desc = self['liste'].getCurrent()[0][3]
		self.getHandlung(desc)
		self.loadPic()
		print "eventP: ",self.eventP.is_set()

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		self.session.open(
			LSDEPlayer,
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

class LSDEPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx):
		print "LSDEPlayer:"
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=True, listTitle="LACHSCHON.DE", ltype='lachschon.de')

	def getVideo(self):
		url = self.playList[self.playIdx][1]
		#print url
		twAgentGetPage(url).addCallback(self.parseStream).addErrback(self.dataError)

	def parseStream(self, data):
		print "parseStream:"
		m2 = re.search('//www.youtube.*?com/(embed|v)/(.*?)(\?|" |&amp)', data)
		if m2:
			print "Streams found"
			dhVideoId = m2.group(2)
			dhTitle = self.playList[self.playIdx][0]
			imgurl =  self.playList[self.playIdx][2]
			YoutubeLink(self.session).getLink(self.playStream, self.ytError, dhTitle, dhVideoId, imgurl=imgurl)
		else:
			print "No stream found"
			self.dataError("Kein Videostream gefunden!")

	def ytError(self, error):
		msg = "Title: %s\n%s" % (self.playList[self.playIdx][0], error)
		self.dataError(msg)