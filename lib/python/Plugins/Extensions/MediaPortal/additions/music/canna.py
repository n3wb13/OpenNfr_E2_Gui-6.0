# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.simpleplayer import SimplePlayerMenu, SimplePlaylistIO
from Plugins.Extensions.MediaPortal.resources.cannalink import CannaLink

class cannaGenreScreen(MPScreen):

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

		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
		else:
			self.lastservice = None
		self.playing = False

		self.keyLocked = True
		self['title'] = Label("Canna.to")
		self['ContentTitle'] = Label("Alben:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)
		self.onClose.append(self.stopPlay)

	def loadPage(self):
		self.genreliste = [('Playlist',"none","3"),
							('TOP100 Single Charts',"http://ua.canna.to/canna/single.php","1"),
							('Austria Single Charts',"http://ua.canna.to/canna/austria.php","1"),
							('Black Charts Top 40',"http://ua.canna.to/canna/black.php","1"),
							('US Billboard Country Charts Top 30',"http://ua.canna.to/canna/country.php","1"),
							('Offizielle Dance Charts Top 50',"http://ua.canna.to/canna/odc.php","1"),
							('Party Schlager Charts Top 30',"http://ua.canna.to/canna/psc.php","1"),
							('Reggae Charts Top 20',"http://ua.canna.to/canna/reggae.php","1"),
							('Rock & Metal Single Charts Top 40',"http://ua.canna.to/canna/metalsingle.php","1"),
							('Swiss Single Charts Top 75',"http://ua.canna.to/canna/swiss.php","1"),
							('UK Single Charts Top 40',"http://ua.canna.to/canna/uksingle.php","1"),
							('US Billboard Single Charts Top 100',"http://ua.canna.to/canna/ussingle.php","1"),
							('-- Jahrescharts --', "dump","1"),
							('Single Jahrescharts',"http://ua.canna.to/canna/jahrescharts.php","2"),
							('Austria Jahrescharts',"http://ua.canna.to/canna/austriajahrescharts.php","2"),
							('Black Jahrescharts',"http://ua.canna.to/canna/blackjahrescharts.php","2"),
							('Dance Jahrescharts',"http://ua.canna.to/canna/dancejahrescharts.php","2"),
							('Party Schlager Jahrescharts',"http://ua.canna.to/canna/partyjahrescharts.php","2"),
							('Swiss Jahrescharts',"http://ua.canna.to/canna/swissjahrescharts.php","2")]

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def seekFwd(self):
		self['liste'].pageDown()

	def seekBack(self):
		self['liste'].pageUp()

	def keyOK(self):
		if self.keyLocked or self['liste'].getCurrent()[0][1] == "dump":
			return
		cannahdGenre = self['liste'].getCurrent()[0][0]
		cannahdUrl = self['liste'].getCurrent()[0][1]
		cannahdID = self['liste'].getCurrent()[0][2]
		print cannahdGenre, cannahdUrl, cannahdID

		if cannahdID == "1":
			self.session.open(cannaMusicListeScreen, cannahdGenre, cannahdUrl)
		elif cannahdID == "2":
			self.session.open(cannaJahreScreen, cannahdGenre, cannahdUrl)
		elif cannahdID == "3":
			self.session.open(cannaPlaylist)

	def keyCancel(self):
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)
		else:
			self.session.nav.stopService()
		self.playing = False
		self.close()

	def stopPlay(self):
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)
		else:
			self.session.nav.stopService()

class cannaPlaylist(MPScreen, InfoBarBase, InfoBarSeek):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultPlaylistScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultPlaylistScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		if not mp_globals.isDreamOS:
			self.skin = re.sub(r'progress_pointer="(.*?):\d+,\d+" render="PositionGauge"', r'pixmap="\1" render="Progress"', self.skin)
			self.skin = re.sub(r'type="MPServicePosition">Gauge</convert>', r'type="MPServicePosition">Position</convert>', self.skin)
		MPScreen.__init__(self, session)
		InfoBarBase.__init__(self)
		InfoBarSeek.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"menu" : self.openMenu,
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"red": self.keyDel,
			"yellow": self.keyPlaymode
		}, -1)

		self.keyLocked = True
		self.playmode = "Next"
		self["title"] = Label("Canna.to - Playlist")
		self["coverArt"] = Pixmap()
		self["songtitle"] = Label ("")
		self["artist"] = Label ("")
		self["album"] = Label ("Playlist")
		self['F3'] = Label(_("Playmode"))
		self['playmode'] = Label(self.playmode)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPlaylist)

	def loadPlaylist(self):
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_canna_playlist"):
			open(config.mediaportal.watchlistpath.value+"mp_canna_playlist","w").close()

		leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_canna_playlist")
		if not leer == 0:
			self.filmliste = []
			self.songs_read = open(config.mediaportal.watchlistpath.value+"mp_canna_playlist" , "r")
			for lines in sorted(self.songs_read.readlines()):
				line = re.findall('"(.*?)" "(.*?)"', lines)
				if line:
					(read_song, read_url) = line[0]
					print read_song, read_url
					self.filmliste.append((decodeHtml(read_song),read_url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.songs_read.close()
		else:
			self.filmliste = []
			self.filmliste.append(("No Songs added.","dump"))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))

	def openMenu(self):
		self.session.openWithCallback(self.cb_Menu, SimplePlayerMenu, 'extern')

	def cb_Menu(self, data):
		print "cb_Menu:"
		if data != []:
			if data[0] == 2:
				nm = self['liste'].getCurrent()[0][0]
				p = nm.find(' - ')
				if p > 0:
					scArtist = nm[:p].strip()
					scTitle = nm[p+3:].strip()
				else:
					p = nm.find('-')
					if p > 0:
						scArtist = nm[:p].strip()
						scTitle = nm[p+1:].strip()
					else:
						scArtist = ''
						scTitle = nm

				url = self['liste'].getCurrent()[0][1]
				ltype = 'canna'
				token = ''
				album = ''
				entry = [scTitle, url, scArtist, album, ltype, token, '', '0']

				res = SimplePlaylistIO.addEntry(data[1], entry)
				if res == 1:
					self.session.open(MessageBoxExt, _("Added entry"), MessageBoxExt.TYPE_INFO, timeout=5)
				elif res == 0:
					self.session.open(MessageBoxExt, _("Entry already exists"), MessageBoxExt.TYPE_INFO, timeout=5)
				else:
					self.session.open(MessageBoxExt, _("Error!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def keyPlaymode(self):
		if self.playmode == "Next":
			self.playmode = "Random"
		elif self.playmode == "Random":
			self.playmode = "Next"

		self["playmode"].setText(self.playmode)

	def keyOK(self):
		if self.keyLocked:
			return
		cannaName = self['liste'].getCurrent()[0][0]
		cannaUrl = self['liste'].getCurrent()[0][1]
		print cannaName, cannaUrl

		if re.match('.*?-', cannaName):
			playinfos = cannaName.split(' - ')
			if playinfos:
				if len(playinfos) == 2:
					self["artist"].setText(playinfos[0])
					self["songtitle"].setText(playinfos[1])
			else:
				playinfos = cannaName.split('-')
				if playinfos:
					if len(playinfos) == 2:
						self["artist"].setText(playinfos[0])
						self["songtitle"].setText(playinfos[1])
		else:
			self["artist"].setText(cannaName)

		#stream_url = self.getDLurl(cannaUrl)
		stream_url = CannaLink(self.session).getDLurl(cannaUrl)
		if stream_url:
			print stream_url
			sref = eServiceReference(0x1001, 0, stream_url)
			self.session.nav.playService(sref)
			self.playing = True

	def keyDel(self):
		if self.keyLocked:
			return

		cannaName = self['liste'].getCurrent()[0][0]
		cannaUrl = self['liste'].getCurrent()[0][1]

		print cannaName, cannaUrl

		writeTmp = open(config.mediaportal.watchlistpath.value+"mp_canna_playlist.tmp","w")
		if fileExists(config.mediaportal.watchlistpath.value+"mp_canna_playlist"):
			readPlaylist = open(config.mediaportal.watchlistpath.value+"mp_canna_playlist","r")
			for rawData in readPlaylist.readlines():
				data = re.findall('"(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(read_name, read_url) = data[0]
					if read_name != cannaName:
						writeTmp.write('"%s" "%s"\n' % (read_name, read_url))
			readPlaylist.close()
			writeTmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_canna_playlist.tmp", config.mediaportal.watchlistpath.value+"mp_canna_playlist")
			self.loadPlaylist()

	def doEofInternal(self, playing):
		print "Play Next Song.."

		if self.playmode == "Next":
			self['liste'].down()
		else:
			count = len(self.filmliste)-1
			get_random = random.randint(0, int(count))
			print "Got Random %s" % get_random
			self['liste'].moveToIndex(get_random)

		cannaName = self['liste'].getCurrent()[0][0]
		cannaUrl = self['liste'].getCurrent()[0][1]
		print cannaName, cannaUrl

		if re.match('.*?-', cannaName):
			playinfos = cannaName.split(' - ')
			if playinfos:
				if len(playinfos) == 2:
					self["artist"].setText(playinfos[0])
					self["songtitle"].setText(playinfos[1])
			else:
				playinfos = cannaName.split('-')
				if playinfos:
					if len(playinfos) == 2:
						self["artist"].setText(playinfos[0])
						self["songtitle"].setText(playinfos[1])
		else:
			self["artist"].setText(cannaName)

		#stream_url = self.getDLurl(cannaUrl)
		stream_url = CannaLink(self.session).getDLurl(cannaUrl)
		if stream_url:
			print stream_url
			sref = eServiceReference(0x1001, 0, stream_url)
			self.session.nav.playService(sref)
			self.playing = True

	def lockShow(self):
		pass

	def unlockShow(self):
		pass

	def seekFwd(self):
		self['liste'].pageDown()

	def seekBack(self):
		self['liste'].pageUp()

class cannaMusicListeScreen(MPScreen, InfoBarBase, InfoBarSeek):

	def __init__(self, session, genreName, genreLink):
		self.genreLink = genreLink
		self.genreName = genreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultPlaylistScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultPlaylistScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		if not mp_globals.isDreamOS:
			self.skin = re.sub(r'progress_pointer="(.*?):\d+,\d+" render="PositionGauge"', r'pixmap="\1" render="Progress"', self.skin)
			self.skin = re.sub(r'type="MPServicePosition">Gauge</convert>', r'type="MPServicePosition">Position</convert>', self.skin)
		MPScreen.__init__(self, session)
		InfoBarBase.__init__(self)
		InfoBarSeek.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"menu" : self.openMenu,
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"green": self.keyAdd,
			"yellow": self.keyPlaymode
		}, -1)

		self.keyLocked = True
		self.playmode = "Random"
		self["title"] = Label("Canna.to - %s" % self.genreName)
		self["coverArt"] = Pixmap()
		self["songtitle"] = Label ("")
		self["artist"] = Label ("")
		self["album"] = Label ("Playlist")
		self['F3'] = Label(_("Playmode"))
		self['playmode'] = Label(self.playmode)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		print self.genreLink
		getPage(self.genreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		print "drin"
		match = re.findall('<tr>.*?<font>(.*?)</font>.*?class="obutton" onClick="window.open..(.*?)...CannaPowerChartsPlayer.*?</tr>', data, re.S)
		if match:
			for title,url in match:
				url = "http://ua.canna.to/canna/"+url
				self.filmliste.append((decodeHtml(title),url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False

	def openMenu(self):
		self.session.openWithCallback(self.cb_Menu, SimplePlayerMenu, 'extern')

	def cb_Menu(self, data):
		print "cb_Menu:"
		if data != []:
			if data[0] == 2:
				nm = self['liste'].getCurrent()[0][0]
				p = nm.find('-')
				if p > 0:
					scArtist = nm[:p].strip()
					scTitle = nm[p+1:].strip()
				else:
					scArtist = ''
					scTitle = nm

				url = self['liste'].getCurrent()[0][1]
				ltype = 'canna'
				token = ''
				album = ''
				entry = [scTitle, url, scArtist, album, ltype, token, '', '0']

				res = SimplePlaylistIO.addEntry(data[1], entry)
				if res == 1:
					self.session.open(MessageBoxExt, _("Added entry"), MessageBoxExt.TYPE_INFO, timeout=5)
				elif res == 0:
					self.session.open(MessageBoxExt, _("Entry already exists"), MessageBoxExt.TYPE_INFO, timeout=5)
				else:
					self.session.open(MessageBoxExt, _("Error!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def keyAdd(self):
		if self.keyLocked:
			return

		cannaName = self['liste'].getCurrent()[0][0]
		cannaUrl = self['liste'].getCurrent()[0][1]

		if not fileExists(config.mediaportal.watchlistpath.value+"mp_canna_playlist"):
			open(config.mediaportal.watchlistpath.value+"mp_canna_playlist","w").close()

		if not self.checkPlaylist(cannaName):
			if fileExists(config.mediaportal.watchlistpath.value+"mp_canna_playlist"):
				writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_canna_playlist","a")
				writePlaylist.write('"%s" "%s"\n' % (cannaName, cannaUrl))
				writePlaylist.close()
				message = self.session.open(MessageBoxExt, _("added"), MessageBoxExt.TYPE_INFO, timeout=2)
		else:
			message = self.session.open(MessageBoxExt, _("Song already exists."), MessageBoxExt.TYPE_INFO, timeout=2)

	def checkPlaylist(self, song):
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_canna_playlist"):
			open(config.mediaportal.watchlistpath.value+"mp_canna_playlist","w").close()
			return False
		else:
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_canna_playlist")
			if not leer == 0:
				self.dupelist = []
				self.songs_read = open(config.mediaportal.watchlistpath.value+"mp_canna_playlist" , "r")
				for lines in sorted(self.songs_read.readlines()):
					line = re.findall('"(.*?)" "(.*?)"', lines)
					if line:
						(read_song, read_url) = line[0]
						self.dupelist.append((read_song))
				self.songs_read.close()

				if song in self.dupelist:
					return True
				else:
					return False
			else:
				return False

	def keyPlaymode(self):
		if self.playmode == "Next":
			self.playmode = "Random"
		elif self.playmode == "Random":
			self.playmode = "Next"

		self["playmode"].setText(self.playmode)

	def keyOK(self):
		if self.keyLocked:
			return
		cannaName = self['liste'].getCurrent()[0][0]
		cannaUrl = self['liste'].getCurrent()[0][1]
		print cannaName, cannaUrl

		if re.match('.*?-', cannaName):
			playinfos = cannaName.split(' - ')
			if playinfos:
				if len(playinfos) == 2:
					self["artist"].setText(playinfos[0])
					self["songtitle"].setText(playinfos[1])
			else:
				playinfos = cannaName.split('-')
				if playinfos:
					if len(playinfos) == 2:
						self["artist"].setText(playinfos[0])
						self["songtitle"].setText(playinfos[1])
		else:
			self["artist"].setText(cannaName)

		#stream_url = self.getDLurl(cannaUrl)
		stream_url = CannaLink(self.session).getDLurl(cannaUrl)
		if stream_url:
			print stream_url
			sref = eServiceReference(0x1001, 0, stream_url)
			self.session.nav.playService(sref)
			self.playing = True

	def seekFwd(self):
		self['liste'].pageDown()

	def seekBack(self):
		self['liste'].pageUp()

	def doEofInternal(self, playing):
		print "Play Next Song.."

		if self.playmode == "Next":
			self['liste'].down()
		else:
			count = len(self.filmliste)-1
			get_random = random.randint(0, int(count))
			print "Got Random %s" % get_random
			self['liste'].moveToIndex(get_random)

		cannaName = self['liste'].getCurrent()[0][0]
		cannaUrl = self['liste'].getCurrent()[0][1]
		print cannaName, cannaUrl

		if re.match('.*?-', cannaName):
			playinfos = cannaName.split(' - ')
			if playinfos:
				if len(playinfos) == 2:
					self["artist"].setText(playinfos[0])
					self["songtitle"].setText(playinfos[1])
			else:
				playinfos = cannaName.split('-')
				if playinfos:
					if len(playinfos) == 2:
						self["artist"].setText(playinfos[0])
						self["songtitle"].setText(playinfos[1])
		else:
			self["artist"].setText(cannaName)

		#stream_url = self.getDLurl(cannaUrl)
		stream_url = CannaLink(self.session).getDLurl(cannaUrl)
		if stream_url:
			print stream_url
			sref = eServiceReference(0x1001, 0, stream_url)
			self.session.nav.playService(sref)
			self.playing = True

	def lockShow(self):
		pass

	def unlockShow(self):
		pass

class cannaJahreScreen(MPScreen):

	def __init__(self, session, genreName, genreLink):
		self.genreLink = genreLink
		self.genreName = genreName

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

		self.keyLocked = True
		self['title'] = Label("Canna.to")
		self['ContentTitle'] = Label("Jahre:")

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		print self.genreLink
		getPage(self.genreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		print "drin"
		match = re.compile('<b><font face="Arial" size="5" color="#FFCC00"><a href="(.*?)">(.*?)</a></font></b>').findall(data, re.S)
		if match:
			for url, title in match:
				url = "http://ua.canna.to/canna/"+url
				self.filmliste.append((decodeHtml(title),url))
			self.filmliste.reverse()
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False

	def seekFwd(self):
		self['liste'].pageDown()

	def seekBack(self):
		self['liste'].pageUp()

	def keyOK(self):
		if self.keyLocked:
			return
		cannahdGenre = self['liste'].getCurrent()[0][0]
		cannahdUrl = self['liste'].getCurrent()[0][1]
		self.session.open(cannaMusicListeScreen2, cannahdGenre, cannahdUrl)

	def keyCancel(self):
		self.playing = False
		self.close()

class cannaMusicListeScreen2(MPScreen, InfoBarBase, InfoBarSeek):

	def __init__(self, session, genreName, genreLink):
		self.genreLink = genreLink
		self.genreName = genreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultPlaylistScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultPlaylistScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		if not mp_globals.isDreamOS:
			self.skin = re.sub(r'progress_pointer="(.*?):\d+,\d+" render="PositionGauge"', r'pixmap="\1" render="Progress"', self.skin)
			self.skin = re.sub(r'type="MPServicePosition">Gauge</convert>', r'type="MPServicePosition">Position</convert>', self.skin)
		MPScreen.__init__(self, session)
		InfoBarBase.__init__(self)
		InfoBarSeek.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"menu" : self.openMenu,
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"green": self.keyAdd,
			"yellow": self.keyPlaymode
		}, -1)

		self.keyLocked = True
		self.playmode = "Next"
		self["title"] = Label("Canna.to - %s" % self.genreName)
		self["coverArt"] = Pixmap()
		self["songtitle"] = Label ("")
		self["artist"] = Label ("")
		self["album"] = Label ("Playlist")
		self['F3'] = Label(_("Playmode"))
		self['playmode'] = Label(self.playmode)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		print self.genreLink
		getPage(self.genreLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		print "drin"
		raw = re.findall('<td align="left" style="border-style:solid; border-width:1px;">(.*?)>>  Player  <<', data, re.S)
		if raw:
			for each in raw:
				match = re.findall('<font size="1" face="Arial"><b>(.*?)</b></font>.*?<font size="1" face="Arial"><b>(.*?)</b></font>.*?(jc_player.php.*?)\'', each, re.S)
				if match:
					for (artist,title,url) in match:
						url = "http://ua.canna.to/canna/"+url
						title = "%s - %s" % (artist, title)
						self.filmliste.append((decodeHtml(title),url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False

	def openMenu(self):
		self.session.openWithCallback(self.cb_Menu, SimplePlayerMenu, 'extern')

	def cb_Menu(self, data):
		print "cb_Menu:"
		if data != []:
			if data[0] == 2:
				nm = self['liste'].getCurrent()[0][0]
				p = nm.find('-')
				if p > 0:
					scArtist = nm[:p].strip()
					scTitle = nm[p+1:].strip()
				else:
					scArtist = ''
					scTitle = nm

				url = self['liste'].getCurrent()[0][1]
				ltype = 'canna'
				token = ''
				album = ''
				entry = [scTitle, url, scArtist, album, ltype, token, '', '0']

				res = SimplePlaylistIO.addEntry(data[1], entry)
				if res == 1:
					self.session.open(MessageBoxExt, _("Added entry"), MessageBoxExt.TYPE_INFO, timeout=5)
				elif res == 0:
					self.session.open(MessageBoxExt, _("Entry already exists"), MessageBoxExt.TYPE_INFO, timeout=5)
				else:
					self.session.open(MessageBoxExt, _("Error!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def keyAdd(self):
		if self.keyLocked:
			return

		cannaName = self['liste'].getCurrent()[0][0]
		cannaUrl = self['liste'].getCurrent()[0][1]

		if not fileExists(config.mediaportal.watchlistpath.value+"mp_canna_playlist"):
			open(config.mediaportal.watchlistpath.value+"mp_canna_playlist","w").close()

		if not self.checkPlaylist(cannaName):
			if fileExists(config.mediaportal.watchlistpath.value+"mp_canna_playlist"):
				writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_canna_playlist","a")
				writePlaylist.write('"%s" "%s"\n' % (cannaName, cannaUrl))
				writePlaylist.close()
				message = self.session.open(MessageBoxExt, _("added"), MessageBoxExt.TYPE_INFO, timeout=2)
		else:
			message = self.session.open(MessageBoxExt, _("Song already exists."), MessageBoxExt.TYPE_INFO, timeout=2)

	def checkPlaylist(self, song):
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_canna_playlist"):
			open(config.mediaportal.watchlistpath.value+"mp_canna_playlist","w").close()
			return False
		else:
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_canna_playlist")
			if not leer == 0:
				self.dupelist = []
				self.songs_read = open(config.mediaportal.watchlistpath.value+"mp_canna_playlist" , "r")
				for lines in sorted(self.songs_read.readlines()):
					line = re.findall('"(.*?)" "(.*?)"', lines)
					if line:
						(read_song, read_url) = line[0]
						self.dupelist.append((read_song))
				self.songs_read.close()

				if song in self.dupelist:
					return True
				else:
					return False
			else:
				return False

	def keyPlaymode(self):
		if self.playmode == "Next":
			self.playmode = "Random"
		elif self.playmode == "Random":
			self.playmode = "Next"

		self["playmode"].setText(self.playmode)

	def keyOK(self):
		if self.keyLocked:
			return
		cannaName = self['liste'].getCurrent()[0][0]
		cannaUrl = self['liste'].getCurrent()[0][1]
		print cannaName, cannaUrl

		if re.match('.*?-', cannaName):
			playinfos = cannaName.split(' - ')
			if playinfos:
				if len(playinfos) == 2:
					self["artist"].setText(playinfos[0])
					self["songtitle"].setText(playinfos[1])
			else:
				playinfos = cannaName.split('-')
				if playinfos:
					if len(playinfos) == 2:
						self["artist"].setText(playinfos[0])
						self["songtitle"].setText(playinfos[1])
		else:
			self["artist"].setText(cannaName)

		#stream_url = self.getDLurl(cannaUrl)
		stream_url = CannaLink(self.session).getDLurl(cannaUrl)
		if stream_url:
			print stream_url
			sref = eServiceReference(0x1001, 0, stream_url)
			self.session.nav.playService(sref)
			self.playing = True

	def seekFwd(self):
		self['liste'].pageDown()

	def seekBack(self):
		self['liste'].pageUp()

	def doEofInternal(self, playing):
		print "Play Next Song.."

		if self.playmode == "Next":
			self['liste'].down()
		else:
			count = len(self.filmliste)-1
			get_random = random.randint(0, int(count))
			print "Got Random %s" % get_random
			self['liste'].moveToIndex(get_random)

		cannaName = self['liste'].getCurrent()[0][0]
		cannaUrl = self['liste'].getCurrent()[0][1]
		print cannaName, cannaUrl

		if re.match('.*?-', cannaName):
			playinfos = cannaName.split(' - ')
			if playinfos:
				if len(playinfos) == 2:
					self["artist"].setText(playinfos[0])
					self["songtitle"].setText(playinfos[1])
			else:
				playinfos = cannaName.split('-')
				if playinfos:
					if len(playinfos) == 2:
						self["artist"].setText(playinfos[0])
						self["songtitle"].setText(playinfos[1])
		else:
			self["artist"].setText(cannaName)

		#stream_url = self.getDLurl(cannaUrl)
		stream_url = CannaLink(self.session).getDLurl(cannaUrl)
		if stream_url:
			print stream_url
			sref = eServiceReference(0x1001, 0, stream_url)
			self.session.nav.playService(sref)
			self.playing = True

	def lockShow(self):
		pass

	def unlockShow(self):
		pass