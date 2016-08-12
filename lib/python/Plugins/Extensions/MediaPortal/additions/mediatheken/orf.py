# -*- coding: utf-8 -*-
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
		self.url = "http://tvthek.orf.at/programs/letter/%s" % self.streamGenreLink
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
		parse = re.search('start latest: '+suchstring+'(.*?)ende latest: '+suchstring, data, re.S)
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
		parse = re.search('<script.*?initializeAdworx(.*?)</script>', data, re.S)
		folgen = re.findall('header":"(.*?)",.*?teaser_text":"(.*?)",.*?teaser_image_url":"(.*?)",.*?sources(.*?)embed', parse.group(1), re.S)
		if folgen:
			self.streamliste = []
			for (title,desc,image,urls) in folgen[1::]:
				url = re.search('"quality":"Q6A","quality_string":"hoch","src":"(http://apasfpd.apa.at.*?.mp4)",', urls.replace('\/','/'), re.S)
				title = title.replace('\\"','"')
				desc = desc.replace('\\"','"')
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