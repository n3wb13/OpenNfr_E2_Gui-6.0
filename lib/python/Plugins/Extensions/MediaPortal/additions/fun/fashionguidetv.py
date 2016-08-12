# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.simpleplayer import SimplePlayer, SimplePlaylist
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

FGTV_Version = "fashionguide-tv.com v0.90"

FGTV_siteEncoding = 'utf-8'

class FashionGuideTvGenreScreen(MPScreen):

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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(FGTV_Version)
		self['ContentTitle'] = Label(_("Menu"))
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label(_("Exit"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(('Aktuelles Programm', 1, 'http://www.fashionguide-tv.tv.grid-tv.com/?contentpart=prog_video'))
		self.genreliste.append(('Filme auf Abruf', 2, 'http://www.fashionguide-tv.tv.grid-tv.com/c/mid,1540,Filme_auf_Abruf/'))
		self.genreliste.append(('TV-Programmvorschau', 3, 'http://www.fashionguide-tv.tv.grid-tv.com/c/mid,2420,Programmhinweis/'))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		genreID = self['liste'].getCurrent()[0][1]
		genre = self['liste'].getCurrent()[0][0]
		tvLink = self['liste'].getCurrent()[0][2]
		if genreID == 1:
			self.session.open(
				GermanyTVPlayer2,
				[(genre, tvLink)],
				'Fashion-TV - aktuelles Programm'
				)
		else:
			self.session.open(FashionGuideTvListScreen, genreID, tvLink, genre)

class FashionGuideTvListScreen(MPScreen):

	def __init__(self, session, genreID, tvLink, stvGenre):
		self.genreID = genreID
		self.tvLink = tvLink
		self.genreName = stvGenre
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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(FGTV_Version)
		self['ContentTitle'] = Label("Genre: %s" % self.genreName)
		self['F1'] = Label(_("Exit"))
		self.keyLocked = True
		self.baseUrl = "http://www.fashionguide-tv.tv"

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		twAgentGetPage(self.tvLink).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		if self.genreID == 2:
			stvDaten = re.findall('<a href="\?v=(.*?)" title="(.*?)".*?<img src="(.*?)".*?_time">(.*?)<', data)
			if stvDaten:
				for (href,title,img,dura) in stvDaten:
					self.filmliste.append(('',title.replace(' - ','\n',1).replace('&amp;','&')+' ['+dura+']',href,img))
				self.keyLocked = False
			else:
				self.filmliste.append((_('No videos found!'),'','',''))
			self.ml.setList(map(self.TvListEntry, self.filmliste))
		elif self.genreID == 3:
			m = re.search('<div id="bx_main_c">(.*?)"center">', data, re.S)
			if m:
				stvDaten = re.findall('<td .*?<strong>(.*?)</strong></td>.*?title="(.*?)"><img src="(.*?)".*?onclick=', m.group(1), re.S)
			if stvDaten:
				for (ptime,title,img) in stvDaten:
					title = title.replace(' - ','\n\t',1).replace('&amp;','&')
					self.filmliste.append((ptime+'\t',title,'',img))
				self.keyLocked = False
			else:
				self.filmliste.append((_('No program data found!'),'','',''))
			self.ml.setList(map(self.TvListEntry, self.filmliste))
		self.ml.l.setItemHeight(self.height*2)

	def keyOK(self):
		if self.keyLocked:
			return
		if self.genreID == 2:
			self.session.open(
				GermanyTVPlayer,
				self.filmliste,
				"http://www.fashionguide-tv.tv.grid-tv.com/inc/mod/video/play.php/vid,%s/q,mp4/typ,ondemand/file.mp4",
				playIdx = self['liste'].getSelectedIndex(),
				playAll = True,
				listTitle = self.genreName
				)

class GermanyTVPlaylist(SimplePlaylist):

	def playListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1].replace('\n',' - ')))
		return res

class GermanyTVPlayer(SimplePlayer):

	def __init__(self, session, playList, tvLink, playIdx=0, playAll=False, listTitle=None):
		self.tvLink = tvLink
		SimplePlayer.__init__(self, session, playList, playIdx, playAll, listTitle, useResume=False)

	def getVideo(self):
		tvLink = self.tvLink % self.playList[self.playIdx][2]
		tvTitle = self.playList[self.playIdx][1]
		self.playStream(tvTitle, tvLink)

	def openPlaylist(self, pl_class=GermanyTVPlaylist):
		SimplePlayer.openPlaylist(self, pl_class)

class GermanyTVPlayer2(SimplePlayer):

	def __init__(self, session, playList, tvTitle, playIdx=0, playAll=False, listTitle=None):
		self.tvLink = None
		self.tryCount = 7
		self.tvTitle = tvTitle

		SimplePlayer.__init__(self, session, playList, playIdx, playAll, listTitle, showPlaylist=False, useResume=False)

	def getVideo(self):
		url = self.playList[self.playIdx][1]
		twAgentGetPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		tvStream = re.findall('video src=&quot;(.*?)&quot;', data)
		if tvStream:
			if self.tvLink != tvStream[0]:
				self.tvLink = tvStream[0]
				self.playStream(self.tvTitle, self.tvLink)
			elif self.tryCount:
				self.tryCount -= 1
				self.getVideo()

	def doEofInternal(self, playing):
		if playing == True:
			self.tryCount = 7
			reactor.callLater(1, self.getVideo)