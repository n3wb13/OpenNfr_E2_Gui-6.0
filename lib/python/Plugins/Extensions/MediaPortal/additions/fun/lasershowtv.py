# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.additions.fun.fashionguidetv import GermanyTVPlayer, GermanyTVPlayer2, GermanyTVPlaylist
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

LSTV_Version = "LASERSHOW-TV v0.90"

LSTV_siteEncoding = 'utf-8'

class LaserShowTvGenreScreen(MPScreen):

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

		self['title'] = Label(LSTV_Version)
		self['ContentTitle'] = Label(_("Menu"))
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label(_("Exit"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(('Aktuelles Programm', 1, 'http://www.lasershow-tv.germany-tv.com/?contentpart=prog_video'))
		self.genreliste.append(('Filme auf Abruf', 2, 'http://www.lasershow-tv.germany-tv.com/c/mid,5523,Filme_auf_Abruf/'))
		self.genreliste.append(('TV-Programmvorschau', 3, 'http://www.lasershow-tv.germany-tv.com/c/mid,5522,TV-Programmvorschau/'))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		genreID = self['liste'].getCurrent()[0][1]
		genre = self['liste'].getCurrent()[0][0]
		tvLink = self['liste'].getCurrent()[0][2]
		if genreID == 1:
			self.session.open(
				GermanyTVPlayer2,
				[(genre, tvLink)],
				'LASERSHOW-TV - aktuelles Programm'
				)
		else:
			self.session.open(LaserShowTvListScreen, genreID, tvLink, genre)

class LaserShowTvListScreen(MPScreen):

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
			"0"	: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(LSTV_Version)
		self['ContentTitle'] = Label("Genre: %s" % self.genreName)
		self['F1'] = Label(_("Exit"))
		self.keyLocked = True
		self.baseUrl = "http://www.lasershow-tv.com"

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
				"http://www.lasershow-tv.com/inc/mod/video/play.php/vid,%s/q,mp4/typ,ondemand/file.mp4",
				playIdx = self['liste'].getSelectedIndex(),
				playAll = True,
				listTitle = self.genreName
				)