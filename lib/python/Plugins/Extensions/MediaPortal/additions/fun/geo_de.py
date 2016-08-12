# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.simpleplayer import SimplePlayer, SimplePlaylist
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

STV_Version = "GEO.de v0.95"

STV_siteEncoding = 'iso8859-1'

class GEOdeGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
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

		self["actions"] = ActionMap(["MP_Actions"], {
			"yellow" :  self.keyTxtPageUp,
			"blue" :  self.keyTxtPageDown,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"0"		: self.closeAll,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(STV_Version)
		self['ContentTitle'] = Label("GEOaudio - Hören und Reisen")
		self['F1'] = Label(_("Exit"))
		self['F3'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))
		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.baseUrl = "http://www.geo.de"

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
		else:
			self.lastservice = None
		self.onClose.append(self.restoreLastService)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		stvLink = self.baseUrl + '/GEO/reisen/podcast/reise-podcast-geoaudio-hoeren-und-reisen-5095.html'
		print "getPage: ",stvLink
		twAgentGetPage(stvLink).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		print "genreData:"
		for m in re.finditer('id:"(.*?)".*?name:"(.*?)".*?mp3:"(.*?)".*?iption:"(.*?)".*?poster: "(.*?)"', data, re.S):
			id, name, mp3, desc, img = m.groups()
			self.filmliste.append(("%s. " % id, decodeHtml2(name), mp3, decodeHtml2(desc), "http://assets.geo.de/images/GEO/geoaudio_logo.png"))
			if self.keyLocked:
				self.keyLocked = False
		if not self.filmliste:
			self.filmliste.append(('Keine Podcasts gefunden !','','','',''))

		self.ml.setList(map(self.GEOdeListEntry, self.filmliste))
		self.th_ThumbsQuery(self.filmliste, 1, 0, 4, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		stvTitle = self['liste'].getCurrent()[0][1]
		stvImage = self['liste'].getCurrent()[0][4]
		stvDesc = self['liste'].getCurrent()[0][3]
		print stvImage
		self['name'].setText(stvTitle)
		self['handlung'].setText(stvDesc)
		CoverHelper(self['coverArt']).getCover(stvImage)

	def keyOK(self):
		if self.keyLocked:
			return
		self.session.open(
			GEOdePlayer,
			self.filmliste,
			playIdx = self['liste'].getSelectedIndex()
			)

	def restoreLastService(self):
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)
		else:
			self.session.nav.stopService()

class GEOdePlaylist(SimplePlaylist):

	def playListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0] + entry[1]))
		return res

class GEOdePlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx):
		print "GEOdePlayer:"

		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=True, listTitle="GEOaudio - Hören und Reisen", autoScrSaver=True, ltype='geo.de', playerMode='MP3')

	def getVideo(self):
		stvLink = self.playList[self.playIdx][2]
		stvTitle = "%s%s" % (self.playList[self.playIdx][0], self.playList[self.playIdx][1])
		stvImage = self.playList[self.playIdx][4]
		self.playStream(stvTitle, stvLink, imgurl=stvImage)

	def openPlaylist(self, pl_class=GEOdePlaylist):
		SimplePlayer.openPlaylist(self, pl_class)