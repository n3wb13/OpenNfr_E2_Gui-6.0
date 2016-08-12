# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2016
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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage, TwAgentHelper
from Plugins.Extensions.MediaPortal.resources.configlistext import ConfigListScreenExt
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

config.mediaportal.hdfilme_userName = ConfigText(default="USERNAME", fixed_size=False)
config.mediaportal.hdfilme_userPass = ConfigPassword(default="PASSWORD", fixed_size=False)

glob_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0'
ck = CookieJar()
initCookies = True
BASEURL = 'http://hdfilme.tv/'
proxyurl = '%s:80/noconnect' % BASEURL
agent = TwAgentHelper(proxy_url=proxyurl, gzip_decoding=True, followRedirect=True, cookieJar=ck, headers={'User-Agent':glob_agent, 'Content-Type': 'application/x-www-form-urlencoded'})

class hdfilmeMain(MPScreen):

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
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green": self.loginSetup
		}, -1)

		self['title'] = Label("HDFilme")

		self.streamList = []
		self.suchString = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self['F2'] = Label(_("Setup"))

		self.keyLocked = False
		self.onFirstExecBegin.append(self.layoutFinished)
		self.onClose.append(self.hdfilmeExit)

	def layoutFinished(self):
		self.username = config.mediaportal.hdfilme_userName.value
		self.password = config.mediaportal.hdfilme_userPass.value
		self['ContentTitle'].setText(_("Try Login..."))
		if self.username == "USERNAME" or self.password == "PASSWORD":
			self['ContentTitle'].setText(_("Selection") + " - " + _("No Login"))
			agent.getWebPage('%s/movie-movies' % BASEURL).addCallback(self.loadPage).addErrback(self.dataError)
		else:
			self.loginUrl = '%s/login.html' % BASEURL
			loginData = {'email': self.username, 'password': self.password, '_submit': 'true', 'remember': 'on'}
			agent.getWebPage(self.loginUrl, method='POST', postdata=urlencode(loginData)).addCallback(self.loginInfo).addErrback(self.dataError)

	def loginInfo(self, data):
		if 'complete":true' in str(data):
			self.loginOK = True
			self['ContentTitle'].setText(_("Selection") + " - " + _("%s logged in") % self.username)
		else:
			self.loginOK = False
			self['ContentTitle'].setText(_("Selection") + " - " + _("Login failed!"))
		agent.getWebPage('%s/movie-movies' % BASEURL).addCallback(self.loadPage).addErrback(self.dataError)

	def loadPage(self, data):
		self.keyLocked = True
		parse = re.search('>Genre</option>(.*?)</select>', data, re.S)
		if parse:
			cats = re.findall('<option value="(\d+)"\s+>\s+(.*?)\s\s', parse.group(1), re.S)
			if cats:
				for tagid, name in cats:
					self.streamList.append(("%s" % name, "%s/movie-movies?cat=%s&country=&order_f=id&order_d=desc&per_page=" % (BASEURL, str(tagid))))
		self.streamList.sort(key=lambda t : t[0].lower())
		self.streamList.insert(0, ("Serien","%s/movie-series?&per_page=" % BASEURL))
		self.streamList.insert(0, ("Kinofilme","%s/movie-cinemas?&per_page=" % BASEURL))
		self.streamList.insert(0, ("--- Search ---", "search"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		genre = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if genre == "--- Search ---":
			self.suchen(auto_text_init=True, suggest_func=self.getSuggestions)
		else:
			self.session.open(hdfilmeParsing, genre, url)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.strip()
			url = '%s/movie/search?key=%s' % (BASEURL, urllib.quote_plus(self.suchString))
			genre = self['liste'].getCurrent()[0][0]
			self.session.open(hdfilmeParsing, genre, url)

	def hdfilmeExit(self):
		global initCookies
		initCookies = True
		ck.clear()

	def loginSetup(self):
		if mp_globals.isDreamOS:
			self.session.openWithCallback(self.callBackSetup, meSetupScreen, is_dialog=True)
		else:
			self.session.openWithCallback(self.callBackSetup, meSetupScreen)

	def callBackSetup(self, answer):
		if answer:
			self.layoutFinished()

	def getSuggestions(self, text, max_res):
		url = "http://hdfilme.tv/movie/search_ac?term=%s" % urllib.quote_plus(text)
		d = twAgentGetPage(url, agent=None, headers=std_headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and suggestions:
			for m in re.finditer('"label":"(.+?)"', suggestions):
				list.append(decodeHtml(m.group(1)))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class hdfilmeParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
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
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("HDFilme")
		self['Page'] = Label(_("Page:"))
		self['ContentTitle'] = Label(genre)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		if initCookies:
			self.onLayoutFinish.append(self.getCookies)
		else:
			self.onLayoutFinish.append(self.loadPage)

	def getCookies(self):
		agent.getWebPage(BASEURL).addCallback(lambda _:self.loadPage()).addErrback(self.dataError)

	def loadPage(self):
		self.streamList = []
		if self.page > 1:
			url = self.url+str((self.page-1)*50)
		else:
			url = self.url
		agent.getWebPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		global initCookies
		if initCookies and 'id="gaIframe"' in data:
			return reactor.callLater(1,self.getCookies)
		initCookies = False

		self.getLastPage(data, '', '</i>\s*Seite.*?/\s*(\d+)')
		movies = re.findall('data-popover="movie-data.*?">\s*<a href="(.*?)">\s*<img.*?src="(.*?)".*?alt="(.*?)"', data, re.I)
		if movies:
			for url,bild,title in movies:
				self.streamList.append((decodeHtml(title),url,bild))
		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), None, None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page, self.lastpage)
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		self.coverurl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(self.coverurl)
		self['name'].setText(title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(hdfilmeStreams, title, url, cover)

class hdfilmeStreams(MPScreen):
	video_formats = (
			{
				'38' : 5, #MP4 Original (HD)
				'37' : 5, #MP4 1080p (HD)
				'22' : 4, #MP4 720p (HD)
				'35' : 2, #FLV 480p
				'18' : 1, #MP4 360p
				'34' : 3, #FLV 360p
			},
			{
				'38' : 5, #MP4 Original (HD)
				'37' : 5, #MP4 1080p (HD)
				'22' : 4, #MP4 720p (HD)
				'35' : 1, #FLV 480p
				'18' : 2, #MP4 360p
				'34' : 3, #FLV 360p
			},
			{
				'38' : 2, #MP4 Original (HD)
				'37' : 1, #MP4 1080p (HD)
				'22' : 1, #MP4 720p (HD)
				'35' : 3, #FLV 480p
				'18' : 4, #MP4 360p
				'34' : 5, #FLV 360p
			}
		)
	new_video_formats = (
			{
				'1080P' : 4, #MP4 1080p
				'720P' : 3, #MP4 720p
				'540P' : 2, #MP4 540p
				'360P' : 1, #MP4 360p
			},
			{
				'1080P' : 4, #MP4 1080p
				'720P' : 3, #MP4 720p
				'540P' : 1, #MP4 540p
				'360P' : 2, #MP4 360p
			},
			{
				'1080P' : 1, #MP4 1080p
				'720P' : 2, #MP4 720p
				'540P' : 3, #MP4 540p
				'360P' : 4, #MP4 360p
			}
		)

	def __init__(self, session, title, url, cover):
		self.movietitle = title
		self.url = url
		self.cover = cover
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
			"cancel": self.keyCancel,
			"green" : self.keyTrailer,
		}, -1)

		self['title'] = Label("HDFilme")
		self['leftContentTitle'] = Label(_("Stream Selection"))
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.movietitle)
		self['F4'] = Label("Stream")
		self['F4'].hide()

		self.trailer = None
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		agent.getWebPage(self.url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		m = re.search('<a class="btn.*?href="(.*?)">Trailer</a>', data)
		if m:
			self.trailer = m.group(1)
			self['F2'].setText('Trailer')

		servers = re.findall('<a.+?href="#(.*?)"\srole="tab" data-toggle="tab"><b>(.*?)</b></a>', data, re.S)
		if servers:
			for tab, server in servers:
				m = re.search('<div\srole="tabpanel"\sclass="tab-pane.*?"\sid="%s">(.*?)</div>' % tab, data, re.S)
				if m:
					streams = re.findall('_episode="(\d+)" _link="" _sub=""\s+href="(.*?)"', m.group(1), re.S)
					if streams:
						folge = 'Folge ' if len(streams) > 1 and len(servers) == 1 else server.strip()
						for (epi_num, link) in streams:
							if not folge[0] == 'F': epi_num = ''
							self.streamList.append((folge+epi_num, link, epi_num))
		if not len(self.streamList):
			streams = re.findall('_episode="(\d+)" _link="" _sub=""\s+href="(.*?)"', data, re.S)
			if streams:
				for (epi_num, link) in streams:
					if re.search('staffel ', self.movietitle, re.I):
						folge = 'Folge ' 
						_epi_num = epi_num
					else:
						folge = 'Stream ' 
						_epi_num = ''
					self.streamList.append((folge+epi_num, link, _epi_num))

		if len(self.streamList) == 0:
			self.streamList.append((_('No supported streams found!'), None, None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlisthoster, self.streamList))
		CoverHelper(self['coverArt']).getCover(self.cover)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		link = self['liste'].getCurrent()[0][1]
		self.getStreamUrl(link)

	def makeTitle(self):
		episode = self['liste'].getCurrent()[0][2]
		if episode:
			title = "%s - Folge %s" % (self.movietitle, episode)
		else:
			title = self.movietitle
		return title

	def getStreamUrl(self, link):
		import codecs, base64
		if not link.startswith('http'):
			stream_url = str(codecs.decode(base64.decodestring(link), 'rot_13'))
		else:
			stream_url = link
		if stream_url.startswith(BASEURL):
			agent.getWebPage(stream_url).addCallback(self.getBaseStreamUrl, stream_url).addErrback(self.dataError)
		elif '/picasaweb' in stream_url:
			agent.getWebPage(stream_url).addCallback(self.extractPicasa, stream_url, videoPrio=int(config.mediaportal.videoquali_others.value)).addErrback(self.dataError)
		elif '.youtube.' in stream_url:
			m = re.search('\?v=(.*?)(&|)', stream_url)
			if m:
				id = m.group(1)
				title = self.makeTitle()
				self.session.open(
					YoutubePlayer,
					[(title, id, self.cover)],
					playAll = False,
					showPlaylist=False,
					showCover=True
					)
			else:
				self.stream_not_found()
		else:
			self.play(stream_url)

	def getBaseStreamUrl(self, data, stream_url):
		m = re.search('myplayer"><iframe.+?src="(.*?)"', data)
		if m:
			std_headers = {
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
				'Accept-Language': 'en-us,en;q=0.5',
				'Referer': stream_url
			}
			twAgentGetPage(m.group(1), agent=glob_agent, headers=std_headers).addCallback(self.extractVimeoStream, videoPrio=int(config.mediaportal.videoquali_others.value)).addErrback(self.dataError)
		else:
			m = re.search('<div\sid="myplayer">\s*<script>(.*?)</iframe></div>', data, re.S)
			if m:
				self.extractPlayerDiv(m.group(1), stream_url)
			else:
				self.extractSourceStream(data, videoPrio=int(config.mediaportal.videoquali_others.value))

	def extractPlayerDiv(self, dcontent, stream_url):
		import array, binascii
		from Crypto.Cipher import AES
		key = array.array('B', "KHONGcoKEYdauMA!")
		decrypter = AES.new(key, AES.MODE_ECB)
		pdiv = '<div id="myplayer">'
		for m in re.finditer('abc\(\'(.*?)\'\);', dcontent):
			abc = m.group(1)
			cipher_str = array.array('B',binascii.unhexlify(abc))
			pdiv += decrypter.decrypt(cipher_str)
		self.getBaseStreamUrl(pdiv, stream_url)

	def extractSourceStream(self, data, videoPrio=2):
		m = re.search('\'sources\' : (\[.*?\])', data)
		if not m:
			m = re.search('\'sources\'\s*:\s*(\w+),', data)
			if m:
				m = re.search('var %s\s*=\s*(\[.*?\])' % m.group(1), data)
		if not m:
			self.extractOthers(data, videoPrio)
		else:
			d = json.loads('{"streams":%s}' % m.group(1)) if m else None
			links = {}
			try:
				for stream in d['streams']:
					key = stream.get('label').upper()
					if key:
						if self.new_video_formats[videoPrio].has_key(key):
							links[self.new_video_formats[videoPrio][key]] = stream.get('file')
						else:
							print 'no format prio:', key
				try:
					video_url = links[sorted(links.iterkeys())[0]]
				except (KeyError,IndexError):
					print "Error: no video url found:\n"
					self.stream_not_found()
				else:
					self.play(str(video_url))
			except:
				self.stream_not_found()

	def extractOthers(self, data, videoPrio):
		m = re.search('<div\sid="mediaplayer".*?<iframe\ssrc="(.*?)"', data, re.S)
		if m:
			link = m.group(1)
			printl(link)
			get_stream_link(self.session).check_link(link, self.play)
		else:
			self.stream_not_found()

	def extractVimeoStream(self, data, videoPrio=2):
		m = re.search('function\(e,a\)\{var\s+\w=(\{.*?\});', data, re.S)
		if not m:
			self.stream_not_found()
		else:
			d = json.loads('{"streams":%s}' % m.group(1)) if m else None
			links = {}
			try:
				for stream in d['streams']['request']['files']['progressive']:
					key = stream.get('quality').upper()
					if key:
						if self.new_video_formats[videoPrio].has_key(key):
							links[self.new_video_formats[videoPrio][key]] = stream.get('url')
						else:
							print 'no format prio:', key
				try:
					video_url = links[sorted(links.iterkeys())[0]]
				except (KeyError,IndexError):
					print "Error: no video url found:\n"
					self.stream_not_found()
				else:
					self.play(str(video_url))
			except:
				self.stream_not_found()

	def extractPicasa(self, data, p_url, videoPrio=2):
		id = p_url.split('#')[-1]
		video_url = None
		m = re.search('"gphoto\$id":"%s".*?"media":\{"content":\[(.*?)\]' % id, data)
		if m:
			links = {}
			streams = re.findall('"url":"(https://redirector.googlevideo.*?)"', m.group(1))
			for url in streams:
				m = re.search('itag=(\d+)', url)
				if m:
					key = m.group(1).upper()
					if self.video_formats[videoPrio].has_key(key):
						links[self.video_formats[videoPrio][key]] = urllib.unquote_plus(url)
					else:
						print 'no stream:',key,url
			try:
				video_url = links[sorted(links.iterkeys())[0]]
			except (KeyError,IndexError):
				print "Error: no video url found"
			else:
				pass
		else:
			print 'no id found'

		if not video_url:
			self.stream_not_found()
		else:
			self.play(video_url)

	def play(self, url):
		title = self.makeTitle()
		self.session.open(SimplePlayer, [(title, url, self.cover)], showPlaylist=False, ltype='hdfilme', cover=True)

	def stream_not_found(self):
		self.session.open(MessageBoxExt, _("Sorry, can't extract a stream url."), MessageBoxExt.TYPE_INFO, timeout=5)

	def keyTrailer(self):
		if self.trailer:
			agent.getWebPage(self.trailer).addCallback(self.playTrailer).addErrback(self.dataError)
			
	def playTrailer(self, data):
		from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
		m = re.search('//www.youtube\.com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		if m:
			trailerId = m.group(2)
			title = self.movietitle
			self.session.open(
				YoutubePlayer,
				[(title+' - Trailer', trailerId, self.cover)],
				playAll = False,
				showPlaylist=False,
				showCover=True
				)
		else:
			self.stream_not_found()

class meSetupScreen(Screen, ConfigListScreenExt):
	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/PluginUserDefault.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/PluginUserDefault.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		self['title'] = Label("HDFilme " + _("Setup"))
		self['F4'] = Label('')
		self.setTitle("HDFilme " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		self.list.append(getConfigListEntry(_("Username:"), config.mediaportal.hdfilme_userName))
		self.list.append(getConfigListEntry(_("Password:"), config.mediaportal.hdfilme_userPass))
		self["config"].setList(self.list)

		self["setupActions"] = ActionMap(["MP_Actions"],
		{
			"ok":		self.saveConfig,
			"cancel":	self.exit
		}, -1)

	def saveConfig(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close(True)

	def exit(self):
		self.close(False)