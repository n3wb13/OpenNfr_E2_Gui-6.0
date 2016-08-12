# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class Radiode(MPScreen):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/Radiode.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/Radiode.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"leavePlayer" : self.keyStop,
			"nextBouquet" : self.keySwitchList,
			"prevBouquet" : self.keySwitchList,
			"green" : self.keyAdd,
			"red" : self.keyDel
		}, -1)

		self['title'] = Label("Radio.de - Radio online hoeren")
		self['leftContentTitle'] = Label("S e n d e r l i s t e")
		self['rightContentTitle'] = Label("P l a y l i s t")
		self['stationIcon'] = Pixmap()
		self['stationInfo'] = Label("")
		self['stationDesc'] = Label("")
		self['F1'] = Label(_("Delete"))
		self['F2'] = Label(_("Add"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.playList = []
		self.ml2 = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['playlist'] = self.ml2

		self.currentList = "playlist"
		self.keyLocked = False
		self.playing = False
		self.lastservice = session.nav.getCurrentlyPlayingServiceReference()

		self.onLayoutFinish.append(self.layoutFinished)

	def radiode_playlist(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml2.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res

	def layoutFinished(self):
		self.keyLocked = True
		self.loadStations("liste")
		self.loadStations("playlist")
		self["liste"].selectionEnabled(0)
		self["playlist"].selectionEnabled(1)

	def loadStations(self, list):
		print list
		if list == "liste":
			self.streamList = []
			path = "/tmp/radiode_sender"
		else:
			self.playList = []
			if not fileExists(config.mediaportal.watchlistpath.value+"mp_radiode_playlist"):
				open(config.mediaportal.watchlistpath.value+"mp_radiode_playlist","w").close()
			if fileExists(config.mediaportal.watchlistpath.value+"mp_radiode_playlist"):
				path = config.mediaportal.watchlistpath.value+"mp_radiode_playlist"

		if fileExists(path):
			readStations = open(path,"r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(stationName, stationLink, stationImage, stationDesc) = data[0]
					if list == "liste":
						stationImage = 'http://radio.de/images/broadcasts/' + stationImage
						self.streamList.append((stationName, stationLink, stationImage, stationDesc))
					else:
						self.playList.append((stationName, stationLink, stationImage, stationDesc))
			if list == "liste":
				self.streamList.sort()
				self.ml.setList(map(self._defaultlistleft, self.streamList))
			else:
				self.playList.sort()
				self.ml2.setList(map(self.radiode_playlist, self.playList))

			readStations.close()

			exist = self[list].getCurrent()
			if exist != None:
				stationImage = self[list].getCurrent()[0][2]
				self.stationIconRead(stationImage)
				stationDesc = self[list].getCurrent()[0][3]
				self['stationDesc'].setText(stationDesc)

			self.keyLocked = False

	def stationIconRead(self, stationIconLink):
		CoverHelper(self['stationIcon']).getCover(stationIconLink)

	def keySwitchList(self):
		if self.currentList == "liste":
			self["liste"].selectionEnabled(0)
			self["playlist"].selectionEnabled(1)
			self.currentList = "playlist"
		else:
			self["playlist"].selectionEnabled(0)
			self["liste"].selectionEnabled(1)
			self.currentList = "liste"

	def keyLeft(self):
		exist = self[self.currentList].getCurrent()
		if self.keyLocked or exist == None:
			return
		self[self.currentList].pageUp()
		stationName = self[self.currentList].getCurrent()[0][0]
		self['stationInfo'].setText(stationName)
		stationImage = self[self.currentList].getCurrent()[0][2]
		self.stationIconRead(stationImage)
		stationDesc = self[self.currentList].getCurrent()[0][3]
		self['stationDesc'].setText(decodeHtml(stationDesc))

	def keyRight(self):
		exist = self[self.currentList].getCurrent()
		if self.keyLocked or exist == None:
			return
		self[self.currentList].pageDown()
		stationName = self[self.currentList].getCurrent()[0][0]
		self['stationInfo'].setText(stationName)
		stationImage = self[self.currentList].getCurrent()[0][2]
		self.stationIconRead(stationImage)
		stationDesc = self[self.currentList].getCurrent()[0][3]
		self['stationDesc'].setText(decodeHtml(stationDesc))

	def keyUp(self):
		exist = self[self.currentList].getCurrent()
		if self.keyLocked or exist == None:
			return
		self[self.currentList].up()
		stationName = self[self.currentList].getCurrent()[0][0]
		self['stationInfo'].setText(stationName)
		stationImage = self[self.currentList].getCurrent()[0][2]
		self.stationIconRead(stationImage)
		stationDesc = self[self.currentList].getCurrent()[0][3]
		self['stationDesc'].setText(decodeHtml(stationDesc))

	def keyDown(self):
		exist = self[self.currentList].getCurrent()
		if self.keyLocked or exist == None:
			return
		self[self.currentList].down()
		stationName = self[self.currentList].getCurrent()[0][0]
		self['stationInfo'].setText(stationName)
		stationImage = self[self.currentList].getCurrent()[0][2]
		self.stationIconRead(stationImage)
		stationDesc = self[self.currentList].getCurrent()[0][3]
		self['stationDesc'].setText(decodeHtml(stationDesc))

	def keyOK(self):
		exist = self[self.currentList].getCurrent()
		if self.keyLocked or exist == None:
			return

		stationUrl = self[self.currentList].getCurrent()[0][1]
		print stationUrl
		getPage(stationUrl).addCallback(self.getStreamTOmp3).addErrback(self.dataError)

	def getStreamTOmp3(self, data):
		stationStream = False
		if re.match('.*?"stream"', data, re.S):
			pattern = re.compile('"stream":"(.*?)"')
			stationStream = pattern.findall(data, re.S)
		elif re.match('.*?"streamUrl"', data, re.S):
			pattern = re.compile('"streamUrl":"(.*?)"')
			stationStream = pattern.findall(data, re.S)
		if stationStream:
			print stationStream[0]
			stationName = self['liste'].getCurrent()[0][0]
			sref = eServiceReference(0x1001, 0, stationStream[0])
			sref.setName(stationName)
			self.session.nav.playService(sref)
			self.playing = True

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None or self.currentList == "playlist":
			return
		stationName = self['liste'].getCurrent()[0][0]
		stationLink = self['liste'].getCurrent()[0][1]
		stationImage = self['liste'].getCurrent()[0][2]
		stationDesc = self['liste'].getCurrent()[0][3]

		path = config.mediaportal.watchlistpath.value+"mp_radiode_playlist"
		if fileExists(path):
			writePlaylist = open(path,"a")
			writePlaylist.write('"%s" "%s" "%s" "%s"\n' % (stationName, stationLink, stationImage, stationDesc))
			writePlaylist.close()
			self.loadStations("playlist")

	def keyDel(self):
		exist = self['playlist'].getCurrent()
		if self.keyLocked or exist == None or self.currentList == "liste":
			self["playlist"].selectionEnabled(0)
			self["liste"].selectionEnabled(1)
			self.currentList = "liste"
			return

		selectedName = self['playlist'].getCurrent()[0][0]

		pathTmp = config.mediaportal.watchlistpath.value+"mp_radiode_playlist.tmp"
		writeTmp = open(pathTmp,"w")

		path = config.mediaportal.watchlistpath.value+"mp_radiode_playlist"
		if fileExists(path):
			readStations = open(path,"r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(stationName, stationLink, stationImage, stationDesc) = data[0]
					if stationName != selectedName:
						writeTmp.write('"%s" "%s" "%s" "%s"\n' % (stationName, stationLink, stationImage, stationDesc))
			readStations.close()
			writeTmp.close()
			shutil.move(pathTmp, path)
			self.loadStations("playlist")
			exist = self['playlist'].getCurrent()
			if exist == None:
				self["liste"].selectionEnabled(1)
				self["playlist"].selectionEnabled(0)
				self.currentList = "liste"

	def keyStop(self):
		if self.playing:
			self.session.nav.stopService()
			self.session.nav.playService(self.lastservice)
			self.playing = False

	def keyCancel(self):
		if self.playing:
			self.session.nav.stopService()
			self.session.nav.playService(self.lastservice)
			self.playing = False
		self.close()