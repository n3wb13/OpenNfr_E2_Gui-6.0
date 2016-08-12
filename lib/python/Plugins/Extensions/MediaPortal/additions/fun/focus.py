# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class focusGenre(MPScreen):

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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Focus.de")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Neueste", "newest"))
		self.genreliste.append(("Meistgesehen", "bookmarks_most-viewed"))
		self.genreliste.append(("Meistkommentiert", "bookmarks_most-commented"))
		self.genreliste.append(("Bestbewertet", "bookmarks_most-rated"))
		self.genreliste.append(("Politik", "4178"))
		self.genreliste.append(("Finanzen", "4343"))
		self.genreliste.append(("Wissen", "5200"))
		self.genreliste.append(("Gesundheit", "4707"))
		self.genreliste.append(("Kultur", "5417"))
		self.genreliste.append(("Panorama", "5603"))
		self.genreliste.append(("Sport", "5731"))
		self.genreliste.append(("Digital", "6392"))
		self.genreliste.append(("Reisen", "6568"))
		self.genreliste.append(("Auto", "6167"))
		self.genreliste.append(("Regional", "7302"))
		self.genreliste.append(("Immobilien", "6767"))
		self.genreliste.append(("Familie", "15310"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Url = 'http://www.focus.de/ajax/video/videoplaylist/?playlist_name=' + self['liste'].getCurrent()[0][1]
		self.session.open(focus, Url, Name)

class focus(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, Name):
		self.streamGenreLink = streamGenreLink
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Focus.de")
		self['ContentTitle'] = Label("%s" %self.Name)


		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.streamList = []
		self['name'].setText(_('Please wait...'))
		getPage(self.streamGenreLink).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		focusVideos = re.findall('<img.*?[rel|src]="(.*?[jpg|png])".*?<a\shref="(.*?)"\stitle="(.*?)"', data, re.S|re.I)
		if focusVideos:
			for (Image, Link, Name) in focusVideos:
				Image = Image.replace('" src="','')
				self.streamList.append((decodeHtml(Name), Image, Link))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 2, 1, None, None, 1, mode=1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][1]
		Link = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def handlungData(self, data):
		handlung = re.findall('og:description"\scontent="(.*?)"', data, re.S)
		if handlung:
			self['handlung'].setText(decodeHtml(handlung[0]))
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][2]
		getPage(Link).addCallback(self.searchStream).addErrback(self.dataError)

	def searchStream(self, data):
		Title = self['liste'].getCurrent()[0][0]
		streamUrl = re.findall('videourl\s=\s"(.*?)"', data, re.S)
		if streamUrl:
			streamUrl = streamUrl[-1]
			self.session.open(SimplePlayer, [(Title, streamUrl)], showPlaylist=False, ltype='focus')