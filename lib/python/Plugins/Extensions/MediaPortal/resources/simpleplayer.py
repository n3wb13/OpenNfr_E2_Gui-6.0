# -*- coding: utf-8 -*-

from Plugins.Extensions.MediaPortal.plugin import _
from debuglog import printlog as printl
from enigma import ePoint
from Components.Pixmap import MultiPixmap
import mp_globals

try:
	import mechanize
except:
	mechanizeModule = False
else:
	mechanizeModule = True

import uuid
import Queue
import random
from messageboxext import MessageBoxExt
from choiceboxext import ChoiceBoxExt
from configlistext import ConfigListScreenExt
from Components.ProgressBar import ProgressBar
from Screens.InfoBarGenerics import *
from imports import *
from youtubelink import YoutubeLink
from ampyalink import AmpyaLink
if mechanizeModule:
	from cannalink import CannaLink
from eightieslink import EightiesLink
from mtvdelink import MTVdeLink
from coverhelper import CoverHelper
from Components.Pixmap import MovingPixmap
from simpleevent import SimpleEvent
from enigma import iPlayableService

is_avSetupScreen = False
try:
	from Plugins.SystemPlugins.Videomode.plugin import VideoSetup
	from Plugins.SystemPlugins.Videomode.VideoHardware import video_hw
except:
	VideoSetupPresent = False
else:
	VideoSetupPresent = True

if not VideoSetupPresent:
	try:
		from Plugins.SystemPlugins.Videomode.plugin import avSetupScreen
	except:
		VideoSetupPresent = False
	else:
		VideoSetupPresent = True
		is_avSetupScreen = True

try:
	from Plugins.Extensions.MediaInfo.plugin import MediaInfo
	MediaInfoPresent = True
except:
	try:
		from Plugins.Extensions.mediainfo.plugin import mediaInfo
		MediaInfoPresent = True
	except:
		MediaInfoPresent = False

try:
	from Plugins.Extensions.TMDb.plugin import *
	TMDbPresent = True
except:
	TMDbPresent = False

try:
	from Plugins.Extensions.IMDb.plugin import *
	IMDbPresent = True
except:
	IMDbPresent = False

seekbuttonpos = None
STREAM_BUFFERING_ENABLED = False

def clearTmpBuffer():
	from enigma import eBackgroundFileEraser
	BgFileEraser = eBackgroundFileEraser.getInstance()
	path = config.mediaportal.storagepath.value
	for fn in next(os.walk(path))[2]:
		BgFileEraser.erase(os.path.join(path,fn))

class M3U8Player:

	def __init__(self):
		from hlsplayer import start_hls_proxy
		self._bitrate = 0
		self._check_cache = True
		start_hls_proxy()
		self.onClose.append(self._m3u8Exit)

	def _setM3U8BufferSize(self):
		if config.mediaportal.use_hls_proxy.value:
			service = self.session.nav.getCurrentService()
			try:
				service.streamed().setBufferSize(long(config.mediaportal.hls_buffersize.value) * 1024 ** 2)
			except:
				pass

	def _getM3U8Video(self, title, url, **kwargs):
		from utopialink import UtopiaLink
		from atvlink import ATVLink

		if self._check_cache:
			if not os.path.isdir(config.mediaportal.storagepath.value):
				self.session.open(MessageBoxExt, _("You've to check Your HLS-PLayer Cachepath-Setting in MP-Setup:\n") + config.mediaportal.storagepath.value, MessageBoxExt.TYPE_ERROR)
				self.close()
				return
			else:
				self._check_cache = False
		us = url.split('-stream-')
		if len(us) > 1 and us[0] in ('atv', 'aspor', 'ahaber', 'atvavrupa', 'minikacocuk', 'minikago'):
			ATVLink().getATVStream(us[0]).addCallback(lambda url: self._playM3U8(title, url, **kwargs)).addErrback(self.dataError)
		elif url.startswith('utopia-stream-nl'):
			UtopiaLink().getNTStream('nl').addCallback(lambda url: self._playM3U8(title, url, **kwargs)).addErrback(self.dataError)
		else:
			self._playM3U8(title, url, **kwargs)

	def _playM3U8(self, title, url, **kwargs):
		def getProxyConfig(url):
			is_proxy_set = config.mediaportal.sp_use_hlsp_with_proxy.value == 'plset' and (url.rfind(' PROXY') > 0)
			useProxy = ((config.mediaportal.sp_use_hlsp_with_proxy.value == 'always') or is_proxy_set) and (config.mediaportal.hlsp_proxy_host.value != 'example_proxy.com!')
			if useProxy:
				if is_proxy_set:
					url = url.replace(' PROXY', '')
				proxyhost = config.mediaportal.hlsp_proxy_host.value
				proxyport = config.mediaportal.hlsp_proxy_port.value
				puser = config.mediaportal.hlsp_proxy_username.value
				ppass = config.mediaportal.hlsp_proxy_password.value

				if '/noconnect' in proxyhost:
					proxyhost, option = proxyhost.split('/')[-2:]
				else:
					option = ''

				if not proxyhost.startswith('http'):
					proxyhost = 'http://' + proxyhost

				proxycfg = '&puser=%s&ppass=%s&purl=%s:%s/%s' % (puser, ppass, proxyhost, proxyport, option)
			else:
				proxycfg = ''
			return url, proxycfg

		if '.m3u8' in url:
			self._bitrate = self._getBandwidth()
			path = config.mediaportal.storagepath.value
			ip = ".".join(str(x) for x in config.mediaportal.hls_proxy_ip.value)
			url, proxycfg = getProxyConfig(url)
			uid = uuid.uuid1()
			if ' headers=' in url:
				url, headers = url.rsplit(' headers=',1)
				headers = '&headers=%s' % headers
			else: headers = ""

			url = 'http://%s:%d/?url=%s&bitrate=%d&path=%s%s%s&uid=%s' % (ip, mp_globals.hls_proxy_port, urllib.quote(url), self._bitrate, path, headers, proxycfg, uid)
		self._initStream(title, url, **kwargs)

	def _getBandwidth(self):
		videoPrio = int(config.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			bw = 4000000
		elif videoPrio == 1:
			bw = 1000000
		else:
			bw = 250000

		return bw

	def _m3u8Exit(self):
		import mp_globals
		mp_globals.yt_tmp_storage_dirty = True

class CoverSearchHelper:

	def __init__(self, coverSupp):
		self.searchCoverSupp = coverSupp
		self.hasGoogleCoverArt = False

	def cleanTitle(self, title, replace_ext=True):
		for ext in ('.flv','.mp3','.mp4', '.mpeg', '.mpg', '.mkv', '.avi', '.wmv', '.ts'):
			if title.endswith(ext):
				if replace_ext:
					title = title.replace(ext, ' movie cover')
				else:
					title = title.replace(ext, '')
				break

		title = re.sub(' - folge \d+|^hd_|dts_|ac3_|_premium|kinofassung|_full_|hd_plus|\(.*?\)', '', title, flags=re.I)
		return title.replace("_"," ")

	def searchCover(self, title):
		if not self.searchCoverSupp or not title: return
		self.hideSPCover()
		if self.playerMode in ('MP3','VIDEO'):
			media = 'music' if self.pl_status[2] or title.endswith('.mp3') else 'movie'
			title = self.cleanTitle(title, False)
			url = "https://itunes.apple.com/search?term=%s&limit=1&media=%s" % (urllib.quote_plus(title), media)
			getPage(url, timeout=10).addCallback(self.cb_searchCover).addErrback(self.searchDataError)
		else:
			self.cb_searchCover(None)

	def cb_searchCover(self, jdata):
		import json
		try:
			jdata = json.loads(jdata)
			url = jdata['results'][0]['artworkUrl100'].encode('utf-8')
			url = url.replace('100x100', '300x300')
			self.hasGoogleCoverArt = True
		except:
			url = ""

		if not self.hasEmbeddedCoverArt:
			self.showCover(url, self.cb_coverDownloaded)
		else:
			self._evEmbeddedCoverArt()

	def cb_coverDownloaded(self, download_path):
		playIdx, title, artist, album, imgurl, plType = self.pl_status
		self.pl_status = (playIdx, title, artist, album, 'file://'+download_path, plType)
		if self.pl_open:
			self.playlistQ.put(self.pl_status)
			self.pl_event.genEvent()

	def searchDataError(self, result):
		url = ""
		playIdx, title, artist, album, imgurl, plType = self.pl_status
		self.pl_status = (playIdx, title, artist, album, url, plType)
		self.pl_entry[6] = url
		printl("[SP]: cover download failed: %s " % result,self,"E")
		self.cb_searchCover(None)

class SimpleSeekHelper:

	def __init__(self):
		self["seekbarcursor"] = MovingPixmap()
		self["seekbarcursor"].hide()
		self["seekbartime"] = Label()
		self["seekbartime"].hide()
		self.cursorTimer = eTimer()
		if mp_globals.isDreamOS:
			self.cursorTimer_conn = self.cursorTimer.timeout.connect(self.__updateCursor)
		else:
			self.cursorTimer.callback.append(self.__updateCursor)
		self.cursorShown = False
		self.seekBarShown = False
		self.seekBarLocked = False
		self.isNumberSeek = False
		self.counter = 0
		self.onHide.append(self.__seekBarHide)
		self.onShow.append(self.__seekBarShown)
		self.resetMySpass()
		self.skinYPos = 0

	def initSeek(self):
		global seekbuttonpos
		if not seekbuttonpos:
			seekbuttonpos = self["seekbarcursor"].instance.position()
		self.percent = 0.0
		self.length = None
		self.cursorShown = False
		self.counter = 1
		service = self.session.nav.getCurrentService()
		if service:
			self.seek = service.seek()
			if self.seek:
				self.length = self.seek.getLength()
				position = self.seek.getPlayPosition()
				if self.length[1] and position[1]:
					if self.myspass_len:
						self.length[1] = self.myspass_len
						position[1] += self.myspass_ofs
					else:
						self.myspass_len = self.length[1]
						self.mySpassPath = self.session.nav.getCurrentlyPlayingServiceReference().getPath()
						if '/myspass' in self.mySpassPath:
							self.isMySpass = True
						elif 'file=retro-tv' in self.mySpassPath:
							#self.isRetroTv = True
							#self.isMySpass = True
							pass
						elif 'eroprofile.com' in self.mySpassPath:
							self.isEroprofile = True
							self.isMySpass = True
						elif 'media.amateurporn.net' in self.mySpassPath:
							self.isMySpass = True
						elif 'media.hdporn.net' in self.mySpassPath:
							self.isMySpass = True

					self.percent = float(position[1]) * 100.0 / float(self.length[1])
					if not self.isNumberSeek:
						InfoBarShowHide.lockShow(self)
						self.seekBarLocked = True
						self["seekbartime"].show()
						self.cursorTimer.start(200, False)

	def __seekBarShown(self):
		self.seekBarShown = True

	def __seekBarHide(self):
		self.seekBarShown = False

	def toggleShow(self):
		if self.seekBarLocked:
			self.seekOK()
		else:
			InfoBarShowHide.toggleShow(self)

	def showInfoBar(self):
		if not self.seekBarShown:
			InfoBarShowHide.toggleShow(self)

	def __updateCursor(self):
		if self.length:
			if mp_globals.videomode >= 2:
				factor = 10.85
			else:
				factor = 6.86
			x = seekbuttonpos.x() + int(factor * self.percent)
			self["seekbarcursor"].moveTo(x, seekbuttonpos.y(), 1)
			self["seekbarcursor"].startMoving()
			pts = int(float(self.length[1]) / 100.0 * self.percent)
			self["seekbartime"].setText("%d:%02d" % ((pts/60/90000), ((pts/90000)%60)))
			if not self.cursorShown:
				if not self.counter:
					self.cursorShown = True
					self["seekbarcursor"].show()
				else:
					self.counter -= 1

	def seekExit(self):
		if not self.isNumberSeek:
			self.seekBarLocked = False
			self.cursorTimer.stop()
			self.unlockShow()
			self["seekbarcursor"].hide()
			self["seekbarcursor"].moveTo(seekbuttonpos.x(), seekbuttonpos.y(), 1)
			self["seekbarcursor"].startMoving()
			self["seekbartime"].hide()
		else:
			self.isNumberSeek = False

	def seekOK(self):
		if self.length:
			seekpos = float(self.length[1]) / 100.0 * self.percent
			#if self.ltype == 'myspass':
			if self.isMySpass:
				self.myspass_ofs = seekpos
				self.doMySpassSeekTo(seekpos)
			else:
				self.seek.seekTo(int(seekpos))
				self.seekExit()
		else:
			self.seekExit()

	def seekLeft(self):
		self.percent -= float(config.mediaportal.sp_seekbar_sensibility.value) / 10.0
		if self.percent < 0.0:
			self.percent = 0.0

	def seekRight(self):
		self.percent += float(config.mediaportal.sp_seekbar_sensibility.value) / 10.0
		if self.percent > 100.0:
			self.percent = 100.0

	def numberKeySeek(self, val):
		length = float(self.length[1])
		if length > 0.0:
			pts = int(length / 100.0 * self.percent) + val * 90000
			self.percent = pts * 100 / length
			if self.percent < 0.0:
				self.percent = 0.0
			elif self.percent > 100.0:
				self.percent = 100.0

			self.seekOK()
			if config.usage.show_infobar_on_skip.value:
				self.doShow()
		else:
			return

	def doMySpassSeekTo(self, seekpos):
		service = self.session.nav.getCurrentService()
		title = service.info().getName()
		path = self.mySpassPath
		seeksecs = seekpos / 90000
		if self.isRetroTv:
			url = "%s&start=%ld" % (path.split('&')[0], int(seeksecs*145000))
		elif self.isEroprofile:
			url = "%s&start=%f" % (path.split('&start')[0], seeksecs)
		else:
			url = "%s?start=%f" % (path.split('?start')[0], seeksecs)
		sref = eServiceReference(0x1001, 0, url)
		sref.setName(title)
		self.seekExit()
		self.session.nav.stopService()
		self.session.nav.playService(sref)

	def restartMySpass(self):
		self.resetMySpass()
		self.doMySpassSeekTo(0L)

	def resetMySpass(self):
		self.myspass_ofs = 0L
		self.myspass_len = 0L
		self.mySpassPath = None
		self.isMySpass = False
		self.isEroprofile = False
		self.isRetroTv = False
		self.isNumberSeek = False

	def cancelSeek(self):
		if self.seekBarLocked:
			self.seekExit()

	def Key1(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(-int(config.seek.selfdefined_13.value))

	def Key3(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(int(config.seek.selfdefined_13.value))

	def Key4(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(-int(config.seek.selfdefined_46.value))

	def Key6(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(int(config.seek.selfdefined_46.value))

	def Key7(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(-int(config.seek.selfdefined_79.value))

	def Key9(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(int(config.seek.selfdefined_79.value))

	def moveSkinUp(self):
		if self.seekBarShown and not self.seekBarLocked:
			self.initSeek()
		if self.seekBarLocked:
			if self.skinYPos >= -450:
				self.skinYPos -= 50
				self.instance.move(ePoint(0, self.skinYPos))

	def moveSkinDown(self):
		if self.seekBarShown and not self.seekBarLocked:
			self.initSeek()
		if self.seekBarLocked:
			if self.skinYPos <= 450:
				self.skinYPos += 50
				self.instance.move(ePoint(0, self.skinYPos))

class SimplePlayerResume:

	def __init__(self):
		self.posTrackerActive = False
		self.currService = None
		self.eof_resume = False
		self.use_sp_resume = config.mediaportal.sp_on_movie_start.value != "start"
		self.posTrackerTimer = eTimer()
		if mp_globals.isDreamOS:
			self.posTrackerTimer_conn = self.posTrackerTimer.timeout.connect(self.savePlayPosition)
		else:
			self.posTrackerTimer.callback.append(self.savePlayPosition)
		self.eofResumeTimer = eTimer()
		if mp_globals.isDreamOS:
			self.eofResumeTimer_conn = self.eofResumeTimer.timeout.connect(self.resetEOFResumeFlag)
		else:
			self.eofResumeTimer.callback.append(self.resetEOFResumeFlag)
		self.eofResumeFlag = False
		self.lruKey = ""

		self.onClose.append(self.stopPlayPositionTracker)

	def initPlayPositionTracker(self, lru_key):
		if self.use_sp_resume and lru_key and not self.posTrackerActive and not self.playerMode in ('MP3',):
			self.currService = None
			self.eofResumeFlag = False
			self.posTrackerActive = True
			self.lruKey = lru_key
			self.posTrackerTimer.start(1000*3, True)

	def stopPlayPositionTracker(self):
		if self.posTrackerActive:
			self.posTrackerTimer.stop()
			self.posTrackerActive = False
		self.eofResumeTimer.stop()

	def savePlayPosition(self, is_eof=False):
		if self.posTrackerActive:
			if is_eof and not self.lruKey in mp_globals.lruCache:
				return

			if not self.currService:
				service = self.session.nav.getCurrentService()
				if service:
					seek = service.seek()
					if seek:
						length = seek.getLength()
						position = seek.getPlayPosition()
						if length[1] > 0 and position[1] > 0:
							if self.lruKey in mp_globals.lruCache:
								lru_value = mp_globals.lruCache[self.lruKey]
								if length[1]+5*90000 > lru_value[0]:
									self.resumePlayback(lru_value[0], lru_value[1])
							self.currService = service
						else:
							return self.posTrackerTimer.start(1000*3, True)
				self.posTrackerTimer.start(1000*15, True)
			else:
				seek = self.currService.seek()
				if seek:
					length = seek.getLength()[1]
					position = seek.getPlayPosition()[1]
					mp_globals.lruCache[self.lruKey] = (length, position)

	def resumePlayback(self, length, last):
		self.resume_point = last
		if (length > 0) and abs(length - last) < 5*90000:
			return
		l = last / 90000
		if self.eof_resume or (config.mediaportal.sp_on_movie_start.value == "resume" and not mp_globals.yt_download_runs):
			self.eof_resume = False
			self.session.openWithCallback(self.playLastCB, MessageBoxExt, _("Resuming playback"), timeout=2, type=MessageBoxExt.TYPE_INFO)
		elif config.mediaportal.sp_on_movie_start.value == "ask" and not mp_globals.yt_download_runs:
			self.session.openWithCallback(self.playLastCB, MessageBoxExt, _("Do you want to resume this playback?") + "\n" + (_("Resume position at %s") % ("%d:%02d:%02d" % (l/3600, l%3600/60, l%60))), timeout=10)

	def resetEOFResumeFlag(self):
		self.eofResumeFlag = False

	def resumeEOF(self):
		if self.use_sp_resume and self.posTrackerActive and self.lruKey in mp_globals.lruCache and self.ltype not in ('rtlnow','nowtv'):
			self.savePlayPosition(is_eof=True)
			lru_value = mp_globals.lruCache[self.lruKey]
			if (lru_value[1]+90000*120) < lru_value[0]:
				if self.eofResumeFlag:
					return True
				self.eofResumeFlag = True
				self.eofResumeTimer.start(1000*15, True)
				self.doSeek(0)
				self.setSeekState(self.SEEK_STATE_PLAY)
				self.eof_resume = True
				self.resumePlayback(lru_value[0], lru_value[1])
				return True
			else:
				self.stopPlayPositionTracker()
				mp_globals.lruCache.cache.pop()

		return False

	def playLastCB(self, answer):
		if answer == True:
			self.doSeek(self.resume_point)
		elif self.lruKey in mp_globals.lruCache:
			del mp_globals.lruCache[self.lruKey]

		self.hideAfterResume()

	def hideAfterResume(self):
		if isinstance(self, InfoBarShowHide):
			self.hide()

class SimplePlaylist(MPScreen):

	def __init__(self, session, playList, playIdx, playMode, listTitle=None, plType='local', title_inr=0, queue=None, mp_event=None, listEntryPar=None, playFunc=None, playerMode=None):

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

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config.mediaportal.minitv.value)

		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions",'MediaPlayerSeekActions',"EPGSelectActions",'ColorActions','InfobarActions'],
		{
			'cancel':	self.exit,
			'red':		self.exit,
			'green':	self.toPlayer,
			'yellow':	self.changePlaymode,
			'blue':		self.deleteEntry,
			'ok': 		self.ok
		}, -2)

		self.playList = playList
		self.playIdx = playIdx
		self.listTitle = listTitle
		self.plType = plType
		self.title_inr = title_inr
		self.playlistQ = queue
		self.event = mp_event
		self.listEntryPar = listEntryPar
		self.playMode = playMode
		self.playFunc = playFunc
		self.playerMode = playerMode

		self["title"] = Label("")
		self["coverArt"] = Pixmap()
		self._Cover = CoverHelper(self['coverArt'])
		self["songtitle"] = Label ("")
		self["artist"] = Label ("")
		self["album"] = Label ("")
		if self.plType == 'global':
			self['F4'] = Label(_("Delete"))
		else:
			self['F4'] = Label("")
		if playerMode in ('MP3',):
			self['F2'] = Label(_("to Player"))
		else:
			self['F2'] = Label("")
		self['F3'] = Label(_("Playmode"))
		self['F1'] = Label(_("Exit"))
		self['playmode'] = Label(self.playMode[0].capitalize())

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onClose.append(self.resetEvent)

		self.onLayoutFinish.append(self.showPlaylist)

	def updateStatus(self):
		if self.playlistQ and not self.playlistQ.empty():
			t = self.playlistQ.get_nowait()
			self["songtitle"].setText(t[1])
			self["artist"].setText(t[2])
			self["album"].setText(t[3])
			self.getCover(t[4])
			if t[5] == self.plType:
				self.playIdx = t[0]
				if self.playIdx >= len(self.playList):
					self.playIdx = 0
				self['liste'].moveToIndex(self.playIdx)

	def playListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		if self.plType != 'global' and self.listEntryPar:
			self.ml.l.setItemHeight(self.listEntryPar[3])
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM + self.listEntryPar[0], self.listEntryPar[1], self.listEntryPar[2] - 2 * self.DEFAULT_LM, self.listEntryPar[3], self.listEntryPar[4], RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[self.listEntryPar[6]]+self.listEntryPar[5]+entry[self.listEntryPar[7]]))
			return res
		else:
			if self.title_inr == 1 and entry[0]:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]+entry[1]))
				return res
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[self.title_inr]))
				return res

	def showPlaylist(self):
		if self.listTitle:
			self['title'].setText(self.listTitle)
		else:
			self['title'].setText("%s Playlist-%02d" % (self.plType, config.mediaportal.sp_pl_number.value))

		from sepg.mp_epg import mpepg
		if self.playerMode == 'IPTV' and not mpepg.isImporting:
			self.ml.setList(map(self.simpleListTVGListEntry, self.playList))
		else:
			self.ml.setList(map(self.playListEntry, self.playList))

		if self.event:
			self.event.addCallback(self.updateStatus)
		else:
			self['liste'].moveToIndex(self.playIdx)

	def getCover(self, url):
		if url != '--download--':
			self._Cover.getCover(url)

	def deleteEntry(self):
		if self.plType == 'global':
			idx = self['liste'].getSelectedIndex()
			self.close([idx,'del',self.playList])

	def toPlayer(self):
		if self.playerMode in ('MP3',):
			self.close([-2,'',self.playList])

	def exit(self):
		self.close([-1,'',self.playList])

	def ok(self):
		if len(self.playList) == 0:
			self.exit()
		idx = self['liste'].getSelectedIndex()
		if self.playFunc:
			self.playFunc(idx)
		else:
			self.close([idx,'',self.playList])

	def resetEvent(self):
		if self.event:
			self.event.reset()

	def createSummary(self):
		return SimplePlayerSummary

	def changePlaymode(self):
		if self.playMode[0] == "forward":
			self.playMode[0] = "backward"
		elif self.playMode[0] == "backward":
			self.playMode[0] = "random"
		elif self.playMode[0] == "random":
			self.playMode[0] = "endless"
		else:
			self.playMode[0] = "forward"

		self["playmode"].setText(self.playMode[0].capitalize())

class SimplePlayerPVRState(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/simpleplayer/SimplePlayerPVRState.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/simpleplayer/SimplePlayerPVRState.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["state"] = Label(text="")
		self["eventname"] = Label()
		self["speed"] = Label()
		self["statusicon"] = MultiPixmap()

class SimplePlayer(Screen, M3U8Player, CoverSearchHelper, SimpleSeekHelper, SimplePlayerResume, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState, InfoBarShowHide, InfoBarAudioSelection, InfoBarSubtitleSupport, InfoBarSimpleEventView):

	ALLOW_SUSPEND = True
	ctr = 0

	def __init__(self, session, playList, playIdx=0, playAll=False, listTitle=None, plType='local', title_inr=0, cover=False, ltype='', autoScrSaver=False, showPlaylist=True, listEntryPar=None, playList2=[], playerMode='VIDEO', useResume=True, bufferingOpt='None', googleCoverSupp=False, embeddedCoverArt=False):

		if (self.__class__.ctr + 1) > 1:
			printl('[SP]: only 1 instance allowed',self,"E")
		else:
			self.__class__.ctr += 1

		try:
			from enigma import eServiceMP3
		except:
			is_eServiceMP3 = False
		else:
			is_eServiceMP3 = True

		Screen.__init__(self, session)
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		self.wallicon_path = mp_globals.pluginPath + "/icons/"
		path = "%s/%s/simpleplayer/SimplePlayer.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/simpleplayer/SimplePlayer.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		if not mp_globals.isDreamOS:
			self.skin = re.sub(r'progress_pointer="(.*?):\d+,\d+" render="PositionGauge"', r'pixmap="\1" render="Progress"', self.skin)
			self.skin = re.sub(r'type="MPServicePosition">Gauge</convert>', r'type="MPServicePosition">Position</convert>', self.skin)

		self.setActionPrio()
		self["actions"] = ActionMap(["WizardActions",'MediaPlayerSeekActions','InfobarInstantRecord',"EPGSelectActions",'MoviePlayerActions','ColorActions','InfobarActions',"MenuActions","HelpActions"],
		{
			"leavePlayer": self.leavePlayer,
			config.mediaportal.sp_mi_key.value: self.openMediainfo,
			config.mediaportal.sp_imdb_key.value: self.openMovieinfo,
			"menu":		self.openMenu,
			"up": 		self.openPlaylist,
			"down":		self.randomNow,
			"back":		self.leavePlayer,
			"left":		self.seekBack,
			"right":	self.seekFwd,
			"seekdef:1": self.Key1,
			"seekdef:3": self.Key3,
			"seekdef:4": self.Key4,
			"seekdef:6": self.Key6,
			"seekdef:7": self.Key7,
			"seekdef:9": self.Key9,
			"prevBouquet": self.moveSkinUp,
			"nextBouquet": self.moveSkinDown

		}, self.action_prio)

		M3U8Player.__init__(self)
		CoverSearchHelper.__init__(self, googleCoverSupp)
		SimpleSeekHelper.__init__(self)
		SimplePlayerResume.__init__(self)
		InfoBarMenu.__init__(self)
		InfoBarNotifications.__init__(self)
		InfoBarServiceNotifications.__init__(self)
		InfoBarBase.__init__(self)
		InfoBarShowHide.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarSubtitleSupport.__init__(self)
		InfoBarSimpleEventView.__init__(self)

		self.allowPiP = False
		InfoBarSeek.__init__(self)
		InfoBarPVRState.__init__(self, screen=SimplePlayerPVRState, force_show=True)

		self.skinName = 'MediaPortal SimplePlayer'
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
		else:
			self.lastservice = None

		self.bufferingOpt = bufferingOpt
		self.use_sp_resume = useResume
		self.playerMode = playerMode
		self.keyPlayNextLocked = False
		self.isTSVideo = False
		self.showGlobalPlaylist = True
		self.showPlaylist = showPlaylist
		self.scrSaver = ''
		self.saverActive = False
		self.autoScrSaver = autoScrSaver
		self.pl_open = False
		self.playMode = [str(config.mediaportal.sp_playmode.value)]
		self.listTitle = listTitle
		self.playAll = playAll
		self.playList = playList
		self.playIdx = playIdx
		if plType == 'local':
			self.playLen = len(playList)
		else:
			self.playLen = len(playList2)

		self.listEntryPar=listEntryPar
		self.returning = False
		self.pl_entry = ['', '', '', '', '', '', '', '', '']
		self.plType = plType
		self.playList2 = playList2
		self.pl_name = 'mp_global_pl_%02d' % config.mediaportal.sp_pl_number.value
		self.title_inr = title_inr
		self.cover = cover
		self.ltype = ltype
		self.playlistQ = Queue.Queue(0)
		self.pl_status = (0, '', '', '', '', '')
		self.pl_event = SimpleEvent()
		self['spcoverframe'] = Pixmap()
		self['spcoverfg'] = Pixmap()
		self['Icon'] = Pixmap()
		self._Icon = CoverHelper(self['Icon'])
		self['premiumoff'] = Pixmap()
		self['premiumizemeon'] = Pixmap()
		self['premiumizemeon'].hide()
		self['realdebridon'] = Pixmap()
		self['realdebridon'].hide()
		self.progrObj = ProgressBar()
		self['dwnld_progressbar'] = self.progrObj
		# load default cover
		self['Cover'] = Pixmap()
		self['noCover'] = Pixmap()
		self._Cover = CoverHelper(self['Cover'], nc_callback=self.hideSPCover)
		self.coverBGisHidden = False
		self.cover2 = False
		self.searchTitle = None
		self.embeddedCoverArt = embeddedCoverArt
		self.hasEmbeddedCoverArt = False
		self.lru_key = None
		self.dwnld_lastnum = 0
		self.downloader = None
		self.last_progress = 0
		self.last_path = None

		self.SaverTimer = eTimer()
		if mp_globals.isDreamOS:
			self.SaverTimer_conn = self.SaverTimer.timeout.connect(self.openSaver)
		else:
			self.SaverTimer.callback.append(self.openSaver)

		self.EmbeddedCoverTimer = eTimer()
		if mp_globals.isDreamOS:
			self.EmbeddedCoverTimer_conn = self.EmbeddedCoverTimer.timeout.connect(self.checkEmbeddedCover)
		else:
			self.EmbeddedCoverTimer.callback.append(self.checkEmbeddedCover)

		self.hideSPCover()
		self.configSaver()
		self.onClose.append(self.playExit)

		self.setPlayerAgent()

		if mp_globals.isDreamOS:
			self.onFirstExecBegin.append(self._animation)
		self.onFirstExecBegin.append(self.showIcon)
		self.onFirstExecBegin.append(self.playVideo)

		if self.playerMode in ('MP3',):
			self.onFirstExecBegin.append(self.openPlaylist)

		if is_eServiceMP3:
			self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
				{
					eServiceMP3.evAudioDecodeError: self.__evAudioDecodeError,
					eServiceMP3.evVideoDecodeError: self.__evVideoDecodeError,
					eServiceMP3.evPluginError: self.__evPluginError,
					eServiceMP3.evStreamingSrcError: self.__evStreamingSrcError,
					eServiceMP3.evEmbeddedCoverArt: self._evEmbeddedCoverArt,
					iPlayableService.evStart: self.__serviceStarted
				})
		else:
			self.embeddedCoverArt = False
			self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
				{
					iPlayableService.evStart: self.__serviceStarted
				})

	def __evAudioDecodeError(self):
		if not config.mediaportal.sp_show_errors.value:
			return
		from enigma import iServiceInformation
		currPlay = self.session.nav.getCurrentService()
		sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
		self.session.open(MessageBoxExt, _("This STB can't decode %s streams!") % sTagAudioCodec, type = MessageBoxExt.TYPE_INFO,timeout = 10 )

	def __evVideoDecodeError(self):
		if not config.mediaportal.sp_show_errors.value:
			return
		from enigma import iServiceInformation
		currPlay = self.session.nav.getCurrentService()
		sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
		self.session.open(MessageBoxExt, _("This STB can't decode %s streams!") % sTagVideoCodec, type = MessageBoxExt.TYPE_INFO,timeout = 10 )

	def __evPluginError(self):
		if not config.mediaportal.sp_show_errors.value:
			return
		from enigma import iServiceInformation
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
		self.session.open(MessageBoxExt, message, type = MessageBoxExt.TYPE_INFO,timeout = 10 )

	def __evStreamingSrcError(self):
		if isinstance(self, SimplePlayerResume):
			self.eofResumeFlag = True
		if not config.mediaportal.sp_show_errors.value:
			return
		from enigma import iServiceInformation
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
		self.session.open(MessageBoxExt, _("Streaming error: %s") % message, type = MessageBoxExt.TYPE_INFO,timeout = 10 )

	def _evEmbeddedCoverArt(self):
		self.hasEmbeddedCoverArt = True
		if not self.cover and not self.cover2 and self.embeddedCoverArt:
			url = 'file:///tmp/.id3coverart'
			playIdx, title, artist, album, imgurl, plType = self.pl_status
			self.pl_status = (playIdx, title, artist, album, url, plType)
			if self.pl_open:
				self.playlistQ.put(self.pl_status)
				self.pl_event.genEvent()
			self.showCover(url)

	def checkEmbeddedCover(self):
		if not self.hasEmbeddedCoverArt:
			if self.searchCoverSupp:
				self.searchCover(self.searchTitle)
			else:
				self.showCover(None, self.cb_coverDownloaded)

	def __serviceStarted(self):
		self._setM3U8BufferSize()
		if self.embeddedCoverArt and not self.hasEmbeddedCoverArt:
			self.EmbeddedCoverTimer.start(1000*5, True)
		self.initPlayPositionTracker(self.lru_key)

	def playVideo(self):
		if self.seekBarLocked:
			self.cancelSeek()
		self.resetMySpass()
		if self.plType == 'global':
			self.getVideo2()
		else:
			self.cover2 = False
			self.getVideo()

	def playSelectedVideo(self, idx):
		self.playIdx = idx
		self.playVideo()

	def dataError(self, error):
		if self.playIdx != self.pl_status[0]:
			self.pl_status = (self.playIdx,) + self.pl_status[1:]
			if self.pl_open:
				self.playlistQ.put(self.pl_status)
				self.pl_event.genEvent()

		if config.mediaportal.sp_show_errors.value:
			self.session.openWithCallback(self.dataError2, MessageBoxExt, str(error), MessageBoxExt.TYPE_INFO, timeout=10)
		else:
			self.dataError2(error)

	def dataError2(self, res):
		self.keyPlayNextLocked = False
		reactor.callLater(2, self.playNextStream, config.mediaportal.sp_on_movie_eof.value)

	def playStream(self, title, url, **kwargs):
		if not url:
			self.dataError('[SP]: no URL given!')
		elif url.startswith('#SERVICE'):
			self._initStream(title, url, **kwargs)
		elif url.rfind('#oklitv-stream#') > 0:
			try:
				from oklitvlink import OkliTVLink
			except:
				print "SP OKLIVETV extension is missing"
			else:
				us = url.split('#oklitv-stream#')
				url = us[0]
				d = twAgentGetPage(url, timeout=10, agent="Mozilla/5.0 (Windows NT 6.1; rv:40.0) Gecko/20100101 Firefox/40.0").addCallback(OkliTVLink(self.session).getStream)
				if us[-1].endswith('#force-hlsp#'):
					d.addCallback(lambda url: self._getM3U8Video(title, url, **kwargs)).addErrback(self.dataError)
				else:
					d.addCallback(lambda url: self._initStream(title, url, **kwargs)).addErrback(self.dataError)
		elif url.endswith('#filmon-stream#'):
			try:
				from oklitvlink import FilmOnLink
			except:
				print "SP FILMON extension is missing"
			else:
				FilmOnLink(self.session).getStream(url.split('#filmon-stream#')[0]).addCallback(lambda url: self._initStream(title, url, **kwargs)).addErrback(self.dataError)
		elif config.mediaportal.use_hls_proxy.value and not self.ltype in ('myvideo2.de',) and '.m3u8' in url:
			self._getM3U8Video(title, url, **kwargs)
		else:
			self._initStream(title, url, **kwargs)

	def downloadStream(self, url, outputfile, callback, proxy=None, supportPartial=False, resume=False, *args, **kwargs):
		if STREAM_BUFFERING_ENABLED:
			if self.downloader != None:
				self.downloader.stop()

			def updateProgressbar(sz_current, sz_total):
				if sz_current > 0 and sz_total >= sz_current:
					progress = int(100 * round(sz_current / sz_total, 2))
					if progress > 100:
						progress = 100
					if progress != self.last_progress:
						self.progrObj.setValue(progress)
						self.last_progress = progress

			if not resume:
				if proxy == None: proxy = (None, None, None)
				from twagenthelper import TwDownloadWithProgress
				self.downloader = TwDownloadWithProgress(url, outputfile, timeout=(10,None), agent="Enigma Mediaplayer", proxy_url=proxy[0], p_user=proxy[1], p_pass=proxy[2], use_pipe=False, supportPartial=supportPartial)
				self.downloader.addProgress(updateProgressbar)

			d = self.downloader.start()
			d.addCallback(callback, *args, **kwargs)
			if not self._playing and self.last_path:
				try:
					os.remove(self.last_path)
				except:
					pass

			self.last_path = outputfile
			if not self.downloader.requestedPartial:
				self.downloader.addThreshold('10').addCallback(callback, *args, **kwargs).addErrback(self.dataError)

			return d
		else:
			callback(url, *args, **kwargs)

	def _initStream(self, title, url, album='', artist='', imgurl='', buffering=False, proxy=None, epg_id=None):
		self.hasGoogleCoverArt = self.hasEmbeddedCoverArt = False

		if not mp_globals.yt_download_runs:
			self['dwnld_progressbar'].setValue(0)

		if mp_globals.premiumize:
			self['premiumoff'].hide()
			self['realdebridon'].hide()
			self['premiumizemeon'].show()
			mp_globals.premiumize = False
		elif mp_globals.realdebrid:
			self['premiumoff'].hide()
			self['premiumizemeon'].hide()
			self['realdebridon'].show()
			mp_globals.realdebrid = False
		else:
			self['premiumizemeon'].hide()
			self['realdebridon'].hide()
			self['premiumoff'].show()

		if artist != '':
			video_title = artist + ' - ' + title
		else:
			video_title = title

		if self.cover:
			cflag = '1'
		else:
			cflag = '0'

		self.pl_entry = [title, None, artist, album, self.ltype, '', imgurl, cflag]
		if self.cover or self.cover2 or self.searchCoverSupp or self.embeddedCoverArt:
			imgurl = '--download--'
		self.pl_status = (self.playIdx, title, artist, album, imgurl, self.plType)
		if self.cover or self.cover2:
			self.showCover(self.pl_entry[6], self.cb_coverDownloaded)
		elif self.embeddedCoverArt:
			self.searchTitle = video_title
		else:
			self.searchCover(video_title)

		if len(video_title) > 0:
			self.lru_key = video_title
		else:
			self.lru_key = url

		self.stopPlayPositionTracker()

		if epg_id and not url.startswith('#SERVICE'):
			url = "#SERVICE 4097:0:0:%s:1955:0:0:0:0:0:%s:%s" % (epg_id, url.replace(':','%3a'), video_title)
		self._playing = False
		self.isTSVideo = False
		def playService(url):
			if url == 'cancelled': return
			if not self._playing:
				self._playing = True
				if url.startswith('#SERVICE'):
					url = url[8:].strip()
					sref = eServiceReference(url)
				else:
					if url.endswith('.ts'):
						sref = eServiceReference(0x0001, 0, unquote(url))
						self.isTSVideo = True
					else:
						if not '/?url=' in url:
							url = unquote(url)
						sref = eServiceReference(0x1001, 0, url)
					sref.setName(video_title)

				self.session.nav.playService(sref)
				if self.pl_open:
					self.playlistQ.put(self.pl_status)
					self.pl_event.genEvent()

				#self.initPlayPositionTracker(self.lru_key)

		self.keyPlayNextLocked = False
		if buffering:
			if not self._playing:
				clearTmpBuffer()
				self.dwnld_lastnum = (self.dwnld_lastnum + 1) % 2
				path = config.mediaportal.storagepath.value + 'downloaded_file_%d.mp4' % self.dwnld_lastnum
				self.downloadStream(url, path, playService, proxy)
		else:
			self.progrObj.setValue(0)
			if self.downloader != None:
				self.downloader.stop()
				clearTmpBuffer()
			playService(url)

	def playPrevStream(self, value):
		if self.keyPlayNextLocked:
			return

		if not self.playAll or self.playLen <= 1:
			self.handleLeave(value)
		else:
			if self.playIdx > 0:
				self.playIdx -= 1
			else:
				self.playIdx = self.playLen - 1

			self.keyPlayNextLocked = True
			if mp_globals.yt_dwnld_agent:
				mp_globals.yt_dwnld_agent.cancelDownload()

			self.playVideo()

	def playNextStream(self, value):
		if self.keyPlayNextLocked:
			return

		if not self.playAll or self.playLen <= 1:
			self.handleLeave(value)
		else:
			if self.playIdx in range(0, self.playLen-1):
				self.playIdx += 1
			else:
				self.playIdx = 0
			self.keyPlayNextLocked = True

			if mp_globals.yt_dwnld_agent:
				mp_globals.yt_dwnld_agent.cancelDownload()

			self.playVideo()

	def playRandom(self, value):
		if self.keyPlayNextLocked:
			return

		if self.playLen > 1 and self.playAll:
			self.playIdx = random.randint(0, self.playLen-1)
			self.keyPlayNextLocked = True

			if mp_globals.yt_dwnld_agent:
				mp_globals.yt_dwnld_agent.cancelDownload()

			self.playVideo()
		else:
			self.handleLeave(value)

	def playEndlessStream(self):
		if self.keyPlayNextLocked:
			return
		self.keyPlayNextLocked = True

		if mp_globals.yt_dwnld_agent:
			mp_globals.yt_dwnld_agent.cancelDownload()

		self.playVideo()

	def randomNow(self):
		if self.playAll:
			self.playRandom(config.mediaportal.sp_on_movie_stop.value)

	def seekFwd(self):
		if self.isTSVideo:
			InfoBarSeek.seekFwd(self)
		elif self.seekBarShown and not self.seekBarLocked:
			self.initSeek()
		elif self.seekBarLocked:
			self.seekRight()
		elif self.playAll:
			self.playNextStream(config.mediaportal.sp_on_movie_stop.value)

	def seekBack(self):
		if self.isTSVideo:
			InfoBarSeek.seekBack(self)
		elif self.seekBarShown and not self.seekBarLocked:
			self.initSeek()
		elif self.seekBarLocked:
			self.seekLeft()
		elif self.playAll:
			self.playPrevStream(config.mediaportal.sp_on_movie_stop.value)

	def handleLeave(self, how):
		if self.playerMode in ('MP3',):
			self.openPlaylist()
			return
		self.is_closing = True
		if how == "ask":
			if self.plType == 'local':
				if 'rtmpbuffering' == self.bufferingOpt:
					list = (
						(_("Yes"), "quit"),
						(_("Yes, but back to caching..."), "rtmpbuffering"),
						(_("No"), "continue"),
						(_("No, but start over from the beginning"), "restart")
					)
				else:
					list = (
						(_("Yes"), "quit"),
						(_("Yes & Add Service to global Playlist-%02d") % config.mediaportal.sp_pl_number.value, "add"),
						(_("No"), "continue"),
						(_("No, but start over from the beginning"), "restart")
					)
			else:
				list = (
					(_("Yes"), "quit"),
					(_("No"), "continue"),
					(_("No, but start over from the beginning"), "restart")
				)

			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBoxExt, title=_("Stop playing this movie?"), list = list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]

		self.savePlayPosition(is_eof=True)

		if answer in ("quit", "movielist"):
			self.close()
		elif answer == "restart":
			if self.isMySpass:
				self.restartMySpass()
			else:
				self.doSeek(0)
				self.setSeekState(self.SEEK_STATE_PLAY)
		elif answer == "add":
			self.addToPlaylist()
			self.close()
		elif answer == "rtmpbuffering":
			self.close('continue')

	def leavePlayer(self):
		if self.seekBarLocked:
			self.cancelSeek()
		else:
			self.handleLeave(config.mediaportal.sp_on_movie_stop.value)

	def doEofInternal(self, playing):
		if playing:
			if not self.resumeEOF():
				if self.playMode[0] == 'random':
					self.playRandom(config.mediaportal.sp_on_movie_eof.value)
				elif self.playMode[0] == 'forward':
					self.playNextStream(config.mediaportal.sp_on_movie_eof.value)
				elif self.playMode[0] == 'backward':
					self.playPrevStream(config.mediaportal.sp_on_movie_eof.value)
				elif self.playMode[0] == 'endless':
					#self.playEndlessStream()
					self.doSeek(0)
					self.setSeekState(self.SEEK_STATE_PLAY)

	def playExit(self):
		self.__class__.ctr -= 1
		self.SaverTimer.stop()
		del self.SaverTimer
		self.EmbeddedCoverTimer.stop()
		del self.EmbeddedCoverTimer
		if mp_globals.yt_dwnld_agent:
			mp_globals.yt_dwnld_agent.cancelDownload()

		mp_globals.yt_download_progress_widget = None
		if isinstance(self, SimpleSeekHelper):
			del self.cursorTimer
		if isinstance(self, SimplePlayerResume):
			del self.posTrackerTimer
			del self.eofResumeTimer

		if not self.playerMode in ('MP3',):
			self.restoreLastService()

		if self.downloader != None:
			self.downloader.stop()
		reactor.callLater(1, clearTmpBuffer)

	def restoreLastService(self):
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)
		else:
			self.session.nav.stopService()

	def getVideo(self):
		entry = self.playList[self.playIdx]
		title = entry[0]
		url = entry[1]
		epg_id = None
		l = len(entry)
		if l >= 3:
			iurl = entry[2]
			if (l > 3):
				epg_id = entry[3][2] if entry[3] and ('tvg-id' in entry[3]) and entry[3][2] and not entry[3][2].endswith('.ink') else None
		else:
			iurl = ''
		self.playStream(title, url, imgurl=iurl, epg_id=epg_id)

	def getVideo2(self):
		if self.playLen > 0:
			titel = self.playList2[self.playIdx][1]
			url = self.playList2[self.playIdx][2]
			album = self.playList2[self.playIdx][3]
			artist = self.playList2[self.playIdx][4]
			imgurl = self.playList2[self.playIdx][7]
			self.cover2 = self.playList2[self.playIdx][8] == '1' and self.plType == 'global'

			if len(self.playList2[self.playIdx]) < 6:
				ltype = ''
			else:
				ltype = self.playList2[self.playIdx][5]

			if ltype == 'youtube':
				YoutubeLink(self.session).getLink(self.playStream, self.dataError, titel, url, imgurl)
			elif ltype == 'ampya':
				token = self.playList2[self.playIdx][6]
				AmpyaLink(self.session).getLink(self.playStream, self.dataError, titel, url, token, imgurl)
			elif mechanizeModule and ltype == 'canna':
				CannaLink(self.session).getLink(self.playStream, self.dataError, titel, artist, album, url, imgurl)
			elif ltype == 'eighties':
				token = self.playList2[self.playIdx][6]
				EightiesLink(self.session).getLink(self.playStream, self.dataError, titel, artist, album, url, token, imgurl)
			elif ltype == 'mtv':
				MTVdeLink(self.session).getLink(self.playStream, self.dataError, titel, artist, url, imgurl)
			elif url:
				self.playStream(titel, url, album=album, artist=artist, imgurl=imgurl)
		else:
			self.close()

	def openPlaylist(self, pl_class=SimplePlaylist):
		if ((self.showGlobalPlaylist and self.plType == 'global') or self.showPlaylist) and self.playLen > 0:
			if self.playlistQ.empty():
				self.playlistQ.put(self.pl_status)
			self.pl_open = True
			self.pl_event.genEvent()

			if self.plType == 'local':
				self.session.openWithCallback(self.cb_Playlist, pl_class, self.playList, self.playIdx, self.playMode, listTitle=self.listTitle, plType=self.plType, title_inr=self.title_inr, queue=self.playlistQ, mp_event=self.pl_event, listEntryPar=self.listEntryPar, playFunc=self.playSelectedVideo,playerMode=self.playerMode)
			else:
				self.session.openWithCallback(self.cb_Playlist, pl_class, self.playList2, self.playIdx, self.playMode, listTitle=None, plType=self.plType, title_inr=0, queue=self.playlistQ, mp_event=self.pl_event, listEntryPar=self.listEntryPar,playFunc=self.playSelectedVideo,playerMode=self.playerMode)
		elif not self.playLen:
			self.session.open(MessageBoxExt, _("No entries in the playlist available!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def cb_Playlist(self, data):
		self.pl_open = False

		while not self.playlistQ.empty():
			t = self.playlistQ.get_nowait()

		if data[0] >= 0:
			self.playIdx = data[0]
			if self.plType == 'global':
				if data[1] == 'del':
					self.session.nav.stopService()
					SimplePlaylistIO.delEntry(self.pl_name, self.playList2, self.playIdx)
					self.playLen = len(self.playList2)
					if self.playIdx >= self.playLen:
						self.playIdx -= 1
					if self.playIdx < 0:
						self.close()
					else:
						self.openPlaylist()
			if not self.keyPlayNextLocked:
				self.keyPlayNextLocked = True
				self.playVideo()
		elif data[0] == -1 and self.playerMode in ('MP3',):
				self.close()
		elif self.playerMode in ('MP3',) and isinstance(self, SimplePlayerResume):
			self.showInfoBar()

	def openMediainfo(self):
		if MediaInfoPresent:
			try:
				self.session.open(MediaInfo)
			except:
				self.session.open(mediaInfo, True)

	def openMovieinfo(self):
		service = self.session.nav.getCurrentService()
		if service:
			title = service.info().getName()
			title = title.translate(None,"[].;:!&?,")
			title = title.replace(' ','_')
			title = self.cleanTitle(title, False)
			if TMDbPresent:
				self.session.open(TMDbMain, title)
			elif IMDbPresent:
				self.session.open(IMDB, title)

	def openMenu(self):
		self.session.openWithCallback(self.cb_Menu, SimplePlayerMenu, self.plType, self.showPlaylist or self.showGlobalPlaylist)

	def cb_Menu(self, data):
		if data != []:
			if data[0] == 1:
				self.playMode[0] = config.mediaportal.sp_playmode.value
				self.configSaver()
				if self.cover or self.cover2 or self.searchCoverSupp:
					self.showCover(self.pl_status[4])
				self.pl_name = 'mp_global_pl_%02d' % config.mediaportal.sp_pl_number.value
			elif data[0] == 2:
				self.addToPlaylist()

			elif data[0] == 3:
				nm = self.pl_name
				pl_list = SimplePlaylistIO.getPL(nm)
				self.playList2 = pl_list
				playLen = len(self.playList2)
				if playLen > 0:
					self.playIdx = 0
					self.playLen = playLen
					self.plType = 'global'
				self.openPlaylist()

			elif data[0] == 4:
				if self.plType != 'local':
					playLen = len(self.playList)
					if playLen > 0:
						self.playIdx = 0
						self.playLen = playLen
						self.plType = 'local'
						self.playList2 = []
					self.openPlaylist()

			elif data[0] == 6:
				self.mainMenu()

	def addToPlaylist(self):
		if self.plType != 'local':
			self.session.open(MessageBoxExt, _("Error: Service may be added only from the local playlist"), MessageBoxExt.TYPE_INFO, timeout=5)
			return

		if self.pl_entry[4] == 'youtube':
			url = self.playList[self.playIdx][self.title_inr+1]
		elif self.pl_entry[4] == 'mtv':
			url = self.playList[self.playIdx][1]
		elif self.pl_entry[4] == 'ampya' and self.playList[self.playIdx][2]:
			url = self.playList[self.playIdx][1]
			self.pl_entry[5] = self.playList[self.playIdx][2]
		else:
			if '.m3u8' in self.playList[self.playIdx][1]:
				url = self.playList[self.playIdx][1]
			else:
				url = self.session.nav.getCurrentlyPlayingServiceReference().getPath()

			if re.search('(putpat.tv|/myspass)', url, re.I):
				self.session.open(MessageBoxExt, _("Error: URL is not persistent!"), MessageBoxExt.TYPE_INFO, timeout=5)
				return

		self.pl_entry[1] = url
		res = SimplePlaylistIO.addEntry(self.pl_name, self.pl_entry)
		if res == 1:
			self.session.open(MessageBoxExt, _("Added entry"), MessageBoxExt.TYPE_INFO, timeout=5)
		elif res == 0:
			self.session.open(MessageBoxExt, _("Entry already exists"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			self.session.open(MessageBoxExt, _("Error!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def showCover(self, cover, download_cb=None):
		if config.mediaportal.sp_infobar_cover_off.value:
			self.hideSPCover()
			self['Cover'].hide()
			self['noCover'].show()
			return
		if self.coverBGisHidden:
			self.showSPCover()
		self._Cover.getCover(cover, download_cb=download_cb)

	def showIcon(self):
		self['dwnld_progressbar'].setValue(0)
		mp_globals.yt_download_progress_widget = self.progrObj
		pm_file = self.wallicon_path + mp_globals.activeIcon + ".png"
		self._Icon.showCoverFile(pm_file, showNoCoverart=False)

	def _animation(self):
		self.setShowHideAnimation(config.mediaportal.animation_simpleplayer.value)

	def hideSPCover(self):
		if not self.coverBGisHidden:
			self['spcoverframe'].hide()
			self['spcoverfg'].hide()
			self['noCover'].show()
			self.coverBGisHidden = True

	def showSPCover(self):
		if self.coverBGisHidden:
			self['spcoverframe'].show()
			self['spcoverfg'].show()
			self['noCover'].hide()
			self.coverBGisHidden = False

	#def lockShow(self):
	#	pass

	#def unlockShow(self):
	#	pass

	def configSaver(self):
		self.scrSaver = config.mediaportal.sp_scrsaver.value
		if self.scrSaver == 'automatic' and self.autoScrSaver or self.scrSaver == 'on':
			if not self.saverActive:
				self.SaverTimer.start(1000*60, True)
				self.saverActive = True
		else:
			self.SaverTimer.stop()
			self.saverActive = False

	def openSaver(self):
		self.session.openWithCallback(self.cb_Saver, SimpleScreenSaver)

	def cb_Saver(self):
		self.saverActive = False
		self.configSaver()

	def createSummary(self):
		return SimplePlayerSummary

	def setActionPrio(self):
		if config.mediaportal.sp_use_number_seek.value:
			self.action_prio = -2
		else:
			self.action_prio = -1

	def runPlugin(self, plugin):
		plugin(session=self.session)

	def setPlayerAgent(self):
		if not mp_globals.player_agent: return
		try:
			config.mediaplayer.useAlternateUserAgent.value = True
			config.mediaplayer.alternateUserAgent.value = mp_globals.player_agent
		except Exception, errormsg:
			if not hasattr(config, "mediaplayer"):
				config.mediaplayer = ConfigSubsection()
				config.mediaplayer.useAlternateUserAgent = ConfigYesNo(default=True)
				config.mediaplayer.alternateUserAgent = ConfigText(default=mp_globals.player_agent)
			else:
				pass
		self.onClose.append(self.clearPlayerAgent)

	def clearPlayerAgent(self):
		mp_globals.player_agent = None
		try:
			config.mediaplayer.useAlternateUserAgent.value = False
			config.mediaplayer.alternateUserAgent.value = ""
		except:
			pass

class SimpleConfig(Screen, ConfigListScreenExt):

	def __init__(self, session):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/simpleplayer/SimplePlayerConfig.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/simpleplayer/SimplePlayerConfig.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		self['title'] = Label(_("SimplePlayer Configuration"))
		self.setTitle(_("SimplePlayer Configuration"))
		self.list = []
		self.list.append(getConfigListEntry(_('Global playlist number:'), config.mediaportal.sp_pl_number))
		self.list.append(getConfigListEntry(_('Playmode:'), config.mediaportal.sp_playmode))
		self.list.append(getConfigListEntry(_('Screensaver:'), config.mediaportal.sp_scrsaver))
		self.list.append(getConfigListEntry(_('Use YT Proxy:'), config.mediaportal.sp_use_yt_with_proxy))
		self.list.append(getConfigListEntry(_("YT-HTTP-Proxy Host or IP:"), config.mediaportal.yt_proxy_host, False))
		self.list.append(getConfigListEntry(_("YT-Proxy Port:"), config.mediaportal.yt_proxy_port, False))
		self.list.append(getConfigListEntry(_("YT-Proxy username:"), config.mediaportal.yt_proxy_username, False))
		self.list.append(getConfigListEntry(_("YT-Proxy password:"), config.mediaportal.yt_proxy_password, False))
		self.list.append(getConfigListEntry(_('Videoquality (Youtube):'), config.mediaportal.youtubeprio))
		self.list.append(getConfigListEntry(_('Videoquality (others):'), config.mediaportal.videoquali_others))
		self.list.append(getConfigListEntry(_('Save resume cache in flash memory:'), config.mediaportal.sp_save_resumecache))
		self.list.append(getConfigListEntry(_('Behavior on movie start:'), config.mediaportal.sp_on_movie_start))
		self.list.append(getConfigListEntry(_('Behavior on movie stop:'), config.mediaportal.sp_on_movie_stop))
		self.list.append(getConfigListEntry(_('Behavior on movie end:'), config.mediaportal.sp_on_movie_eof))
		self.list.append(getConfigListEntry(_('Seekbar sensibility:'), config.mediaportal.sp_seekbar_sensibility))
		self.list.append(getConfigListEntry(_('Infobar cover always off:'), config.mediaportal.sp_infobar_cover_off))
		self.list.append(getConfigListEntry(_('Show errors:'), config.mediaportal.sp_show_errors))
		self.list.append(getConfigListEntry(_('Use SP number seek:'), config.mediaportal.sp_use_number_seek))
		if MediaInfoPresent:
			self.list.append(getConfigListEntry(_('MediaInfo on key:'), config.mediaportal.sp_mi_key))
		self.list.append(getConfigListEntry(_('TMDb/IMDb on key:'), config.mediaportal.sp_imdb_key))
		ConfigListScreenExt.__init__(self, self.list)
		self['setupActions'] = ActionMap(['SetupActions'],
		{
			'ok': 		self.keySave,
			'cancel': 	self.keyCancel
		},-2)

class SimplePlayerMenu(Screen):

	def __init__(self, session, pltype, showPlaylist=True):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/simpleplayer/SimplePlayerMenu.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/simpleplayer/SimplePlayerMenu.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		self['title'] = Label(_("SimplePlayer Menu"))
		self.setTitle(_("SimplePlayer Menu"))
		self.pltype = pltype
		self['setupActions'] = ActionMap(['SetupActions'],
		{
			'ok': 		self.keyOk,
			'cancel':	self.keyCancel
		}, -2)

		self.liste = []
		if pltype != 'extern':
			self.liste.append((_('Configuration'), 1))
		if pltype in ('local', 'extern') :
			self.pl_name = 'mp_global_pl_%02d' % config.mediaportal.sp_pl_number.value
			self.liste.append((_('Add service to global playlist-%02d') % config.mediaportal.sp_pl_number.value, 2))
			if showPlaylist and pltype == 'local':
				self.liste.append((_('Open global playlist-%02d') % config.mediaportal.sp_pl_number.value, 3))
		elif showPlaylist:
			self.liste.append((_('Open local playlist'), 4))
		if VideoSetupPresent:
			self.liste.append((_('A/V Settings'), 5))
		self.liste.append((_('Mainmenu'), 6))
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.ml.l.setFont(0, gFont(mp_globals.font, mp_globals.fontsize))
		self.ml.l.setItemHeight(mp_globals.fontsize + 2 * mp_globals.sizefactor)
		self.ml.setList(map(self.menulistentry, self.liste))
		self['menu'] = self.ml

	def menulistentry(self, entry):
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 1000, mp_globals.fontsize + 2 * mp_globals.sizefactor, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0])
			]

	def openConfig(self):
		self.session.open(SimpleConfig)
		self.close([1, ''])

	def addToPlaylist(self, id, name):
		self.close([id, name])

	def openPlaylist(self, id, name):
		self.close([id, name])

	def openSetup(self):
		if VideoSetupPresent:
			if is_avSetupScreen:
				self.session.open(avSetupScreen)
			else:
				self.session.open(VideoSetup, video_hw)
		self.close([5, ''])

	def openMainmenu(self, id, name):
		self.close([id, name])

	def keyOk(self):
		choice = self['menu'].getCurrent()[0][1]
		if choice == 1:
			self.openConfig()
		elif choice == 2:
			self.addToPlaylist(2, self.pl_name)
		elif choice == 3:
			self.openPlaylist(3, '')
		elif choice == 4:
			self.openPlaylist(4, '')
		elif choice == 5:
			self.openSetup()
		elif choice == 6:
			self.openMainmenu(6, '')

	def keyCancel(self):
		self.close([])

class SimplePlaylistIO:

	Msgs = [_("The directory path does not end with '/':\n%s"),
		_("File with the same name exists in the directory path:\n%s"),
		_("The missing directory:\n%s could not be created!"),
		_("The directory path:\n%s does not exist!"),
		_("There exists already a directory with this name:\n%s"),
		_("The path is OK, the file name was not specified:\n%s"),
		_("The directory path and file name is OK:\n%s"),
		_("The directory path is not specified!"),
		_("Symbolic link with the same name in the directory path:\n%s available!")]

	@staticmethod
	def checkPath(path, pl_name, createPath=False):
		if not path:
			return (0, SimplePlaylistIO.Msgs[7])
		if path[-1] != '/':
			return (0, SimplePlaylistIO.Msgs[0] % path)
		if not os.path.isdir(path):
			if os.path.isfile(path[:-1]):
				return (0, SimplePlaylistIO.Msgs[1] % path)
			if os.path.islink(path[:-1]):
				return (0, SimplePlaylistIO.Msgs[8] % path)
			if createPath:
				if createDir(path, True) == 0:
					return (0, SimplePlaylistIO.Msgs[2] % path)
			else:
				return (0, SimplePlaylistIO.Msgs[3] % path)
		if not pl_name:
			return (1, SimplePlaylistIO.Msgs[5] % path)
		if os.path.isdir(path+pl_name):
			return (0, SimplePlaylistIO.Msgs[4] % (path, pl_name))

		return (1, SimplePlaylistIO.Msgs[6] % (path, pl_name))

	@staticmethod
	def delEntry(pl_name, list, idx):
		assert pl_name != None
		assert list != []

		pl_path = config.mediaportal.watchlistpath.value + pl_name

		l = len(list)
		if idx in range(0, l):
			del list[idx]
			l = len(list)

		j = 0
		try:
			f1 = open(pl_path, 'w')
			while j < l:
				wdat = '<title>%s</<url>%s</<album>%s</<artist>%s</<ltype %s/><token %s/><img %s/><cflag %s/>\n' % (list[j][1], list[j][2], list[j][3], list[j][4], list[j][5], list[j][6], list[j][7], list[j][8])
				f1.write(wdat)
				j += 1

			f1.close()

		except IOError, e:
			f1.close()

	@staticmethod
	def addEntry(pl_name, entry):
		cflag = entry[7]
		imgurl = entry[6]
		if imgurl and not imgurl.startswith('http'):
			imgurl = ""
		token = entry[5]
		ltype = entry[4]
		album = entry[3]
		artist = entry[2]
		url = entry[1]
		title = entry[0].replace('\n\t', ' - ')
		title = title.replace('\n', ' - ')

		if token == None:
			token = ''

		if url == None:
			url = ''

		if imgurl == None:
			imgurl = ''

		cmptup = (url, artist, title)

		assert pl_name != None

		pl_path = config.mediaportal.watchlistpath.value + pl_name
		try:
			if fileExists(pl_path):
				f1 = open(pl_path, 'a+')

				data = f1.read()
				m = re.findall('<title>(.*?)</<url>(.*?)</.*?<artist>(.*?)</', data)
				if m:
					found = False
					for (t,u,a) in m:
						if (u,a,t)  == cmptup:
							found = True
							break

					if found:
						f1.close()
						return 0
			else:
				f1 = open(pl_path, 'w')

			wdat = '<title>%s</<url>%s</<album>%s</<artist>%s</<ltype %s/><token %s/><img %s/><cflag %s/>\n' % (title, url, album, artist, ltype, token, imgurl, cflag)
			f1.write(wdat)
			f1.close()
			return 1

		except IOError, e:
			f1.close()
			return -1

	@staticmethod
	def getPL(pl_name):
		list = []

		assert pl_name != None

		pl_path = config.mediaportal.watchlistpath.value + pl_name
		try:
			if not fileExists(pl_path):
				f_new = True
			else:
				f_new = False
				f1 = open(pl_path, 'r')

			if not f_new:
				while True:
					entry = f1.readline().strip()
					if entry == "":
						break
					m = re.search('<title>(.*?)</<url>(.*?)</<album>(.*?)</<artist>(.*?)</<ltype (.*?)/><token (.*?)/><img (.*?)/><cflag (.*?)/>', entry)
					if m:
						titel = m.group(1)
						url = m.group(2)
						album = m.group(3)
						artist = m.group(4)
						ltype = m.group(5)
						token = m.group(6)
						imgurl = m.group(7)
						cflag = m.group(8)

						if artist != '':
							name = "%s - %s" % (artist, titel)
						else:
							name = titel

						list.append((name, titel, url, album, artist, ltype, token, imgurl, cflag))

				f1.close()

			return list

		except IOError, e:
			f1.close()
			return list

try:
	from Plugins.Extensions.MerlinMusicPlayer.plugin import MerlinMusicPlayerScreenSaver
	class SimpleScreenSaver(MerlinMusicPlayerScreenSaver):
		def __init__(self, session):
			MerlinMusicPlayerScreenSaver.__init__(self, session)

		def createSummary(self):
			return SimplePlayerSummary

except:
	class SimpleScreenSaver(Screen):
		if mp_globals.videomode == 3:
			skin = '<screen position="0,0" size="3840,2160" flags="wfNoBorder" zPosition="15" transparent="0" backgroundColor="#00000000"></screen>'
		elif mp_globals.videomode == 2:
			skin = '<screen position="0,0" size="1920,1080" flags="wfNoBorder" zPosition="15" transparent="0" backgroundColor="#00000000"></screen>'
		else:
			skin = '<screen position="0,0" size="1280,720" flags="wfNoBorder" zPosition="15" transparent="0" backgroundColor="#00000000"></screen>'

		def __init__(self, session):
			Screen.__init__(self, session)
			self.skin = SimpleScreenSaver.skin

			self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EventViewActions"],
			{
				"back": self.close,
				"right": self.close,
				"left": self.close,
				"up": self.close,
				"down": self.close,
				"ok": self.close,
				"pageUp": self.close,
				"pageDown": self.close,
				"yellow": self.close,
				"blue": self.close,
				"red": self.close,
				"green": self.close,
				"right": self.close,
				"left": self.close,
				"prevBouquet": self.close,
				"nextBouquet": self.close,
				"info": self.close

			}, -1)

		def createSummary(self):
			return SimplePlayerSummary

class SimplePlayerSummary(Screen):

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self.skinName = "InfoBarMoviePlayerSummary"