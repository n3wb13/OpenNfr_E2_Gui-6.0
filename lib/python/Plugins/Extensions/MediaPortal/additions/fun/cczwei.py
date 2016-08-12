# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class cczwei(MPScreen):

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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("Cczwei.de")
		self['ContentTitle'] = Label("Folgen:")
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://www.cczwei.de/index.php?id=tvissuearchive"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('CLASS="header"><b>TV-SENDUNGEN(.*?)class="header">AKTUELLE', data, re.S)
		videos = re.findall('<b>Folge (.*?)</b>.*?<a href="(index.php.*?)">(.*?)</a>', parse.group(1), re.S)
		if videos:
			for (folge, url, title) in videos:
				title = "Folge %s - %s" % (folge, title)
				url = "http://www.cczwei.de/" + url
				self.streamList.append((decodeHtml2(title), folge))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][1]
		if int(auswahl) < 10:
			auswahl = "00" + auswahl
		elif int(auswahl) < 100:
			auswahl = "0" + auswahl
		file = "http://cczwei.mirror.speedpartner.de/cc2tv/CC2_%s.mp4" % auswahl
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Title, file)], showPlaylist=False, ltype='cczwei')