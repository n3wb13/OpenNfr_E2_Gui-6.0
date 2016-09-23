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

SHOW_HANG_STAT = False

# General imports
from . import _
import bz2
from Tools.BoundFunction import boundFunction
from base64 import b64decode as bsdcd
from resources.imports import *
from resources.update import *
from resources.simplelist import *
from resources.simpleplayer import SimplePlaylistIO
from resources.twagenthelper import twAgentGetPage
from resources.configlistext import ConfigListScreenExt
from resources.pininputext import PinInputExt
from resources.decrypt import *
from resources.realdebrid import realdebrid_oauth2
try:
	from Components.config import ConfigPassword
except ImportError:
	ConfigPassword = ConfigText

from twisted.internet import task
from resources.twisted_hang import HangWatcher

CONFIG = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/additions/additions.xml"

desktopSize = getDesktop(0).size()
if desktopSize.height() == 2160:
	mp_globals.videomode = 3
elif desktopSize.height() == 1080:
	mp_globals.videomode = 2
else:
	mp_globals.videomode = 1

try:
	from enigma import eMediaDatabase
	mp_globals.isDreamOS = True
except:
	mp_globals.isDreamOS = False

try:
	from Components.ScreenAnimations import *
	mp_globals.animations = True
	sa = ScreenAnimations()
	sa.fromXML(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/animations.xml"))
except:
	mp_globals.animations = False

try:
	from Components.CoverCollection import CoverCollection
	if mp_globals.isDreamOS:
		mp_globals.covercollection = True
	else:
		mp_globals.covercollection = False
except:
	mp_globals.covercollection = False

try:
	from enigma import getVTiVersionString
	mp_globals.fakeScale = True
except:
	try:
		import boxbranding
		mp_globals.fakeScale = True
	except:
		if fileExists("/etc/.box"):
			mp_globals.fakeScale = True
		else:
			mp_globals.fakeScale = False

try:
	import mechanize
except:
	mechanizeModule = False
else:
	mechanizeModule = True

try:
	from Plugins.Extensions.MediaInfo.plugin import MediaInfo
	MediaInfoPresent = True
except:
	try:
		from Plugins.Extensions.mediainfo.plugin import mediaInfo
		MediaInfoPresent = True
	except:
		MediaInfoPresent = False

def lastMACbyte():
	try:
		return int(open('/sys/class/net/eth0/address').readline().strip()[-2:], 16)
	except:
		return 256

def calcDefaultStarttime():
	try:
		# Use the last MAC byte as time offset (half-minute intervals)
		offset = lastMACbyte() * 30
	except:
		offset = 7680
	return (5 * 60 * 60) + offset

from Components.config import ConfigEnableDisable, ConfigClock

config.mediaportal = ConfigSubsection()

# Fake entry fuer die Kategorien
config.mediaportal.fake_entry = NoSave(ConfigNothing())

# EPG Import
config.mediaportal.epg_enabled = ConfigEnableDisable(default = False)
config.mediaportal.epg_runboot = ConfigEnableDisable(default = False)
config.mediaportal.epg_wakeupsleep = ConfigEnableDisable(default = False)
config.mediaportal.epg_wakeup = ConfigClock(default = calcDefaultStarttime())
config.mediaportal.epg_deepstandby = ConfigSelection(default = "skip", choices = [
		("wakeup", _("Wake up and import")),
		("skip", _("Skip the import"))
		])

# Allgemein
config.mediaportal.version = NoSave(ConfigText(default="761"))
config.mediaportal.versiontext = NoSave(ConfigText(default="7.6.1"))
config.mediaportal.autoupdate = ConfigYesNo(default = True)
config.mediaportal.pincode = ConfigPIN(default = 0000)
config.mediaportal.showporn = ConfigYesNo(default = False)
config.mediaportal.showgrauzone = ConfigYesNo(default = False)
config.mediaportal.pingrauzone = ConfigYesNo(default = False)
config.mediaportal.ena_suggestions = ConfigYesNo(default = True)

config.mediaportal.animation_coverart = ConfigSelection(default = "mp_crossfade_fast", choices = [("mp_crossfade_fast", _("Crossfade (fast)")),("mp_crossfade_slow", _("Crossfade (slow)"))])
config.mediaportal.animation_label = ConfigSelection(default = "mp_crossfade_fast", choices = [("mp_crossfade_fast", _("Crossfade (fast)")),("mp_crossfade_slow", _("Crossfade (slow)"))])
config.mediaportal.animation_simpleplayer = ConfigSelection(default = "mp_player_animation", choices = [("mp_player_animation", _("Slide from bottom")),("mp_crossfade_slow", _("Crossfade"))])

skins = []
if mp_globals.videomode == 3:
	mp_globals.skinFallback = "/clean_uhd"
	for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_2160/"):
		if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_2160/", skin)):
			skins.append(skin)
	mp_globals.skinsPath = "/skins_2160"
	if mp_globals.isDreamOS:
		config.mediaportal.skin = ConfigSelection(default = skins[0], choices = skins)
	else:
		config.mediaportal.skin = ConfigSelection(default = skins[0], choices = skins)
	if len(skins) == 0:
		mp_globals.videomode = 2
		mp_globals.skinsPath = "/skins_1080"
		for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/"):
			if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/", skin)):
				skins.append(skin)
		config.mediaportal.skin = ConfigSelection(default = "clean_fhd", choices = ["clean_fhd"])
		mp_globals.skinFallback = "/clean_fhd"
elif mp_globals.videomode == 2:
	mp_globals.skinsPath = "/skins_1080"
	for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/"):
		if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/", skin)):
			skins.append(skin)
	config.mediaportal.skin = ConfigSelection(default = "clean_fhd", choices = skins)
	mp_globals.skinFallback = "/clean_fhd"
else:
	mp_globals.skinsPath = "/skins_720"
	for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_720/"):
		if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_720/", skin)):
			skins.append(skin)
	config.mediaportal.skin = ConfigSelection(default = "tec", choices = skins)
	if os.path.isdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_720/tec"):
		mp_globals.skinFallback = "/tec"
	else:
		mp_globals.skinFallback = "/original"

if mp_globals.covercollection:
	config.mediaportal.ansicht = ConfigSelection(default = "wall2", choices = [("liste", _("List")),("wall", _("Wall")),("wall2", _("Wall 2.0"))])
elif mp_globals.videomode >= 2 and mp_globals.fakeScale:
	config.mediaportal.ansicht = ConfigSelection(default = "wall", choices = [("liste", _("List")),("wall", _("Wall"))])
elif mp_globals.videomode >= 2 and not mp_globals.isDreamOS:
	config.mediaportal.ansicht = ConfigSelection(default = "liste", choices = [("liste", _("List"))])
else:
	config.mediaportal.ansicht = ConfigSelection(default = "wall", choices = [("liste", _("List")),("wall", _("Wall"))])
config.mediaportal.wallmode = ConfigSelection(default = "color", choices = [("color", _("Color")),("bw", _("Black&White")),("color_zoom", _("Color (Zoom)")),("bw_zoom", _("Black&White (Zoom)"))])
config.mediaportal.wall2mode = ConfigSelection(default = "color", choices = [("color", _("Color")),("bw", _("Black&White"))])
config.mediaportal.listmode = ConfigSelection(default = "full", choices = [("full", _("Full")),("single", _("Single"))])
config.mediaportal.selektor = ConfigSelection(default = "white", choices = [("blue", _("Blue")),("green", _("Green")),("red", _("Red")),("turkis", _("Aqua")),("white", _("White"))])
config.mediaportal.use_hls_proxy = ConfigYesNo(default = False)
config.mediaportal.hls_proxy_ip = ConfigIP(default = [127,0,0,1], auto_jump = True)
config.mediaportal.hls_proxy_port = ConfigInteger(default = 0, limits = (0,65535))
config.mediaportal.hls_buffersize = ConfigInteger(default = 16, limits = (1,32))
config.mediaportal.storagepath = ConfigText(default="/media/hdd/mediaportal/tmp/", fixed_size=False)
config.mediaportal.autoplayThreshold = ConfigInteger(default = 50, limits = (1,100))
config.mediaportal.filter = ConfigSelection(default = "ALL", choices = ["ALL", "Mediathek", "Grauzone", "Fun", "Sport", "Music", "Porn"])
config.mediaportal.youtubeprio = ConfigSelection(default = "1", choices = [("0", _("Low")),("1", _("Medium")),("2", _("High"))])
config.mediaportal.videoquali_others = ConfigSelection(default = "1", choices = [("0", _("Low")),("1", _("Medium")),("2", _("High"))])
config.mediaportal.youtube_max_items_pp = ConfigInteger(default = 12, limits = (10,50))
config.mediaportal.pornpin = ConfigYesNo(default = True)
config.mediaportal.pornpin_cache = ConfigSelection(default = "0", choices = [("0", _("never")), ("5", _("5 minutes")), ("15", _("15 minutes")), ("30", _("30 minutes")), ("60", _("60 minutes"))])
config.mediaportal.kidspin = ConfigYesNo(default = False)
config.mediaportal.setuppin = ConfigYesNo(default = False)
config.mediaportal.watchlistpath = ConfigText(default="/etc/enigma2/", fixed_size=False)
config.mediaportal.sortplugins = ConfigSelection(default = "abc", choices = [("hits", "Hits"), ("abc", "ABC"), ("user", "User")])
config.mediaportal.pagestyle = ConfigSelection(default="Graphic", choices = ["Graphic", "Text"])
config.mediaportal.debugMode = ConfigSelection(default="Silent", choices = ["High", "Normal", "Silent"])
config.mediaportal.font = ConfigSelection(default = "1", choices = [("1", "Mediaportal 1"),("2", "Mediaportal 2")])
config.mediaportal.showAsThumb = ConfigYesNo(default = False)
config.mediaportal.restorelastservice = ConfigSelection(default = "1", choices = [("1", _("after SimplePlayer quits")),("2", _("after MediaPortal quits"))])
config.mediaportal.filterselector = ConfigYesNo(default = True)
config.mediaportal.backgroundtv = ConfigYesNo(default = False)
config.mediaportal.minitv = ConfigYesNo(default = True)
config.mediaportal.showTipps = ConfigYesNo(default = True)
config.mediaportal.simplelist_key = ConfigSelection(default = "showMovies", choices = [("showMovies", _("PVR/VIDEO")),("instantRecord", _("RECORD"))])

# Konfiguration erfolgt in SimplePlayer
config.mediaportal.sp_playmode = ConfigSelection(default = "forward", choices = [("forward", _("Forward")),("backward", _("Backward")),("random", _("Random"))])
config.mediaportal.sp_scrsaver = ConfigSelection(default = "off", choices = [("on", _("On")),("off", _("Off")),("automatic", _("Automatic"))])
config.mediaportal.sp_on_movie_stop = ConfigSelection(default = "ask", choices = [("ask", _("Ask user")), ("quit", _("Return to previous service"))])
config.mediaportal.sp_on_movie_eof = ConfigSelection(default = "ask", choices = [("ask", _("Ask user")), ("quit", _("Return to previous service")), ("pause", _("Pause movie at end"))])
config.mediaportal.sp_seekbar_sensibility = ConfigInteger(default = 10, limits = (1,50))
config.mediaportal.sp_infobar_cover_off = ConfigYesNo(default = False)
config.mediaportal.sp_show_errors = ConfigYesNo(default = False)
config.mediaportal.sp_use_number_seek = ConfigYesNo(default = True)
config.mediaportal.sp_pl_number = ConfigInteger(default = 1, limits = (1,99))
config.mediaportal.sp_mi_key = ConfigSelection(default = "instantRecord", choices = [("displayHelp", _("HELP")),("showMovies", _("PVR/VIDEO")),("instantRecord", _("RECORD"))])
config.mediaportal.sp_use_yt_with_proxy = ConfigSelection(default = "no", choices = [("no", _("No")), ("prz", "with Premiumize"), ("rdb", "with Real-Debrid"), ("proxy", "with a HTTP Proxy")])
config.mediaportal.sp_on_movie_start = ConfigSelection(default = "ask", choices = [("start", _("Start from the beginning")), ("ask", _("Ask user")), ("resume", _("Resume from last position"))])
config.mediaportal.sp_save_resumecache = ConfigYesNo(default = False)
config.mediaportal.premiumize_yt_buffering_opt = ConfigSelection(default = "off", choices = [("off", _("Off")), ("smart", _("Smart")), ("all", _("Always"))])
config.mediaportal.premiumize_use_yt_buffering_size = ConfigSelection(default = "2", choices = [("0", _("Whole file size")), ("1", "1MB"), ("2", "2MB"), ("5", "5MB"), ("10", "10MB")])
config.mediaportal.sp_imdb_key = ConfigSelection(default = "info", choices = [("displayHelp", _("HELP")),("showMovies", _("PVR/VIDEO")),("info", _("EPG/INFO"))])
config.mediaportal.yt_proxy_username = ConfigText(default="user!", fixed_size=False)
config.mediaportal.yt_proxy_password = ConfigPassword(default="pass!", fixed_size=False)
config.mediaportal.yt_proxy_host = ConfigText(default = "example_proxy.com!", fixed_size = False)
config.mediaportal.yt_proxy_port = ConfigInteger(default = 8080, limits = (0,65535))
config.mediaportal.hlsp_proxy_username = ConfigText(default="user!", fixed_size=False)
config.mediaportal.hlsp_proxy_password = ConfigPassword(default="pass!", fixed_size=False)
config.mediaportal.hlsp_proxy_host = ConfigText(default = "example_proxy.com!", fixed_size = False)
config.mediaportal.hlsp_proxy_port = ConfigInteger(default = 8080, limits = (0,65535))
config.mediaportal.sp_use_hlsp_with_proxy = ConfigSelection(default = "no", choices = [("no", _("No")), ("always", "Use it always"), ("plset", "Set in the playlist")])

# premiumize.me
config.mediaportal.premiumize_use = ConfigYesNo(default = False)
config.mediaportal.premiumize_username = ConfigText(default="user!", fixed_size=False)
config.mediaportal.premiumize_password = ConfigPassword(default="pass!", fixed_size=False)
config.mediaportal.premiumize_proxy_config_url = ConfigText(default="", fixed_size=False)

# real-debrid.com
config.mediaportal.realdebrid_use = ConfigYesNo(default = False)
config.mediaportal.realdebrid_accesstoken = ConfigText(default="", fixed_size=False)
config.mediaportal.realdebrid_refreshtoken = ConfigText(default="", fixed_size=False)
config.mediaportal.realdebrid_rclient_id = ConfigText(default="", fixed_size=False)
config.mediaportal.realdebrid_rclient_secret = ConfigText(default="", fixed_size=False)

# Premium Hosters
config.mediaportal.premium_color = ConfigSelection(default="0xFFFF00", choices = [("0xFF0000",_("Red")),("0xFFFF00",_("Yellow")),("0x00FF00",_("Green")),("0xFFFFFF",_("White")),("0x00ccff",_("Light Blue")),("0x66ff99",_("Light Green"))])

# Userchannels Help
config.mediaportal.show_userchan_help = ConfigYesNo(default = True)

# SimpleList
config.mediaportal.simplelist_gcoversupp = ConfigYesNo(default = True)

mp_globals.bsp = bsdcd(bsdcd(bsdcd(decrypt('Sz/1Vnx8fHysl9jsO32INqWDtQEsyyDPYlBc56P675cPRhMtaLEseb91C9KBEFa3EZ+PMz9EDz6zBc8t9jzgepxFy3B/XABw6bVPLEDyQJ7AUhDMlMtawA==', CONFIG, 256))))
mp_globals.yt_a = bsdcd(bsdcd(bsdcd(decrypt('kj8yV97e3t4fDPdo3ca07O6kKsuY9oZkvUqpBPJPkvzRYyzeAuLofAra3HKWsJmhvQ8EsGMDfnziGjqj3047WS8bojGewMj+in3daO4hlTSA6GUSwft7LNFdibC0hxTppR1VLXaRvKs=', CONFIG, 256))))
mp_globals.yt_i = bsdcd(bsdcd(bsdcd(decrypt('6T8yV5mZmZkf3mpGhQOBtEl8qSHI314cYq7dLTlEswoOTaaMktY5N37bfxUXGzUcKMBVEjMRiiTOSkNBaOzfKLy3tPmUvE3dYv2CAmayBgrftcOkb7hMaz6Y/jAQym1oT6E/X7P7tpComuUMFWJhDhSuYYt1o3CFx3j53vFgAdUdsWNlN96bgwCEUaJr4JeuaCh+4mMZbN0mDHb0D8jscSZ1MJ97En2ZMRbanG5O/e/3d3kvxN4dU0PaVy4qRUQ9UEhO0XL1E0eV2S4dORGFqXeLTvs=', CONFIG, 256))))
mp_globals.yt_s = bsdcd(bsdcd(bsdcd(decrypt('LUAyV6SkpKS3bO2Io81BlkONIwZfjHfCJgDdZMqw47QAGmIZT7tupMulXgbH+EkiOqKf84cqJX4T0EJYyhfiWF2Fy3Tb/nRdkzlcv5GgCF8rXFo1rFTW5ibXzsHu5HCmqRLW5meGHTo=', CONFIG, 256))))

# Global variable
autoStartTimer = None
_session = None

conf = xml.etree.cElementTree.parse(CONFIG)
for x in conf.getroot():
	if x.tag == "set" and x.get("name") == 'additions':
		root =  x
for x in root:
	if x.tag == "plugin":
		if x.get("type") == "mod":
			modfile = x.get("modfile")
			if modfile == "music.canna" and not mechanizeModule:
				pass
			else:
				if fileExists('/etc/enigma2/mp_override/'+modfile.split('.')[1]+'.py'):
					sys.path.append('/etc/enigma2/mp_override')
					exec("from "+modfile.split('.')[1]+" import *")
				else:
					exec("from additions."+modfile+" import *")
				exec("config.mediaportal."+x.get("confopt")+" = ConfigYesNo(default = "+x.get("default")+")")

class CheckPathes:

	def __init__(self, session):
		self.session = session
		self.cb = None

	def checkPathes(self, cb):
		self.cb = cb
		res, msg = SimplePlaylistIO.checkPath(config.mediaportal.watchlistpath.value, '', True)
		if not res:
			self.session.openWithCallback(self._callback, MessageBoxExt, msg, MessageBoxExt.TYPE_ERROR)

		if config.mediaportal.use_hls_proxy.value:
			res, msg = SimplePlaylistIO.checkPath(config.mediaportal.storagepath.value, '', True)
			if not res:
				self.session.openWithCallback(self._callback, MessageBoxExt, msg, MessageBoxExt.TYPE_ERROR)

	def _callback(self, answer):
		if self.cb:
			self.cb()

class PinCheck:

	def __init__(self):
		self.pin_entered = False
		self.timer = eTimer()
		if mp_globals.isDreamOS:
			self.timer_conn = self.timer.timeout.connect(self.lock)
		else:
			self.timer.callback.append(self.lock)

	def pinEntered(self):
		self.pin_entered = True
		self.timer.start(60000*int(config.mediaportal.pornpin_cache.value), 1)

	def lock(self):
		self.pin_entered = False

pincheck = PinCheck()

class CheckPremiumize:

	def __init__(self, session):
		self.session = session

	def premiumize(self):
		if config.mediaportal.premiumize_use.value:
			self.puser = config.mediaportal.premiumize_username.value
			self.ppass = config.mediaportal.premiumize_password.value
			url = "https://api.premiumize.me/pm-api/v1.php?method=accountstatus&params[login]=%s&params[pass]=%s" % (self.puser, self.ppass)
			r_getPage(url, timeout=15).addCallback(self.premiumizeData).addErrback(self.dataError)
		else:
			self.session.open(MessageBoxExt, _("premiumize.me is not activated."), MessageBoxExt.TYPE_ERROR)

	def premiumizeData(self, data):
		if re.search('status":200', data):
			infos = re.findall('"account_name":"(.*?)","type":"(.*?)","expires":(.*?),".*?trafficleft_gigabytes":(.*?)}', data, re.S|re.I)
			if infos:
				(a_name, a_type, a_expires, a_left) = infos[0]
				deadline = datetime.datetime.fromtimestamp(int(a_expires)).strftime('%d-%m-%Y')
				pmsg = "premiumize.me\n\nUser: %s\nType: %s\nExpires: %s\nTraffic: %s GB" % (a_name, a_type, deadline, int(float(a_left)))
				self.session.open(MessageBoxExt, pmsg , MessageBoxExt.TYPE_INFO)
			else:
				self.session.open(MessageBoxExt, _("premiumize.me failed."), MessageBoxExt.TYPE_ERROR)
			"""
			m = re.search('"extuid":"(.*?)"', data, re.S)
			pac_url = m and 'https://secure.premiumize.me/%s/proxy.pac' % m.group(1)
			if m and pac_url != config.mediaportal.premiumize_proxy_config_url.value:
				config.mediaportal.premiumize_proxy_config_url.value = pac_url
				config.mediaportal.premiumize_proxy_config_url.save()
				configfile.save()
				self.premiumizeProxyConfig()
			else:
				config.mediaportal.premiumize_proxy_config_url.value = ''
			"""
		elif re.search('status":401', data):
			self.session.open(MessageBoxExt, _("premiumize: Login failed."), MessageBoxExt.TYPE_INFO, timeout=3)

	def premiumizeProxyConfig(self, msgbox=True):
		return
		url = config.mediaportal.premiumize_proxy_config_url.value
		if re.search('^https://.*?\.pac', url):
			r_getPage(url, method="GET", timeout=15).addCallback(self.premiumizeProxyData, msgbox).addErrback(self.dataError)
		else:
			self.premiumize()

	def premiumizeProxyData(self, data, msgbox):
		m = re.search('PROXY (.*?):(\d{2}); PROXY', data)
		if m:
			mp_globals.premium_yt_proxy_host = m.group(1)
			mp_globals.premium_yt_proxy_port = int(m.group(2))
			print 'YT-Proxy:',m.group(1), ':', mp_globals.premium_yt_proxy_port
			if msgbox:
				self.session.open(MessageBoxExt, _("premiumize: YT ProxyHost found."), MessageBoxExt.TYPE_INFO)
		else:
			if msgbox:
				self.session.open(MessageBoxExt, _("premiumize: YT ProxyHost not found!"), MessageBoxExt.TYPE_ERROR)

	def dataError(self, error):
		print error

class MPSetup(Screen, CheckPremiumize, ConfigListScreenExt):

	def __init__(self, session):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/hauptScreenSetup.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/hauptScreenSetup.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config.mediaportal.minitv.value)

		Screen.__init__(self, session)

		self.configlist = []

		ConfigListScreenExt.__init__(self, self.configlist, on_change = self._onKeyChange)

		skins = []
		if mp_globals.videomode == 3:
			mp_globals.skinsPath = "/skins_2160"
			for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_2160/"):
				if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_2160/", skin)):
					skins.append(skin)
			if mp_globals.isDreamOS:
				config.mediaportal.skin.setChoices(skins, skins[0])
			else:
				config.mediaportal.skin.setChoices(skins, skins[0])
			if len(skins) == 0:
				mp_globals.videomode = 2
				mp_globals.skinsPath = "/skins_1080"
				config.mediaportal.skin.setChoices(["clean_fhd"], "clean_fhd")
		elif mp_globals.videomode == 2:
			mp_globals.skinsPath = "/skins_1080"
			for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/"):
				if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/", skin)):
					skins.append(skin)
			config.mediaportal.skin.setChoices(skins, "clean_fhd")
		else:
			mp_globals.skinsPath = "/skins_720"
			for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_720/"):
				if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_720/", skin)):
					skins.append(skin)
			config.mediaportal.skin.setChoices(skins, "tec")

		self._getConfig()

		self['title'] = Label("MediaPortal - Setup - (Version %s)" % config.mediaportal.versiontext.value)
		self['name'] = Label("Setup")
		self['F1'] = Label("Premium")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label("")

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keySave,
			"cancel": self.keyCancel,
			"nextBouquet": self.keyPreviousSection,
			"prevBouquet": self.keyNextSection,
			"red" : self.premium
		}, -1)

	def _separator(self):
		if mp_globals.isDreamOS:
			pass
		else:
			self.configlist.append(getConfigListEntry(400 * "—", ))

	def _getConfig(self):
		self.configlist = []
		self.sport = []
		self.music = []
		self.fun = []
		self.mediatheken = []
		self.porn = []
		self.grauzone = []
		self.watchlist = []
		### Allgemein
		self._separator()
		self.configlist.append(getConfigListEntry(_("GENERAL"), ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Automatic Update Check:"), config.mediaportal.autoupdate, False))
		self.configlist.append(getConfigListEntry(_("Mainview Style:"), config.mediaportal.ansicht, True))
		if config.mediaportal.ansicht.value == "wall":
			self.configlist.append(getConfigListEntry(_("Wall Mode:"), config.mediaportal.wallmode, True))
		if config.mediaportal.ansicht.value == "wall2":
			self.configlist.append(getConfigListEntry(_("Wall 2.0 Mode:"), config.mediaportal.wall2mode, False))
		if (config.mediaportal.ansicht.value == "wall" or config.mediaportal.ansicht.value == "wall2"):
			self.configlist.append(getConfigListEntry(_("Wall-Selector-Color:"), config.mediaportal.selektor, False))
			self.configlist.append(getConfigListEntry(_("Page Display Style:"), config.mediaportal.pagestyle, False))
			self.configlist.append(getConfigListEntry(_("Activate Filtermenu:"), config.mediaportal.filterselector, False))
		if config.mediaportal.ansicht.value == "liste":
			self.configlist.append(getConfigListEntry(_("List Mode:"), config.mediaportal.listmode, True))
		self.configlist.append(getConfigListEntry(_("Skin:"), config.mediaportal.skin, False))
		self.configlist.append(getConfigListEntry(_("Skin-Font:"), config.mediaportal.font, False))
		self.configlist.append(getConfigListEntry(_("ShowAsThumb as Default:"), config.mediaportal.showAsThumb, False))
		self.configlist.append(getConfigListEntry(_("Disable Background-TV:"), config.mediaportal.backgroundtv, True))
		if not config.mediaportal.backgroundtv.value:
			self.configlist.append(getConfigListEntry(_("Restore last service:"), config.mediaportal.restorelastservice, False))
			self.configlist.append(getConfigListEntry(_("Disable Mini-TV:"), config.mediaportal.minitv, False))
		self.configlist.append(getConfigListEntry(_("Show Tips:"), config.mediaportal.showTipps, False))
		self.configlist.append(getConfigListEntry(_("Enable search suggestions:"), config.mediaportal.ena_suggestions, False))
		if mp_globals.animations:
			self.configlist.append(getConfigListEntry(_("Coverart animation")+":", config.mediaportal.animation_coverart, False))
			self.configlist.append(getConfigListEntry(_("Label animation")+":", config.mediaportal.animation_label, False))
			self.configlist.append(getConfigListEntry(_("SimplePlayer animation")+":", config.mediaportal.animation_simpleplayer, False))
		else:
			self.configlist.append(getConfigListEntry(_("Coverart animation")+" (not available)"+":", config.mediaportal.fake_entry, False))
			self.configlist.append(getConfigListEntry(_("Label animation")+" (not available)"+":", config.mediaportal.fake_entry, False))
			self.configlist.append(getConfigListEntry(_("SimplePlayer animation")+" (not available)"+":", config.mediaportal.fake_entry, False))
		self._separator()
		self.configlist.append(getConfigListEntry(_("YOUTH PROTECTION"), ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Pincode:"), config.mediaportal.pincode, False))
		self.configlist.append(getConfigListEntry(_("Setup-Pincode Query:"), config.mediaportal.setuppin, False))
		self.configlist.append(getConfigListEntry(_("Kids-Pincode Query:"), config.mediaportal.kidspin, False))
		self.configlist.append(getConfigListEntry(_("Adult-Pincode Query:"), config.mediaportal.pornpin, False))
		self.configlist.append(getConfigListEntry(_("Remember Adult-Pincode:"), config.mediaportal.pornpin_cache, False))
		self._separator()
		self.configlist.append(getConfigListEntry(_("OTHER"), ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Use HLS-Player:"), config.mediaportal.use_hls_proxy, True))
		if config.mediaportal.use_hls_proxy.value:
			self.configlist.append(getConfigListEntry(_("HLS-Player buffersize [MB]:"), config.mediaportal.hls_buffersize, False))
			self.configlist.append(getConfigListEntry(_("HLS-Player IP:"), config.mediaportal.hls_proxy_ip, False))
			self.configlist.append(getConfigListEntry(_("HLS-Player Port:"), config.mediaportal.hls_proxy_port, False))
			self.configlist.append(getConfigListEntry(_('Use HLS-Player Proxy:'), config.mediaportal.sp_use_hlsp_with_proxy, False))
			self.configlist.append(getConfigListEntry(_("HLSP-HTTP-Proxy Host or IP:"), config.mediaportal.hlsp_proxy_host, False))
			self.configlist.append(getConfigListEntry(_("HLSP-Proxy Port:"), config.mediaportal.hlsp_proxy_port, False))
			self.configlist.append(getConfigListEntry(_("HLSP-Proxy username:"), config.mediaportal.hlsp_proxy_username, False))
			self.configlist.append(getConfigListEntry(_("HLSP-Proxy password:"), config.mediaportal.hlsp_proxy_password, False))
		if config.mediaportal.use_hls_proxy.value:
			self.configlist.append(getConfigListEntry(_("HLS-PLayer Cachepath:"), config.mediaportal.storagepath, False))
		self.configlist.append(getConfigListEntry(_("Max. count results/page (Youtube):"), config.mediaportal.youtube_max_items_pp, False))
		self.configlist.append(getConfigListEntry(_("Videoquality (Youtube):"), config.mediaportal.youtubeprio, False))
		self.configlist.append(getConfigListEntry(_("Videoquality (others):"), config.mediaportal.videoquali_others, False))
		self.configlist.append(getConfigListEntry(_("Watchlist/Playlist/Userchan path:"), config.mediaportal.watchlistpath, False))
		self.configlist.append(getConfigListEntry(_("Show USER-Channels Help:"), config.mediaportal.show_userchan_help, False))
		self.configlist.append(getConfigListEntry(_("Activate Grauzone:"), config.mediaportal.showgrauzone, False))
		self.configlist.append(getConfigListEntry(_('SimpleList on key:'), config.mediaportal.simplelist_key, False))
		if MediaInfoPresent:
			self.configlist.append(getConfigListEntry(_('MediaInfo on key:'), config.mediaportal.sp_mi_key, False))
		self._separator()
		self.configlist.append(getConfigListEntry("MP-EPG-IMPORTER", ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Enable import:"), config.mediaportal.epg_enabled, True))
		if config.mediaportal.epg_enabled.value:
			self.configlist.append(getConfigListEntry(_("Automatic start time:"), config.mediaportal.epg_wakeup, False))
			self.configlist.append(getConfigListEntry(_("Standby at startup:"), config.mediaportal.epg_wakeupsleep, False))
			self.configlist.append(getConfigListEntry(_("When in deep standby:"), config.mediaportal.epg_deepstandby, False))
			self.configlist.append(getConfigListEntry(_("Start import after booting up:"), config.mediaportal.epg_runboot, False))
		self._separator()
		self.configlist.append(getConfigListEntry("PREMIUMIZE.ME", ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Activate premiumize.me:"), config.mediaportal.premiumize_use, True))
		if config.mediaportal.premiumize_use.value:
			self.configlist.append(getConfigListEntry(_("Customer ID:"), config.mediaportal.premiumize_username, False))
			self.configlist.append(getConfigListEntry(_("PIN:"), config.mediaportal.premiumize_password, False))
			#self.configlist.append(getConfigListEntry(_("Autom. Proxy-Config.-URL:"), config.mediaportal.premiumize_proxy_config_url, False))
		self._separator()
		self.configlist.append(getConfigListEntry("REAL-DEBRID.COM", ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Activate Real-Debrid.com:"), config.mediaportal.realdebrid_use, True))
		if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
			self._separator()
			self.configlist.append(getConfigListEntry("PREMIUM", ))
			self._separator()
			self.configlist.append(getConfigListEntry(_("Streammarkercolor:"), config.mediaportal.premium_color, False))

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					modfile = x.get("modfile")
					gz = x.get("gz")
					if modfile == "music.canna" and not mechanizeModule:
						if not config.mediaportal.showgrauzone.value and gz == "1":
							pass
						else:
							exec("self."+x.get("confcat")+".append(getConfigListEntry(\""+x.get("name").replace("&amp;","&")+" (not available)\", config.mediaportal.fake_entry, False))")
					else:
						if not config.mediaportal.showgrauzone.value and gz == "1":
							pass
						else:
							exec("self."+x.get("confcat")+".append(getConfigListEntry(\""+x.get("name").replace("&amp;","&")+"\", config.mediaportal."+x.get("confopt")+", False))")

		self._separator()
		self.configlist.append(getConfigListEntry(_("SPORTS"), ))
		self._separator()
		self.sport.sort(key=lambda t : t[0].lower())
		for x in self.sport:
			self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		self._separator()
		self.configlist.append(getConfigListEntry(_("MUSIC"), ))
		self._separator()
		self.music.sort(key=lambda t : t[0].lower())
		for x in self.music:
			self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		self._separator()
		self.configlist.append(getConfigListEntry(_("FUN"), ))
		self._separator()
		self.fun.sort(key=lambda t : t[0].lower())
		for x in self.fun:
			self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		self._separator()
		self.configlist.append(getConfigListEntry(_("LIBRARIES"), ))
		self._separator()
		self.mediatheken.sort(key=lambda t : t[0].lower())
		for x in self.mediatheken:
			self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		if config.mediaportal.showporn.value:
			self._separator()
			self.configlist.append(getConfigListEntry(_("PORN"), ))
			self._separator()
			self.porn.sort(key=lambda t : t[0].lower())
			for x in self.porn:
				self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		if config.mediaportal.showgrauzone.value:
			self._separator()
			self.configlist.append(getConfigListEntry(_("GRAYZONE"), ))
			self._separator()
			self.grauzone.sort(key=lambda t : t[0].lower())
			for x in self.grauzone:
				self.configlist.append((_("Show ")+x[0]+":",x[1], False))
			self._separator()
			self.configlist.append(getConfigListEntry("WATCHLIST", ))
			self._separator()
			self.watchlist.sort(key=lambda t : t[0].lower())
			for x in self.watchlist:
				self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		self._separator()
		self.configlist.append(getConfigListEntry("DEBUG", ))
		self._separator()
		self.configlist.append(getConfigListEntry("Debug-Mode:", config.mediaportal.debugMode, False))

		self["config"].list = self.configlist
		self["config"].setList(self.configlist)

	def keyPreviousSection(self):
		self["config"].jumpToPreviousSection()

	def keyNextSection(self):
		self["config"].jumpToNextSection()

	def _onKeyChange(self):
		try:
			cur = self["config"].getCurrent()
			if cur and cur[2]:
				self._getConfig()
		except:
			pass

	def keyOK(self):
		if self["config"].current:
			self["config"].current[1].onDeselect(self.session)
		if config.mediaportal.watchlistpath.value[-1] != '/':
			config.mediaportal.watchlistpath.value = config.mediaportal.watchlistpath.value + '/'
		if config.mediaportal.storagepath.value[-1] != '/':
			config.mediaportal.storagepath.value = config.mediaportal.storagepath.value + '/'
		if config.mediaportal.storagepath.value[-4:] != 'tmp/':
			config.mediaportal.storagepath.value = config.mediaportal.storagepath.value + 'tmp/'
		if (config.mediaportal.showporn.value == False and config.mediaportal.filter.value == 'Porn'):
			config.mediaportal.filter.value = 'ALL'
		if (config.mediaportal.showgrauzone.value == False and config.mediaportal.filter.value == 'Grauzone'):
			config.mediaportal.filter.value = 'ALL'

		CheckPathes(self.session).checkPathes(self.cb_checkPathes)

		if (config.mediaportal.showgrauzone.value and not config.mediaportal.pingrauzone.value):
			self.a = str(random.randint(1,9))
			self.b = str(random.randint(0,9))
			self.c = str(random.randint(0,9))
			self.d = str(random.randint(0,9))
			code = "%s %s %s %s" % (self.a,self.b,self.c,self.d)
			message = _("Some of the plugins may not be legally used in your country!\n\nIf you accept this then enter the following code now:\n\n%s" % (code))
			self.session.openWithCallback(self.keyOK2, MessageBoxExt, message, MessageBoxExt.TYPE_YESNO)
		else:
			if not config.mediaportal.showgrauzone.value:
				config.mediaportal.pingrauzone.value = False
				config.mediaportal.pingrauzone.save()
			self.keySave()

	def premium(self):
		self.session.open(realdebrid_oauth2, None, calltype='user')
		self.premiumize()

	def cb_checkPathes(self):
		pass

	def keyOK2(self, answer):
		if answer is True:
			self.session.openWithCallback(self.validcode, PinInputExt, pinList = [(int(self.a+self.b+self.c+self.d))], triesEntry = self.getTriesEntry(), title = _("Please enter the correct code"), windowTitle = _("Enter code"))
		else:
			config.mediaportal.showgrauzone.value = False
			config.mediaportal.showgrauzone.save()
			config.mediaportal.pingrauzone.value = False
			config.mediaportal.pingrauzone.save()
			self.keySave()

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def validcode(self, code):
		if code:
			config.mediaportal.pingrauzone.value = True
			config.mediaportal.pingrauzone.save()
			self.keySave()
		else:
			config.mediaportal.showgrauzone.value = False
			config.mediaportal.showgrauzone.save()
			config.mediaportal.pingrauzone.value = False
			config.mediaportal.pingrauzone.save()
			self.keySave()

class MPList(Screen, HelpableScreen):

	def __init__(self, session, lastservice):
		self.lastservice = lastservice

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/haupt_Screen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/haupt_Screen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config.mediaportal.minitv.value)

		Screen.__init__(self, session)

		registerFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal%s.ttf" % config.mediaportal.font.value, "mediaportal", 100, False)
		registerFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal_clean.ttf", "mediaportal_clean", 100, False)

		if config.mediaportal.backgroundtv.value:
			config.mediaportal.minitv.value = True
			config.mediaportal.minitv.save()
			config.mediaportal.restorelastservice.value = "2"
			config.mediaportal.restorelastservice.save()
			configfile.save()
			session.nav.stopService()

		self["actions"] = ActionMap(["MP_Actions"], {
			"info" : self.showPorn
		}, -1)
		self["MP_Actions"] = HelpableActionMap(self, "MP_Actions", {
			"up"    : (self.keyUp, _("Up")),
			"down"  : (self.keyDown, _("Down")),
			"left"  : (self.keyLeft, _("Left")),
			"right" : (self.keyRight, _("Right")),
			"red"   : (self.keySimpleList, _("Open SimpleList")),
			"ok"    : (self.keyOK, _("Open selected Plugin")),
			"cancel": (self.keyCancel, _("Exit MediaPortal")),
			"nextBouquet" :	(self.keyPageDown, _("Next page")),
			"prevBouquet" :	(self.keyPageUp, _("Previous page")),
			"menu" : (self.keySetup, _("MediaPortal Setup")),
			config.mediaportal.simplelist_key.value: (self.keySimpleList, _("Open SimpleList"))
		}, -1)

		self['title'] = Label("MediaPortal")

		self['name'] = Label(_("Plugin Selection"))

		self['red'] = Label("SimpleList")

		self['PVR'] = Label(_("PVR"))
		self['Menu'] = Label(_("Menu"))
		self['Help'] = Label(_("Help"))
		self['Exit'] = Label(_("Exit"))

		self.chooseMenuList1 = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList1.l.setFont(0, gFont(mp_globals.font, mp_globals.fontsize))
		if mp_globals.videomode == 3:
			self.chooseMenuList1.l.setItemHeight(100)
		elif mp_globals.videomode == 2:
			self.chooseMenuList1.l.setItemHeight(60)
		else:
			self.chooseMenuList1.l.setItemHeight(44)
		self['mediatheken'] = self.chooseMenuList1
		self['Mediatheken'] = Label(_("Libraries"))

		self.chooseMenuList2 = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList2.l.setFont(0, gFont(mp_globals.font, mp_globals.fontsize))
		if mp_globals.videomode == 3:
			self.chooseMenuList1.l.setItemHeight(100)
		elif mp_globals.videomode == 2:
			self.chooseMenuList1.l.setItemHeight(60)
		else:
			self.chooseMenuList2.l.setItemHeight(44)
		self['grauzone'] = self.chooseMenuList2
		self['Grauzone'] = Label("")

		self.chooseMenuList3 = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList3.l.setFont(0, gFont(mp_globals.font, mp_globals.fontsize))
		if mp_globals.videomode == 3:
			self.chooseMenuList1.l.setItemHeight(100)
		elif mp_globals.videomode == 2:
			self.chooseMenuList1.l.setItemHeight(60)
		else:
			self.chooseMenuList3.l.setItemHeight(44)
		self['funsport'] = self.chooseMenuList3
		self['Funsport'] = Label(_("Fun/Music/Sports"))

		self.chooseMenuList4 = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList4.l.setFont(0, gFont(mp_globals.font, mp_globals.fontsize))
		if mp_globals.videomode == 3:
			self.chooseMenuList1.l.setItemHeight(100)
		elif mp_globals.videomode == 2:
			self.chooseMenuList1.l.setItemHeight(60)
		else:
			self.chooseMenuList4.l.setItemHeight(44)
		self['porn'] = self.chooseMenuList4
		self['Porn'] = Label("")

		self.currentlist = "porn"
		self.picload = ePicLoad()

		HelpableScreen.__init__(self)
		self.onLayoutFinish.append(self.layoutFinished)
		self.onFirstExecBegin.append(self.checkPathes)
		self.onFirstExecBegin.append(self.status)

	def layoutFinished(self):
		_hosters()
		if not mp_globals.start:
			self.close(self.session, True, self.lastservice)
		if config.mediaportal.autoupdate.value:
			checkupdate(self.session).checkforupdate()

		self.mediatheken = []
		self.grauzone = []
		self.funsport = []
		self.porn = []

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					modfile = x.get("modfile")
					confcat = x.get("confcat")
					if modfile == "music.canna" and not mechanizeModule:
						pass
					elif not config.mediaportal.showporn.value and confcat == "porn":
						pass
					else:
						gz = x.get("gz")
						if not config.mediaportal.showgrauzone.value and gz == "1":
							pass
						else:
							mod = eval("config.mediaportal." + x.get("confopt") + ".value")
							if mod:
								exec("self."+x.get("listcat")+".append(self.hauptListEntry(\""+x.get("name").replace("&amp;","&")+"\", \""+x.get("icon")+"\", \""+x.get("modfile")+"\"))")

		if len(self.porn) < 1:
			self['Porn'].hide()
		else:
			self['Porn'].setText(_("Porn"))

		if len(self.grauzone) < 1:
			self['Grauzone'].hide()
		else:
			self['Grauzone'].setText(_("Grayzone"))

		self.mediatheken.sort(key=lambda t : t[0][0].lower())
		self.grauzone.sort(key=lambda t : t[0][0].lower())
		self.funsport.sort(key=lambda t : t[0][0].lower())
		self.porn.sort(key=lambda t : t[0][0].lower())

		self.chooseMenuList1.setList(self.mediatheken)
		self.chooseMenuList2.setList(self.grauzone)
		self.chooseMenuList3.setList(self.funsport)
		self.chooseMenuList4.setList(self.porn)
		self.keyRight()

	def checkPathes(self):
		CheckPathes(self.session).checkPathes(self.cb_checkPathes)

	def cb_checkPathes(self):
		self.session.openWithCallback(self.restart, MPSetup)

	def status(self):
		if not fileExists('/tmp/radiode_sender'):
			filepath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/radiode_sender.bz2")
			newfilepath = ('/tmp/radiode_sender')
			with open(newfilepath, 'wb') as new_file, bz2.BZ2File(filepath, 'rb') as file:
				for data in iter(lambda : file.read(100 * 1024), b''):
					new_file.write(data)
		update_agent = getUserAgent()
		update_url = getUpdateUrl()
		twAgentGetPage(update_url, agent=update_agent, timeout=30).addCallback(self.checkstatus)

	def checkstatus(self, html):
		if re.search(".*?<html", html):
			return
		self.html = html
		tmp_infolines = html.splitlines()
		statusurl = tmp_infolines[4]
		update_agent = getUserAgent()
		twAgentGetPage(statusurl, agent=update_agent, timeout=30).addCallback(_status).addCallback(self.markDefect)

	def markDefect(self, dummy=None):
		reloadit = False
		for defitem in mp_globals.status:
			if config.mediaportal.version.value < defitem[1]:
				for confcatitem in [self.mediatheken, self.grauzone, self.funsport, self.porn]:
					lst = list(confcatitem)
					for n,i in enumerate(lst):
						if i[0][2] == defitem[0]:
							modlst = list(lst[n][2])
							reloadit = True
							try:
								if int(defitem[1]) > 999:
									modlst[8] = 16711680
								else:
									modlst[8] = 16776960
							except:
								pass
							lst[n][2] = tuple(modlst)
					confcatitem = tuple(lst)
		if reloadit:
			self.chooseMenuList1.setList(self.mediatheken)
			self.chooseMenuList2.setList(self.grauzone)
			self.chooseMenuList3.setList(self.funsport)
			self.chooseMenuList4.setList(self.porn)

	def hauptListEntry(self, name, icon, modfile=None):
		res = [(name, icon, modfile)]
		icon = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/icons/%s.png" % icon
		if not fileExists(icon):
			icon = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/icons/no_icon.png"
		scale = AVSwitch().getFramebufferScale()
		if mp_globals.videomode == 3:
			self.picload.setPara((105, 56, scale[0], scale[1], False, 1, "#FF000000"))
		elif mp_globals.videomode == 2:
			self.picload.setPara((105, 56, scale[0], scale[1], False, 1, "#FF000000"))
		else:
			self.picload.setPara((75, 40, scale[0], scale[1], False, 1, "#FF000000"))
		if mp_globals.isDreamOS:
			self.picload.startDecode(icon, False)
		else:
			self.picload.startDecode(icon, 0, 0, False)
		pngthumb = self.picload.getData()
		if mp_globals.videomode == 3:
			res.append(MultiContentEntryPixmapAlphaBlend(pos=(0, 0), size=(105, 60), png=pngthumb))
			res.append(MultiContentEntryText(pos=(110, 0), size=(400, 60), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
		elif mp_globals.videomode == 2:
			res.append(MultiContentEntryPixmapAlphaBlend(pos=(0, 0), size=(105, 60), png=pngthumb))
			res.append(MultiContentEntryText(pos=(110, 0), size=(400, 60), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
		else:
			res.append(MultiContentEntryPixmapAlphaBlend(pos=(0, 0), size=(75, 44), png=pngthumb))
			res.append(MultiContentEntryText(pos=(80, 0), size=(300, 44), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
		return res

	def showPorn(self):
		if config.mediaportal.showporn.value:
			config.mediaportal.showporn.value = False
			config.mediaportal.showporn.save()
			configfile.save()
			self.restart()
		else:
			self.session.openWithCallback(self.showPornOK, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))

	def showPornOK(self, pincode):
		if pincode:
			config.mediaportal.showporn.value = True
			config.mediaportal.showporn.save()
			configfile.save()
			self.restart()

	def keySetup(self):
		if config.mediaportal.setuppin.value:
			self.session.openWithCallback(self.pinok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))
		else:
			self.session.openWithCallback(self.restart, MPSetup)

	def keySimpleList(self):
		mp_globals.activeIcon = "simplelist"
		self.session.open(simplelistGenreScreen)

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def pinok(self, pincode):
		if pincode:
			self.session.openWithCallback(self.restart, MPSetup)

	def keyUp(self):
		exist = self[self.currentlist].getCurrent()
		if exist == None:
			return
		self[self.currentlist].up()
		auswahl = self[self.currentlist].getCurrent()[0][0]
		self.title = auswahl
		self['name'].setText(auswahl)

	def keyDown(self):
		exist = self[self.currentlist].getCurrent()
		if exist == None:
			return
		self[self.currentlist].down()
		auswahl = self[self.currentlist].getCurrent()[0][0]
		self.title = auswahl
		self['name'].setText(auswahl)

	def keyPageUp(self):
		self[self.currentlist].pageUp()

	def keyPageDown(self):
		self[self.currentlist].pageDown()

	def keyRight(self):
		self.cur_idx = self[self.currentlist].getSelectedIndex()
		if config.mediaportal.listmode.value == "single":
			self["mediatheken"].hide()
			self["Mediatheken"].hide()
			self["grauzone"].hide()
			self["Grauzone"].hide()
			self["funsport"].hide()
			self["Funsport"].hide()
			self["porn"].hide()
			self["Porn"].hide()
		self["mediatheken"].selectionEnabled(0)
		self["grauzone"].selectionEnabled(0)
		self["funsport"].selectionEnabled(0)
		self["porn"].selectionEnabled(0)
		if self.currentlist == "mediatheken":
			if len(self.grauzone) > 0:
				self["grauzone"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["grauzone"].show()
					self["Grauzone"].show()
				self.currentlist = "grauzone"
				cnt_tmp_ls = len(self.grauzone)
			elif len(self.funsport) > 0:
				self["funsport"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["funsport"].show()
					self["Funsport"].show()
				self.currentlist = "funsport"
				cnt_tmp_ls = len(self.funsport)
			elif len(self.porn) > 0:
				self["porn"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["porn"].show()
					self["Porn"].show()
				self.currentlist = "porn"
				cnt_tmp_ls = len(self.porn)
			else:
				self["mediatheken"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["mediatheken"].show()
					self["Mediatheken"].show()
				self.currentlist = "mediatheken"
				cnt_tmp_ls = len(self.mediatheken)
		elif self.currentlist == "grauzone":
			if len(self.funsport) > 0:
				self["funsport"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["funsport"].show()
					self["Funsport"].show()
				self.currentlist = "funsport"
				cnt_tmp_ls = len(self.funsport)
			elif len(self.porn) > 0:
				self["porn"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["porn"].show()
					self["Porn"].show()
				self.currentlist = "porn"
				cnt_tmp_ls = len(self.porn)
			elif len(self.mediatheken) > 0:
				self["mediatheken"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["mediatheken"].show()
					self["Mediatheken"].show()
				self.currentlist = "mediatheken"
				cnt_tmp_ls = len(self.mediatheken)
			else:
				self["grauzone"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["grauzone"].show()
					self["Grauzone"].show()
				self.currentlist = "grauzone"
				cnt_tmp_ls = len(self.grauzone)
		elif self.currentlist == "funsport":
			if len(self.porn) > 0:
				self["porn"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["porn"].show()
					self["Porn"].show()
				self.currentlist = "porn"
				cnt_tmp_ls = len(self.porn)
			elif len(self.mediatheken) > 0:
				self["mediatheken"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["mediatheken"].show()
					self["Mediatheken"].show()
				self.currentlist = "mediatheken"
				cnt_tmp_ls = len(self.mediatheken)
			elif len(self.grauzone) > 0:
				self["grauzone"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["grauzone"].show()
					self["Grauzone"].show()
				self.currentlist = "grauzone"
				cnt_tmp_ls = len(self.grauzone)
			else:
				self["funsport"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["funsport"].show()
					self["Funsport"].show()
				self.currentlist = "funsport"
				cnt_tmp_ls = len(self.funsport)
		elif self.currentlist == "porn":
			if len(self.mediatheken) > 0:
				self["mediatheken"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["mediatheken"].show()
					self["Mediatheken"].show()
				self.currentlist = "mediatheken"
				cnt_tmp_ls = len(self.mediatheken)
			elif len(self.grauzone) > 0:
				self["grauzone"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["grauzone"].show()
					self["Grauzone"].show()
				self.currentlist = "grauzone"
				cnt_tmp_ls = len(self.grauzone)
			elif len(self.funsport) > 0:
				self["funsport"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["funsport"].show()
					self["Funsport"].show()
				self.currentlist = "funsport"
				cnt_tmp_ls = len(self.funsport)
			else:
				self["porn"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["porn"].show()
					self["Porn"].show()
				self.currentlist = "porn"
				cnt_tmp_ls = len(self.porn)

		cnt_tmp_ls = int(cnt_tmp_ls)
		if int(self.cur_idx) < int(cnt_tmp_ls):
			self[self.currentlist].moveToIndex(int(self.cur_idx))
		else:
			idx = int(cnt_tmp_ls) -1
			self[self.currentlist].moveToIndex(int(idx))

		if cnt_tmp_ls > 0:
			auswahl = self[self.currentlist].getCurrent()[0][0]
			self.title = auswahl
			self['name'].setText(auswahl)

	def keyLeft(self):
		self.cur_idx = self[self.currentlist].getSelectedIndex()
		if config.mediaportal.listmode.value == "single":
			self["mediatheken"].hide()
			self["Mediatheken"].hide()
			self["grauzone"].hide()
			self["Grauzone"].hide()
			self["funsport"].hide()
			self["Funsport"].hide()
			self["porn"].hide()
			self["Porn"].hide()
		self["mediatheken"].selectionEnabled(0)
		self["grauzone"].selectionEnabled(0)
		self["funsport"].selectionEnabled(0)
		self["porn"].selectionEnabled(0)
		if self.currentlist == "porn":
			if len(self.funsport) > 0:
				self["funsport"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["funsport"].show()
					self["Funsport"].show()
				self.currentlist = "funsport"
				cnt_tmp_ls = len(self.funsport)
			elif len(self.grauzone) > 0:
				self["grauzone"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["grauzone"].show()
					self["Grauzone"].show()
				self.currentlist = "grauzone"
				cnt_tmp_ls = len(self.grauzone)
			elif len(self.mediatheken) > 0:
				self["mediatheken"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["mediatheken"].show()
					self["Mediatheken"].show()
				self.currentlist = "mediatheken"
				cnt_tmp_ls = len(self.mediatheken)
			else:
				self["porn"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["porn"].show()
					self["Porn"].show()
				self.currentlist = "porn"
				cnt_tmp_ls = len(self.porn)
		elif self.currentlist == "funsport":
			if len(self.grauzone) > 0:
				self["grauzone"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["grauzone"].show()
					self["Grauzone"].show()
				self.currentlist = "grauzone"
				cnt_tmp_ls = len(self.grauzone)
			elif len(self.mediatheken) > 0:
				self["mediatheken"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["mediatheken"].show()
					self["Mediatheken"].show()
				self.currentlist = "mediatheken"
				cnt_tmp_ls = len(self.mediatheken)
			elif len(self.porn) > 0:
				self["porn"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["porn"].show()
					self["Porn"].show()
				self.currentlist = "porn"
				cnt_tmp_ls = len(self.porn)
			else:
				self["funsport"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["funsport"].show()
					self["Funsport"].show()
				self.currentlist = "funsport"
				cnt_tmp_ls = len(self.funsport)
		elif self.currentlist == "grauzone":
			if len(self.mediatheken) > 0:
				self["mediatheken"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["mediatheken"].show()
					self["Mediatheken"].show()
				self.currentlist = "mediatheken"
				cnt_tmp_ls = len(self.mediatheken)
			elif len(self.porn) > 0:
				self["porn"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["porn"].show()
					self["Porn"].show()
				self.currentlist = "porn"
				cnt_tmp_ls = len(self.porn)
			elif len(self.funsport) > 0:
				self["funsport"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["funsport"].show()
					self["Funsport"].show()
				self.currentlist = "funsport"
				cnt_tmp_ls = len(self.funsport)
			else:
				self["grauzone"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["grauzone"].show()
					self["Grauzone"].show()
				self.currentlist = "grauzone"
				cnt_tmp_ls = len(self.grauzone)
		elif self.currentlist == "mediatheken":
			if len(self.porn) > 0:
				self["porn"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["porn"].show()
					self["Porn"].show()
				self.currentlist = "porn"
				cnt_tmp_ls = len(self.porn)
			elif len(self.funsport) > 0:
				self["funsport"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["funsport"].show()
					self["Funsport"].show()
				self.currentlist = "funsport"
				cnt_tmp_ls = len(self.funsport)
			elif len(self.grauzone) > 0:
				self["grauzone"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["grauzone"].show()
					self["Grauzone"].show()
				self.currentlist = "grauzone"
				cnt_tmp_ls = len(self.grauzone)
			else:
				self["mediatheken"].selectionEnabled(1)
				if config.mediaportal.listmode.value == "single":
					self["mediatheken"].show()
					self["Mediatheken"].show()
				self.currentlist = "mediatheken"
				cnt_tmp_ls = len(self.mediatheken)

		cnt_tmp_ls = int(cnt_tmp_ls)
		if int(self.cur_idx) < int(cnt_tmp_ls):
			self[self.currentlist].moveToIndex(int(self.cur_idx))
		else:
			idx = int(cnt_tmp_ls) -1
			self[self.currentlist].moveToIndex(int(idx))

		if cnt_tmp_ls > 0:
			auswahl = self[self.currentlist].getCurrent()[0][0]
			self.title = auswahl
			self['name'].setText(auswahl)

	def keyOK(self):
		if not testWebConnection():
			self.session.open(MessageBoxExt, _('No connection to the Internet available.'), MessageBoxExt.TYPE_INFO, timeout=3)
			return

		exist = self[self.currentlist].getCurrent()
		if exist == None:
			return
		auswahl = self[self.currentlist].getCurrent()[0][0]
		icon = self[self.currentlist].getCurrent()[0][1]
		mp_globals.activeIcon = icon

		self.pornscreen = None
		self.par1 = ""
		self.par2 = ""

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					confcat = x.get("confcat")
					if auswahl ==  x.get("name").replace("&amp;","&"):
						status = [item for item in mp_globals.status if item[0] == x.get("modfile")]
						if status:
							if config.mediaportal.version.value < status[0][1]:
								if not config.mediaportal.debugMode.value == "High":
									if status[0][1] == "9999":
										self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"\n\nIf someone else is willing to provide a fix for this Plugin then please get in contact with us.") % status[0][2], MessageBoxExt.TYPE_INFO)
									else:
										self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"") % status[0][2], MessageBoxExt.TYPE_INFO)
									return
						param = ""
						param1 = x.get("param1")
						param2 = x.get("param2")
						kids = x.get("kids")
						if param1 != "":
							param = ", \"" + param1 + "\""
							exec("self.par1 = \"" + x.get("param1") + "\"")
						if param2 != "":
							param = param + ", \"" + param2 + "\""
							exec("self.par2 = \"" + x.get("param2") + "\"")
						if confcat == "porn":
							exec("self.pornscreen = " + x.get("screen") + "")
						elif kids != "1" and config.mediaportal.kidspin.value:
							exec("self.pornscreen = " + x.get("screen") + "")
						else:
							exec("self.session.open(" + x.get("screen") + param + ")")
		if self.pornscreen:
			if config.mediaportal.pornpin.value:
				if pincheck.pin_entered == False:
					self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))
				else:
					if self.par1 == "":
						self.session.open(self.pornscreen)
					elif self.par2 == "":
						self.session.open(self.pornscreen, self.par1)
					else:
						self.session.open(self.pornscreen, self.par1, self.par2)
			else:
				if self.par1 == "":
					self.session.open(self.pornscreen)
				elif self.par2 == "":
					self.session.open(self.pornscreen, self.par1)
				else:
					self.session.open(self.pornscreen, self.par1, self.par2)

	def pincheckok(self, pincode):
		if pincode:
			pincheck.pinEntered()
			if self.par1 == "":
				self.session.open(self.pornscreen)
			elif self.par2 == "":
				self.session.open(self.pornscreen, self.par1)
			else:
				self.session.open(self.pornscreen, self.par1, self.par2)

	def keyCancel(self):
		self.close(self.session, True, self.lastservice)

	def restart(self):
		if autoStartTimer is not None:
			autoStartTimer.update()
		self.close(self.session, False, self.lastservice)

class MPpluginSort(Screen):

	def __init__(self, session):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/pluginSortScreen.xml" % (self.skin_path, config.mediaportal.skin.value)

		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/pluginSortScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config.mediaportal.minitv.value)

		Screen.__init__(self, session)

		self.list = []
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont(mp_globals.font, mp_globals.fontsize))
		self.chooseMenuList.l.setItemHeight(mp_globals.fontsize + 2 * mp_globals.sizefactor)
		self["config2"] = self.chooseMenuList
		self.plugin_path = ""
		self.selected = False
		self.move_on = False

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok":	self.select,
			"cancel": self.keyCancel
		}, -1)

		self.readconfig()

	def select(self):
		if not self.selected:
			self.last_newidx = self["config2"].getSelectedIndex()
			self.last_plugin_name = self["config2"].getCurrent()[0][0]
			self.last_plugin_pic = self["config2"].getCurrent()[0][1]
			self.last_plugin_genre = self["config2"].getCurrent()[0][2]
			self.last_plugin_hits = self["config2"].getCurrent()[0][3]
			self.last_plugin_msort = self["config2"].getCurrent()[0][4]
			print "Select:", self.last_plugin_name, self.last_newidx
			self.selected = True
			self.readconfig()
		else:
			self.now_newidx = self["config2"].getSelectedIndex()
			self.now_plugin_name = self["config2"].getCurrent()[0][0]
			self.now_plugin_pic = self["config2"].getCurrent()[0][1]
			self.now_plugin_genre = self["config2"].getCurrent()[0][2]
			self.now_plugin_hits = self["config2"].getCurrent()[0][3]
			self.now_plugin_msort = self["config2"].getCurrent()[0][4]

			count_move = 0
			config_tmp = open("/etc/enigma2/mp_pluginliste.tmp" , "w")
			# del element from list
			del self.config_list_select[int(self.last_newidx)];
			# add element to list at the right place
			self.config_list_select.insert(int(self.now_newidx), (self.last_plugin_name, self.last_plugin_pic, self.last_plugin_genre, self.last_plugin_hits, self.now_newidx));

			# liste neu nummerieren
			for (name, pic, genre, hits, msort) in self.config_list_select:
				count_move += 1
				config_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (name, pic, genre, hits, count_move))

			print "change:", self.last_newidx+1, "with", self.now_newidx+1, "total:", len(self.config_list_select)

			config_tmp.close()
			shutil.move("/etc/enigma2/mp_pluginliste.tmp", "/etc/enigma2/mp_pluginliste")
			self.selected = False
			self.readconfig()

	def readconfig(self):
		config_read = open("/etc/enigma2/mp_pluginliste","r")
		self.config_list = []
		self.config_list_select = []
		print "Filter:", config.mediaportal.filter.value
		for line in config_read.readlines():
			ok = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', line, re.S)
			if ok:
				(name, pic, genre, hits, msort) = ok[0]
				if config.mediaportal.filter.value != "ALL":
					if genre == config.mediaportal.filter.value:
						self.config_list_select.append((name, pic, genre, hits, msort))
						self.config_list.append(self.show_menu(name, pic, genre, hits, msort))
				else:
					self.config_list_select.append((name, pic, genre, hits, msort))
					self.config_list.append(self.show_menu(name, pic, genre, hits, msort))

		self.config_list.sort(key=lambda x: int(x[0][4]))
		self.config_list_select.sort(key=lambda x: int(x[4]))
		self.chooseMenuList.setList(self.config_list)
		config_read.close()

	def show_menu(self, name, pic, genre, hits, msort):
		res = [(name, pic, genre, hits, msort)]
		if mp_globals.videomode == 3:
			res.append(MultiContentEntryText(pos=(80, 0), size=(500, 30), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			if self.selected and name == self.last_plugin_name:
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(45, 3), size=(24, 24), png=loadPNG("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/select.png")))
		elif mp_globals.videomode == 2:
			res.append(MultiContentEntryText(pos=(80, 0), size=(500, 30), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			if self.selected and name == self.last_plugin_name:
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(45, 3), size=(24, 24), png=loadPNG("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/select.png")))
		else:
			res.append(MultiContentEntryText(pos=(80, 0), size=(500, 23), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			if self.selected and name == self.last_plugin_name:
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(45, 2), size=(21, 21), png=loadPNG("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/select.png")))
		return res

	def keyCancel(self):
		config.mediaportal.sortplugins.value = "user"
		self.close()

class MPWall(Screen, HelpableScreen):

	def __init__(self, session, lastservice, filter):
		self.lastservice = lastservice
		self.wallbw = False
		self.wallzoom = False

		self.plugin_liste = []

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					modfile = x.get("modfile")
					confcat = x.get("confcat")
					if modfile == "music.canna" and not mechanizeModule:
						pass
					elif not config.mediaportal.showporn.value and confcat == "porn":
						pass
					else:
						gz = x.get("gz")
						if not config.mediaportal.showgrauzone.value and gz == "1":
							pass
						else:
							mod = eval("config.mediaportal." + x.get("confopt") + ".value")
							if mod:
								y = eval("self.plugin_liste.append((\"" + x.get("name").replace("&amp;","&") + "\", \"" + x.get("icon") + "\", \"" + x.get("filter") + "\"))")

		if len(self.plugin_liste) == 0:
			self.plugin_liste.append(("","","Mediathek"))

		# Porn
		if (config.mediaportal.showporn.value == False and config.mediaportal.filter.value == 'Porn'):
			config.mediaportal.filter.value = 'ALL'

		# Grauzone
		if (config.mediaportal.showgrauzone.value == False and config.mediaportal.filter.value == 'Grauzone'):
			config.mediaportal.filter.value = 'ALL'

		# Plugin Sortierung
		if config.mediaportal.sortplugins != "default":

			# Erstelle Pluginliste falls keine vorhanden ist.
			self.sort_plugins_file = "/etc/enigma2/mp_pluginliste"
			if not fileExists(self.sort_plugins_file):
				print "Erstelle Wall-Pluginliste."
				open(self.sort_plugins_file,"w").close()

			pluginliste_leer = os.path.getsize(self.sort_plugins_file)
			if pluginliste_leer == 0:
				print "1st time - Schreibe Wall-Pluginliste."
				first_count = 0
				read_pluginliste = open(self.sort_plugins_file,"a")
				for name,picname,genre in self.plugin_liste:
					read_pluginliste.write('"%s" "%s" "%s" "%s" "%s"\n' % (name, picname, genre, "0", str(first_count)))
					first_count += 1
				read_pluginliste.close()
				print "Wall-Pluginliste wurde erstellt."

			# Lese Pluginliste ein.
			if fileExists(self.sort_plugins_file):

				count_sort_plugins_file = len(open(self.sort_plugins_file).readlines())
				count_plugin_liste = len(self.plugin_liste)

				if int(count_plugin_liste) != int(count_sort_plugins_file):
					print "Ein Plugin wurde aktiviert oder deaktiviert.. erstelle neue pluginliste."

					read_pluginliste_tmp = open(self.sort_plugins_file+".tmp","w")
					read_pluginliste = open(self.sort_plugins_file,"r")
					p_dupeliste = []

					for rawData in read_pluginliste.readlines():
						data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)

						if data:
							(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
							pop_count = 0
							for pname, ppic, pgenre in self.plugin_liste:
								if p_name not in p_dupeliste:
									if p_name == pname:
										read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, pgenre, p_hits, p_sort))
										p_dupeliste.append((p_name))
										self.plugin_liste.pop(int(pop_count))

									pop_count += 1

					if len(self.plugin_liste) != 0:
						for pname, ppic, pgenre in self.plugin_liste:
							read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (pname, ppic, pgenre, "0", "99"))

					read_pluginliste.close()
					read_pluginliste_tmp.close()
					shutil.move(self.sort_plugins_file+".tmp", self.sort_plugins_file)

				self.new_pluginliste = []
				read_pluginliste = open(self.sort_plugins_file,"r")
				for rawData in read_pluginliste.readlines():
					data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
					if data:
						(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
						self.new_pluginliste.append((p_name, p_picname, p_genre, p_hits, p_sort))
				read_pluginliste.close()

			# Sortieren nach hits
			if config.mediaportal.sortplugins.value == "hits":
				self.new_pluginliste.sort(key=lambda x: int(x[3]))
				self.new_pluginliste.reverse()

			# Sortieren nach abcde..
			elif config.mediaportal.sortplugins.value == "abc":
				self.new_pluginliste.sort(key=lambda x: str(x[0]).lower())

			elif config.mediaportal.sortplugins.value == "user":
				self.new_pluginliste.sort(key=lambda x: int(x[4]))

			self.plugin_liste = self.new_pluginliste

		skincontent = ""

		if config.mediaportal.wallmode.value == "bw":
			self.wallbw = True
		elif config.mediaportal.wallmode.value == "bw_zoom":
			self.wallbw = True
			self.wallzoom = True
		elif config.mediaportal.wallmode.value == "color_zoom":
			self.wallzoom = True

		if mp_globals.videomode == 3:
			screenwidth = 3840
			posxstart = 85
			posxplus = 220
			posystart = 310
			posyplus = 122
			iconsize = "210,112"
			iconsizezoom = "308,190"
			zoomoffsetx = 49
			zoomoffsety = 39
		elif mp_globals.videomode == 2:
			screenwidth = 1920
			posxstart = 85
			posxplus = 220
			posystart = 310
			posyplus = 122
			iconsize = "210,112"
			iconsizezoom = "308,190"
			zoomoffsetx = 49
			zoomoffsety = 39
		else:
			screenwidth = 1280
			posxstart = 22
			posxplus = 155
			posystart = 210
			posyplus = 85
			iconsize = "150,80"
			iconsizezoom = "220,136"
			zoomoffsetx = 35
			zoomoffsety = 28
		posx = posxstart
		posy = posystart
		for x in range(1,len(self.plugin_liste)+1):
			skincontent += "<widget name=\"zeile" + str(x) + "\" position=\"" + str(posx) + "," + str(posy) + "\" size=\"" + iconsize + "\" zPosition=\"1\" transparent=\"1\" alphatest=\"blend\" />"
			if self.wallzoom:
				skincontent += "<widget name=\"zeile_bw" + str(x) + "\" position=\"" + str(posx-zoomoffsetx) + "," + str(posy-zoomoffsety) + "\" size=\"" + iconsizezoom + "\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
			elif self.wallbw:
				skincontent += "<widget name=\"zeile_bw" + str(x) + "\" position=\"" + str(posx) + "," + str(posy) + "\" size=\"" + iconsize + "\" zPosition=\"1\" transparent=\"1\" alphatest=\"blend\" />"
			posx += posxplus
			if x in [8, 16, 24, 32, 48, 56, 64, 72, 88, 96, 104, 112, 128, 136, 144, 152, 168, 176, 184, 192]:
				posx = posxstart
				posy += posyplus
			elif x in [40, 80, 120, 160, 200]:
				posx = posxstart
				posy = posystart

		# Page Style
		if config.mediaportal.pagestyle.value == "Graphic":
			self.dump_liste_page_tmp = self.plugin_liste
			if config.mediaportal.filter.value != "ALL":
				self.plugin_liste_page_tmp = []
				self.plugin_liste_page_tmp = [x for x in self.dump_liste_page_tmp if re.search(config.mediaportal.filter.value, x[2])]
			else:
				self.plugin_liste_page_tmp = self.plugin_liste

			if len(self.plugin_liste_page_tmp) != 0:
				self.counting_pages = int(round(float((len(self.plugin_liste_page_tmp)-1) / 40) + 0.5))
				print "COUNTING PAGES:", self.counting_pages
				pagebar_size = self.counting_pages * 26 + (self.counting_pages-1) * 4
				start_pagebar = int(screenwidth / 2 - pagebar_size / 2)

				for x in range(1,self.counting_pages+1):
					if mp_globals.videomode == 3:
						normal = 960
					elif mp_globals.videomode == 2:
						normal = 960
					elif config.mediaportal.skin.value == "original":
						normal = 650
					else:
						normal = 669
					skincontent += "<widget name=\"page_empty" + str(x) + "\" position=\"" + str(start_pagebar) + "," + str(normal) + "\" size=\"26,26\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
					skincontent += "<widget name=\"page_sel" + str(x) + "\" position=\"" + str(start_pagebar) + "," + str(normal) + "\" size=\"26,26\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
					start_pagebar += 30

		self.skin_dump = ""
		if self.wallzoom:
			pass
		else:
			self.skin_dump += "<widget name=\"frame\" position=\"" + str(posxstart) + "," + str(posystart) + "\" size=\"" + iconsize + "\" zPosition=\"3\" transparent=\"1\" alphatest=\"blend\" />"
		self.skin_dump += skincontent
		self.skin_dump += "</screen>"

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		self.images_path = "%s/%s/images" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(self.images_path):
			self.images_path = self.skin_path + mp_globals.skinFallback + "/images"

		path = "%s/%s/hauptScreenWall.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/hauptScreenWall.xml"

		with open(path, "r") as f:
			self.skin_dump2 = f.read()
			self.skin_dump2 += self.skin_dump
			self.skin = self.skin_dump2
			f.close()

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config.mediaportal.minitv.value)

		Screen.__init__(self, session)

		registerFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal%s.ttf" % config.mediaportal.font.value, "mediaportal", 100, False)
		registerFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal_clean.ttf", "mediaportal_clean", 100, False)

		if config.mediaportal.backgroundtv.value:
			config.mediaportal.minitv.value = True
			config.mediaportal.minitv.save()
			config.mediaportal.restorelastservice.value = "2"
			config.mediaportal.restorelastservice.save()
			configfile.save()
			session.nav.stopService()

		self["actions"] = ActionMap(["MP_Actions"], {
			"info" : self.showPorn,
			"0": boundFunction(self.gotFilter, "ALL"),
			"1": boundFunction(self.gotFilter, "Mediathek"),
			"2": boundFunction(self.gotFilter, "Fun"),
			"3": boundFunction(self.gotFilter, "Music"),
			"4": boundFunction(self.gotFilter, "Sport"),
			"5": boundFunction(self.gotFilter, "Grauzone"),
			"6": boundFunction(self.gotFilter, "Porn")
		}, -1)
		self["MP_Actions"] = HelpableActionMap(self, "MP_Actions", {
			"up"    : (self.keyUp, _("Up")),
			"down"  : (self.keyDown, _("Down")),
			"left"  : (self.keyLeft, _("Left")),
			"right" : (self.keyRight, _("Right")),
			"blue"  : (self.changeFilter, _("Change filter")),
			"green" : (self.chSort, _("Change sort order")),
			"yellow": (self.manuelleSortierung, _("Manual sorting")),
			"red"   : (self.keySimpleList, _("Open SimpleList")),
			"ok"    : (self.keyOK, _("Open selected Plugin")),
			"cancel": (self.keyCancel, _("Exit MediaPortal")),
			"nextBouquet" :	(self.page_next, _("Next page")),
			"prevBouquet" :	(self.page_back, _("Previous page")),
			"menu" : (self.keySetup, _("MediaPortal Setup")),
			"leavePlayer": (self.openGlWatchlist, _("Global Watchlist")),
			config.mediaportal.simplelist_key.value: (self.keySimpleList, _("Open SimpleList"))
		}, -1)

		self['name'] = Label(_("Plugin Selection"))
		self['tipps'] = Label("")
		self['red'] = Label("SimpleList")
		self['green'] = Label("")
		self['yellow'] = Label(_("Sort"))
		self['blue'] = Label("")
		self['CH+'] = Label(_("CH+"))
		self['CH-'] = Label(_("CH-"))
		self['PVR'] = Label(_("PVR"))
		self['Exit'] = Label(_("Exit"))
		self['Help'] = Label(_("Help"))
		self['Menu'] = Label(_("Menu"))
		self['page'] = Label("")
		self["frame"] = MovingPixmap()
		self['tipps_bg'] = Pixmap()
		self['tipps_bg'].hide()

		for x in range(1,len(self.plugin_liste)+1):
			if self.wallbw or self.wallzoom:
				self["zeile"+str(x)] = Pixmap()
				self["zeile"+str(x)].show()
				self["zeile_bw"+str(x)] = Pixmap()
				self["zeile_bw"+str(x)].hide()
			else:
				self["zeile"+str(x)] = Pixmap()
				self["zeile"+str(x)].show()

		# Apple Page Style
		if config.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			for x in range(1,self.counting_pages+1):
				self["page_empty"+str(x)] = Pixmap()
				self["page_empty"+str(x)].show()
				self["page_sel"+str(x)] = Pixmap()
				self["page_sel"+str(x)].show()

		if config.mediaportal.showTipps.value:
			self['tipps_bg'].show()
			self.loadTipp = eTimer()
			if mp_globals.isDreamOS:
				self.loadTipp_conn = self.loadTipp.timeout.connect(self.randomTipp)
			else:
				self.loadTipp.callback.append(self.randomTipp)
			self.loadTipp.start(20000)

		self.selektor_index = 1
		self.select_list = 0
		self.picload = ePicLoad()

		HelpableScreen.__init__(self)
		self.onFirstExecBegin.append(self._onFirstExecBegin)
		self.onFirstExecBegin.append(self.checkPathes)
		self.onFirstExecBegin.append(self.status)

	def openGlWatchlist(self):
		self.session.open(globalWatchlist)

	def randomTipp(self):
		lines = []
		tippFile = "%s/resources/tipps.txt" % self.plugin_path
		if fileExists(tippFile):
			with open(tippFile, "r") as tipps:
				lines = tipps.readlines();
				rline = random.randrange(0, len(lines))
				self['tipps'].setText(lines[rline].strip('\n'))

	def checkPathes(self):
		CheckPathes(self.session).checkPathes(self.cb_checkPathes)

	def cb_checkPathes(self):
		self.session.openWithCallback(self.restart, MPSetup)

	def status(self):
		if not fileExists('/tmp/radiode_sender'):
			filepath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/radiode_sender.bz2")
			newfilepath = ('/tmp/radiode_sender')
			with open(newfilepath, 'wb') as new_file, bz2.BZ2File(filepath, 'rb') as file:
				for data in iter(lambda : file.read(100 * 1024), b''):
					new_file.write(data)
		update_agent = getUserAgent()
		update_url = getUpdateUrl()
		twAgentGetPage(update_url, agent=update_agent, timeout=30).addCallback(self.checkstatus)

	def checkstatus(self, html):
		if re.search(".*?<html", html):
			return
		self.html = html
		tmp_infolines = html.splitlines()
		statusurl = tmp_infolines[4]
		update_agent = getUserAgent()
		twAgentGetPage(statusurl, agent=update_agent, timeout=30).addCallback(_status)

	def manuelleSortierung(self):
		if config.mediaportal.filter.value == 'ALL':
			self.session.openWithCallback(self.restart, MPpluginSort)
		else:
			self.session.open(MessageBoxExt, _('Ordering is only possible with filter "ALL".'), MessageBoxExt.TYPE_INFO, timeout=3)

	def hit_plugin(self, pname):
		if fileExists(self.sort_plugins_file):
			read_pluginliste = open(self.sort_plugins_file,"r")
			read_pluginliste_tmp = open(self.sort_plugins_file+".tmp","w")
			for rawData in read_pluginliste.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
					if pname == p_name:
						new_hits = int(p_hits)+1
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, p_genre, str(new_hits), p_sort))
					else:
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, p_genre, p_hits, p_sort))
			read_pluginliste.close()
			read_pluginliste_tmp.close()
			shutil.move(self.sort_plugins_file+".tmp", self.sort_plugins_file)

	def _onFirstExecBegin(self):
		_hosters()
		if not mp_globals.start:
			self.close(self.session, True, self.lastservice)
		if config.mediaportal.autoupdate.value:
			checkupdate(self.session).checkforupdate()

		if config.mediaportal.filter.value == "ALL":
			name = _("ALL")
		elif config.mediaportal.filter.value == "Mediathek":
			name = _("Libraries")
		elif config.mediaportal.filter.value == "Grauzone":
			name = _("Grayzone")
		elif config.mediaportal.filter.value == "Fun":
			name = _("Fun")
		elif config.mediaportal.filter.value == "Music":
			name = _("Music")
		elif config.mediaportal.filter.value == "Sport":
			name = _("Sports")
		elif config.mediaportal.filter.value == "Porn":
			name = _("Porn")
		self['blue'].setText(name)
		self.sortplugin = config.mediaportal.sortplugins.value
		if self.sortplugin == "hits":
			self.sortplugin = "Hits"
		elif self.sortplugin == "abc":
			self.sortplugin = "ABC"
		elif self.sortplugin == "user":
			self.sortplugin = "User"
		self['green'].setText(self.sortplugin)
		self.dump_liste = self.plugin_liste
		if config.mediaportal.filter.value != "ALL":
			self.plugin_liste = []
			self.plugin_liste = [x for x in self.dump_liste if re.search(config.mediaportal.filter.value, x[2])]
		if len(self.plugin_liste) == 0:
			self.chFilter()
			if config.mediaportal.filter.value == "ALL":
				name = _("ALL")
			elif config.mediaportal.filter.value == "Mediathek":
				name = _("Libraries")
			elif config.mediaportal.filter.value == "Grauzone":
				name = _("Grayzone")
			elif config.mediaportal.filter.value == "Fun":
				name = _("Fun")
			elif config.mediaportal.filter.value == "Music":
				name = _("Music")
			elif config.mediaportal.filter.value == "Sport":
				name = _("Sports")
			elif config.mediaportal.filter.value == "Porn":
				name = _("Porn")
			self['blue'].setText(name)

		if config.mediaportal.sortplugins.value == "hits":
			self.plugin_liste.sort(key=lambda x: int(x[3]))
			self.plugin_liste.reverse()
		elif config.mediaportal.sortplugins.value == "abc":
			self.plugin_liste.sort(key=lambda t : t[0].lower())
		elif config.mediaportal.sortplugins.value == "user":
			self.plugin_liste.sort(key=lambda x: int(x[4]))

		poster_path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/icons/Selektor_%s.png" % config.mediaportal.selektor.value

		scale = AVSwitch().getFramebufferScale()
		if mp_globals.videomode == 3:
			self.picload.setPara((210, 112, scale[0], scale[1], True, 1, "#FF000000"))
		elif mp_globals.videomode == 2:
			self.picload.setPara((210, 112, scale[0], scale[1], True, 1, "#FF000000"))
		else:
			self.picload.setPara((150, 80, scale[0], scale[1], True, 1, "#FF000000"))
		if mp_globals.isDreamOS:
			self.picload.startDecode(poster_path, False)
		else:
			self.picload.startDecode(poster_path, 0, 0, False)

		self["frame"].instance.setPixmap(gPixmapPtr())
		pic = self.picload.getData()
		if pic != None:
			self["frame"].instance.setPixmap(pic)

		for x in range(1,len(self.plugin_liste)+1):
			postername = self.plugin_liste[int(x)-1][1]
			if self.wallbw:
				poster_path = "%s/%s.png" % ("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/icons_bw", postername)
			else:
				poster_path = "%s/%s.png" % ("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/icons", postername)

			if not fileExists(poster_path):
				poster_path = "%s/icons/no_icon.png" % self.plugin_path

			scale = AVSwitch().getFramebufferScale()
			if mp_globals.videomode == 3:
				self.picload.setPara((210, 112, scale[0], scale[1], True, 1, "#FF000000"))
			elif mp_globals.videomode == 2:
				self.picload.setPara((210, 112, scale[0], scale[1], True, 1, "#FF000000"))
			else:
				self.picload.setPara((150, 80, scale[0], scale[1], True, 1, "#FF000000"))
			if mp_globals.isDreamOS:
				self.picload.startDecode(poster_path, False)
			else:
				self.picload.startDecode(poster_path, 0, 0, False)

			self["zeile"+str(x)].instance.setPixmap(gPixmapPtr())
			self["zeile"+str(x)].hide()
			pic = self.picload.getData()
			if pic != None:
				self["zeile"+str(x)].instance.setPixmap(pic)
				if x <= 40:
					self["zeile"+str(x)].show()

			if self.wallzoom:
				poster_path = "%s/%s.png" % ("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/icons_zoom", postername)
				if not fileExists(poster_path):
					poster_path = "%s/icons_zoom/no_icon.png" % self.plugin_path

				scale = AVSwitch().getFramebufferScale()
				if mp_globals.videomode == 3:
					self.picload.setPara((308, 190, scale[0], scale[1], True, 1, "#FF000000"))
				elif mp_globals.videomode == 2:
					self.picload.setPara((308, 190, scale[0], scale[1], True, 1, "#FF000000"))
				else:
					self.picload.setPara((220, 136, scale[0], scale[1], True, 1, "#FF000000"))
				if mp_globals.isDreamOS:
					self.picload.startDecode(poster_path, False)
				else:
					self.picload.startDecode(poster_path, 0, 0, False)

				self["zeile_bw"+str(x)].instance.setPixmap(gPixmapPtr())
				self["zeile_bw"+str(x)].hide()
				pic = self.picload.getData()
				if pic != None:
					self["zeile_bw"+str(x)].instance.setPixmap(pic)
					if x <= 40:
						self["zeile_bw"+str(x)].hide()

			elif self.wallbw:
				poster_path = "%s/%s.png" % ("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/icons", postername)
				if not fileExists(poster_path):
					poster_path = "%s/icons/no_icon.png" % self.plugin_path

				scale = AVSwitch().getFramebufferScale()
				if mp_globals.videomode == 3:
					self.picload.setPara((210, 112, scale[0], scale[1], True, 1, "#FF000000"))
				elif mp_globals.videomode == 2:
					self.picload.setPara((210, 112, scale[0], scale[1], True, 1, "#FF000000"))
				else:
					self.picload.setPara((150, 80, scale[0], scale[1], True, 1, "#FF000000"))
				if mp_globals.isDreamOS:
					self.picload.startDecode(poster_path, False)
				else:
					self.picload.startDecode(poster_path, 0, 0, False)

				self["zeile_bw"+str(x)].instance.setPixmap(gPixmapPtr())
				self["zeile_bw"+str(x)].hide()
				pic = self.picload.getData()
				if pic != None:
					self["zeile_bw"+str(x)].instance.setPixmap(pic)
					if x <= 40:
						self["zeile_bw"+str(x)].hide()

		if config.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			for x in range(1,self.counting_pages+1):
				poster_path = "%s/page_select.png" % (self.images_path)
				self["page_sel"+str(x)].instance.setPixmap(gPixmapPtr())
				self["page_sel"+str(x)].hide()
				pic = LoadPixmap(cached=True, path=poster_path)
				if pic != None:
					self["page_sel"+str(x)].instance.setPixmap(pic)
					if x == 1:
						self["page_sel"+str(x)].show()

			for x in range(1,self.counting_pages+1):
				poster_path = "%s/page.png" % (self.images_path)
				self["page_empty"+str(x)].instance.setPixmap(gPixmapPtr())
				self["page_empty"+str(x)].hide()
				pic = LoadPixmap(cached=True, path=poster_path)
				if pic != None:
					self["page_empty"+str(x)].instance.setPixmap(pic)
					if x > 1:
						self["page_empty"+str(x)].show()

		self.widget_list()
		if config.mediaportal.showTipps.value:
			self.randomTipp()

	def widget_list(self):
		count = 1
		counting = 1
		self.mainlist = []
		list_dummy = []
		self.plugin_counting = len(self.plugin_liste)

		for x in range(1,int(self.plugin_counting)+1):
			if count == 40:
				count += 1
				counting += 1
				list_dummy.append(x)
				self.mainlist.append(list_dummy)
				count = 1
				list_dummy = []
			else:
				count += 1
				counting += 1
				list_dummy.append(x)
				if int(counting) == int(self.plugin_counting)+1:
					self.mainlist.append(list_dummy)

		if config.mediaportal.pagestyle.value == "Graphic":
			pageinfo = ""
		else:
			pageinfo = _("Page") + " %s / %s" % (self.select_list+1, len(self.mainlist))
		self['page'].setText(pageinfo)
		select_nr = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
		plugin_name = self.plugin_liste[int(select_nr)-1][0]
		self['name'].setText(plugin_name)
		self.hideshow2()

	def move_selector(self):
		select_nr = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
		plugin_name = self.plugin_liste[int(select_nr)-1][0]
		self['name'].setText(plugin_name)
		if not self.wallzoom:
			position = self["zeile"+str(self.selektor_index)].instance.position()
			self["frame"].moveTo(position.x(), position.y(), 1)
			self["frame"].show()
			self["frame"].startMoving()

	def keyOK(self):
		if not testWebConnection():
			self.session.open(MessageBoxExt, _('No connection to the Internet available.'), MessageBoxExt.TYPE_INFO, timeout=3)
			return

		if self.check_empty_list():
			return

		select_nr = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
		auswahl = self.plugin_liste[int(select_nr)-1][0]
		icon = self.plugin_liste[int(select_nr)-1][1]
		mp_globals.activeIcon = icon
		print "Plugin:", auswahl

		self.pornscreen = None
		self.par1 = ""
		self.par2 = ""
		self.hit_plugin(auswahl)

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					confcat = x.get("confcat")
					if auswahl ==  x.get("name").replace("&amp;","&"):
						status = [item for item in mp_globals.status if item[0] == x.get("modfile")]
						if status:
							if config.mediaportal.version.value < status[0][1]:
								if not config.mediaportal.debugMode.value == "High":
									if status[0][1] == "9999":
										self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"\n\nIf someone else is willing to provide a fix for this Plugin then please get in contact with us.") % status[0][2], MessageBoxExt.TYPE_INFO)
									else:
										self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"") % status[0][2], MessageBoxExt.TYPE_INFO)
									return
						param = ""
						param1 = x.get("param1")
						param2 = x.get("param2")
						kids = x.get("kids")
						if param1 != "":
							param = ", \"" + param1 + "\""
							exec("self.par1 = \"" + x.get("param1") + "\"")
						if param2 != "":
							param = param + ", \"" + param2 + "\""
							exec("self.par2 = \"" + x.get("param2") + "\"")
						if confcat == "porn":
							exec("self.pornscreen = " + x.get("screen") + "")
						elif kids != "1" and config.mediaportal.kidspin.value:
							exec("self.pornscreen = " + x.get("screen") + "")
						else:
							exec("self.session.open(" + x.get("screen") + param + ")")
		if self.pornscreen:
			if config.mediaportal.pornpin.value:
				if pincheck.pin_entered == False:
					self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))
				else:
					if self.par1 == "":
						self.session.open(self.pornscreen)
					elif self.par2 == "":
						self.session.open(self.pornscreen, self.par1)
					else:
						self.session.open(self.pornscreen, self.par1, self.par2)
			else:
				if self.par1 == "":
					self.session.open(self.pornscreen)
				elif self.par2 == "":
					self.session.open(self.pornscreen, self.par1)
				else:
					self.session.open(self.pornscreen, self.par1, self.par2)

	def pincheckok(self, pincode):
		if pincode:
			pincheck.pinEntered()
			if self.par1 == "":
				self.session.open(self.pornscreen)
			elif self.par2 == "":
				self.session.open(self.pornscreen, self.par1)
			else:
				self.session.open(self.pornscreen, self.par1, self.par2)

	def hideshow(self):
		if self.wallbw or self.wallzoom:
			test = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
			self["zeile_bw"+str(test)].hide()
			self["zeile"+str(test)].show()

	def hideshow2(self):
		if self.wallbw or self.wallzoom:
			test = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
			self["zeile_bw"+str(test)].show()
			self["zeile"+str(test)].hide()

	def	keyLeft(self):
		if self.check_empty_list():
			return
		if self.selektor_index > 1:
			self.hideshow()
			self.selektor_index -= 1
			self.move_selector()
			self.hideshow2()
		else:
			self.page_back()

	def	keyRight(self):
		if self.check_empty_list():
			return
		if self.selektor_index < 40 and self.selektor_index != len(self.mainlist[int(self.select_list)]):
			self.hideshow()
			self.selektor_index += 1
			self.move_selector()
			self.hideshow2()
		else:
			self.page_next()

	def keyUp(self):
		if self.check_empty_list():
			return
		if self.selektor_index-8 > 1:
			self.hideshow()
			self.selektor_index -=8
			self.move_selector()
			self.hideshow2()
		else:
			self.hideshow()
			self.selektor_index = 1
			self.move_selector()
			self.hideshow2()

	def keyDown(self):
		if self.check_empty_list():
			return
		if self.selektor_index+8 <= len(self.mainlist[int(self.select_list)]):
			self.hideshow()
			self.selektor_index +=8
			self.move_selector()
			self.hideshow2()
		else:
			self.hideshow()
			self.selektor_index = len(self.mainlist[int(self.select_list)])
			self.move_selector()
			self.hideshow2()

	def page_next(self):
		if self.check_empty_list():
			return
		if self.select_list < len(self.mainlist)-1:
			self.hideshow()
			self.paint_hide()
			self.select_list += 1
			self.paint_new()

	def page_back(self):
		if self.check_empty_list():
			return
		if self.select_list > 0:
			self.hideshow()
			self.paint_hide()
			self.select_list -= 1
			self.paint_new_last()

	def check_empty_list(self):
		if len(self.plugin_liste) == 0:
			self['name'].setText('Keine Plugins der Kategorie %s aktiviert!' % config.mediaportal.filter.value)
			self["frame"].hide()
			return True
		else:
			return False

	def paint_hide(self):
		for x in self.mainlist[int(self.select_list)]:
			self["zeile"+str(x)].hide()

	def paint_new_last(self):
		if config.mediaportal.pagestyle.value == "Graphic":
			pageinfo = ""
		else:
			pageinfo = _("Page") + " %s / %s" % (self.select_list+1, len(self.mainlist))
		self['page'].setText(pageinfo)
		self.selektor_index = len(self.mainlist[int(self.select_list)])
		self.move_selector()
		# Apple Page Style
		if config.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			self.refresh_apple_page_bar()

		for x in self.mainlist[int(self.select_list)]:
			self["zeile"+str(x)].show()

		self.hideshow2()

	def paint_new(self):
		if config.mediaportal.pagestyle.value == "Graphic":
			pageinfo = ""
		else:
			pageinfo = _("Page") + " %s / %s" % (self.select_list+1, len(self.mainlist))
		self['page'].setText(pageinfo)
		self.selektor_index = 1
		self.move_selector()
		# Apple Page Style
		if config.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			self.refresh_apple_page_bar()

		for x in self.mainlist[int(self.select_list)]:
			self["zeile"+str(x)].show()

		self.hideshow2()

	# Apple Page Style
	def refresh_apple_page_bar(self):
		for x in range(1,len(self.mainlist)+1):
			if x == self.select_list+1:
				self["page_empty"+str(x)].hide()
				self["page_sel"+str(x)].show()
			else:
				self["page_sel"+str(x)].hide()
				self["page_empty"+str(x)].show()

	def keySetup(self):
		if config.mediaportal.setuppin.value:
			self.session.openWithCallback(self.pinok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))
		else:
			self.session.openWithCallback(self.restart, MPSetup)

	def keySimpleList(self):
		mp_globals.activeIcon = "simplelist"
		self.session.open(simplelistGenreScreen)

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def pinok(self, pincode):
		if pincode:
			self.session.openWithCallback(self.restart, MPSetup)

	def chSort(self):
		print "Sort: %s" % config.mediaportal.sortplugins.value

		if config.mediaportal.sortplugins.value == "hits":
			config.mediaportal.sortplugins.value = "abc"
		elif config.mediaportal.sortplugins.value == "abc":
			config.mediaportal.sortplugins.value = "user"
		elif config.mediaportal.sortplugins.value == "user":
			config.mediaportal.sortplugins.value = "hits"

		print "Sort changed:", config.mediaportal.sortplugins.value
		self.restart()

	def changeFilter(self):
		if config.mediaportal.filterselector.value:
			self.startChoose()
		else:
			self.chFilter()

	def chFilter(self):
		print "Filter:", config.mediaportal.filter.value

		if config.mediaportal.filter.value == "ALL":
			config.mediaportal.filter.value = "Mediathek"
		elif config.mediaportal.filter.value == "Mediathek":
			config.mediaportal.filter.value = "Grauzone"
		elif config.mediaportal.filter.value == "Grauzone":
			config.mediaportal.filter.value = "Sport"
		elif config.mediaportal.filter.value == "Sport":
			config.mediaportal.filter.value = "Music"
		elif config.mediaportal.filter.value == "Music":
			config.mediaportal.filter.value = "Fun"
		elif config.mediaportal.filter.value == "Fun":
			config.mediaportal.filter.value = "Porn"
		elif config.mediaportal.filter.value == "Porn":
			config.mediaportal.filter.value = "ALL"

		print "Filter changed:", config.mediaportal.filter.value
		self.restartAndCheck()

	def restartAndCheck(self):
		if config.mediaportal.filter.value != "ALL":
			dump_liste2 = self.dump_liste
			self.plugin_liste = []
			self.plugin_liste = [x for x in dump_liste2 if re.search(config.mediaportal.filter.value, x[2])]
			if len(self.plugin_liste) == 0:
				print "Filter ist deaktviert.. recheck..: %s" % config.mediaportal.filter.value
				self.chFilter()
			else:
				print "Mediaportal restart."
				config.mediaportal.filter.save()
				configfile.save()
				self.close(self.session, False, self.lastservice)
		else:
			print "Mediaportal restart."
			config.mediaportal.filter.save()
			configfile.save()
			self.close(self.session, False, self.lastservice)

	def showPorn(self):
		if config.mediaportal.showporn.value:
			config.mediaportal.showporn.value = False
			if config.mediaportal.filter.value == "Porn":
				self.chFilter()
			config.mediaportal.showporn.save()
			config.mediaportal.filter.save()
			configfile.save()
			self.restart()
		else:
			self.session.openWithCallback(self.showPornOK, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))

	def showPornOK(self, pincode):
		if pincode:
			config.mediaportal.showporn.value = True
			config.mediaportal.showporn.save()
			configfile.save()
			self.restart()

	def keyCancel(self):
		config.mediaportal.filter.save()
		configfile.save()
		self.close(self.session, True, self.lastservice)

	def restart(self):
		config.mediaportal.filter.save()
		config.mediaportal.sortplugins.save()
		configfile.save()
		if autoStartTimer is not None:
			autoStartTimer.update()
		self.close(self.session, False, self.lastservice)

	def startChoose(self):
		if mp_globals.isDreamOS:
			self.session.openWithCallback(self.gotFilter, MPchooseFilter, self.dump_liste, config.mediaportal.filter.value, is_dialog=True)
		else:
			self.session.openWithCallback(self.gotFilter, MPchooseFilter, self.dump_liste, config.mediaportal.filter.value)

	def gotFilter(self, filter):
		if filter != True:
			print "Set new filter to:", filter
			config.mediaportal.filter.value = filter
			print "Filter changed:", config.mediaportal.filter.value
			self.restartAndCheck()

class MPWall2(Screen, HelpableScreen):

	def __init__(self, session, lastservice, filter):
		self.lastservice = lastservice
		self.wallbw = False
		self.plugin_liste = []
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		self.images_path = "%s/%s/images" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(self.images_path):
			self.images_path = self.skin_path + mp_globals.skinFallback + "/images"

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					modfile = x.get("modfile")
					confcat = x.get("confcat")
					if modfile == "music.canna" and not mechanizeModule:
						pass
					elif not config.mediaportal.showporn.value and confcat == "porn":
						pass
					else:
						gz = x.get("gz")
						if not config.mediaportal.showgrauzone.value and gz == "1":
							pass
						else:
							mod = eval("config.mediaportal." + x.get("confopt") + ".value")
							if mod:
								y = eval("self.plugin_liste.append((\"" + x.get("name").replace("&amp;","&") + "\", \"" + x.get("icon") + "\", \"" + x.get("filter") + "\"))")

		if len(self.plugin_liste) == 0:
			self.plugin_liste.append(("","","Mediathek"))

		# Porn
		if (config.mediaportal.showporn.value == False and config.mediaportal.filter.value == 'Porn'):
			config.mediaportal.filter.value = 'ALL'

		# Grauzone
		if (config.mediaportal.showgrauzone.value == False and config.mediaportal.filter.value == 'Grauzone'):
			config.mediaportal.filter.value = 'ALL'

		# Plugin Sortierung
		if config.mediaportal.sortplugins != "default":

			# Erstelle Pluginliste falls keine vorhanden ist.
			self.sort_plugins_file = "/etc/enigma2/mp_pluginliste"
			if not fileExists(self.sort_plugins_file):
				print "Erstelle Wall-Pluginliste."
				open(self.sort_plugins_file,"w").close()

			pluginliste_leer = os.path.getsize(self.sort_plugins_file)
			if pluginliste_leer == 0:
				print "1st time - Schreibe Wall-Pluginliste."
				first_count = 0
				read_pluginliste = open(self.sort_plugins_file,"a")
				for name,picname,genre in self.plugin_liste:
					read_pluginliste.write('"%s" "%s" "%s" "%s" "%s"\n' % (name, picname, genre, "0", str(first_count)))
					first_count += 1
				read_pluginliste.close()
				print "Wall-Pluginliste wurde erstellt."

			# Lese Pluginliste ein.
			if fileExists(self.sort_plugins_file):

				count_sort_plugins_file = len(open(self.sort_plugins_file).readlines())
				count_plugin_liste = len(self.plugin_liste)

				if int(count_plugin_liste) != int(count_sort_plugins_file):
					print "Ein Plugin wurde aktiviert oder deaktiviert.. erstelle neue pluginliste."

					read_pluginliste_tmp = open(self.sort_plugins_file+".tmp","w")
					read_pluginliste = open(self.sort_plugins_file,"r")
					p_dupeliste = []

					for rawData in read_pluginliste.readlines():
						data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)

						if data:
							(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
							pop_count = 0
							for pname, ppic, pgenre in self.plugin_liste:
								if p_name not in p_dupeliste:
									if p_name == pname:
										read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, pgenre, p_hits, p_sort))
										p_dupeliste.append((p_name))
										self.plugin_liste.pop(int(pop_count))

									pop_count += 1

					if len(self.plugin_liste) != 0:
						for pname, ppic, pgenre in self.plugin_liste:
							read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (pname, ppic, pgenre, "0", "99"))

					read_pluginliste.close()
					read_pluginliste_tmp.close()
					shutil.move(self.sort_plugins_file+".tmp", self.sort_plugins_file)

				self.new_pluginliste = []
				read_pluginliste = open(self.sort_plugins_file,"r")
				for rawData in read_pluginliste.readlines():
					data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
					if data:
						(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
						self.new_pluginliste.append((p_name, p_picname, p_genre, p_hits, p_sort))
				read_pluginliste.close()

			# Sortieren nach hits
			if config.mediaportal.sortplugins.value == "hits":
				self.new_pluginliste.sort(key=lambda x: int(x[3]))
				self.new_pluginliste.reverse()

			# Sortieren nach abcde..
			elif config.mediaportal.sortplugins.value == "abc":
				self.new_pluginliste.sort(key=lambda x: str(x[0]).lower())

			elif config.mediaportal.sortplugins.value == "user":
				self.new_pluginliste.sort(key=lambda x: int(x[4]))

			self.plugin_liste = self.new_pluginliste

		if config.mediaportal.wall2mode.value == "bw":
			self.wallbw = True

		if mp_globals.videomode == 3:
			self.perpage = 48
			pageiconwidth = 36
			pageicondist = 8
			screenwidth = 3840
			screenheight = 2160
		elif mp_globals.videomode == 2:
			self.perpage = 48
			pageiconwidth = 36
			pageicondist = 8
			screenwidth = 1920
			screenheight = 1080
		else:
			self.perpage = 40
			pageiconwidth = 26
			pageicondist = 4
			screenwidth = 1280
			screenheight = 720

		path = "%s/%s/hauptScreenWall2.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/hauptScreenWall2.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		# Page Style
		if config.mediaportal.pagestyle.value == "Graphic":
			skincontent = ""
			self.skin = self.skin.replace('</screen>', '')
			self.dump_liste_page_tmp = self.plugin_liste
			if config.mediaportal.filter.value != "ALL":
				self.plugin_liste_page_tmp = []
				self.plugin_liste_page_tmp = [x for x in self.dump_liste_page_tmp if re.search(config.mediaportal.filter.value, x[2])]
			else:
				self.plugin_liste_page_tmp = self.plugin_liste

			if len(self.plugin_liste_page_tmp) != 0:
				self.counting_pages = int(round(float((len(self.plugin_liste_page_tmp)-1) / self.perpage) + 0.5))
				pagebar_size = self.counting_pages * pageiconwidth + (self.counting_pages-1) * pageicondist
				start_pagebar = int(screenwidth / 2 - pagebar_size / 2)

				for x in range(1,self.counting_pages+1):
					normal = screenheight - 2 * pageiconwidth
					if config.mediaportal.skin.value == "original":
						normal = normal - 20
					if mp_globals.videomode == 3:
						normal = normal - 30
					elif mp_globals.videomode == 2:
						normal = normal - 30
					skincontent += "<widget name=\"page_empty" + str(x) + "\" position=\"" + str(start_pagebar) + "," + str(normal) + "\" size=\"" + str(pageiconwidth) + "," + str(pageiconwidth) + "\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
					skincontent += "<widget name=\"page_sel" + str(x) + "\" position=\"" + str(start_pagebar) + "," + str(normal) + "\" size=\"" + str(pageiconwidth) + "," + str(pageiconwidth) + "\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
					start_pagebar += pageiconwidth + pageicondist

			self.skin += skincontent
			self.skin += "</screen>"

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config.mediaportal.minitv.value)

		Screen.__init__(self, session)

		registerFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal%s.ttf" % config.mediaportal.font.value, "mediaportal", 100, False)
		registerFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal_clean.ttf", "mediaportal_clean", 100, False)

		if config.mediaportal.backgroundtv.value:
			config.mediaportal.minitv.value = True
			config.mediaportal.minitv.save()
			config.mediaportal.restorelastservice.value = "2"
			config.mediaportal.restorelastservice.save()
			configfile.save()
			session.nav.stopService()

		self["actions"] = ActionMap(["MP_Actions"], {
			"info" : self.showPorn,
			"0": boundFunction(self.gotFilter, "ALL"),
			"1": boundFunction(self.gotFilter, "Mediathek"),
			"2": boundFunction(self.gotFilter, "Fun"),
			"3": boundFunction(self.gotFilter, "Music"),
			"4": boundFunction(self.gotFilter, "Sport"),
			"5": boundFunction(self.gotFilter, "Grauzone"),
			"6": boundFunction(self.gotFilter, "Porn")
		}, -1)
		self["MP_Actions"] = HelpableActionMap(self, "MP_Actions", {
			"up"    : (self.keyUp, _("Up")),
			"down"  : (self.keyDown, _("Down")),
			"left"  : (self.keyLeft, _("Left")),
			"right" : (self.keyRight, _("Right")),
			"blue"  : (self.changeFilter, _("Change filter")),
			"green" : (self.chSort, _("Change sort order")),
			"yellow": (self.manuelleSortierung, _("Manual sorting")),
			"red"   : (self.keySimpleList, _("Open SimpleList")),
			"ok"    : (self.keyOK, _("Open selected Plugin")),
			"cancel": (self.keyCancel, _("Exit MediaPortal")),
			"nextBouquet" :	(self.page_next, _("Next page")),
			"prevBouquet" :	(self.page_back, _("Previous page")),
			"menu" : (self.keySetup, _("MediaPortal Setup")),
			config.mediaportal.simplelist_key.value: (self.keySimpleList, _("Open SimpleList"))
		}, -1)

		self['name'] = Label(_("Plugin Selection"))
		self['tipps'] = Label("")
		self['red'] = Label("SimpleList")
		self['green'] = Label("")
		self['yellow'] = Label(_("Sort"))
		self['blue'] = Label("")
		self['CH+'] = Label(_("CH+"))
		self['CH-'] = Label(_("CH-"))
		self['PVR'] = Label(_("PVR"))
		self['Exit'] = Label(_("Exit"))
		self['Help'] = Label(_("Help"))
		self['Menu'] = Label(_("Menu"))
		self['page'] = Label("")
		self['tipps_bg'] = Pixmap()
		self['tipps_bg'].hide()
		self["covercollection"] = CoverCollection()

		# Apple Page Style
		if config.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			for x in range(1,self.counting_pages+1):
				self["page_empty"+str(x)] = Pixmap()
				self["page_empty"+str(x)].show()
				self["page_sel"+str(x)] = Pixmap()
				self["page_sel"+str(x)].show()

		if config.mediaportal.showTipps.value:
			self['tipps_bg'].show()
			self.loadTipp = eTimer()
			if mp_globals.isDreamOS:
				self.loadTipp_conn = self.loadTipp.timeout.connect(self.randomTipp)
			else:
				self.loadTipp.callback.append(self.randomTipp)
			self.loadTipp.start(20000) # alle 20 sek.

		HelpableScreen.__init__(self)
		self.onFirstExecBegin.append(self._onFirstExecBegin)
		self.onFirstExecBegin.append(self.checkPathes)
		self.onFirstExecBegin.append(self.status)

	def randomTipp(self):
		lines = []
		tippFile = "%s/resources/tipps.txt" % self.plugin_path
		if fileExists(tippFile):
			with open(tippFile, "r") as tipps:
				lines = tipps.readlines();
				rline = random.randrange(0, len(lines))
				self['tipps'].setText(lines[rline].strip('\n'))

	def checkPathes(self):
		CheckPathes(self.session).checkPathes(self.cb_checkPathes)

	def cb_checkPathes(self):
		self.session.openWithCallback(self.restart, MPSetup)

	def status(self):
		if not fileExists('/tmp/radiode_sender'):
			filepath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/radiode_sender.bz2")
			newfilepath = ('/tmp/radiode_sender')
			with open(newfilepath, 'wb') as new_file, bz2.BZ2File(filepath, 'rb') as file:
				for data in iter(lambda : file.read(100 * 1024), b''):
					new_file.write(data)
		update_agent = getUserAgent()
		update_url = getUpdateUrl()
		twAgentGetPage(update_url, agent=update_agent, timeout=30).addCallback(self.checkstatus)

	def checkstatus(self, html):
		if re.search(".*?<html", html):
			return
		self.html = html
		tmp_infolines = html.splitlines()
		statusurl = tmp_infolines[4]
		update_agent = getUserAgent()
		twAgentGetPage(statusurl, agent=update_agent, timeout=30).addCallback(_status)

	def manuelleSortierung(self):
		if config.mediaportal.filter.value == 'ALL':
			self.session.openWithCallback(self.restart, MPpluginSort)
		else:
			self.session.open(MessageBoxExt, _('Ordering is only possible with filter "ALL".'), MessageBoxExt.TYPE_INFO, timeout=3)

	def hit_plugin(self, pname):
		if fileExists(self.sort_plugins_file):
			read_pluginliste = open(self.sort_plugins_file,"r")
			read_pluginliste_tmp = open(self.sort_plugins_file+".tmp","w")
			for rawData in read_pluginliste.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
					if pname == p_name:
						new_hits = int(p_hits)+1
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, p_genre, str(new_hits), p_sort))
					else:
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, p_genre, p_hits, p_sort))
			read_pluginliste.close()
			read_pluginliste_tmp.close()
			shutil.move(self.sort_plugins_file+".tmp", self.sort_plugins_file)

	def _onFirstExecBegin(self):
		_hosters()
		if not mp_globals.start:
			self.close(self.session, True, self.lastservice)
		if config.mediaportal.autoupdate.value:
			checkupdate(self.session).checkforupdate()

		# load plugin icons
		print "Set Filter:", config.mediaportal.filter.value
		if config.mediaportal.filter.value == "ALL":
			name = _("ALL")
		elif config.mediaportal.filter.value == "Mediathek":
			name = _("Libraries")
		elif config.mediaportal.filter.value == "Grauzone":
			name = _("Grayzone")
		elif config.mediaportal.filter.value == "Fun":
			name = _("Fun")
		elif config.mediaportal.filter.value == "Music":
			name = _("Music")
		elif config.mediaportal.filter.value == "Sport":
			name = _("Sports")
		elif config.mediaportal.filter.value == "Porn":
			name = _("Porn")
		self['blue'].setText(name)
		self.sortplugin = config.mediaportal.sortplugins.value
		if self.sortplugin == "hits":
			self.sortplugin = "Hits"
		elif self.sortplugin == "abc":
			self.sortplugin = "ABC"
		elif self.sortplugin == "user":
			self.sortplugin = "User"
		self['green'].setText(self.sortplugin)
		self.dump_liste = self.plugin_liste
		if config.mediaportal.filter.value != "ALL":
			self.plugin_liste = []
			self.plugin_liste = [x for x in self.dump_liste if re.search(config.mediaportal.filter.value, x[2])]
		if len(self.plugin_liste) == 0:
			self.chFilter()
			if config.mediaportal.filter.value == "ALL":
				name = _("ALL")
			elif config.mediaportal.filter.value == "Mediathek":
				name = _("Libraries")
			elif config.mediaportal.filter.value == "Grauzone":
				name = _("Grayzone")
			elif config.mediaportal.filter.value == "Fun":
				name = _("Fun")
			elif config.mediaportal.filter.value == "Music":
				name = _("Music")
			elif config.mediaportal.filter.value == "Sport":
				name = _("Sports")
			elif config.mediaportal.filter.value == "Porn":
				name = _("Porn")
			self['blue'].setText(name)

		if config.mediaportal.sortplugins.value == "hits":
			self.plugin_liste.sort(key=lambda x: int(x[3]))
			self.plugin_liste.reverse()

		# Sortieren nach abcde..
		elif config.mediaportal.sortplugins.value == "abc":
			self.plugin_liste.sort(key=lambda t : t[0].lower())

		elif config.mediaportal.sortplugins.value == "user":
			self.plugin_liste.sort(key=lambda x: int(x[4]))

		itemList = []
		posterlist = []
		for p_name, p_picname, p_genre, p_hits, p_sort in self.plugin_liste:
			row = []
			itemList.append(((row),))
			if self.wallbw:
				poster_path = "%s/%s.png" % ("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/icons_bw", p_picname)
				if not fileExists(poster_path):
					poster_path = "%s/icons/no_icon.png" % self.plugin_path
			else:
				poster_path = "%s/%s.png" % ("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/icons", p_picname)
				if not fileExists(poster_path):
					poster_path = "%s/icons/no_icon.png" % self.plugin_path
			row.append((p_name, p_picname, poster_path, p_genre, p_hits, p_sort))
			posterlist.append(poster_path)
		self["covercollection"].setList(itemList,posterlist)

		if config.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			for x in range(1,self.counting_pages+1):
				poster_path = "%s/page_select.png" % (self.images_path)
				self["page_sel"+str(x)].instance.setPixmap(gPixmapPtr())
				self["page_sel"+str(x)].hide()
				pic = LoadPixmap(cached=True, path=poster_path)
				if pic != None:
					self["page_sel"+str(x)].instance.setPixmap(pic)
					if x == 1:
						self["page_sel"+str(x)].show()

			for x in range(1,self.counting_pages+1):
				poster_path = "%s/page.png" % (self.images_path)
				self["page_empty"+str(x)].instance.setPixmap(gPixmapPtr())
				self["page_empty"+str(x)].hide()
				pic = LoadPixmap(cached=True, path=poster_path)
				if pic != None:
					self["page_empty"+str(x)].instance.setPixmap(pic)
					if x > 1:
						self["page_empty"+str(x)].show()
		self.setInfo()
		if config.mediaportal.showTipps.value:
			self.randomTipp()

	def keyOK(self):
		if not testWebConnection():
			self.session.open(MessageBoxExt, _('No connection to the Internet available.'), MessageBoxExt.TYPE_INFO, timeout=3)
			return

		if self["covercollection"].getCurrentIndex() >=0:
			item = self["covercollection"].getCurrent()
			(p_name, p_picname, p_picpath, p_genre, p_hits, p_sort) = item[0]

		mp_globals.activeIcon = p_picname
		print "Plugin:", p_name

		self.pornscreen = None
		self.par1 = ""
		self.par2 = ""
		self.hit_plugin(p_name)

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					confcat = x.get("confcat")
					if p_name ==  x.get("name").replace("&amp;","&"):
						status = [item for item in mp_globals.status if item[0] == x.get("modfile")]
						if status:
							if config.mediaportal.version.value < status[0][1]:
								if not config.mediaportal.debugMode.value == "High":
									if status[0][1] == "9999":
										self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"\n\nIf someone else is willing to provide a fix for this Plugin then please get in contact with us.") % status[0][2], MessageBoxExt.TYPE_INFO)
									else:
										self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"") % status[0][2], MessageBoxExt.TYPE_INFO)
									return
						param = ""
						param1 = x.get("param1")
						param2 = x.get("param2")
						kids = x.get("kids")
						if param1 != "":
							param = ", \"" + param1 + "\""
							exec("self.par1 = \"" + x.get("param1") + "\"")
						if param2 != "":
							param = param + ", \"" + param2 + "\""
							exec("self.par2 = \"" + x.get("param2") + "\"")
						if confcat == "porn":
							exec("self.pornscreen = " + x.get("screen") + "")
						elif kids != "1" and config.mediaportal.kidspin.value:
							exec("self.pornscreen = " + x.get("screen") + "")
						else:
							exec("self.session.open(" + x.get("screen") + param + ")")
		if self.pornscreen:
			if config.mediaportal.pornpin.value:
				if pincheck.pin_entered == False:
					self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))
				else:
					if self.par1 == "":
						self.session.open(self.pornscreen)
					elif self.par2 == "":
						self.session.open(self.pornscreen, self.par1)
					else:
						self.session.open(self.pornscreen, self.par1, self.par2)
			else:
				if self.par1 == "":
					self.session.open(self.pornscreen)
				elif self.par2 == "":
					self.session.open(self.pornscreen, self.par1)
				else:
					self.session.open(self.pornscreen, self.par1, self.par2)

	def pincheckok(self, pincode):
		if pincode:
			pincheck.pinEntered()
			if self.par1 == "":
				self.session.open(self.pornscreen)
			elif self.par2 == "":
				self.session.open(self.pornscreen, self.par1)
			else:
				self.session.open(self.pornscreen, self.par1, self.par2)

	def setInfo(self):
		if self["covercollection"].getCurrentIndex() >=0:
			item = self["covercollection"].getCurrent()
			(p_name, p_picname, p_picpath, p_genre, p_hits, p_sort) = item[0]
			try:
				self['name'].instance.setShowHideAnimation(config.mediaportal.animation_label.value)
			except:
				pass
			self['name'].setText(p_name)
			if config.mediaportal.pagestyle.value == "Graphic":
				self.refresh_apple_page_bar()
			else:
				currentPage = self["covercollection"].getCurrentPage()
				totalPages = self["covercollection"].getTotalPages()
				pageinfo = _("Page") + " %s / %s" % (currentPage, totalPages)
				self['page'].setText(pageinfo)

	def keyLeft(self):
		self["covercollection"].MoveLeft()
		self.setInfo()

	def keyRight(self):
		self["covercollection"].MoveRight()
		self.setInfo()

	def keyUp(self):
		self["covercollection"].MoveUp()
		self.setInfo()

	def keyDown(self):
		self["covercollection"].MoveDown()
		self.setInfo()

	def page_next(self):
		self["covercollection"].NextPage()
		self.setInfo()

	def page_back(self):
		self["covercollection"].PreviousPage()
		self.setInfo()

	def check_empty_list(self):
		if len(self.plugin_liste) == 0:
			self['name'].setText('Keine Plugins der Kategorie %s aktiviert!' % config.mediaportal.filter.value)
			return True
		else:
			return False

	# Apple Page Style
	def refresh_apple_page_bar(self):
		if config.mediaportal.pagestyle.value == "Graphic":
			if self["covercollection"].getCurrentIndex() >=0:
				currentPage = self["covercollection"].getCurrentPage()
				totalPages = self["covercollection"].getTotalPages()
				for x in range(1,totalPages+1):
					if x == currentPage:
						self["page_empty"+str(x)].hide()
						self["page_sel"+str(x)].show()
					else:
						self["page_sel"+str(x)].hide()
						self["page_empty"+str(x)].show()

	def keySetup(self):
		if config.mediaportal.setuppin.value:
			self.session.openWithCallback(self.pinok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))
		else:
			self.session.openWithCallback(self.restart, MPSetup)

	def keySimpleList(self):
		mp_globals.activeIcon = "simplelist"
		self.session.open(simplelistGenreScreen)

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def pinok(self, pincode):
		if pincode:
			self.session.openWithCallback(self.restart, MPSetup)

	def chSort(self):
		print "Sort: %s" % config.mediaportal.sortplugins.value

		if config.mediaportal.sortplugins.value == "hits":
			config.mediaportal.sortplugins.value = "abc"
		elif config.mediaportal.sortplugins.value == "abc":
			config.mediaportal.sortplugins.value = "user"
		elif config.mediaportal.sortplugins.value == "user":
			config.mediaportal.sortplugins.value = "hits"

		print "Sort changed:", config.mediaportal.sortplugins.value
		self.restart()

	def changeFilter(self):
		if config.mediaportal.filterselector.value:
			self.startChoose()
		else:
			self.chFilter()

	def chFilter(self):
		print "Filter:", config.mediaportal.filter.value

		if config.mediaportal.filter.value == "ALL":
			config.mediaportal.filter.value = "Mediathek"
		elif config.mediaportal.filter.value == "Mediathek":
			config.mediaportal.filter.value = "Grauzone"
		elif config.mediaportal.filter.value == "Grauzone":
			config.mediaportal.filter.value = "Sport"
		elif config.mediaportal.filter.value == "Sport":
			config.mediaportal.filter.value = "Music"
		elif config.mediaportal.filter.value == "Music":
			config.mediaportal.filter.value = "Fun"
		elif config.mediaportal.filter.value == "Fun":
			config.mediaportal.filter.value = "Porn"
		elif config.mediaportal.filter.value == "Porn":
			config.mediaportal.filter.value = "ALL"

		print "Filter changed:", config.mediaportal.filter.value
		self.restartAndCheck()

	def restartAndCheck(self):
		if config.mediaportal.filter.value != "ALL":
			dump_liste2 = self.dump_liste
			self.plugin_liste = []
			self.plugin_liste = [x for x in dump_liste2 if re.search(config.mediaportal.filter.value, x[2])]
			if len(self.plugin_liste) == 0:
				print "Filter ist deaktviert.. recheck..: %s" % config.mediaportal.filter.value
				self.chFilter()
			else:
				print "Mediaportal restart."
				config.mediaportal.filter.save()
				configfile.save()
				self.close(self.session, False, self.lastservice)
		else:
			print "Mediaportal restart."
			config.mediaportal.filter.save()
			configfile.save()
			self.close(self.session, False, self.lastservice)

	def showPorn(self):
		if config.mediaportal.showporn.value:
			config.mediaportal.showporn.value = False
			if config.mediaportal.filter.value == "Porn":
				self.chFilter()
			config.mediaportal.showporn.save()
			config.mediaportal.filter.save()
			configfile.save()
			self.restart()
		else:
			self.session.openWithCallback(self.showPornOK, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))

	def showPornOK(self, pincode):
		if pincode:
			config.mediaportal.showporn.value = True
			config.mediaportal.showporn.save()
			configfile.save()
			self.restart()

	def keyCancel(self):
		config.mediaportal.filter.save()
		configfile.save()
		self.close(self.session, True, self.lastservice)

	def restart(self):
		config.mediaportal.filter.save()
		config.mediaportal.sortplugins.save()
		configfile.save()
		if autoStartTimer is not None:
			autoStartTimer.update()
		self.close(self.session, False, self.lastservice)

	def startChoose(self):
		if mp_globals.isDreamOS:
			self.session.openWithCallback(self.gotFilter, MPchooseFilter, self.dump_liste, config.mediaportal.filter.value, is_dialog=True)
		else:
			self.session.openWithCallback(self.gotFilter, MPchooseFilter, self.dump_liste, config.mediaportal.filter.value)

	def gotFilter(self, filter):
		if filter != True:
			print "Set new filter to:", filter
			config.mediaportal.filter.value = filter
			print "Filter changed:", config.mediaportal.filter.value
			self.restartAndCheck()

class MPchooseFilter(Screen):

	def __init__(self, session, plugin_liste, old_filter):
		self.plugin_liste = plugin_liste
		self.old_filter = old_filter

		self.dupe = []
		self.dupe.append("ALL")
		for (pname, iname, filter, hits, count) in self.plugin_liste:
			#check auf mehrere filter
			if re.search('/', filter):
				mfilter_raw = re.split('/', filter)
				for mfilter in mfilter_raw:
					if not mfilter in self.dupe:
						self.dupe.append(mfilter)
			else:
				if not filter in self.dupe:
					self.dupe.append(filter)

		self.dupe.sort()

		hoehe = 197
		breite = 531
		skincontent = ""
		for x in range(1,len(self.dupe)+1):
			skincontent += "<widget name=\"menu" + str(x) + "\" position=\"" + str(breite) + "," + str(hoehe) + "\" size=\"218,38\" zPosition=\"1\" transparent=\"1\" alphatest=\"blend\" />"
			hoehe += 48

		self.skin_dump = ""
		self.skin_dump += "<widget name=\"frame\" position=\"531,197\" size=\"218,38\" pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/category_selector_%s.png\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />" % config.mediaportal.selektor.value
		self.skin_dump += skincontent
		self.skin_dump += "</screen>"

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/category_selector.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/category_selector.xml"

		with open(path, "r") as f:
			self.skin_dump2 = f.read()
			self.skin_dump2 += self.skin_dump
			self.skin = self.skin_dump2
			f.close()

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config.mediaportal.minitv.value)

		Screen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"up": self.keyup,
			"down": self.keydown
		}, -1)

		self["frame"] = MovingPixmap()
		self["frame"].hide()

		self['F1'] = Label("")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label("")
		self['F5'] = Label("")
		self['F6'] = Label("")
		self['F7'] = Label("")

		for x in range(1,len(self.dupe)+1):
			self["menu"+str(x)] = Pixmap()
			self["menu"+str(x)].show()

		self.onFirstExecBegin.append(self.loadPage)

	def loadPage(self):
		for x in range(1,len(self.dupe)+1):
			filtername = self.dupe[int(x)-1]
			if filtername == "ALL":
				name = _("ALL")
			elif filtername == "Mediathek":
				name = _("Libraries")
			elif filtername == "Grauzone":
				name = _("Grayzone")
			elif filtername == "Fun":
				name = _("Fun")
			elif filtername == "Music":
				name = _("Music")
			elif filtername == "Sport":
				name = _("Sports")
			elif filtername == "Porn":
				name = _("Porn")
			self['F'+str(x)].setText(name)
			poster_path = "%s/images/category_selector_button.png" % self.plugin_path
			if fileExists(poster_path):
				self["menu"+str(x)].instance.setPixmap(gPixmapPtr())
				self["menu"+str(x)].hide()
				pic = LoadPixmap(cached=True, path=poster_path)
				if pic != None:
					self["menu"+str(x)].instance.setPixmap(pic)
					self["menu"+str(x)].show()
		self.getstartframe()

	def getstartframe(self):
		x = 1
		for fname in self.dupe:
			if fname == self.old_filter:
				position = self["menu"+str(x)].instance.position()
				self["frame"].moveTo(position.x(), position.y(), 1)
				self["frame"].show()
				self["frame"].startMoving()
				self.selektor_index = x
			x += 1

	def moveframe(self):
		position = self["menu"+str(self.selektor_index)].instance.position()
		self["frame"].moveTo(position.x(), position.y(), 1)
		self["frame"].show()
		self["frame"].startMoving()

	def keyOk(self):
		self.close(self.dupe[self.selektor_index-1])

	def keyup(self):
		if int(self.selektor_index) != 1:
			self.selektor_index -= 1
			self.moveframe()

	def keydown(self):
		if int(self.selektor_index) != len(self.dupe):
			self.selektor_index += 1
			self.moveframe()

	def keyCancel(self):
		self.close(True)

def exit(session, result, lastservice):
	global lc_stats
	if not result:
		if config.mediaportal.premiumize_use.value:
			if not mp_globals.premium_yt_proxy_host:
				CheckPremiumize(session).premiumizeProxyConfig(False)

		if config.mediaportal.ansicht.value == "liste":
			session.openWithCallback(exit, MPList, lastservice)
		elif config.mediaportal.ansicht.value == "wall":
			session.openWithCallback(exit, MPWall, lastservice, config.mediaportal.filter.value)
		elif config.mediaportal.ansicht.value == "wall2":
			session.openWithCallback(exit, MPWall2, lastservice, config.mediaportal.filter.value)
	else:
		session.nav.playService(lastservice)
		_stylemanager(0)
		reactor.callLater(1, export_lru_caches)
		reactor.callLater(5, clearTmpBuffer)
		watcher.stop()
		if SHOW_HANG_STAT:
			lc_stats.stop()
			del lc_stats

def _stylemanager(mode):
	desktopSize = getDesktop(0).size()
	if desktopSize.height() == 2160:
		mp_globals.videomode = 3
		mp_globals.fontsize = 50
		mp_globals.sizefactor = 7
	elif desktopSize.height() == 1080:
		mp_globals.videomode = 2
		mp_globals.fontsize = 30
		mp_globals.sizefactor = 3
	else:
		mp_globals.videomode = 1
		mp_globals.fontsize = 23
		mp_globals.sizefactor = 1
	try:
		from enigma import eWindowStyleManager, eWindowStyleSkinned, eSize, eListboxPythonStringContent, eListboxPythonConfigContent
		try:
			from enigma import eWindowStyleScrollbar
		except:
			pass
		from skin import parseSize, parseFont, parseColor
		try:
			from skin import parseValue
		except:
			pass

		stylemgr = eWindowStyleManager.getInstance()
		desktop = getDesktop(0)
		styleskinned = eWindowStyleSkinned()

		try:
			stylescrollbar = eWindowStyleScrollbar()
			skinScrollbar = True
		except:
			skinScrollbar = False

		if mode == 0:
			skin_path = resolveFilename(SCOPE_CURRENT_SKIN) + "skin_user_colors.xml"
			if not fileExists(skin_path):
				skin_path = resolveFilename(SCOPE_CURRENT_SKIN) + "skin.xml"
			file_path = resolveFilename(SCOPE_SKIN)
		else:
			skin_path = mp_globals.pluginPath + mp_globals.skinsPath + "/" + config.mediaportal.skin.value + "/skin.xml"
			if not fileExists(skin_path):
				skin_path = mp_globals.pluginPath + mp_globals.skinsPath + mp_globals.skinFallback + "/skin.xml"
			file_path = mp_globals.pluginPath + "/"

		if fileExists(skin_path):
			conf = xml.etree.cElementTree.parse(skin_path)
			for x in conf.getroot():
				if x.tag == "windowstylescrollbar":
					if skinScrollbar:
						windowstylescrollbar =  x
						for x in windowstylescrollbar:
							if x.tag == "value":
								if x.get("name") == "BackgroundPixmapTopHeight":
									stylescrollbar.setBackgroundPixmapTopHeight(int(x.get("value")))
								elif x.get("name") == "BackgroundPixmapBottomHeight":
									stylescrollbar.setBackgroundPixmapBottomHeight(int(x.get("value")))
								elif x.get("name") == "ValuePixmapTopHeight":
									stylescrollbar.setValuePixmapTopHeight(int(x.get("value")))
								elif x.get("name") == "ValuePixmapBottomHeight":
									stylescrollbar.setValuePixmapBottomHeight(int(x.get("value")))
								elif x.get("name") == "ScrollbarWidth":
									stylescrollbar.setScrollbarWidth(int(x.get("value")))
								elif x.get("name") == "ScrollbarBorderWidth":
									stylescrollbar.setScrollbarBorderWidth(int(x.get("value")))
							if x.tag == "pixmap":
								if x.get("name") == "BackgroundPixmap":
									stylescrollbar.setBackgroundPixmap(LoadPixmap(file_path + x.get("filename"), desktop))
								elif x.get("name") == "ValuePixmap":
									stylescrollbar.setValuePixmap(LoadPixmap(file_path + x.get("filename"), desktop))
				elif x.tag == "windowstyle" and x.get("id") == "0":
					font = gFont("Regular", 20)
					offset = eSize(20, 5)
					windowstyle = x
					for x in windowstyle:
						if x.tag == "title":
							font = parseFont(x.get("font"), ((1,1),(1,1)))
							offset = parseSize(x.get("offset"), ((1,1),(1,1)))
						elif x.tag == "color":
							colorType = x.get("name")
							color = parseColor(x.get("color"))
							try:
								styleskinned.setColor(eWindowStyleSkinned.__dict__["col" + colorType], color)
							except:
								pass
						elif x.tag == "borderset":
							bsName = str(x.get("name"))
							borderset =  x
							for x in borderset:
								if x.tag == "pixmap":
									bpName = x.get("pos")
									try:
										styleskinned.setPixmap(eWindowStyleSkinned.__dict__[bsName], eWindowStyleSkinned.__dict__[bpName], LoadPixmap(file_path + x.get("filename"), desktop))
									except:
										pass
						elif x.tag == "listfont":
							fontType = x.get("type")
							fontSize = int(x.get("size"))
							fontFace = x.get("font")
							try:
								styleskinned.setListFont(eWindowStyleSkinned.__dict__["listFont" + fontType], fontSize, fontFace)
							except:
								pass
					try:
						styleskinned.setTitleFont(font)
						styleskinned.setTitleOffset(offset)
					except:
						pass
				elif x.tag == "listboxcontent":
					listboxcontent = x
					for x in listboxcontent:
						if x.tag == "offset":
							name = x.get("name")
							value = x.get("value")
							if name and value:
								try:
									if name == "left":
											eListboxPythonStringContent.setLeftOffset(parseValue(value))
									elif name == "right":
											eListboxPythonStringContent.setRightOffset(parseValue(value))
								except:
									pass
						elif x.tag == "font":
							name = x.get("name")
							font = x.get("font")
							if name and font:
								try:
									if name == "string":
											eListboxPythonStringContent.setFont(parseFont(font, ((1,1),(1,1))))
									elif name == "config_description":
											eListboxPythonConfigContent.setDescriptionFont(parseFont(font, ((1,1),(1,1))))
									elif name == "config_value":
											eListboxPythonConfigContent.setValueFont(parseFont(font, ((1,1),(1,1))))
								except:
									pass
						elif x.tag == "value":
							name = x.get("name")
							value = x.get("value")
							if name and value:
								try:
									if name == "string_item_height":
											eListboxPythonStringContent.setItemHeight(parseValue(value))
									elif name == "config_item_height":
											eListboxPythonConfigContent.setItemHeight(parseValue(value))
								except:
									pass
				elif x.tag == "mediaportal":
					mediaportal = x
					for x in mediaportal:
						if x.tag == "color":
							colorType = x.get("name")
							exec("mp_globals." + x.get("name") + "=\"" + x.get("color") + "\"")
						elif x.tag == "overridefont":
							exec("mp_globals.font=\"" + x.get("font") + "\"")
						elif x.tag == "overridefontsize":
							mp_globals.fontsize = int(x.get("value"))
						elif x.tag == "overridesizefactor":
							mp_globals.sizefactor = int(x.get("value"))

			stylemgr.setStyle(0, styleskinned)
			try:
				stylemgr.setStyle(4, stylescrollbar)
			except:
				pass
		else:
			printl('Missing MP skin.xml this file is mandatory!','','E')
	except:
		printl('Fatal skin.xml error!','','E')
		pass

class globalWatchlist(MPScreen):

	def __init__(self, session):
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
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Last seen Movies/Series")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label("")

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.readGlWatchlist)

	def readGlWatchlist(self):
		self.keyLocked = True
		self.wlgl_path = config.mediaportal.watchlistpath.value+"mp_global_watchlist"
		if not fileExists(self.wlgl_path):
			self.streamList.append(("Global Watchlist is empty!", None, None))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			return
		try:
			readGlwl = open(self.wlgl_path,"r")
			glWldata = readGlwl.read()
			readGlwl.close()

			for lst in re.findall('"(.*?)"', glWldata):
				list = lst.split(',')
				self.streamList.append((list[0], list[1], list))
			self.keyLocked = False
		except:
			self.streamList.append(("Global Watchlist is empty!", None, None))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		self.Title = self['liste'].getCurrent()[0][0]
		self.Cover = self['liste'].getCurrent()[0][1]
		CoverHelper(self['coverArt']).getCover(self.Cover)
		self['name'].setText(self.Title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		list = self['liste'].getCurrent()[0][2]
		open = "self.session.open("
		count = 0
		counting = len(list)
		for each in list:
			if count == 0 or count == 1:
				count += 1
				continue
			elif count == 2:
				count += 1
				open += each+','
			else:
				count += 1
				if counting == count:
					open += '"'+each+'"'
				else:
					open += '"'+each+'",'
		open += ")"
		exec(open)

def _hosters():
	hosters_file = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/resources/hosters.xml"
	open_hosters = open(hosters_file)
	data = open_hosters.read()
	open_hosters.close()
	hosters = re.findall('<hoster>(.*?)</hoster><regex>(.*?)</regex>', data)
	mp_globals.hosters = ["|".join([hoster for hoster,regex in hosters])]
	mp_globals.hosters += ["|".join([regex for hoster,regex in hosters])]

def _status(data):
	statusdata = re.findall('"(.*?)"\s"(.*?)"\s"(.*?)"', data)
	if statusdata:
		mp_globals.status = []
		for (plugin, version, status) in statusdata:
			mp_globals.status.append((plugin,version,status))

mp_globals.lruCache = SimpleLRUCache(50, config.mediaportal.watchlistpath.value + 'mp_lru_cache')
mp_globals.yt_lruCache = SimpleLRUCache(100, config.mediaportal.watchlistpath.value + 'mp_yt_lru_cache')

watcher = None
lc_stats = None

def export_lru_caches():
	if config.mediaportal.sp_save_resumecache.value:
		mp_globals.lruCache.saveCache()
		mp_globals.yt_lruCache.saveCache()

def import_lru_caches():
	if config.mediaportal.sp_save_resumecache.value:
		mp_globals.lruCache.readCache()
		mp_globals.yt_lruCache.readCache()

def clearTmpBuffer():
	if mp_globals.yt_tmp_storage_dirty:
		mp_globals.yt_tmp_storage_dirty = False
		BgFileEraser = eBackgroundFileEraser.getInstance()
		path = config.mediaportal.storagepath.value
		for fn in next(os.walk(path))[2]:
			BgFileEraser.erase(os.path.join(path,fn))

def MPmain(session, **kwargs):
	mp_globals.start = True
	startMP(session)

def startMP(session):
	global watcher, lc_stats

	reactor.callLater(2, import_lru_caches)

	registerFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal%s.ttf" % config.mediaportal.font.value, "mediaportal", 100, False)
	registerFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal_clean.ttf", "mediaportal_clean", 100, False)
	mp_globals.font = 'mediaportal'
	_stylemanager(1)

	if watcher == None:
		watcher = HangWatcher()
	watcher.start()
	if SHOW_HANG_STAT:
		lc_stats = task.LoopingCall(watcher.print_stats)
		lc_stats.start(60)

	if config.mediaportal.epg_enabled.value and not config.mediaportal.epg_runboot.value and not mpepg.has_epg:
		def importFini(msg):
			session.open(MessageBoxExt, msg, type = MessageBoxExt.TYPE_INFO, timeout=5)
		mpepg.importEPGData().addCallback(importFini)

	if config.mediaportal.premiumize_use.value:
		if not mp_globals.premium_yt_proxy_host:
			CheckPremiumize(session).premiumizeProxyConfig(False)

	mp_globals.currentskin = config.mediaportal.skin.value
	lastservice = session.nav.getCurrentlyPlayingServiceReference()

	if config.mediaportal.ansicht.value == "liste":
		session.openWithCallback(exit, MPList, lastservice)
	elif config.mediaportal.ansicht.value == "wall":
		session.openWithCallback(exit, MPWall, lastservice, config.mediaportal.filter.value)
	elif config.mediaportal.ansicht.value == "wall2":
		session.openWithCallback(exit, MPWall2, lastservice, config.mediaportal.filter.value)

##################################
# Autostart section
class AutoStartTimer:
	def __init__(self, session):
		import enigma

		self.session = session
		self.timer = enigma.eTimer()
		if mp_globals.isDreamOS:
			self.timer_conn = self.timer.timeout.connect(self.onTimer)
		else:
			self.timer.callback.append(self.onTimer)
		self.update()

	def getWakeTime(self):
		import time
		if config.mediaportal.epg_enabled.value:
			clock = config.mediaportal.epg_wakeup.value
			nowt = time.time()
			now = time.localtime(nowt)
			return int(time.mktime((now.tm_year, now.tm_mon, now.tm_mday,
				clock[0], clock[1], lastMACbyte()/5, 0, now.tm_yday, now.tm_isdst)))
		else:
			return -1

	def update(self, atLeast = 0):
		import time
		self.timer.stop()
		wake = self.getWakeTime()
		now = int(time.time())
		if wake > 0:
			if wake < now + atLeast:
				# Tomorrow.
				wake += 24*3600
			next = wake - now
			self.timer.startLongTimer(next)
		else:
			wake = -1
		print>>log, "[MP EPGImport] WakeUpTime now set to", wake, "(now=%s)" % now
		return wake

	def runImport(self):
		if config.mediaportal.epg_enabled.value:
			mpepg.getEPGData()

	def onTimer(self):
		import time
		self.timer.stop()
		now = int(time.time())
		print>>log, "[MP EPGImport] onTimer occured at", now
		wake = self.getWakeTime()
		# If we're close enough, we're okay...
		atLeast = 0
		if wake - now < 60:
			self.runImport()
			atLeast = 60
		self.update(atLeast)

def onBootStartCheck():
	import time
	global autoStartTimer
	print>>log, "[MP EPGImport] onBootStartCheck"
	now = int(time.time())
	wake = autoStartTimer.update()
	print>>log, "[MP EPGImport] now=%d wake=%d wake-now=%d" % (now, wake, wake-now)
	if (wake < 0) or (wake - now > 600):
		print>>log, "[MP EPGImport] starting import because auto-run on boot is enabled"
		autoStartTimer.runImport()
	else:
		print>>log, "[MP EPGImport] import to start in less than 10 minutes anyway, skipping..."

def autostart(reason, session=None, **kwargs):
	"called with reason=1 to during shutdown, with reason=0 at startup?"
	global autoStartTimer
	global _session
	import time
	print>>log, "[MP EPGImport] autostart (%s) occured at" % reason, time.time()
	if reason == 0:
		if session is not None:
			_session = session
		if autoStartTimer is None:
			autoStartTimer = AutoStartTimer(session)
		if config.mediaportal.epg_runboot.value:
			# timer isn't reliable here, damn
			onBootStartCheck()
		if config.mediaportal.epg_deepstandby.value == 'wakeup':
			if config.mediaportal.epg_wakeupsleep.value:
				print>>log, "[MP EPGImport] Returning to standby"
				from Tools import Notifications
				Notifications.AddNotification(Screens.Standby.Standby)
	else:
		print>>log, "[MP EPGImport] Stop"
		#if autoStartTimer:
		#autoStartTimer.stop()

def getNextWakeup():
	"returns timestamp of next time when autostart should be called"
	if autoStartTimer:
		if config.mediaportal.epg_deepstandby.value == 'wakeup':
			print>>log, "[MP EPGImport] Will wake up from deep sleep"
			return autoStartTimer.update()
	return -1

def Plugins(path, **kwargs):
	mp_globals.pluginPath = path

	result = [
		PluginDescriptor(
			name="MediaPortal",
			description = "MediaPortal - EPG Importer",
			where = [
				PluginDescriptor.WHERE_AUTOSTART,
				PluginDescriptor.WHERE_SESSIONSTART
			],
			fnc = autostart,
			wakeupfnc = getNextWakeup
		),
		PluginDescriptor(name="MediaPortal", description="MediaPortal", where = [PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU], icon="plugin.png", fnc=MPmain)
	]
	return result