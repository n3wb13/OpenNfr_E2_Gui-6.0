# -*- coding: utf-8 -*-
import mp_globals
from imports import *
from mpscreen import MPScreen
from debuglog import printlog as printl
from coverhelper import CoverHelper

class FirediveFilmScreen(MPScreen):

	def __init__(self, session, link, callback, playercallback):
		self.link = link
		self._callback = callback
		self.playercallback = playercallback
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Firedrive.com")
		self['ContentTitle'] = Label("Firedrive MultiStreams")
		self['name'] = Label("")
		self['F1'] = Label("")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label("")
		self['coverArt'] = Pixmap()
		self['Page'] = Label("")
		self['page'] = Label("")
		self['handlung'] = Label("")
		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		getPage(self.link).addCallback(self.firedriveData).addErrback(self.dataError)

	def firedriveData(self, data):
		streams = re.findall('image:url\((.*?)\);">\n<a href="(.*?)".*?>(.*?)<', data, re.S)
		if streams:
			for (image, url, title) in streams:
				url = "http://www.firedrive.com%s" % url
				image = "http:%s" % image
				title = title.replace("_"," ")
				self.filmliste.append((title, url, image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No supported streams found!"), '', ''))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self['name'].setText('')
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		link = self['liste'].getCurrent()[0][1]
		print link
		if link:
			self._callback(link, self.playercallback)