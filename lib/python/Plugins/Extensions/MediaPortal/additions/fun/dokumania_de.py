# -*- coding: utf-8 -*-
#
#    Copyright (c) 2016 Billy2011, MediaPortal Team
#
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
try:
	from youtube_dl import YoutubeDL
except:
	YoutubeDL = None

DMDE_Version = "Dokumania v0.91"

DMDE_siteEncoding = 'utf-8'

cookies = CookieJar()
BASE_URL = "https://dokumania.de"

class show_DMDE_Genre(MenuHelper):

	def __init__(self, session):
		MenuHelper.__init__(self, session, 0, None, BASE_URL, "", self._defaultlistcenter)

		self['title'] = Label(DMDE_Version)
		self['ContentTitle'] = Label("Genres")

		self.param_qr = ''

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_parseCategorys(self, data):
		menu_marker = '">Kategorien</'
		if YoutubeDL == None:
			excludes = ['/vice']
		else:
			excludes = []
		menu = [(0, "/", "Neueste Beiträge")]
		menu += self.scanMenu(data, menu_marker, base_url=self.mh_baseUrl, url_ex=excludes)
		if menu:
			menu.append((0, "/?s=%s", "Suche..."))
		self.mh_genMenu2(menu)

	def mh_callGenreListScreen(self):
		if re.search('Suche...', self.mh_genreTitle):
			self.paraQuery()
		else:
			genreurl = self.mh_genreUrl[self.mh_menuLevel]
			if not genreurl.startswith('http'): 
				genreurl = self.mh_baseUrl + genreurl
			print 'GenreURL:',genreurl
			self.session.open(DMDE_FilmListeScreen, genreurl, self.mh_genreTitle)

	def paraQuery(self):
		self.param_qr = ''
		self.session.openWithCallback(self.cb_paraQuery, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_qr, is_dialog=True)

	def cb_paraQuery(self, callback = None, entry = None):
		if callback != None:
			self.param_qr = callback.strip()
			if len(self.param_qr) > 0:
				qr = self.param_qr.replace(' ','+')
				genreurl = self.mh_baseUrl + self.mh_genreUrl[0] % qr
				self.session.open(DMDE_FilmListeScreen, genreurl, self.mh_genreTitle)

class DMDE_FilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/dokuListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions", "EPGSelectActions","DirectionActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"upUp" : self.key_repeatedUp,
			"rightUp" : self.key_repeatedUp,
			"leftUp" : self.key_repeatedUp,
			"downUp" : self.key_repeatedUp,
			"upRepeated" : self.keyUpRepeated,
			"downRepeated" : self.keyDownRepeated,
			"rightRepeated" : self.keyRightRepeated,
			"leftRepeated" : self.keyLeftRepeated,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"1" : self.key_1,
			"3" : self.key_3,
			"4" : self.key_4,
			"6" : self.key_6,
			"7" : self.key_7,
			"9" : self.key_9,
			"0"	: self.closeAll,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self.sortOrder = 0
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label(DMDE_Version)

		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))
		self['Page'] = Label(_("Page:"))

		self.filmQ = Queue.Queue(0)
		self.hanQ = Queue.Queue(0)
		self.picQ = Queue.Queue(0)
		self.updateP = 0
		self.eventL = threading.Event()
		self.eventP = threading.Event()
		self.keyLocked = True
		self.dokusListe = []
		self.page = 0
		self.pages = 0;

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)
		if '/?' in self.genreLink:
			self.genreLink = self.genreLink.replace('/?', '/page/%d/?', 1)
		else:
			self.genreLink += "/page/%d/"

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		url = self.genreLink % max(self.page,1)
		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.pages))

		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()

	def loadPageQueued(self):
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		twAgentGetPage(url, cookieJar=cookies, agent=None, headers=std_headers).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		printl(error,self,"E")
		if not 'TimeoutError' in str(error):
			message = self.session.open(MessageBoxExt, _("No dokus / streams found!"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			message = self.session.open(MessageBoxExt, str(error), MessageBoxExt.TYPE_INFO)

	def loadPageData(self, data):
		self.dokusListe = []
		dokus = re.findall('<div class="featured-thumb col-md-12">.*?href="(.*?)"\stitle="(.*?)".*?<img.*?src="(.*?)".*?class="entry-excerpt">(.*?)</span>', data, re.S)
		if dokus:
			if not self.pages:
				m = re.search('<div class="pagination"><div><ul><li><span>1 of (\d+)<', data)
				try:
					pages = int(m.group(1))
				except:
					pages = 1
				if pages > self.pages:
					self.pages = pages
			if not self.page:
				self.page = 1
			self['page'].setText("%d / %d" % (self.page,self.pages))
			for	(url,name,img,desc) in dokus:
				self.dokusListe.append((decodeHtml(name), url, img, decodeHtml(desc.strip())))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self.th_ThumbsQuery(self.dokusListe, 0, 1, 2, None, None, self.page, self.pages, mode=1)
			self.loadPicQueued()
		else:
			self.dokusListe.append((_("No dokus found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()

	def loadPic(self):
		if self.picQ.empty():
			self.eventP.clear()
			return
		if self.updateP:
			return
		while not self.picQ.empty():
			self.picQ.get_nowait()
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		self.updateP = 1
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def getHandlung(self, desc):
		if desc == None:
			self['handlung'].setText(_("No further information available!"))
			return
		self.setHandlung(desc)

	def setHandlung(self, data):
		self['handlung'].setText(data)

	def ShowCoverFileExit(self):
		self.updateP = 0;
		self.keyLocked	= False
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
			self.loadPic()

	def loadPicQueued(self):
		self.picQ.put(None)
		if not self.eventP.is_set():
			self.eventP.set()
		desc = self['liste'].getCurrent()[0][3]
		self.getHandlung(desc)
		self.loadPic()

	def parseStream(self, data):
		m = re.search('<div class="entry-content">(.*?)</div>', data, re.S)
		if m:
			m2 = re.search('<a href="(.*?")', m.group(1))
			if not m2:
				m2 = re.search('src="(.*?")', m.group(1))
			if m2:
				url = m2.group(1)
				if 'vice.com' in url:
					if YoutubeDL == None:
						return self.playStream(None, emsg=_('"vice.com" is not supported.'))
					else:
						return self.viceLink(self.playStream, url[:-1])
				elif 'youtube.com' in url:
					return self.parseYTStream(url)
				elif 'dailymotion.com' in url:
					m = re.search('//www.dailymotion.com/embed/video/(.*?)("|\?)', url)
					if m:
						id = m.group(1)
						return DailyMotionLink(self.playStream, id)
				else:
					return self.playStream(url[:-1])
		self.playStream(None)

	def viceLink(self, callback, url):
		video_url = None
		m = re.search('share_url=(.+)("|&)*', url)
		if m:
			url = m.group(1)
			#print 'url:',url
			try:
				ytdl = YoutubeDL()
				result = ytdl.extract_info(url, download=False)
				#print 'result:',result
				video_url = str(result["url"])
			except Exception, e:
				printl(str(e),self,"E")
		callback(video_url)

	def parseYTStream(self, data):
		m2 = re.search('//www.youtube.com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		if m2:
			dhVideoId = m2.group(2)
			dhTitle = self['liste'].getCurrent()[0][0]
			self.session.open(
				YoutubePlayer,
				[(dhTitle, dhVideoId, None)],
				showPlaylist=False
				)
		else:
			self.playStream(None)

	def playStream(self, stream_url, emsg=_("No stream found.")):
		if stream_url:
			title = self['liste'].getCurrent()[0][0]
			img = self['liste'].getCurrent()[0][2]
			self.session.open(SimplePlayer, [(title, stream_url, img)], cover=True, showPlaylist=False, ltype='dokumania')
		else:
			self.session.open(MessageBoxExt, emsg, MessageBoxExt.TYPE_INFO, timeout=3)

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		streamLink = self['liste'].getCurrent()[0][1]
		twAgentGetPage(streamLink, cookieJar=cookies, agent=None, headers=std_headers).addCallback(self.parseStream).addErrback(self.dataError)

	def keyUpRepeated(self):
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		if self.keyLocked:
			return
		self.loadPicQueued()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyPageDown(self):
		self.keyPageDownFast(1)

	def keyPageUp(self):
		self.keyPageUpFast(1)

	def keyPageUpFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page + step) <= self.pages:
			self.page += step
		else:
			self.page = 1
		if oldpage != self.page:
			self.loadPage()

	def keyPageDownFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page - step) >= 1:
			self.page -= step
		else:
			self.page = self.pages
		if oldpage != self.page:
			self.loadPage()

	def key_1(self):
		self.keyPageDownFast(2)

	def key_4(self):
		self.keyPageDownFast(5)

	def key_7(self):
		self.keyPageDownFast(10)

	def key_3(self):
		self.keyPageUpFast(2)

	def key_6(self):
		self.keyPageUpFast(5)

	def key_9(self):
		self.keyPageUpFast(10)

class DailyMotionLink(object):
	def __init__(self, callback, id):
		self._callback = callback
		self.videoQuality = int(config.mediaportal.videoquali_others.value)
		self.getStreamPage(id)

	def getStreamPage(self, id):
		url = "https://www.dailymotion.com/video/"+id
		twAgentGetPage(url, agent="Mozilla/5.0 (Windows NT 6.1; rv:44.0) Gecko/20100101 Firefox/44.0").addCallback(self.getStreamUrl).addErrback(self.dataError)

	def dataError(self, error):
		printl("dataError:"+str(error),self,'E')
		self._callback(None)

	def getStreamUrl(self, content):
		from os import path as os_path
		patterns = [r'buildPlayer\(({.+?})\);\n',
            r'playerV5\s*=\s*dmp\.create\([^,]+?,\s*({.+?})\);',
            r'buildPlayer\(({.+?})\);']

		for p in patterns:
			mobj = re.search(p, content, 0)
			if mobj:
				break

		if mobj:
			player_v5 = next(g for g in mobj.groups() if g is not None)
			try:
				player = json.loads(player_v5)
			except Exception, e:
				print 'Exception:',e
				return self._callback(None)

		metadata = player['metadata']
		if metadata.get('error') is not None:
			return self._callback(None)

		formats = []
		video_url = None
		for quality, media_list in metadata['qualities'].items():
			for media in media_list:
				media_url = media.get('url')
				if not media_url:
					continue
				type_ = media.get('type')
				if type_ == 'application/vnd.lumberjack.manifest':
					continue

				sname, ext = os_path.splitext(media_url)
				if type_ == 'application/x-mpegURL' or ext == 'm3u8':
					print 'media_url:',media_url
					video_url = str(media_url)
				elif type_ == 'application/f4m' or ext == 'f4m':
					print 'f4m-media_url:',media_url
				else:
					f = {
						'url': media_url,
						'format_id': 'http-%s' % quality,
					}
					
					m = re.search(r'H264-(?P<width>\d+)x(?P<height>\d+)', media_url)
					if m:
						f.update({
							'width': int(m.group('width')),
							'height': int(m.group('height')),
						})
					formats.append(f)
		def getKey(item):
			return item['width']

		if formats:
			sorted(formats, key=getKey)
			while (self.videoQuality+1) > len(formats):
				self.videoQuality -= 1
			video_url = str(formats[self.videoQuality]['url'])
		self._callback(video_url)
