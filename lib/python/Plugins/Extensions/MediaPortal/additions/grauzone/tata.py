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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

try:
	from Plugins.Extensions.MediaPortal.resources import cfscrape
except:
	cfscrapeModule = False
else:
	cfscrapeModule = True

try:
	import requests
except:
	requestsModule = False
else:
	requestsModule = True

import urlparse
import thread

tat_cookies = CookieJar()
tat_ck = {}
tat_agent = ''
BASE_URL = 'http://www.tata.to'

def tat_grabpage(pageurl):
	if requestsModule:
		try:
			s = requests.session()
			url = urlparse.urlparse(pageurl)
			headers = {'User-Agent': tat_agent}
			page = s.get(url.geturl(), cookies=tat_cookies, headers=headers)
			return page.content
		except:
			pass

class tataMain(MPScreen):

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
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("tata.to")

		self.streamList = []
		self.suchString = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onFirstExecBegin.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		thread.start_new_thread(self.get_tokens,("GetTokens",))
		self['name'].setText(_("Please wait..."))

	def get_tokens(self, threadName):
		if requestsModule and cfscrapeModule:
			printl("Calling thread: %s" % threadName,self,'A')
			global tat_ck
			global tat_agent
			if tat_ck == {} or tat_agent == '':
				tat_ck, tat_agent = cfscrape.get_tokens(BASE_URL)
				requests.cookies.cookiejar_from_dict(tat_ck, cookiejar=tat_cookies)
			else:
				s = requests.session()
				url = urlparse.urlparse(BASE_URL)
				headers = {'user-agent': tat_agent}
				page = s.get(url.geturl(), cookies=tat_cookies, headers=headers, allow_redirects=False)
				if page.status_code == 503 and page.headers.get("Server") == "cloudflare-nginx":
					tat_ck, tat_agent = cfscrape.get_tokens(BASE_URL)
					requests.cookies.cookiejar_from_dict(tat_ck, cookiejar=tat_cookies)
			self.keyLocked = False
			reactor.callFromThread(self.getPage)
		else:
			reactor.callFromThread(self.tat_error)

	def tat_error(self):
		message = self.session.open(MessageBoxExt, _("Some mandatory Python modules are missing!"), MessageBoxExt.TYPE_ERROR)
		self.keyCancel()

	def getPage(self):
		if not mp_globals.requests:
			twAgentGetPage(BASE_URL, agent=tat_agent, cookieJar=tat_cookies).addCallback(self.loadPage).addErrback(self.dataError)
		else:
			data = tat_grabpage(BASE_URL)
			self.loadPage(data)

	def loadPage(self, data):
		self.keyLocked = True
		parse = re.search('Genres</span>(.*?)</ul>', data, re.S)
		if parse:
			cats = re.findall('href="(.*?)">(.*?)</a>', parse.group(1), re.S)
			if cats:
				for url, name in cats:
					url = url + '/'
					self.streamList.append((name, url))
		self.streamList.sort(key=lambda t : t[0].lower())
		self.streamList.insert(0, ("Serien","%s/tv/" % BASE_URL))
		self.streamList.insert(0, ("Filme","%s/filme/" % BASE_URL))
		self.streamList.insert(0, ("--- Search ---", None))
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
			self.suchen(auto_text_init=True)
		else:
			self.session.open(tataParsing, genre, url)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.strip()
			url = self.suchString
			genre = self['liste'].getCurrent()[0][0]
			self.session.open(tataParsing, genre, url)

class tataParsing(MPScreen):

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

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("tata.to")
		self['Page'] = Label(_("Page:"))
		self['ContentTitle'] = Label(genre)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		if re.match('.*?Search', self.genre):
			url = BASE_URL + '/filme/%s?suche=%s&type=alle' % (str(self.page), self.url)
		else:
			url = self.url + str(self.page)
		if not mp_globals.requests:
			twAgentGetPage(url, agent=tat_agent, cookieJar=tat_cookies).addCallback(self.parseData).addErrback(self.dataError)
		else:
			data = tat_grabpage(url)
			self.parseData(data)

	def parseData(self, data):
		self.getLastPage(data, 'class="page-nav">(.*?)</ul>', '.*(?:>|")(\d+)(?:<|")')
		movies = re.findall('<div class="ml-item-content">.*?<a href="(.*?)" class="ml-image">.*?<img src="(.*?)".*?<h6>(.*?)</h6>', data, re.S)
		if movies:
			for url,image,title in movies:
				title = title.strip().replace('<span class="mark-wc">','').replace('</span>','')
				self.streamList.append((decodeHtml(title), url, image))
		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), None, None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		self.coverurl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(self.coverurl, agent=tat_agent, cookieJar=tat_cookies)
		self['name'].setText(title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		if not mp_globals.requests:
			twAgentGetPage(url, agent=tat_agent, cookieJar=tat_cookies).addCallback(self.getAjax).addErrback(self.dataError)
		else:
			data = tat_grabpage(url)
			self.getAjax(data)

	def getAjax(self, data):
		ajax = re.findall('class="video-blk".*?data-url=["|\'](.*?)["|\']', data, re.S)
		if not mp_globals.requests:
			twAgentGetPage(ajax[0], agent=tat_agent, cookieJar=tat_cookies).addCallback(self.getStream).addErrback(self.dataError)
		else:
			data = tat_grabpage(ajax[0])
			self.getStream(data)

	def getStream(self, data):
		title = self['liste'].getCurrent()[0][0]
		cover = self['liste'].getCurrent()[0][2]
		stream = re.findall('link_mp4":"(.*?)"', data, re.S)
		if stream:
			url = stream[0].replace('\/','/')
			self.session.open(SimplePlayer, [(title, url, cover)], showPlaylist=False, ltype='tata', cover=True)
		else:
			self.session.open(MessageBoxExt, _("Sorry, can't extract a stream url."), MessageBoxExt.TYPE_INFO, timeout=5)