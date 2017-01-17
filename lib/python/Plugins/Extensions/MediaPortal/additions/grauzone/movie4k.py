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
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

config.mediaportal.movie4klang = ConfigText(default="all", fixed_size=False)
config.mediaportal.movie4kdomain3 = ConfigText(default="http://movie4k.me", fixed_size=False)

if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/TMDb/plugin.pyo'):
	from Plugins.Extensions.TMDb.plugin import *
	TMDbPresent = True
elif fileExists('/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo'):
	TMDbPresent = False
	IMDbPresent = True
	from Plugins.Extensions.IMDb.plugin import *
else:
	IMDbPresent = False
	TMDbPresent = False

m4k = config.mediaportal.movie4kdomain3.value.replace('https://','').replace('http://','')
m4k_url = "%s/" % config.mediaportal.movie4kdomain3.value
g_url = "%s/movies-genre-" % config.mediaportal.movie4kdomain3.value
t_url = "https://movie4k.tv/thumbs"

movie4kheader = {}
ds = defer.DeferredSemaphore(tokens=1)

#TODO handle http timeout

def m4kcancel_defer(deferlist):
	try:
		[x.cancel() for x in deferlist]
	except:
		pass

class m4kGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.showM4kPorn = mode
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"yellow" : self.keyLocale,
			"blue" : self.keyDomain,
			"cancel": self.keyCancel
		}, -1)

		self.locale = config.mediaportal.movie4klang.value
		self.domain = config.mediaportal.movie4kdomain3.value
		global movie4kheader
		if self.locale == "de":
			movie4kheader = {'User-Agent': std_headers['User-Agent'], 'Cookie':'lang=de'}
		elif self.locale == "en":
			movie4kheader = {'User-Agent': std_headers['User-Agent'], 'Cookie':'lang=en'}
		elif self.locale == "all":
			movie4kheader = {'User-Agent': std_headers['User-Agent']}

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Genre:")
		if self.showM4kPorn != "porn":
			self['F3'] = Label(self.locale)
		self['F4'] = Label(self.domain)

		self.searchStr = ''
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.list = []
		if self.showM4kPorn == "porn":
			self.list.append(("Letzte Updates (XXX)", m4k_url+"xxx-updates.html"))
			self.list.append(('Genres', m4k_url+"genres-xxx.html"))
			self.list.append(("Alle Filme A-Z (XXX)", "XXXAZ"))
		else:
			self.list.append(("Kinofilme", m4k_url+"index.php"))
			self.list.append(("Videofilme", m4k_url+"index.php"))
			self.list.append(("Letzte Updates (Filme)", m4k_url+"index.php"))
			self.list.append(("Letzte Updates (Serien)", m4k_url+"tvshows-updates.html"))
			self.list.append(("Empfohlene Serien", m4k_url+"featuredtvshows.html"))
			self.list.append(("Alle Filme A-Z", "FilmeAZ"))
			self.list.append(("Alle Serien A-Z", "SerienAZ"))
			self.list.append(("Suche", m4k_url+"movies.php?list=search"))
			self.list.append(("Watchlist", "Watchlist"))
			self.list.append(("Abenteuer", g_url+"4-"))
			self.list.append(("Action", g_url+"1-"))
			self.list.append(("Biografie", g_url+"6-"))
			self.list.append(("Bollywood", g_url+"27-"))
			self.list.append(("Dokumentation", g_url+"8-"))
			self.list.append(("Drama", g_url+"2-"))
			self.list.append(("Erwachsene", g_url+"58-"))
			self.list.append(("Familie", g_url+"9-"))
			self.list.append(("Fantasy", g_url+"10-"))
			self.list.append(("Geschichte", g_url+"13-"))
			self.list.append(("Horror", g_url+"14-"))
			self.list.append(("Komödie", g_url+"3-"))
			self.list.append(("Kriegsfilme", g_url+"24-"))
			self.list.append(("Krimi", g_url+"7-"))
			self.list.append(("Kurzfilme", g_url+"55-"))
			self.list.append(("Musicals", g_url+"56-"))
			self.list.append(("Musik", g_url+"15-"))
			self.list.append(("Mystery", g_url+"17-"))
			self.list.append(("Reality TV", g_url+"59-"))
			self.list.append(("Romantik", g_url+"20-"))
			self.list.append(("Sci-Fi", g_url+"21-"))
			self.list.append(("Sport", g_url+"22-"))
			self.list.append(("Thriller", g_url+"23-"))
			self.list.append(("Trickfilm", g_url+"5-"))
			self.list.append(("Western", g_url+"25-"))
		self.ml.setList(map(self._defaultlistcenter, self.list))
		self.keyLocked = False

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		self.url = self['liste'].getCurrent()[0][1]
		if name == "Watchlist":
			self.session.open(m4kWatchlist)
		elif name == "Kinofilme":
			self.session.open(m4kFilme, self.url, name)
		elif name == "Videofilme":
			self.session.open(m4kFilme, self.url, name)
		elif name == "Letzte Updates (Filme)":
			self.session.open(m4kupdateFilme, self.url, name)
		elif name == "Letzte Updates (Serien)":
			self.session.open(m4kSerienUpdateFilme, self.url, name)
		elif name == "Empfohlene Serien":
			self.session.open(m4kTopSerienFilme, self.url, name)
		elif name == "Alle Serien A-Z" or name == "Alle Filme A-Z" or name == "Alle Filme A-Z (XXX)":
			self.session.open(m4kABCAuswahl, self.url, name)
		elif self.url == '%smovies.php?list=search' % m4k_url:
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True)
		elif name == "Letzte Updates (XXX)":
			self.session.open(m4kXXXListeScreen, self.url, name, '')
		else:
			self.session.open(m4kKinoAlleFilmeListeScreen, self.url, name)

	def keyDomain(self):
		if self.domain == "http://movie4k.me":
			config.mediaportal.movie4kdomain3.value = "https://movie.to"
		elif self.domain == "https://movie.to":
			config.mediaportal.movie4kdomain3.value = "http://movie4k.to"
		elif self.domain == "http://movie4k.to":
			config.mediaportal.movie4kdomain3.value = "https://movie4k.tv"
		elif self.domain == "https://movie4k.tv":
			config.mediaportal.movie4kdomain3.value = "http://movie4k.me"
		else:
			config.mediaportal.movie4kdomain3.value = "http://movie4k.me"
		config.mediaportal.movie4kdomain3.save()
		configfile.save()
		self.domain = config.mediaportal.movie4kdomain3.value
		global m4k, m4k_url, g_url
		m4k = "%s" % self.domain.replace('https://','').replace('http://','')
		m4k_url = "%s/" % self.domain
		g_url = "%s/movies-genre-" % self.domain
		self['title'].setText(m4k)
		self['F4'].setText(self.domain)

	def keyLocale(self):
		if self.showM4kPorn != "porn":
			global movie4kheader
			if self.locale == "de":
				movie4kheader = {'User-Agent': std_headers['User-Agent'], 'Cookie':'lang=en'}
				self.locale = "en"
				config.mediaportal.movie4klang.value = "en"
			elif self.locale == "en":
				movie4kheader = {'User-Agent': std_headers['User-Agent'], }
				self.locale = "all"
				config.mediaportal.movie4klang.value = "all"
			elif self.locale == "all":
				self.locale = "de"
				movie4kheader = {'User-Agent': std_headers['User-Agent'], 'Cookie':'lang=de'}
				config.mediaportal.movie4klang.value = "de"
			config.mediaportal.movie4klang.save()
			configfile.save()
			self['F3'].setText(self.locale)
			self.layoutFinished()

	def searchCallback(self, callbackStr):
		if callbackStr is not None:
			self.searchStr = callbackStr
			self.searchData = self.searchStr
			self.session.open(m4kSucheAlleFilmeListeScreen, self.url, self.searchData)

class m4kWatchlist(MPScreen):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"red" : self.keyDel,
			"info": self.update
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Watchlist")
		self['F1'] = Label(_("Delete"))

		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPlaylist)

	def loadPlaylist(self):
		self.list = []
		if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
			readStations = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(stationName, stationLink, stationLang, stationTotaleps) = data[0]
					self.list.append((stationName, stationLink, stationLang, stationTotaleps, "0"))
			self.list.sort()
			self.ml.setList(map(self.kinoxlistleftflagged, self.list))
			readStations.close()
			self.keyLocked = False

	def update(self):
		#TODO not checked if it works correct yet
		self.count = len(self.list)
		self.counting = 0

		if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp"):
			self.write_tmp = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp" , "a")
			self.write_tmp.truncate(0)
		else:
			self.write_tmp = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp" , "a")

		if len(self.list) != 0:
			self.keyLocked = True
			self.streamList2 = []
			downloads = [ds.run(self.download,item[1]).addCallback(self.check_data, item[0], item[1], item[2], item[3]).addErrback(self.dataError) for item in self.list]
			finished = defer.DeferredList(downloads).addErrback(self.dataError)

	def download(self, item):
		return twAgentGetPage(item)

	def check_data(self, data, sname, surl, slang, stotaleps):
		count_all_eps = 0
		self.counting += 1
		self['title'].setText("Update %s/%s" % (self.counting,self.count))

		staffeln = re.findall('<FORM name="episodeform(.*?)">(.*?)</FORM>', data, re.S)
		for (staffel, ep_data) in staffeln:
			episodes = re.findall('<OPTION value=".*?".*?>Episode.(.*?)</OPTION>', ep_data, re.S)
			count_all_eps += int(len(episodes))
			last_new_ep = staffel, episodes[-1]
		new_eps = int(count_all_eps) - int(stotaleps)

		self.write_tmp.write('"%s" "%s" "%s" "%s"\n' % (sname, surl, slang, count_all_eps))

		self.streamList2.append((sname, surl, slang, str(stotaleps), str(new_eps)))
		self.streamList2.sort()
		self.ml.setList(map(self.kinoxlistleftflagged, self.streamList2))

		if self.counting == self.count:
			self['title'].setText("Update done.")
			self.write_tmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp", config.mediaportal.watchlistpath.value+"mp_m4k_watchlist")
			self.keyLocked = False

		if last_new_ep:
			(staffel, episode) = last_new_ep
			if int(staffel) < 10:
				staffel3 = "S0"+str(staffel)
			else:
				staffel3 = "S"+str(staffel)

			if int(episode) < 10:
				episode3 = "E0"+str(episode)
			else:
				episode3 = "E"+str(episode)

			SeEp = "%s%s" % (staffel3, episode3)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(m4kEpisodenListeScreen, url, stream_name)

	def keyDel(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		selectedName = self['liste'].getCurrent()[0][0]

		writeTmp = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp","w")
		if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
			readStations = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(stationName, stationLink, stationLang, stationTotaleps) = data[0]
					if stationName != selectedName:
						writeTmp.write('"%s" "%s" "%s" "%s"\n' % (stationName, stationLink, stationLang, stationTotaleps))
			readStations.close()
			writeTmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp", config.mediaportal.watchlistpath.value+"mp_m4k_watchlist")
			self.loadPlaylist()

class m4kSucheAlleFilmeListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, searchUrl, searchData):
		self.searchUrl = searchUrl
		self.searchData = searchData
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyTMDbInfo
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Suche nach: %s" % self.searchData)

		self.deferreds = []
		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_("Please wait..."))
		url = "%s&search=%s" % (self.searchUrl, self.searchData)
		twAgentGetPage(url, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		kino = re.findall('<TR id="coverPreview(.*?)">.*?<a href="(.*?)">(.*?)<', data, re.S)
		if kino:
			self.list = []
			for image, teil_url, title in kino:
				url = '%s%s' % (m4k_url, teil_url)
				self.list.append((decodeHtml(title), url, image))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), '', None))
		self.ml.setList(map(self._defaultlistleft, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.list, 0, 1, None, None, '<img\ssrc="(http[s]?.*?/thumbs/.*?movie4k-film.jpg)".*?class="moviedescription"', 1, 1)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		streamUrl = self['liste'].getCurrent()[0][1]
		self['name'].setText(streamName)
		m4kcancel_defer(self.deferreds)
		downloads = ds.run(twAgentGetPage, streamUrl, agent=None, timeout=30, headers=movie4kheader).addCallback(self.showHandlung).addErrback(self.dataError)
		self.deferreds.append(downloads)

	def showHandlung(self, data):
		filmdaten = re.findall('<div style="float:left">.*?<img src="(.*?)".*?<div class="moviedescription">(.*?)</div>', data, re.S)
		if filmdaten:
			streamPic, handlung = filmdaten[0]
			CoverHelper(self['coverArt']).getCover(streamPic)
			self['handlung'].setText(decodeHtml(handlung).strip())

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(m4kStreamListeScreen, streamLink, streamGenreName, "movie")

	def keyTMDbInfo(self):
		if not self.keyLocked and TMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(TMDbMain, title)
		elif not self.keyLocked and IMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(IMDB, title)

class m4kKinoAlleFilmeListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber,
			"red" : self.keyTMDbInfo
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Filme Auswahl: %s" % self.streamGenreName)
		self['F2'] = Label(_("Page"))

		self.deferreds = []
		self.keyLocked = True
		self.preview = False
		self.XXX = False
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.lastpage = 1

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		if self.streamGenreLink == '%sgenres-xxx.html' % m4k_url:
			twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadXXXPageData).addErrback(self.dataError)
		elif re.search('%sxxx' % m4k_url, self.streamGenreLink):
			url = '%s%s%s' % (self.streamGenreLink, self.page, '.html')
			twAgentGetPage(url, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)
		elif re.search('http[s]?://(www.|)movie[^/]+/movies-(updates|all|genre)-', self.streamGenreLink):
			url = '%s%s%s' % (self.streamGenreLink, self.page, '.html')
			twAgentGetPage(url, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)
		else:
			twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadXXXPageData(self, data):
		self.XXX = True
		xxxGenre = re.findall('<TD\sid="tdmovies"\swidth="155">.*?<a\shref="(xxx-genre.*?)">(.*?)</a>', data, re.S)
		if xxxGenre:
			self.list = []
			for teil_url, title in xxxGenre:
				url = '%s%s' % (m4k_url, teil_url)
				title = title.replace("\t","")
				title = title.strip(" ")
				self.list.append((decodeHtml(title), url))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), ''))
		self.ml.setList(map(self._defaultlistleft, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def loadPageData(self, data):
		self['Page'].setText(_("Page:"))
		self.getLastPage(data, 'id="boxwhite"(.*?)<br>', '.*>(\d+)\s<')
		kino = re.findall('<TR id="coverPreview(.*?)">.*?<a href="(.*?)">(.*?)</a>', data, re.S)
		self.preview = False
		self.thumbfilmliste = []
		if re.search('hover\(function\(e\)', data, re.S):
			self.preview = True
		if kino:
			self.list = []
			for image, teil_url, title in kino:
				url = '%s%s' % (m4k_url, teil_url)
				if self.preview == True:
					imagelink = re.findall('coverPreview%s"\).hover\(.*?<img src=\'(.*?)\' alt' % image, data, re.S)
					if imagelink:
						self.list.append((decodeHtml(title).strip(), url, imagelink[0]))
					else:
						self.list.append((decodeHtml(title).strip(), url, None))
				else:
					self.list.append((decodeHtml(title).strip(), url, None))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), '', None))
		self.ml.setList(map(self._defaultlistleft, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		if self.XXX == False:
			if self.preview == False:
				self.th_ThumbsQuery(self.list,0,1,None,None,'<div style="float:left">.*?<img src="(.*?)"',self.page)
			else:
				self.th_ThumbsQuery(self.list,0,1,2,None,None,self.page)
		else:
			if self.preview == False:
				self.th_ThumbsQuery(self.list,0,1,None,None,'<div style="float:left">.*?<img src="(.*?)"',self.page)
			else:
				self.th_ThumbsQuery(self.list,0,1,2,None,None,self.page)
		self.showInfos()

	def showInfos(self):
		if self.XXX != True:
			streamName = self['liste'].getCurrent()[0][0]
			streamUrl = self['liste'].getCurrent()[0][1]
			self['name'].setText(streamName)
			m4kcancel_defer(self.deferreds)
			downloads = ds.run(twAgentGetPage, streamUrl, agent=None, timeout=30, headers=movie4kheader).addCallback(self.showHandlung).addErrback(self.dataError)
			self.deferreds.append(downloads)

	def showHandlung(self, data):
		filmdaten = re.findall('<div style="float:left">.*?<img src="(.*?)".*?<div class="moviedescription">(.*?)</div>', data, re.S)
		if filmdaten:
			streamPic, handlung = filmdaten[0]
			CoverHelper(self['coverArt']).getCover(streamPic)
			self['handlung'].setText(decodeHtml(handlung).strip())

	def keyOK(self):
		if self.keyLocked:
			return
		if self.XXX == False:
			streamGenreName = self['liste'].getCurrent()[0][0]
			streamLink = self['liste'].getCurrent()[0][1]
			self.session.open(m4kStreamListeScreen, streamLink, streamGenreName, "movie")
		else:
			streamGenreName= self['liste'].getCurrent()[0][0]
			xxxGenreLink = self['liste'].getCurrent()[0][1]
			self.session.open(m4kXXXListeScreen, xxxGenreLink, streamGenreName, 'X')

	def keyTMDbInfo(self):
		if not self.keyLocked and TMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(TMDbMain, title)
		elif not self.keyLocked and IMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(IMDB, title)

class m4kupdateFilme(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyTMDbInfo
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Filme Auswahl: %s" % self.streamGenreName)

		self.deferreds = []
		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_("Please wait..."))
		twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		last = re.findall('<td valign="top" height="100.*?"><a href="(.*?)"><font color="#000000" size="-1"><strong>(.*?)</strong></font></a></td>', data, re.S)
		if last:
			for url,title in last:
				url = "%s%s" % (m4k_url, url)
				self.list.append((decodeHtml(title), url))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), ''))
		self.ml.setList(map(self._defaultlistleft, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.list, 0, 1, None, None, '<img\ssrc="(http[s]?.*?/thumbs/.*?movie4k-film.jpg)".*?class="moviedescription"', 1, 1)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamUrl = self['liste'].getCurrent()[0][1]
		m4kcancel_defer(self.deferreds)
		downloads = ds.run(twAgentGetPage, streamUrl, agent=None, timeout=30, headers=movie4kheader).addCallback(self.showHandlung).addErrback(self.dataError)
		self.deferreds.append(downloads)

	def showHandlung(self, data):
		image = re.search('<img\ssrc="(http[s]?.*?/thumbs/.*?movie4k-film.jpg)"\sborder=0', data, re.S)
		if image:
			image = image.group(1)
			CoverHelper(self['coverArt']).getCover(image)
		handlung = re.findall('<div class="moviedescription">(.*?)<', data, re.S)
		if handlung:
			handlung = re.sub(r"\s+", " ", handlung[0])
			self['handlung'].setText(decodeHtml(handlung).strip())
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(m4kStreamListeScreen, streamLink, streamName, "movie")

	def keyTMDbInfo(self):
		if not self.keyLocked and TMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(TMDbMain, title)
		elif not self.keyLocked and IMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(IMDB, title)

class m4kFilme(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyTMDbInfo
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Filme Auswahl: %s" % self.streamGenreName)

		self.deferreds = []
		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if self.streamGenreName == "Kinofilme":
			kino = re.findall('<div style="float:left">.*?<a href="(.*?)"><img src="(.*?)" border=0 style="width:105px;max-width:105px;max-height:160px;min-height:140px;" alt=".*?kostenlos" title="(.*?).kostenlos"></a>', data, re.S)
		else:
			kino = re.findall('<div style="float: left;">.*?<a href="(.*?)"><img src="(.*?)" alt=".*?" title="(.*?)" border="0" style="width:105px;max-width:105px;max-height:160px;min-height:140px;"></a>', data, re.S)
		if kino:
			for url,image,title in kino:
				url = "%s%s" % (m4k_url, url)
				self.list.append((decodeHtml(title), url, image))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), '', None))
		self.ml.setList(map(self._defaultlistleft, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.list, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamUrl = self['liste'].getCurrent()[0][1]
		m4kcancel_defer(self.deferreds)
		downloads = ds.run(twAgentGetPage, streamUrl, agent=None, timeout=30, headers=movie4kheader).addCallback(self.showHandlung).addErrback(self.dataError)
		self.deferreds.append(downloads)
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(streamPic)

	def showHandlung(self, data):
		handlung = re.findall('<div class="moviedescription">(.*?)<', data, re.S)
		if handlung:
			handlung = re.sub(r"\s+", " ", handlung[0])
			self['handlung'].setText(decodeHtml(handlung).strip())
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(m4kStreamListeScreen, streamLink, streamName, "movie")

	def keyTMDbInfo(self):
		if not self.keyLocked and TMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(TMDbMain, title)
		elif not self.keyLocked and IMDbPresent:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(IMDB, title)

class m4kTopSerienFilme(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyAdd
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Serien Auswahl: %s" % self.streamGenreName)
		self['F2'] = Label(_("Add to Watchlist"))

		self.deferreds = []
		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		serien = re.findall('<div style="float:left"><a href="(.*?)"><img src="(.*?)" border=0 width=105 height=150 alt=".*?" title="(.*?)"></a>', data, re.S)
		if serien:
			for url,image,title in serien:
				url = "%s%s" % (m4k_url, url)
				self.list.append((decodeHtml(title), url, image))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), '', None))
		self.ml.setList(map(self._defaultlistleft, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.list, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamUrl = self['liste'].getCurrent()[0][1]
		m4kcancel_defer(self.deferreds)
		downloads = ds.run(twAgentGetPage, streamUrl, agent=None, timeout=30, headers=movie4kheader).addCallback(self.showHandlung).addErrback(self.dataError)
		self.deferreds.append(downloads)
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(streamPic)

	def showHandlung(self, data):
		handlung = re.findall('<div class="moviedescription">(.*?)<', data, re.S)
		if handlung:
			handlung = re.sub(r"\s+", " ", handlung[0])
			self['handlung'].setText(decodeHtml(handlung).strip())
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(m4kEpisodenListeScreen, streamLink, streamGenreName)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		self.mTitle = self['liste'].getCurrent()[0][0]
		self.mUrl = self['liste'].getCurrent()[0][1]

		if not fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
			open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
			writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","a")
			Lang = ""
			writePlaylist.write('"%s" "%s" "%s" "0"\n' % (self.mTitle, self.mUrl, Lang))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)

class m4kSerienUpdateFilme(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyAdd
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Serien Auswahl: %s" % self.streamGenreName)
		self['F2'] = Label(_("Add to Watchlist"))

		self.deferreds = []
		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		serien = re.findall('<TD id="tdmovies" width=.*?<a href="(.*?)">(.*?)</a>', data, re.S)
		if serien:
			for url,title in serien:
				url = m4k_url + url
				self.list.append((decodeHtml(title), url))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), ''))
		self.ml.setList(map(self._defaultlistleft, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.list, 0, 1, None, None, '"og:image" content="(http[s]?.*?/thumbs/.*?movie4k-film.jpg)"', 1, 1, coverlink=t_url)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamUrl = self['liste'].getCurrent()[0][1]
		m4kcancel_defer(self.deferreds)
		downloads = ds.run(twAgentGetPage, streamUrl, agent=None, timeout=30, headers=movie4kheader).addCallback(self.showHandlung).addErrback(self.dataError)
		self.deferreds.append(downloads)

	def showHandlung(self, data):
		image = re.search('"og:image" content="(http[s]?.*?/thumbs/.*?movie4k-film.jpg)"', data, re.S)
		if image:
			image = image.group(1)
		else:
			image = None
		CoverHelper(self['coverArt']).getCover(image)
		handlung = re.findall('<div class="moviedescription">(.*?)<', data, re.S)
		if handlung:
			handlung = re.sub(r"\s+", " ", handlung[0])
			self['handlung'].setText(decodeHtml(handlung).strip())
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		if re.match('.*?,.*?,.*?', streamGenreName):
			cname = re.findall('(.*?),.*?,.*?', streamGenreName, re.S)
			if cname:
				streamGenreName = cname[0]
		self.session.open(m4kEpisodenListeScreen, streamLink, streamGenreName)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		mTitle = self['liste'].getCurrent()[0][0]
		mUrl = self['liste'].getCurrent()[0][1]
		if re.match('.*?,.*?,.*?', mTitle):
			cname = re.findall('(.*?),.*?,.*?', mTitle, re.S)
			if cname:
				mTitle = cname[0]

		if not fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
			open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
			writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","a")
			writePlaylist.write('"%s" "%s" "%s" "0"\n' % (mTitle, mUrl, "de"))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)

class m4kStreamListeScreen(MPScreen):

	def __init__(self, session, streamGenreLink, streamName, which):
		self.streamGenreLink = streamGenreLink
		self.streamName = streamName
		self.which = which
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label(_("Stream Selection"))

		self.deferreds = []
		self.coverUrl = None
		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_("Please wait..."))
		twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if re.match('.*?(/img/parts/teil1_aktiv.png|/img/parts/teil1_inaktiv.png|/img/parts/part1_active.png|/img/parts/part1_inactive.png)', data, re.S):
			self.session.open(m4kPartListeScreen, data, self.streamName)
			self.close()
		else:
			if self.which == "movie":
				dupe = []
				hosters = re.findall('<tr id=.*?tablemoviesindex2.*?>(.*?)</td></tr>', data, re.S)
				if hosters:
					self.list = []
					for hoster_raw in hosters:
						hoster_data = re.findall('href.*?"(.*?)">(.*?)<img.*?&nbsp;(.*?)<', hoster_raw)
						if hoster_data:
							(h_url, h_date, h_name) = hoster_data[0]
							hoster_url = "%s%s" % (m4k_url, h_url.replace('\\',''))
							if not hoster_url in dupe:
								dupe.append(hoster_url)
								if isSupportedHoster(h_name, True):
									self.list.append((h_name, hoster_url, h_date))
				else:
					hosters = re.findall('<a target="_blank" href="(http[s]?://(.*?)/.*?)"', data, re.S)
					if not hosters:
						hosters = re.findall('<iframe src="(http[s]?://(.*?)/.*?)"', data, re.S)
					if hosters:
						(h_url, h_name) = hosters[0]
						h_name = h_name.split('.')[-2]
						h_name = h_name.lower().replace('faststream', 'rapidvideo').replace('fastvideo', 'rapidvideo')
						h_url = h_url.replace('faststream.in', 'rapidvideo.ws').replace('fastvideo.in', 'rapidvideo.ws')
						if re.search('(streamin|porntube4k|pandamovie|plashporn|porntorpia)', h_name)or isSupportedHoster(h_name, True):
							self.list.append((h_name.capitalize(), h_url, ""))
			else:
				hosters = re.findall('"tablemoviesindex2.*?<a href.*?"(.*?.html).*?style.*?src.*?"/img/.*?.[gif|png].*?> \&nbsp;(.*?)</a></td></tr>', data, re.S)
				if hosters:
					for url,h_name in hosters:
						url = "%s%s" % (m4k_url, url)
						if isSupportedHoster(h_name, True):
							self.list.append((h_name,url,'','',''))
			if len(self.list) == 0:
				self.list.append(("No supported streams found.", '', '', '', ''))
			self.ml.setList(map(self._defaultlisthoster, self.list))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfosData(data)
			self['name'].setText(self.streamName)

	def showInfos(self):
		m4kcancel_defer(self.deferreds)
		downloads = ds.run(twAgentGetPage, self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.showInfosData).addErrback(self.dataError)
		self.deferreds.append(downloads)

	def showInfosData(self, data):
		image = re.search('<img\ssrc="(http[s]?.*?/thumbs/.*?movie4k-film.jpg)".*?class="moviedescription"', data, re.S)
		if image:
			image = image.group(1)
		else:
			image = None
		CoverHelper(self['coverArt']).getCover(image)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		if isSupportedHoster(streamLink, True):
			get_stream_link(self.session).check_link(streamLink, self.got_link)
		else:
			twAgentGetPage(streamLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.get_streamlink, streamLink).addErrback(self.dataError)

	def get_streamlink(self, data, streamLink):
		link = re.search('<a\starget="_blank"\shref="(.*?)"><img\sborder=0\ssrc="/img/click_link.jpg"', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<iframe\swidth=".*?"\sheight=".*?"\sframeborder="0"\ssrc="(.*?)"\sscrolling="no"></iframe>', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<iframe\ssrc="(.*?)"\sframeborder=0\smarginwidth=0\smarginheight=0\sscrolling=no\swidth=.*?height=.*?></iframe>', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search("<iframe\sstyle=.*?src='(.*?)'\sscrolling='no'></iframe>", data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<div\sid="emptydiv"><iframe.*?src=["|\'](.*?)["|\']', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<div\sid="emptydiv"><script type="text/javascript"\ssrc=["|\'](.*?)["|\']>', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1).replace('?embed',''), self.got_link)
			return
		link = re.search('<object\sid="vbbplayer".*?src=["|\'](.*?)["|\']', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<param\sname="movie"\svalue="(.*?)"', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<a target="_blank" href="(.*?)"><img border=0 src="/img/click_link.jpg"', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<iframe\ssrc="(.*?)"\swidth=".*?"\sheight=".*?"\sframeborder="0"\sscrolling="no"></iframe>', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('(http[s]?://o(pen)?load.co/embed/.*?)"', data, re.S|re.I)
		if link:
			#oload is used at plashporn
			get_stream_link(self.session).check_link(link.group(1).replace('oload.co', 'openload.co'), self.got_link)
			return
		message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			if not fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watched"):
				open(config.mediaportal.watchlistpath.value+"mp_m4k_watched","w").close()

			self.update_liste = []
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_m4k_watched")
			if not leer == 0:
				self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_m4k_watched" , "r")
				for lines in sorted(self.updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						self.update_liste.append("%s" % (line[0]))
				self.updates_read.close()

				updates_read2 = open(config.mediaportal.watchlistpath.value+"mp_m4k_watched" , "a")
				check = ("%s" % self.streamName)
				if not check in self.update_liste:
					updates_read2.write('"%s"\n' % (self.streamName))
					updates_read2.close()
			else:
				updates_read3 = open(config.mediaportal.watchlistpath.value+"mp_m4k_watched" , "a")
				updates_read3.write('"%s"\n' % (self.streamName))
				updates_read3.close()

			self.session.open(SimplePlayer, [(self.streamName, stream_url, self.coverUrl)], showPlaylist=False, ltype='movie4k', cover=True)

class m4kPartListeScreen(MPScreen):

	def __init__(self, session, data, streamName):
		self.data = data
		self.streamName = streamName
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label(_("Parts Selection"))
		self['name'] = Label(self.streamName)

		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		idnr = re.findall('<a href="((film|movie)\.php\?id=\d+&part=(\d+))', self.data, re.S)
		if idnr:
			for links in idnr:
				url = "%s%s" % (m4k_url, links[0])
				part = "Disk %s" % str(links[2])
				self.list.append((part, url))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), ''))
		self.ml.setList(map(self._defaultlistcenter, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamPart = self['liste'].getCurrent()[0][0]
		streamLinkPart = self['liste'].getCurrent()[0][1]
		self.sname = "%s - Teil %s" % (self.streamName, streamPart)
		twAgentGetPage(streamLinkPart, agent=None, timeout=30, headers=movie4kheader).addCallback(self.get_streamlink).addErrback(self.dataError)

	def get_streamlink(self, data):
		link = re.search('<a\starget="_blank"\shref="(.*?)"><img\sborder=0\ssrc="/img/click_link.jpg"', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<iframe\swidth=".*?"\sheight=".*?"\sframeborder="0"\ssrc="(.*?)"\sscrolling="no"></iframe>', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<iframe\ssrc="(.*?)"\sframeborder=0\smarginwidth=0\smarginheight=0\sscrolling=no\swidth=.*?height=.*?></iframe>', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search("<iframe\sstyle=.*?src='(.*?)'\sscrolling='no'></iframe>", data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<div\sid="emptydiv"><iframe.*?src=["|\'](.*?)["|\']', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<div\sid="emptydiv"><script type="text/javascript"\ssrc=["|\'](.*?)["|\']>', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1).replace('?embed',''), self.got_link)
			return
		link = re.search('<object\sid="vbbplayer".*?src=["|\'](.*?)["|\']', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<param\sname="movie"\svalue="(.*?)"', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return
		link = re.search('<iframe\ssrc="(.*?)"\swidth=".*?"\sheight=".*?"\sframeborder="0"\sscrolling="no"></iframe>', data, re.S|re.I)
		if link:
			get_stream_link(self.session).check_link(link.group(1), self.got_link)
			return

		message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(SimplePlayer, [(self.sname, stream_url)], showPlaylist=False, ltype='movie4k', cover=False)

class m4kEpisodenListeScreen(MPScreen):

	def __init__(self, session, streamGenreLink, streamName):
		self.streamGenreLink = streamGenreLink
		self.streamName = streamName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label(_("Episode Selection"))
		self['name'] = Label(self.streamName)

		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_("Please wait..."))
		twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.watched_liste = []
		self.mark_last_watched = []
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_m4k_watched","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watched"):
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_m4k_watched")
			if not leer == 0:
				self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_m4k_watched" , "r")
				for lines in sorted(self.updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						self.watched_liste.append("%s" % (line[0]))
				self.updates_read.close()

		folgen = re.findall('<FORM name="episodeform(.*?)">(.*?)</FORM>', data, re.S)
		if folgen:
			for staffel,ep_data in folgen:
				episodes = re.findall('<OPTION value="(.*?)".*?>Episode.(.*?)</OPTION>', ep_data, re.S)
				if episodes:
					for url_to_streams, episode in episodes:
						if int(staffel) < 10:
							staffel3 = "S0"+str(staffel)
						else:
							staffel3 = "S"+str(staffel)

						if int(episode) < 10:
							episode3 = "E0"+str(episode)
						else:
							episode3 = "E"+str(episode)
						staffel_episode = "%s - %s%s" % (self.streamName,staffel3,episode3)
						staffel_episode = staffel_episode.replace('	','')
						url_to_streams = "%s%s" % (m4k_url,url_to_streams)
						if staffel_episode in self.watched_liste:
							self.list.append((staffel_episode,url_to_streams,True))
							self.mark_last_watched.append(staffel_episode)
						else:
							self.list.append((staffel_episode,url_to_streams,False))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), '', False))
		self.ml.setList(map(self._defaultlistleftmarked, self.list))
		self.ml.moveToIndex(0)

		# jump to last watched episode
		if len(self.mark_last_watched) != 0:
			counting_watched = 0
			for (name,url,watched) in self.list:
				counting_watched += 1
				if self.mark_last_watched[-1] == name:
					counting_watched = int(counting_watched) - 1
					break
			self['liste'].moveToIndex(int(counting_watched))
		else:
			if len(self.list) != 0:
				jump_last = len(self.list) -1
			else:
				jump_last = 0
			self['liste'].moveToIndex(int(jump_last))

		self.keyLocked = False
		self.showInfosData(data)

	def showInfosData(self, data):
		self['name'].setText(self.streamName)
		image = re.search('<img\ssrc="(http[s]?.*?/thumbs/.*?movie4k-film.jpg)".*?class="moviedescription"', data, re.S)
		if image:
			image = image.group(1)
		else:
			image = None
		CoverHelper(self['coverArt']).getCover(image)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamEpisode = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(m4kStreamListeScreen, streamLink, streamEpisode, "tv")

class m4kXXXListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, streamXXXLink, streamGenreName, genre):
		self.streamXXXLink = streamXXXLink
		self.streamGenreName = streamGenreName
		self.genre = False
		if genre == 'X':
			self.genre = True
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyPageNumber,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("XXX Auswahl")
		self['Page'].setText(_("Page:"))
		self['F2'] = Label(_("Page"))

		self.deferreds = []
		self.keyLocked = True
		self.preview = False
		self.page = 1
		self.lastpage = 1
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		if self.genre == True:
			shortUrl = re.findall('%sxxx-genre-[0-9]*[0-9]*.*?' % m4k_url, self.streamXXXLink)
			shortUrlC = str(shortUrl[0])
			url = shortUrlC + '-' + str(self.page) + '.html'
		else:
			url = str(self.streamXXXLink)
		twAgentGetPage(url, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.getLastPage(data, 'id="boxwhite"(.*?)<br>', '.*>(\d+)\s<')
		self.list = []
		if self.genre == False:
			streams = re.findall('<TD id="(.*?)" width="380">.*?<a href="(.*?)">(.*?)</a>', data, re.S)
		else:
			streams = re.findall('<TR id="(.*?)">.*?<TD width="550" id="tdmovies">.*?<a href="(.*?)">(.*?)</a>', data, re.S)
		self.preview = False
		self.thumbfilmliste = []
		if re.search('hover\(function\(e\)', data, re.S):
			self.preview = True

		if streams:
			for cover,url,title in streams:
				url = "%s%s" % (m4k_url, url)
				title = title.replace("\t","")
				title = title.strip(" ")

				if self.preview == True:
					imagelink = re.findall('%s"\).hover\(.*?<img src=\'(.*?)\' alt' % cover, data, re.S)
					if imagelink:
						self.list.append((decodeHtml(title), url, imagelink[0]))
					else:
						self.list.append((decodeHtml(title), url, None))
				else:
					self.list.append((decodeHtml(title), url, None))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), '', None))
		self.ml.setList(map(self._defaultlistleft, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		if self.preview == False:
			self.th_ThumbsQuery(self.list, 0, 1, None, None, '<img\ssrc="(http[s]?.*?/thumbs/.*?-film.jpg)"\sborder=0', self.page,self.lastpage)
		else:
			self.th_ThumbsQuery(self.list,0,1,2,None,None,self.page,self.lastpage)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamUrl = self['liste'].getCurrent()[0][1]
		m4kcancel_defer(self.deferreds)
		downloads = ds.run(twAgentGetPage, streamUrl, agent=None, timeout=30, headers=movie4kheader).addCallback(self.showHandlung).addErrback(self.dataError)
		self.deferreds.append(downloads)

	def showHandlung(self, data):
		image = self['liste'].getCurrent()[0][2]
		if not image:
			image = re.search('<img\ssrc="(http[s]?.*?/thumbs/.*?-film.jpg)"\sborder=0', data, re.S)
			if image:
				image = image.group(1)
			else:
				image = None
		CoverHelper(self['coverArt']).getCover(image)
		handlung = re.findall('<div class="moviedescription">(.*?)<', data, re.S)
		if handlung:
			handlung = re.sub(r"\s+", " ", handlung[0])
			self['handlung'].setText(decodeHtml(handlung).strip())
		else:
			self['handlung'].setText(_("No information found."))

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(m4kStreamListeScreen, streamLink, streamName, "movie")

class m4kABCAuswahl(MPScreen):

	def __init__(self, session, url, name):
		self.url = url
		self.name = name
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("%s" % self.name)

		self.keyLocked = True

		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.list = []
		abc = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","#"]
		for letter in abc:
			self.list.append((letter))
		self.ml.setList(map(self._defaultlistcenter, self.list))
		self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0]
		if auswahl == '#':
			auswahl = '1'
		if self.url == 'SerienAZ':
			streamGenreName = "%s" % auswahl
			streamGenreLink = "%stvshows-all-%s.html" % (m4k_url, auswahl)
			self.session.open(m4kSerienABCListe, streamGenreLink, streamGenreName)
		elif self.url == 'FilmeAZ':
			streamGenreName = "%s" % auswahl
			streamGenreLink = '%smovies-all-%s-' % (m4k_url, auswahl)
			self.session.open(m4kKinoAlleFilmeListeScreen, streamGenreLink, streamGenreName)
		elif self.url == 'XXXAZ':
			streamGenreName = "%s" % auswahl
			streamGenreLink = '%sxxx-all-%s-' % (m4k_url, auswahl)
			self.session.open(m4kKinoAlleFilmeListeScreen, streamGenreLink, streamGenreName)

class m4kSerienABCListe(MPScreen):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyAdd
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Serie Auswahl: %s" % self.streamGenreName)
		self['F2'] = Label(_("Add to Watchlist"))

		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		serien = re.findall('<TD id="tdmovies" width="538"><a href="(.*?)">(.*?)<.*?src="/img/(.*?)\.', data, re.S)
		if serien:
			self.list = []
			for urlPart, title, landImage in serien:
				url = '%s%s' % (m4k_url, urlPart)
				self.list.append((decodeHtml(title), url, landImage))
		if len(self.list) == 0:
			self.list.append(("No supported streams found.", '', None))
		self.ml.setList(map(self.kinoxlistleftflagged, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		landImageUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(landImageUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(m4kSerienABCListeStaffeln, streamLink, streamGenreName)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		self.mTitle = self['liste'].getCurrent()[0][0]
		self.mUrl = self['liste'].getCurrent()[0][1]
		self.mLang = self['liste'].getCurrent()[0][2]
		self.flag_stored = self.mLang.replace('/img/','').replace('.png','')

		twAgentGetPage(self.mUrl, agent=None, timeout=30, headers=movie4kheader).addCallback(self.get_final).addErrback(self.dataError)

	def get_final(self, data):
		season_link = False
		serien = re.findall('<TD id="tdmovies" width="538"><a href="(.*?)">(.*?)<.*?src="/img/(.*?)\.', data, re.S)
		if serien:
			for each in serien:
				(link, seriesname, flag) = each
				if flag == self.flag_stored:
					season_link = "%s%s" % (m4k_url, link)
		else:
			message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)

		if season_link:
			twAgentGetPage(season_link, agent=None, timeout=30, headers=movie4kheader).addCallback(self.get_final2).addErrback(self.dataError)
		else:
			message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)

	def get_final2(self, data):
		serien = re.findall('<TD id="tdmovies" width="538"><a href="(.*?)">(.*?)<.*?border=0 src="/img/(.*?)\.', data, re.S)
		if serien:
			for each in serien:
				(link, seriesname, flag) = each
				if flag == self.flag_stored:
					season_link = "%s%s" % (m4k_url, link)
		else:
			message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)

		if season_link:
			if not fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
				open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","w").close()
			if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
				writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","a")
				if self.mLang == "us_ger_small":
					Lang = "de"
				elif self.mLang == "us_flag_small":
					Lang = "en"
				else:
					Lang = ""

				seriesname = re.search("^(.*?)(, |$)", seriesname)
				writePlaylist.write('"%s" "%s" "%s" "0"\n' % (seriesname.group(1), season_link, Lang))
				writePlaylist.close()
				message = self.session.open(MessageBoxExt, _("Selection was added to the watchlist."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)

class m4kSerienABCListeStaffeln(MPScreen):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Staffel Auswahl:")
		self['name'] = Label(self.streamGenreName)
		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_("Please wait..."))
		twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		staffeln = re.findall('<TD id="tdmovies" width="538"><a href="(.*?)".*?Season:(.*?)<', data, re.S)
		if staffeln:
			self.list = []
			for urlPart, season in staffeln:
				url = '%s%s' % (m4k_url, urlPart)
				formatTitle = 'Season %s' % season
				self.list.append((decodeHtml(formatTitle), url))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), ''))
		self.ml.setList(map(self._defaultlistcenter, self.list))
		self.keyLocked = False
		self['name'].setText(self.streamGenreName)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(m4kSerienABCListeStaffelnFilme, streamLink, streamGenreName)

class m4kSerienABCListeStaffelnFilme(MPScreen):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label(_("Season Selection"))
		self['name'] = Label(self.streamGenreName)
		self.keyLocked = True
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_("Please wait..."))
		twAgentGetPage(self.streamGenreLink, agent=None, timeout=30, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		staffeln = re.findall('<TD id="tdmovies" width="538"><a href="(.*?)">(.*?), Season:(.*?), Episode:(.*?)<', data, re.S)
		if staffeln:
			self.list = []
			for urlPart, title, season, episode in staffeln:
				url = '%s%s' % (m4k_url, urlPart)
				formatTitle = 'Season %s Episode %s' % (season, episode)
				self.list.append((decodeHtml(formatTitle), url, title))
		if len(self.list) == 0:
			self.list.append((_('No movies found!'), '', ''))
		self.ml.setList(map(self._defaultlistcenter, self.list))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self['name'].setText(self.streamGenreName)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamEpisode = self['liste'].getCurrent()[0][2] + self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(m4kStreamListeScreen, streamLink, streamEpisode, "tv")