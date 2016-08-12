# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class arteFirstScreen(MPScreen):

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
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("arte Mediathek")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.filmliste.append(("Neueste Videos", "http://www.arte.tv/papi/tvguide/videos/plus7/program/D/L2/ALL/ALL/-1/AIRDATE_DESC/0/0/DE_FR.json"))
		self.filmliste.append(("Meistgesehen Videos", "http://www.arte.tv/papi/tvguide/videos/plus7/program/D/L2/ALL/ALL/-1/VIEWS/0/0/DE_FR.json"))
		self.filmliste.append(("Letzte Change Videos", "http://www.arte.tv/papi/tvguide/videos/plus7/program/D/L2/ALL/ALL/-1/LAST_CHANCE/0/0/DE_FR.json"))
		self.filmliste.append(("Themen", "by_channel"))
		self.filmliste.append(("Datum", "by_date"))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if ' Videos' in Name:
			self.session.open(arteSecondScreen, Link, Name)
		else:
			self.session.open(arteSubGenreScreen, Link, Name)

class arteSubGenreScreen(MPScreen):

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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("arte Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % Name)
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		if self.Name == "Datum":
			today = datetime.date.today()
			for daynr in range(0,31):
				day1 = today -datetime.timedelta(days=daynr)
				dateselect =  day1.strftime('%Y-%m-%d')
				link = 'http://www.arte.tv/guide/de/plus7/videos?day=-%s' % str(daynr)
				self.filmliste.append((dateselect, link, ''))
		elif self.Name == "Themen":
			link = 'http://www.arte.tv/guide/de/plus7/videos?category=%s'
			self.filmliste.append(('Aktuelles & Gesellschaft', link % 'ACT', ''))
			self.filmliste.append(('Fernsehfilme & Serien', link % 'FIC', ''))
			self.filmliste.append(('Kino', link % 'CIN', ''))
			self.filmliste.append(('Kunst & Kultur', link % 'ART', ''))
			self.filmliste.append(('Popkultur & Alternativ', link % 'CUL', ''))
			self.filmliste.append(('Entdeckung', link % 'DEC', ''))
			self.filmliste.append(('Geschichte', link % 'HIS', ''))
			self.filmliste.append(('Junior', link % 'JUN', ''))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(arteSecondScreen, Link, Name)

class arteSecondScreen(MPScreen, ThumbsHelper):

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
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("arte Mediathek")
		self['ContentTitle'] = Label("Auswahl: %s" % self.Name)
		self['Page'] = Label(_("Page:"))
		self['F2'] = Label(_("Page"))

		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		if ' Videos' in self.Name:
			url = self.Link
		else:
			url = "%s&page=%s&limit=24&sort=newest" % (self.Link, self.page)
		getPage(url, agent=std_headers, headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'Referer': self.Link}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		try:
			player = json.loads(data)
			getLastpage = player.get('total_count')
			if getLastpage:
				if int(getLastpage) >= 24:
					self.lastpage = int(getLastpage) / 24
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
			if player.has_key('videos'):
				try:
					for node in player["videos"]:
						subtitle = node.get('subtitle', '')
						if subtitle:
							title = "%s - %s" % (node.get('title'), subtitle)
						else:
							title = node.get('title')
						handlung = "Sendedatum: %s - %s min \n%s" % (node.get('scheduled_on', ''), str(int(node.get('duration', ''))/60), node.get('teaser', ''))
						link = "http://arte.tv/papi/tvguide/videos/stream/D/%s_PLUS7-D/ALL/ALL.json" % node.get('id')
						self.filmliste.append((title.encode('utf-8'), link.encode('utf-8'), node.get('thumbnail_url', '').encode('utf-8'), handlung.encode('utf-8').encode('utf-8')))
				except:
					pass
			else:
				try:
					if player.has_key('programDEList'):
						for node in player["programDEList"]:
							subtitle = node.get('STL', '')
							if subtitle:
								title = "%s - %s" % (node.get('TIT'), node.get('STL', ''))
							else:
								title = node.get('TIT')
							handlung = "%s min\n%s" % (str(int(node['VDO'].get('videoDurationSeconds', ''))/60), node.get('DTW', ''))
							self.filmliste.append((title.encode('utf-8'),node['VDO'].get('videoStreamUrl', '').encode('utf-8'),node['VDO'].get('programImage', '').encode('utf-8'),handlung.encode('utf-8')))	
				except:
					pass
		except:
			pass
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"), '','','','',''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self.ImageUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(_(title))
		self['handlung'].setText(handlung)
		CoverHelper(self['coverArt']).getCover(self.ImageUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		self.title = self['liste'].getCurrent()[0][0]
		link = self['liste'].getCurrent()[0][1]
		getPage(link, headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		streamSQ = re.findall('"HBBTV","VQU":"SQ","VMT":"mp4","VUR":"(.+?)"', data)
		if streamSQ:
			self.playStream(streamSQ[0])
		else:
			streamEQ = re.findall('"HBBTV","VQU":"EQ","VMT":"mp4","VUR":"(.+?)"', data)
			if streamEQ:
				self.playStream(streamEQ[0])

	def playStream(self, url):
		self.session.open(SimplePlayer, [(self.title, url, self.ImageUrl)], showPlaylist=False, ltype='arte')