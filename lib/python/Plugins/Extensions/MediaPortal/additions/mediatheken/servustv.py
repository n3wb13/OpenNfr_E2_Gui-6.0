# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

baseurl = "http://www.servustv.com"
basename = "ServusTV"

class sTVGenreScreen(MPScreen):

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

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Aktuelles", "/de/Themen/Aktuelles"))
		self.genreliste.append(("Das Salzkammergut", "/de/Videos/Alle-Videos-zu-Sendungen/Das-Salzkammergut"))
		self.genreliste.append(("Die Frühstückerinnen", "/de/Videos/Alle-Videos-zu-Sendungen/Die-Fruehstueckerinnen"))
		self.genreliste.append(("Dokumentationen", "/de/Videos/Dokumentationen"))
		self.genreliste.append(("Kultur", "/de/Themen/Kultur"))
		self.genreliste.append(("Mei Tracht mei Gwand", "/de/Videos/Alle-Videos-zu-Sendungen/Mei-Tracht-mei-Gwand"))
		self.genreliste.append(("Natur", "/de/Themen/Natur"))
		self.genreliste.append(("Neueste", "/de/Videos/Neueste-Videos"))
		self.genreliste.append(("Sport", "/de/Themen/Sport"))
		self.genreliste.append(("Städte Trips", "/de/Videos/Alle-Videos-zu-Sendungen/Staedte-Trips"))
		self.genreliste.append(("Süsser am Morgen", "/de/Videos/Alle-Videos-zu-Sendungen/Suesser-am-Morgen"))
		self.genreliste.append(("Top Videos", "/de/Videos/Top-Videos"))
		self.genreliste.append(("Unterhaltung", "/de/Themen/Unterhaltung"))
		self.genreliste.append(("Volkskultur", "/de/Themen/Volkskultur"))
		self.genreliste.append(("Wissen", "/de/Themen/Wissen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		url = baseurl + url + "?page="
		self.session.open(sTVids,name,url)

class sTVids(MPScreen):

	def __init__(self, session,name,url):
		self.Link = url
		self.Name = name
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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))

		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "%s%s" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.getLastPage(data, 'class="org paging(.*?)</ul>', '.*page=(\d+)')
		raw = re.findall('block-(.*?)class="org\sFooter">', data, re.S)
		shows = re.findall('href="(/de/Medien/.*?)".*?src="(.*?)".*?videoleange">(.*?)<.*?<h4.*?">(.*?)</.*?subtitel">(.*?)<', raw[0], re.S)
		if shows:
			self.filmliste = []
			for (url,pic,leng,title,stitle) in shows:
				title = title.strip() + " - " + stitle.strip()
				pic = baseurl + pic
				self.filmliste.append((decodeHtml(title),url,pic,leng))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		self['handlung'].setText("Runtime: %s" % runtime)
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		self['name'] = Label(_("Please wait..."))
		url = baseurl + self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.getID).addErrback(self.dataError)

	def getID(self, data):
		id = re.findall('data-videoid="(.*?)"', data, re.S)[0]
		url = "http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=" + id
		getPage(url).addCallback(self.loadplaylist).addErrback(self.dataError)

	def loadplaylist(self, data):
		videoPrio = int(config.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			bw = 3000000
		elif videoPrio == 1:
			bw = 1500000
		else:
			bw = 750000
		title = self['liste'].getCurrent()[0][0]
		self.bandwith_list = []
		match_sec_m3u8=re.findall('BANDWIDTH=(\d+).*?(http://.*?videoId=\d+)', data, re.S)
		for each in match_sec_m3u8:
			bandwith,url = each
			self.bandwith_list.append((int(bandwith),url))
		_, best = min((abs(int(x[0]) - bw), x) for x in self.bandwith_list)
		self['name'].setText(title)
		self.keyLocked = False
		self.session.open(SimplePlayer, [(title, best[1])], showPlaylist=False, ltype='servustv')