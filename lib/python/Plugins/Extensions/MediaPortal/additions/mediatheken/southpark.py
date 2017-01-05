# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2017
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding execution on hardware, you are permitted to execute this plugin on VU+ hardware
#  which is licensed by satco europe GmbH, if the VTi image is used on that hardware.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
###############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

config.mediaportal.southparklang = ConfigText(default="de", fixed_size=False)

class SouthparkGenreScreen(MPScreen):

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
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"blue"	: self.keyLocale
		}, -1)

		self.locale = config.mediaportal.southparklang.value

		self['title'] = Label("Southpark.de")
		self['ContentTitle'] = Label("Genre:")
		self['F4'] = Label(self.locale)

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "http://www.southpark.de/alle-episoden"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		jsonurl = re.findall('data-url="(/feeds/carousel/.*?){', data, re.S)
		raw = re.findall('data-value="(season.*?)"\sdata-title="(.*?)"', data, re.S)
		if raw:
			for (ID, Title) in raw:
				Url = "http://www.southpark.de" + jsonurl[0] + "/30/1/json/!airdate/" + ID
				self.filmliste.append((Title, Url))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(SouthparkListScreen, Link, Name)

	def keyLocale(self):
		if self.keyLocked:
			return
		self.keyLocked = True
		if self.locale == "de":
			self.locale = "en"
			config.mediaportal.southparklang.value = "en"
		elif self.locale == "en":
			self.locale = "de"
			config.mediaportal.southparklang.value = "de"

		config.mediaportal.southparklang.save()
		configfile.save()
		self['F4'].setText(self.locale)
		self.loadPage()

class SouthparkListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label("Southpark.de")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = self.Link
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		json_data = json.loads(data)
		if json_data:
			for node in json_data['results']:
				try:
					itemid = str(node['itemId']) if 'itemId' in node else ""
					title = str(node['title']) if 'title' in node else ""
					description = str(node['description']) if 'description' in node else ""
					image = str(node['images']) if 'images' in node else ""
					episode = str(node['episodeNumber']) if 'episodeNumber' in node else ""
					avail = str(node['_availability']) if '_availability' in node else ""
				except:
					pass
				title = "S" + episode[:2] + "E" + episode[2:] + " - " + title
				self.filmliste.append((title, itemid, image, description, episode, avail))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No episodes found!"), None, '', '', '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		name = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(name)
		self['handlung'].setText(handlung)
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link:
			Name = self['liste'].getCurrent()[0][0]
			Pic = self['liste'].getCurrent()[0][2]
			Handlung = self['liste'].getCurrent()[0][3]
			available = self['liste'].getCurrent()[0][5]
			if available == "true":
				self.session.open(SouthparkAktScreen, Link, Name, Pic, Handlung)
			else:
				message = self.session.open(MessageBoxExt, _("Sorry, this video is not found or no longer available due to date or rights restrictions."), MessageBoxExt.TYPE_INFO, timeout=5)
				return

class SouthparkAktScreen(MPScreen):

	def __init__(self, session, Link, Name, Pic, Handlung):
		self.Link = Link
		self.Name = Name
		self.Pic = Pic
		self.Handlung = Handlung
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self.locale = config.mediaportal.southparklang.value

		self['title'] = Label("Southpark.de")
		self['ContentTitle'] = Label("Folge: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.keyLocked = True

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = "http://www.southpark.de/feeds/video-player/mrss/mgid:arc:episode:southpark.de:" + self.Link
		getPage(url).addCallback(self.getxmls).addErrback(self.dataError)

	def getxmls(self, data):
		if self.locale == "de":
			self.lang = "&lang=de"
		else:
			self.lang = "&lang=en"
		x = 0
		xmls = re.findall('<item>.*?<title>(.*?)</title>.*?<media:category\sscheme="urn:mtvn:id">mgid:arc:video:southparkstudios.com:(.*?)</media:category>', data, re.S)
		if xmls:
			for title, id in xmls:
				if not re.match(".*?Intro\sHD", title):
					x += 1
					url = "http://www.southpark.de/feeds/video-player/mediagen?uri=mgid:arc:episode:southpark.de:%s&suppressRegisterBeacon=true&suppressRegisterBeacon=true&acceptMethods=hls%s" % (id, self.lang)
					Titel = self.Name + " - Teil " + str(x)
					self.filmliste.append((Titel, url, self.Link))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		name = self['liste'].getCurrent()[0][0]
		coverUrl = self.Pic
		handlung = self.Handlung
		self['name'].setText(decodeHtml(name))
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		self.keyLocked = True
		self.link = self['liste'].getCurrent()[0][1]
		if config.mediaportal.use_hls_proxy.value:
			getPage(self.link).addCallback(self.StartStream).addErrback(self.dataError)
		else:
			message = self.session.open(MessageBoxExt, _("If you want to play this stream, you have to activate the HLS-Player in the MP-Setup"), MessageBoxExt.TYPE_INFO, timeout=5)

	def StartStream(self, data):
		title = self['liste'].getCurrent()[0][0]
		http_data = re.findall('<rendition.*?".*?<src>(.*?)</src>.*?</rendition>', data, re.S|re.I)
		if http_data:
			idx = self['liste'].getSelectedIndex()
			self.session.open(SouthparkPlayer, self.filmliste, int(idx) , True, False)
		else:
			message = self.session.open(MessageBoxExt, _("Sorry, this video is not found or no longer available due to date or rights restrictions."), MessageBoxExt.TYPE_INFO, timeout=5)
		self.keyLocked = False

class SouthparkPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx=0, playAll=True, showPlaylist=False):
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=playAll, showPlaylist=showPlaylist, ltype='southpark')

	def getVideo(self):
		self.title = self.playList[self.playIdx][0]
		self.pageurl = self.playList[self.playIdx][2]
		url = self.playList[self.playIdx][1]
		getPage(url).addCallback(self.gotVideo).addErrback(self.dataError)

	def gotVideo(self, data):
		http_data = re.findall('<rendition.*?".*?<src>(.*?)</src>.*?</rendition>', data, re.S|re.I)
		self.playStream(self.title, http_data[-1].replace('&amp;','&'))