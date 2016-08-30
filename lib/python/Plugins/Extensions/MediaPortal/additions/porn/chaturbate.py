# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2016
#
#    m3u8 Player for MediaPortal based on ChunkPlayer for Kodi by LivingOn
#    Copyright (c) 2015-2016 MediaPortal Team
#    Copyright (c) 2014 LivingOn <LivingOn@xmail.net>
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

BASEURL = "https://chaturbate.com/"

config.mediaportal.chaturbate_filter = ConfigText(default="all", fixed_size=False)

class chaturbateGenreScreen(MPScreen):

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
			"cancel" : self.keyCancel,
			"yellow": self.keyFilter
		}, -1)

		self.filter = config.mediaportal.chaturbate_filter.value

		self['title'] = Label("Chaturbate.com")
		self['ContentTitle'] = Label("Genre:")
		self['F3'] = Label(self.filter)

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.genreliste.append(("Featured", ""))
		self.genreliste.append(("Female", "female"))
		self.genreliste.append(("Couple", "couple"))
		self.genreliste.append(("HD", "hd"))
		self.genreliste.append(("Teen (18+)", "teen"))
		self.genreliste.append(("18 to 21", "18to21"))
		self.genreliste.append(("20 to 30", "20to30"))
		self.genreliste.append(("30 to 50", "30to50"))
		self.genreliste.append(("Mature (50+)", "mature"))
		self.genreliste.append(("North American", "north-american"))
		self.genreliste.append(("Euro Russian", "euro-russian"))
		self.genreliste.append(("Philippines", "philippines"))
		self.genreliste.append(("Asian", "asian"))
		self.genreliste.append(("South American", "south-american"))
		self.genreliste.append(("Other Region", "other-region"))
		self.genreliste.append(("Exhibitionist", "exhibitionist"))
		self.genreliste.append(("Male", "male"))
		self.genreliste.append(("Transsexual", "transsexual"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(chaturbateFilmScreen, Link, Name)

	def keyFilter(self):
		if self.filter == "all":
			self.filter = "female"
			config.mediaportal.chaturbate_filter.value = "female"
		elif self.filter == "female":
			self.filter = "couple"
			config.mediaportal.chaturbate_filter.value = "couple"
		elif self.filter == "couple":
			self.filter = "male"
			config.mediaportal.chaturbate_filter.value = "male"
		elif self.filter == "male":
			self.filter = "transsexual"
			config.mediaportal.chaturbate_filter.value = "transsexual"
		elif self.filter == "transsexual":
			self.filter = "all"
			config.mediaportal.chaturbate_filter.value = "all"

		config.mediaportal.chaturbate_filter.save()
		configfile.save()
		self['F3'].setText(self.filter)

class m3u8ChunkGrabber(threading.Thread):

	DELAY_AT_START = 2
	DELAY_AT_RUN = 1

	def __init__(self, streamurl, sequencenr, streamqueue, playlisturl, streambasepost):
		threading.Thread.__init__(self)
		self._streamurl = streamurl
		self._sequencenr = sequencenr + 1
		self._streamqueue = streamqueue
		self._playlisturl = playlisturl
		self._streambasepost = streambasepost
		self._stop_running_thread = False
		self.running = True
		self.lastID = ""
		self._delay = self.DELAY_AT_START

	def run(self):
		for i in xrange(self._sequencenr, sys.maxint):
			if self._playlisturl:
				data = self._get_data(self._playlisturl)
				getURL, getID = re.findall('(index-\d+-(.*?).ts)', data)[0]
				if getID != self.lastID:
					url = "%s%s" % (self._streamurl, getURL)
					self.lastID = getID
				else:
					from time import sleep
					sleep(1)
					continue
			else:
				url = "%s%d%s" % (self._streamurl, i, self._streambasepost)
			while self.running:
				data = self._get_data(url)
				if data:
					printl(url,self,"H")
					self._streamqueue.put(data)
					self._delay = self.DELAY_AT_RUN
					break
				else:
					from time import sleep
					sleep(self._delay)
				if self._stop_running_thread:
					printl('Exiting ChunkGrabber "while" loop',self,"H")
					break
			if self._stop_running_thread:
				printl('Exiting ChunkGrabber "for" loop',self,"H")
				break

	def stop(self):
		self._stop_running_thread = True
		self.running = False

	def _get_data(self, url):
		result = None
		try:
			result = urllib2.urlopen(url).read()
		except:
			pass
		return result

class m3u8StreamServer(threading.Thread):

	def __init__(self, streamurl, sequencenr, port, playlisturl, streambasepost):
		threading.Thread.__init__(self)
		self._streamurl = streamurl
		self._sequencenr = sequencenr
		self._port = port
		self._streamqueue = Queue.Queue()
		self._playlisturl = playlisturl
		self._streambasepost = streambasepost
		self._chunkgrabber_thread = m3u8ChunkGrabber(self._streamurl, self._sequencenr, self._streamqueue, self._playlisturl, self._streambasepost)

	def run(self):
		self._chunkgrabber_thread.start()
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_address = ("127.0.0.1", self._port)
		self.socket.bind(server_address)
		self.socket.listen(1)
		self.active = True
		while self.active:
			connection = self.socket.accept()[0]
			client_header = connection.recv(4096)
			connection.send(self._get_header())
			if client_header.startswith("HEAD"):
				connection.close()
				continue
			else:
				is_initial_call = True
				initial_call_counter = 0
				while self.active:
					if not self._streamqueue.empty():
						is_initial_call = False
						try:
							chunk = self._streamqueue.get()
							connection.send(chunk)
						except:
							self._chunkgrabber_thread.stop()
							printl('Sending ChunkGrabber stop signal',self,"H")
							break
					else:
						try:
							connection.send("")
						except:
							self._chunkgrabber_thread.stop()
							printl('Sending ChunkGrabber stop signal',self,"H")
							break
						if is_initial_call:
							initial_call_counter += 1
							if initial_call_counter > 15:
								self._chunkgrabber_thread.stop()
								self.active = False
						from time import sleep
						sleep(1)
				printl('Exiting StreamServer "while" loop 2',self,"H")
				break
			printl('Exiting StreamServer "while" loop 1',self,"H")
			break

	def stop(self):
		self.socket.shutdown()
		self.socket.close()
		self.active = False
		self.keyLocked = False
		self._chunkgrabber_thread.stop()

	def _get_header(self):
		return "\r\n".join(["HTTP/1.1 200 OK", "Accept-Ranges: bytes", "Content-Type: video/mp4", "", "",])

class m3u8Player:

	def __init__(self, session):
		self.session = session
		self.playing = False

	def play_stream(self, data, playlisturl=None):
		self.playlisturl = playlisturl
		self.streambasepost = ".ts"
		if data:
			try:
				playlist = re.findall('(http[s]?://.*?.stream.highwebmedia.com.*?m3u8)', data)[0]
				self.streambase = re.findall('(.*)playlist.*', playlist)[0]
				getPage(playlist).addCallback(self.getplaylist).addErrback(self.dataError)
			except:
				self.quitStream()
		else:
			self.quitStream()

	def getplaylist(self, data):
		try:
			chunkurl = re.findall('(chunk.*)', data)[0]
			url = self.streambase + chunkurl
			getPage(url).addCallback(self.getseq).addErrback(self.dataError)
		except:
			self.quitStream()

	def getseq(self, data):
		try:
			sequencenr = int(re.findall('EXT-X-MEDIA-SEQUENCE:(\d*)', data)[0])
			filename = re.findall('(media_w.*?_)', data)[0]
			streamurl = self.streambase + filename
			playlisturl = None
			if streamurl and sequencenr:
				port = 52000 + random.randint(100,500)
				self.lsst = m3u8StreamServer(streamurl, sequencenr, port, playlisturl, self.streambasepost)
				self.lsst.start()
				self.url = "http://127.0.0.1:" + str(port)
				from Plugins.Extensions.MediaPortal.resources.DelayedFunction import DelayedFunction
				DelayedFunction(1000, self.play)
		except:
			self.quitStream()

	def dataError(self, error):
		printl(error,self,"E")

	def play(self):
		try:
			if not self.playing:
				self.playing = True
				name = self['liste'].getCurrent()[0][0]
				self.session.openWithCallback(self.quitStream, SimplePlayer, [(name, self.url)], showPlaylist=False, ltype='chaturbate')
		except:
			self.quitStream()

	def quitStream(self):
		try:
			self.playing = False
			self.lsst.stop()
			name = self['liste'].getCurrent()[0][0]
			self['name'].setText(name)
		except:
			pass
		self.keyLocked = False

class chaturbateFilmScreen(MPScreen, ThumbsHelper, m3u8Player):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		if config.mediaportal.chaturbate_filter.value == "all":
			self.filter = ""
		else:
			self.filter = config.mediaportal.chaturbate_filter.value + "/"
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
		m3u8Player.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("Chaturbate.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F1'] = Label(_("Text-"))
		self['F2'] = Label(_("Page"))
		self['F4'] = Label(_("Text+"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 999

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		self['page'].setText(str(self.page))
		if self.Name == "Featured":
			url = BASEURL + "?page=%s" % self.page
		else:
			if self.Name == "Female" or self.Name == "Couple" or self.Name == "Male" or self.Name == "Transsexual":
				url = BASEURL + "%s-cams/?page=%s" % (self.Link, self.page)
			else:
				url = BASEURL + "%s-cams/%s?page=%s" % (self.Link, self.filter, self.page)
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		parse = re.search('class="list">(.*)class="featured_blog_posts">', data, re.S)
		Movies = re.findall('<li>.*?<a\shref="(.*?)".*?<img\ssrc="(.*?)".*?gender(\w)">(\d+)</span>.*?<li\stitle="(.*?)">.*?location.*?>(.*?)</li>.*?class="cams">(.*?)</li>.*?</div>.*?</li>', parse.group(1), re.S)
		if Movies:
			for (Url, Image, Gender, Age, Description, Location, Viewers) in Movies:
				self.filmliste.append((Url.strip('\/'), Url, Image, decodeHtml(Description), Gender, Age, decodeHtml(Location), Viewers))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No livestreams found!'), None, None, None, None, None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Url = self['liste'].getCurrent()[0][1]
		if Url == None:
			return
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		desc = self['liste'].getCurrent()[0][3]
		gender = self['liste'].getCurrent()[0][4]
		age = self['liste'].getCurrent()[0][5]
		location = self['liste'].getCurrent()[0][6]
		viewers = self['liste'].getCurrent()[0][7]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)
		if gender == "f":
			gender = "female"
		elif gender == "m":
			gender = "male"
		elif gender == "c":
			gender = "couple"
		elif gender == "s":
			gender = "transsexual"
		self['handlung'].setText("Age: %s, Gender: %s, Location: %s\n%s\n%s" % (age, gender, location, viewers, desc))

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_('Please wait...'))
		url = "https://chaturbate.com/" + name
		if mp_globals.isDreamOS:
			self.keyLocked = True
			getPage(url).addCallback(self.play_stream).addErrback(self.dataError)
		else:
			getPage(url).addCallback(self.play_stream2).addErrback(self.dataError)

	def keyCancel(self):
		if self.keyLocked:
			return
		try:
			self.lsst.stop()
		except:
			pass
		self.close()

	def play_stream2(self, data):
		url = re.findall('(http.*?://.*?.stream.highwebmedia.com:1935.*?m3u8)', data)[0]
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		if config.mediaportal.use_hls_proxy.value:
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='chaturbate')
		else:
			message = self.session.open(MessageBoxExt, _("If you want to play this stream, you have to activate the HLS-Player in the MP-Setup"), MessageBoxExt.TYPE_INFO, timeout=5)