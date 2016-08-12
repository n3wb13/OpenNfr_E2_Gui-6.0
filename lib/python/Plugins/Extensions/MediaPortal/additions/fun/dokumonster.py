# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

api = "http://dokumonster.de/api/0.1/get_items?limit=9999&online=true"

class dokumonsterGenreScreen(MPScreen):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Dokumonster.de")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Alle Dokus", api+"&sort=title&sortorder=asc&page="))
		self.genreliste.append(("Neueste", api+"&sort=date&sortorder=desc&page="))
		self.genreliste.append(("Top Dokus", api+"&sort=fire&sortorder=desc&page="))
		self.genreliste.append(("Themen", "http://dokumonster.de"))
		self.genreliste.append(("A-Z", api+"&sort=title&sortorder=asc&initial="))
		self.genreliste.append(("Suche", api+"&sortorder=desc&query="))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "Suche":
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True)
		elif Name == "A-Z":
			self.session.open(dokumonsterAZScreen, Link, Name)
		elif Name == "Themen":
			self.session.open(dokumonsterThemenScreen, Link, Name)
		else:
			self.session.open(DokuScreen, Link, Name)

	def searchCallback(self, callbackStr):
		if callbackStr is not None:
			Name = "Suche"
			Link = self['liste'].getCurrent()[0][1]
			URL = Link + "%s" % callbackStr.replace(' ','+') + "&page="
			self.session.open(DokuScreen, URL, Name)

class dokumonsterThemenScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Dokumonster.de")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)

		self.keyLocked = True
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		URL = self.Link
		getPage(URL).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		parse = re.findall('<option value="http://dokumonster.de/thema/(.*?)/">(.*?)</option>', data, re.S)
		for (tag, title) in parse:
			self.genreliste.append((decodeHtml(title), tag))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		API = api+"&sort=title&sortorder=desc&tag=" + Link + "&page="
		self.session.open(DokuScreen, API, Name)

class dokumonsterAZScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Dokumonster.de")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		for c in xrange(26):
			self.genreliste.append((chr(ord('A') + c), self.Link+chr(ord('a') + c)+"&page="))
		self.genreliste.append(("1", self.Link+"1&page="))
		self.genreliste.append(("2", self.Link+"2&page="))
		self.genreliste.append(("3", self.Link+"3&page="))
		self.genreliste.append(("4", self.Link+"4&page="))
		self.genreliste.append(("5", self.Link+"5&page="))
		self.genreliste.append(("6", self.Link+"6&page="))
		self.genreliste.append(("7", self.Link+"7&page="))
		self.genreliste.append(("8", self.Link+"8&page="))
		self.genreliste.append(("9", self.Link+"9&page="))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(DokuScreen, Link, Name)

class DokuScreen(MPScreen, ThumbsHelper):

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
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("Dokumonster.de")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 2
		self.lastpage = 1
		self.totalcount = 0
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		URL = self.Link + str(self.page)
		getPage(URL).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		lastp = re.search('totalcount":"(.*?)"', data, re.S)
		if lastp.group(1) != "0":
			self.totalcount = int(lastp.group(1))
		if self.totalcount != 0:
			lastp = round((float(self.totalcount) / 50) + 0.5)
			self.lastpage = int(lastp)
			self['page'].setText(str(self.page-1) + ' / ' + str(self.lastpage))
		else:
			self.lastpage = 999
			self['page'].setText(str(self.page-1))

		parse = re.findall('title":"(.*?)","link":"(.*?)","thumb":"(.*?)","description":"(.*?)","', data, re.S)
		for (Title, Link, Pic, Handlung) in parse:
			Title = Title.replace('\/','/').replace('\"','')
			Link = Link.replace('\/','/')
			Pic = Pic.replace('\/','/')
			Handlung = Handlung.replace('\\"','"').replace('\/','/')
			self.filmliste.append((decodeHtml(Title), Link, Pic, decodeHtml(Handlung)))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"),"",""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page-1, self.lastpage, mode=1, pagefix=+1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(handlung)
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 3:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.keyLocked:
			return
		if self.page-1 < self.lastpage:
			self.page += 1
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		title = self['liste'].getCurrent()[0][0]
		if re.search('.*?src="http://www.youtube.com/embed/videoseries.*?"', data):
			playlistPage = re.findall('Quelle:\s<a href="(.*?)"', data, re.S)
			Link = playlistPage[0]
			Name = title
			self.session.open(PlaylistParsingScreen, Link, Name)
		else:
			videoPage = re.findall('"http://www.youtube.com/(v|embed)/(.*?)\?.*?"', data, re.S)
			if videoPage:
				title = self['liste'].getCurrent()[0][0]
				self.session.open(YoutubePlayer,[(title, videoPage[0][1], None)],playAll= False,showPlaylist=False,showCover=False)

class PlaylistParsingScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("Dokumonster.de")
		self['ContentTitle'] = Label("Playlist:  %s" % self.Name)
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.Link).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		getVideos = re.findall('<td class="pl-video-title">.*?dir="ltr" href="(.*?)&amp;.*?">(.*?)</a>', data, re.S)
		for (Link, Title) in getVideos:
			Title = Title.title()
			vidLink = "http://www.youtube.com" + Link
			self.filmliste.append((decodeHtml(Title), vidLink))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		title = self['liste'].getCurrent()[0][0]
		videoPage = re.findall('"http://www.youtube.com/(v|embed)/(.*?)\?.*?"', data, re.S)
		if videoPage:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(YoutubePlayer,[(title, videoPage[0][1], None)],playAll= False,showPlaylist=False,showCover=False)