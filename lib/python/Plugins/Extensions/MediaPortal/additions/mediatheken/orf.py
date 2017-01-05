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

class ORFGenreScreen(MPScreen):

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
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("ORF TVthek")
		self['ContentTitle'] = Label("Auswahl der Sendung")

		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		for c in xrange(26):
			self.genreliste.append((chr(ord('A') + c), chr(ord('A') + c)))
		self.genreliste.insert(0, ('0-9', '0'))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(ORFSubGenreScreen, streamGenreLink)

class ORFSubGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink):
		self.streamGenreLink = streamGenreLink
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
			"5" : self.keyShowThumb,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("ORF TVthek")
		self['ContentTitle'] = Label("Auswahl der Sendung")


		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.url = "http://tvthek.orf.at/profiles/letter/%s" % self.streamGenreLink
		getPage(self.url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('subheadline">Verfügbare\sSendungen(.*?)<footer', data, re.S)
		sendungen = re.findall('base_list_item_headline">(.*?)</.*?class="episode_image">.*?src="(.*?)".*?</figure>', parse.group(1), re.S)
		if sendungen:
			self.genreliste = []
			for (title, image) in sendungen:
				self.genreliste.append((decodeHtml(title),title,image.replace('&amp;','&')))
			self.genreliste.sort(key=lambda t : t[0].lower())
		else:
			self.genreliste.append(('Keine Sendungen mit diesem Buchstaben vorhanden.', None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.genreliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		self.Name = self['liste'].getCurrent()[0][1]
		if self.Name != None:
			self.session.open(ORFFilmeListeScreen, self.url, self.Name)

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][2]
		if streamPic == None:
			return
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		CoverHelper(self['coverArt']).getCover(streamPic)

class ORFFilmeListeScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name= Name
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

		self['title'] = Label("ORF TVthek")
		self['ContentTitle'] = Label("Auswahl: %s" % decodeHtml(self.Name))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.Link).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		suchstring = self.Name
		suchstring = suchstring.replace('(','\(').replace(')','\)')
		parse = re.search('base_list_item_headline">'+suchstring+'(.*?)</ul>', data, re.S)
		folgen = re.findall('a\shref="(.*?)".*?meta_date">(.*?)</span.*?meta_time">(.*?)</span', parse.group(1), re.S)
		self.filmliste = []
		if folgen:
			for (url, date, time) in folgen:
				self.filmliste.append((decodeHtml(date + ', ' + time),url))
		else:
			self.filmliste.append(('Momentan ist keine Sendung in der TVthek vorhanden.', None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			self.session.open(ORFStreamListeScreen, url)

class ORFStreamListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link):
		self.Link = Link
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
			"5" : self.keyShowThumb,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("ORF TVthek")
		self['ContentTitle'] = Label(_("Selection:"))


		self.keyLocked = True
		self.streamliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.Link).addCallback(self.gotPageData).addErrback(self.dataError)

	def gotPageData(self, data):
		parse = re.search('jsb_VideoPlaylist" data-jsb="(.*?)"></div>', data, re.S)
		folgen = re.findall('episode_id.*?title":"(.*?)","description":(.*?),".*?preview_image_url":"(.*?)","sources":(\[.*?\])', parse.group(1).replace('&quot;','"').replace('\/','/'), re.S)
		if folgen:
			self.streamliste = []
			for (title, desc, image, urls) in folgen[:-1]:
				url = re.search('"quality":"Q6A","quality_string":"hoch","src":"(http://apasfpd.apa.at.*?.mp4)",', urls, re.S)
				title = title.replace('\\"','"')
				if desc == "null":
					desc = ""
				else:
					desc = desc.strip('"')
				self.streamliste.append((decodeHtml(title),url.group(1).replace('\/','/'),image.replace('\/','/'),desc))
			self.ml.setList(map(self._defaultlistleft, self.streamliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamliste, 0, 1, 2, None, None, 1, 1, mode=1)
			self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(SimplePlayer, self.streamliste, playIdx=self['liste'].getSelectedIndex(), playAll=True, showPlaylist=False, ltype='orf')

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][2]
		if streamPic == None:
			return
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamHandlung = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(decodeHtml(streamHandlung))
		CoverHelper(self['coverArt']).getCover(streamPic)