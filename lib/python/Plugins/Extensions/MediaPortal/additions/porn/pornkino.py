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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
import base64
import cookielib

MozillaAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'
ck = CookieJar()

class pornkinoGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		if self.mode == "pornkino":
			keckse = cookielib.Cookie(version=0, name='hasVsitedSite', value='yes', port=None, port_specified=False, domain='pornkino.to', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
			self.portal = "PornKino.to"
			self.baseurl = "http://pornkino.to"
		if self.mode == "pornkinox":
			keckse = cookielib.Cookie(version=0, name='hasVsitedSite', value='yes', port=None, port_specified=False, domain='pornkinox.to', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
			self.portal = "PornKinox.to"
			self.baseurl = "http://www.pornkinox.to"
		ck.set_cookie(keckse)

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
		self.suchString = ''
		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		twAgentGetPage(self.baseurl, agent=MozillaAgent, cookieJar=ck).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('Kategorien</span></h4>(.*?)</ul>', data, re.S)
		if parse:
			Cat = re.findall('cat-item.*?href="(.*?)".*?>(.*?)</a>', parse.group(1), re.S)
			if Cat:
				for (Url, Title) in Cat:
					Url = Url+'/page/'
					self.genreliste.append((Title, Url))
				self.genreliste.sort()
				self.genreliste.insert(0, ("Newest", "%s/page/" % self.baseurl))
				self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
				self.ml.setList(map(self._defaultlistcenter, self.genreliste))
				self.keyLocked = False

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = '%s' % (self.suchString)
			Name = "--- Search ---"
			self.session.open(pornkinoFilmListeScreen, Link, Name, self.portal, self.baseurl)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		else:
			self.session.open(pornkinoFilmListeScreen, Link, Name, self.portal, self.baseurl)

class pornkinoFilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal, baseurl):
		self.Link = Link
		self.Name = Name
		self.portal = portal
		self.baseurl = baseurl
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
			"ok"    : self.keyOK,
			"0" : self.closeAll,
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

		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['Page'] = Label(_("Page:"))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "%s/page/%s/?s=%s" % (self.baseurl, str(self.page), self.Link)
		else:
			url = "%s%s/" % (self.Link, str(self.page))
		twAgentGetPage(url, agent=MozillaAgent, cookieJar=ck).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.getLastPage(data, '', 'class=\'page-numbers.*>(\d+)</')
		movies = re.findall('<article\sid="post.*?<a\shref=".*?href="(.*?)"\stitle="(.*?)".*?<img\sclass="cover"\ssrc="(.*?)"\swidth=', data, re.S)
		if movies:
			self.filmliste = []
			for (url,title,image) in movies:
				if image[:2] == "//":
					image = "http:" + image
				self.filmliste.append((decodeHtml(title),url,image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		if url:
			self.session.open(pornkinoFilmAuswahlScreen, title, url, image, self.portal, self.baseurl)

class pornkinoFilmAuswahlScreen(MPScreen):

	def __init__(self, session, Name, Link, cover, portal, baseurl):
		self.Link = Link
		self.Name = Name
		self.cover = cover
		self.portal = portal
		self.baseurl = baseurl
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
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Streams")
		self['name'] = Label(_('Please wait...'))

		self.filmliste = []
		self.captchainfo = {}
		self.keepurl = None
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		twAgentGetPage(self.Link, agent=MozillaAgent, cookieJar=ck).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('post-header">(.*?)class="single-nav', data, re.S)
		streams = re.findall('(http[s]?://(?!(pornkino.to|pornkinox.to|picload.org))(.*?)\/.*?)[\'|"|\&|<]', parse.group(1), re.S|re.I)
		if streams:
			cleanedlist = [ x for x in streams if 'favicon.ico' not in x[0] ]
			keepcheck =  filter(lambda x: 'http://www.keeplinks' in x, cleanedlist[1])
			if keepcheck:
				self.keepurl = keepcheck[-1]
				twAgentGetPage(self.keepurl, agent=MozillaAgent, cookieJar=ck).addCallback(self.getkeeplinks).addErrback(self.dataError)
			else:
				for (stream, dummy, hostername) in cleanedlist:
					if isSupportedHoster(hostername, True):
						hostername = hostername.replace('www.','').replace('embed.','').replace('play.','')
						self.filmliste.append((hostername, stream))
				self.showlinks()

	#TODO fix relink.to links
	# keeplinks only found in pornkino plugin
	def getkeeplinks(self, data):
		streams = re.findall('selecttext live">(http[s]?://(.*?)\/.*?)<', data, re.S|re.I)
		if streams:
			for (stream, hostername) in streams:
				if isSupportedHoster(hostername, True):
					hostername = hostername.replace('www.','').replace('embed.','').replace('play.','')
					self.filmliste.append((hostername, stream))
			self.showlinks()
		else:
			twAgentGetPage(self.keepurl, agent=MozillaAgent, cookieJar=ck).addCallback(self.loadKeepData).addErrback(self.dataError)

	def loadKeepData(self, data):
		link = re.search('captcha_div">.*?src="(.*?)"', data, re.S)
		if link:
			link = link.group(1)
			MyHeaders= {'Accept':'*/*', 
					'Accept-Language':'en-US,en;q=0.5',
					'Referer': self.keepurl}
			twAgentGetPage(link, agent=MozillaAgent, cookieJar=ck).addCallback(self.loadKeepPapi).addErrback(self.dataError)
		else:
			self.showlinks()

	def loadKeepPapi(self, data):
		link = re.search('ckey:\s+["|\'](.*?)["|\']', data, re.S)
		chalstamp = re.search('chalstamp:\s+(\d+)', data, re.S)
		if link and chalstamp:
			chalstamp1 = str(chalstamp.group(1))
			chalstamp2 = str(int(chalstamp.group(1))-763)
			link = 'http://api.solvemedia.com/papi/_challenge.js?k=%s;f=_ACPuzzleUtil.callbacks%s;l=en;t=img;s=standard;c=js,h5c,h5ct,svg,h5v,v/h264,v/ogg,v/webm,h5a,a/mp3,a/ogg,ua/firefox,ua/firefox47,os/linux,expand,swf11,swf11.2,swf,fwv/MwV2cA.ydnl74,jslib/jquery,htmlplus;am=mcivF63DyR-qzd5ircPJHw;ca=script;ts=%s;ct=%s;th=white;r=0.09173458138015778' % (link.group(1),'%5B0%5D', chalstamp2, chalstamp1)
			MyHeaders= {'Accept':'*/*', 
					'Accept-Language':'en-US,en;q=0.5',
					'Referer': self.keepurl}
			twAgentGetPage(link, agent=MozillaAgent, cookieJar=ck).addCallback(self.loadKeepPapi2).addErrback(self.dataError)
		else:
			self.showlinks()

	def loadKeepPapi2(self, data):
		link = re.search('"chid"\s+:\s+"(.*?)"', data, re.S)
		if link:
			url = "http://api.solvemedia.com/papi/media?c=%s;w=300;h=150;fg=000000;bg=f8f8f8" % link.group(1)
			MyHeaders= {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
					'Accept-Language':'en-US,en;q=0.5',
					'Accept-Encoding':"gzip, deflate", 
					'Referer': self.keepurl}
			twAgentGetPage(url, agent=MozillaAgent, cookieJar=ck, headers=MyHeaders).addCallback(self.loadKeepImg, link.group(1)).addErrback(self.dataError)
		else:
			self.showlinks()

	def loadKeepImg(self, data, adcopy):
		link = re.findall('url\("data:image/png;base64,(.*?)"', data, re.S)
		if link:
			jpgfile = ('/tmp/captcha.jpg')
			g = open(jpgfile, "w")
			g.write(base64.decodestring(link[-1]))
			g.close()
			self.captchainfo = {
				'myhiddenpwd': '',
				'hiddenaction':'Q2hlY2tJbmZv',
				'captchatype': 'Re',
				'hiddencaptcha':'1',
				'hiddenpwd':'',
				'used_captcha':'SolveMedia',
				'adcopy_challenge':adcopy,
				}
			self.session.openWithCallback(self.captchaCallback, VirtualKeyBoardExt, title = (_("Captcha input:")), text = "", captcha = "/tmp/captcha.jpg", is_dialog=True)
		else:
			self.showlinks()

	def captchaCallback(self, callback=None, entry=None):
		if callback != None or callback != "":
			self.captchainfo.update({'adcopy_response': callback})
			MyHeaders= {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					'Accept-Language':'en-US,en;q=0.5',
					'Accept-Encoding':"gzip, deflate",
					'Content-Type': 'application/x-www-form-urlencoded',
					'Referer': self.keepurl}
			
			twAgentGetPage(self.keepurl, agent=MozillaAgent, cookieJar=ck, method='POST', postdata=urlencode(self.captchainfo), headers=MyHeaders).addCallback(self.loadKeepFinalLinks).addErrback(self.dataError)
		else:
			self.showlinks()

	def loadKeepFinalLinks(self, data):
		parse = re.search('class="nolive">(.*?)</div>', data, re.S)
		if parse:
			streams = re.findall('<a href=[\'|"](http[s]?://(.*?)\/.*?)[\'|"]', parse.group(1), re.S)
			if streams:
					for (stream, hostername) in streams:
						if isSupportedHoster(hostername, True):
							hostername = hostername.replace('www.','').replace('embed.','').replace('play.','')
							self.filmliste.append((hostername, stream))
		self.showlinks()

	def showlinks(self):
		self.filmliste = list(set(self.filmliste))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self['name'].setText(self.Name)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, url):
		if re.search('no_cover', self.cover):
			cover = None
		else:
			cover = self.cover
		self.session.open(SimplePlayer, [(self.Name, url, cover)], showPlaylist=False, ltype='pornkino', cover=True)