# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubelink import YoutubeLink
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

FVCDE_Version = "FUNNY-VIDEOCLIPS.DE v1.00"

FVCDE_siteEncoding = 'utf-8'

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

class show_FVCDE_Genre(MenuHelper):

	def __init__(self, session):
		MenuHelper.__init__(self, session, 0, [[]], "http://www.funny-videoclips.de", "", self._defaultlistcenter)

		self['title'] = Label(FVCDE_Version)
		self['ContentTitle'] = Label("Genres")

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_parseData(self, data):
		entrys = [('', 'Neue Clips')]
		menu = re.search('class="widget-title widgettitle">Videos</h4>(.*?)</ul>', data, re.S)
		if menu:
			entrys += re.findall('<li.*?href="(.*?)"\s*>(.*?)</a>', menu.group(1))

		return entrys

	def mh_callGenreListScreen(self):
		genreurl = self.mh_baseUrl+self.mh_genreUrl[0]+self.mh_genreUrl[1]
		self.session.open(FVCDE_FilmListeScreen, genreurl, self.mh_genreTitle)

class FVCDE_FilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
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
		self.baseUrl = "http://www.funny-videoclips.de"
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label(FVCDE_Version)

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
		self.newVids = 'Neue Clips' in self.genreName

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		if self.page > 1:
			url = "%s/page/%d/" % (self.genreLink, self.page)
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
		twAgentGetPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		printl(error,self,"E")
		self.dokusListe.append((_("No videos found!"),"","",""))
		self.ml.setList(map(self._defaultlistleft, self.dokusListe))

	def loadPageData(self, data):
		self.dokusListe = []
		a = 0
		l = len(data)
		while a < l:
			if self.newVids:
				m = re.search('class="entry-title"(.*?)</iframe></span></p>', data[a:], re.S)
				if m:
					a += m.end()
					d = re.search('rel="bookmark">(.*?)</a.*?//www.youtube.*?com/(embed|v)/(.*?)(\?|" |&amp)', m.group(1), re.S)
					if d:
						t = re.search('<img.*?src="(.*?)"', m.group(1), re.S)
						if t:
							img = t.group(1)
							if not img.startswith('http'):
								img = self.baseUrl + img
						else: img = None

						t = re.search('/></a>(.*?)</p>', m.group(1))
						if t:
							desc = decodeHtml(t.group(1))
						else:
							desc = None
						self.dokusListe.append((decodeHtml(d.group(1)), d.group(3), img, desc))
				else:
					break
			else:
				m = re.search('"associated-post">(.*?)</div></div>', data[a:])
				if m:
					a += m.end()
					d = re.search('"thumb-frame">.*?href="(.*?)".*?title="(.*?)".*?<img.*?src="(.*?)"', m.group(1))
					if d:
						t = re.search('"post-excerpt"><p>(.*?)</p>', m.group(1))
						if t:
							desc = decodeHtml(t.group(1))
						else:
							desc = None
						self.dokusListe.append((decodeHtml(d.group(2)), d.group(1), d.group(3), desc))
				else:
					break

		if self.dokusListe:
			if not self.page:
				pages = 0
				try:
					m = re.search('pagination"><ul>(.*?)</ul></div>', data, re.S)
					for p in re.finditer('">(\w+)</', m.group(1)):
						page = int(p.group(1))
						if page > pages: pages = page
					self.pages = pages
					self.page = 1
				except:
					pass
				else:
					self['page'].setText("%d / %d" % (self.page,self.pages))

			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self.th_ThumbsQuery(self.dokusListe, 0, 1, 2, None, None, self.page, self.pages, mode=1)
			self.loadPicQueued()
		else:
			self.dokusListe.append((_("No videos found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()

	def loadPic(self):

		if self.picQ.empty():
			self.eventP.clear()
			return

		if self.updateP:
			return

		while not self.picQ.empty():
			self.picQ.get_nowait()

		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		desc = self['liste'].getCurrent()[0][3]
		self.getHandlung(desc)
		self.updateP = 1
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def getHandlung(self, desc):
		if desc == None:
			self['handlung'].setText(_("No further information available!"))
			return
		self.setHandlung(desc)

	def setHandlung(self, data):
		self['handlung'].setText(decodeHtml(data))

	def ShowCoverFileExit(self):
		self.updateP = 0;
		self.keyLocked	= False
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
			self.loadPic()

	def loadPicQueued(self):
		self.picQ.put(None)
		if not self.eventP.is_set():
			self.eventP.set()
		self.loadPic()

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		self.session.open(
			FVCDEPlayer,
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

class FVCDEPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx):
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=True, listTitle="FUNNY-VIDEOCLIPS.DE", ltype='funny-videoclips.de')

	def getVideo(self):
		dhVideoId = self.playList[self.playIdx][1]
		dhTitle = self.playList[self.playIdx][0]
		imgurl =  self.playList[self.playIdx][2]
		if not dhVideoId.startswith('http'):
			YoutubeLink(self.session).getLink(self.playStream, self.ytError, dhTitle, dhVideoId, imgurl=imgurl)
		else:
			getPage(dhVideoId).addCallback(self.parseStream).addErrback(self.dataError)

	def parseStream(self, data):
		m2 = re.search('//www.youtube.com/(embed|v)/(.*?)(\?|" |&amp)', data)
		if m2:
			dhVideoId = m2.group(2)
			dhTitle = self.playList[self.playIdx][0]
			imgurl =  self.playList[self.playIdx][2]
			YoutubeLink(self.session).getLink(self.playStream, self.ytError, dhTitle, dhVideoId, imgurl=imgurl)
		else:
			self.dataError("Kein Videostream gefunden!")

	def ytError(self, error):
		msg = "Title: %s\n%s" % (self.playList[self.playIdx][0], error)
		self.dataError(msg)