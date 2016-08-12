# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import TwAgentHelper
import base64

spezialagent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.46 Safari/535.11"

class megaskanksGenreScreen(MPScreen):

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
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("MegaSkanks.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.megaskanks.com"
		getPage(url, agent=std_headers).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cat = re.findall('cat-item-([0-9]+)"><a\shref="(.*?)".*?>(.*?)</a>\s\((.*?)\)', data, re.S)
		if Cat:
			for (ID, Url, Title, Count) in Cat:
				if ID != "1" and ID != "857" and ID != "906":
					Url = Url + "page/"
					self.genreliste.append((decodeHtml(Title), Url, Count.replace(",","")))
			self.genreliste.sort()
		self.genreliste.insert(0, ("Newest", "http://www.megaskanks.com/page/", None))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()

		else:
			Link = self['liste'].getCurrent()[0][1]
			count = self['liste'].getCurrent()[0][2]
			self.session.open(megaskanksFilmScreen, Link, Name, count)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = '%s' % (self.suchString)
			Name = "--- Search ---"
			count = None
			self.session.open(megaskanksFilmScreen, Link, Name, count)

class megaskanksFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Count):
		self.Link = Link
		self.Name = Name
		self.Count = Count
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
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("MegaSkanks.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://www.megaskanks.com/page/%s/?s=%s" % (str(self.page), self.Link)
		else:
			url = "%s%s/" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if self.Count:
			self.lastpage = int(round((float(self.Count) / 15) + 0.5))
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self.getLastPage(data, '', 'class=\'pages\'>.*?of\s(.*?)</span>')
		Movies = re.findall('PostHeader.*?<a\shref="(.*?)".*?title=".*?">\n{0,2}(.*?)</a>.*?PostHeaderIcons.*?>.*?<.*?PostContent(.*?)PostMetadataFooter', data, re.S|re.I)
		if Movies:
			for (Url, Title, Image) in Movies:
				if not (Title.strip() == "Direct Streaming"):
					Image = re.search('\ssrc=["|\'](.*?)["|\'].*?\/>', Image)
					if Image:
						Image = Image.group(1)
					else:
						Image = None
					Title = Title.strip()
					self.filmliste.append((decodeHtml(Title), Url, Image))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(megaskanksStreamListeScreen, Link, Title)

class megaskanksStreamListeScreen(MPScreen):

	def __init__(self, session, streamFilmLink, streamName):
		self.streamFilmLink = streamFilmLink
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("MegaSkanks.com")
		self['name'] = Label(self.streamName)
		self['ContentTitle'] = Label("Streams:")

		self.tw_agent_hlp = TwAgentHelper(followRedirect=True)
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.streamFilmLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		parse = re.search('PostHeaderIcon.png(.*?)PostMetadataFooter', data, re.S)
		streams = re.findall('(<p>(\w+):\s)?<a\shref="(http.*?//(.*?)/.*?)"', parse.group(1), re.S|re.I)
		if streams:
			for (x, hoster, stream, hostername) in streams:
				stream = stream.split('"')[0].replace("putlocker","firedrive").replace('https', 'http')
				if isSupportedHoster(stream, True):
					self.filmliste.append((hostername, stream))
				if re.match('(.*?\.allanalpass.com|sh.st|linkshrink.net|adfoc.us|adf.ly|www\.amy\.gs)', hostername, re.S|re.I):
					hostername = hostername.replace('www.allanalpass.com', 'Allanalpass redirect')
					hostername = hostername.replace('sh.st', 'Sh redirect %s' % hoster.capitalize())
					hostername = hostername.replace('linkshrink.net', 'Linkshrink redirect')
					hostername = hostername.replace('adfoc.us', 'Adfoc redirect')
					hostername = hostername.replace('adf.ly', 'ADF redirect %s' % hoster.capitalize())
					hostername = hostername.replace('www.amy.gs', 'AMY redirect %s' % hoster.capitalize())
					disc = re.search('.*?(CD1|CD2).*?', stream, re.S|re.I)
					if disc:
						discno = disc.group(1)
						discno = discno.replace('CD1','Teil 1').replace('CD2','Teil 2')
						hostername = hostername + ' (' + discno + ')'
					self.filmliste.append((hostername, stream))
		if len(self.filmliste) == 0:
			self.filmliste.append(("No Hoster found.", ""))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self['name'].setText(self.streamName)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		streamHoster = self['liste'].getCurrent()[0][0]
		if streamLink == None:
			return
		url = streamLink
		self['name'].setText(_('Please wait...'))
		if re.search('redirect', streamHoster):
			self.checkStreamLink(url)
		else:
			self.get_stream(url)

	def checkStreamLink(self, url):
		if re.search('http.*?sh\.st', url): # and allanal sh.st
			getPage(url, agent=spezialagent).addCallback(self.shst, url).addErrback(self.dataError)
		elif re.search('http.*?allanalpass\.com', url): # and allanal sh.st
			getPage(url, agent=spezialagent).addCallback(self.allanal, url).addErrback(self.dataError)
		elif re.search('http.*?linkshrink\.net', url): # and allanal sh.st
			getPage(url, agent=spezialagent).addCallback(self.linkshrink, url).addErrback(self.dataError)
		elif re.search('http.*?adfoc\.us', url): # and allanal sh.st
			getPage(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}).addCallback(self.adfoc).addErrback(self.dataError)
		elif re.search('http.*?adf\.ly', url):
			getPage(url, agent=spezialagent).addCallback(self.adfly).addErrback(self.dataError)
		elif re.search('http.*?amy\.gs', url):
			getPage(url, agent=spezialagent).addCallback(self.allanal, url).addErrback(self.dataError)

	def adfly(self, data):
		ysmm = re.search("var\sysmm\s=\s'(.*?)'", data)
		if ysmm:
			ysmm = ysmm.group(1)
			left = ''
			right = ''
			for c in [ysmm[i:i+2] for i in range(0, len(ysmm), 2)]:
				left += c[0]
				right = c[1] + right
			url = base64.b64decode(left.encode() + right.encode())[2:].decode()
			if re.search(r'go\.php\?u\=', url):
				url = base64.b64decode(re.sub(r'(.*?)u=', '', url)).decode()
			self.get_stream(str(url))
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def adfoc(self, data):
		link = re.findall('var\sclick_url\s=\s"(.*?)"', data, re.S)
		if link:
			self.get_stream(link[0])
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def linkshrink(self, data, baseurl):
		link = re.findall('<a\sclass="bt"\shref="(.*?)"', data)
		if link:
			url = link[0]
			user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
			self.tw_agent_hlp.headers['User-Agent'] = user_agent
			self.tw_agent_hlp.headers['Referer'] = baseurl
			self.tw_agent_hlp.getRedirectedUrl(url).addCallback(self.linkshrinkLink).addErrback(self.dataError)

	def linkshrinkLink(self, url):
		if re.search('(www.allanalpass.com|linkbucks.com|adfoc.us)', url):
			self.checkStreamLink(url)
		else:
			self.get_stream(url)

	def shst(self, data, baseurl):
		session_id = re.findall('sessionId:\s"(.*?)"', data)
		if session_id:
			url = 'http://sh.st/shortest-url/end-adsession?adSessionId=%s' % (session_id[0])
			reactor.callLater(6, self.shstData, url, baseurl)
			message = self.session.open(MessageBoxExt, _("Stream starts in 6 sec."), MessageBoxExt.TYPE_INFO, timeout=6)
		else:
			self.stream_not_found()

	def shstData(self, url, baseurl):
		http_header = {
			"Accept": "*/*",
			"Accept-Encoding": "gzip,deflate",
			"Accept-Language": "en-US,en;,q=0.8",
			"Host": "sh.st",
			"Referer": baseurl,
			"Origin": "http://sh.st",
			"X-Requested-With": "XMLHttpRequest"
		}
		getPage(url, agent=spezialagent, headers=http_header).addCallback(self.shstLink).addErrback(self.dataError)

	def shstLink(self, data):
		VideoUrl = re.findall('destinationUrl":"(.*?)"', data, re.S)
		if VideoUrl:
			url = VideoUrl[0].replace('\/','/')
			if re.search('(www.allanalpass.com|linkbucks.com|adfoc.us)', url):
				self.checkStreamLink(url)
			else:
				self.get_stream(url)
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def allanal(self, data, baseurl):
		Tokens = re.findall("Token:\s'(.*?)',.*?'thKey']\s=\s(.*?);", data, re.S)
		if Tokens:
			addToken = re.findall("\s\s\sparams\['Au' \+ 'th' \+ 'Key'\] = params\['AuthK' \+ 'ey'\] \+ (.*?);", data)
			if addToken:
				Token2 = int(Tokens[-1][1]) + int(addToken[-1])
				if Token2 == int(Tokens[0][1]):
					Token2 = int(Tokens[1][1]) + int(addToken[-1])
				if Token2 == int(Tokens[1][1]):
					Token2 = int(Tokens[1][1]) + int(addToken[-1])
				if Token2 == int(Tokens[0][1]):
					Token2 = int(Tokens[0][1]) + int(addToken[-1])
				rand = random.randrange(10000000,99999999)
				url = "http://www.allanalpass.com/scripts/generated/key.js?t=%s&%s" % (Tokens[-1][0],rand)
				getPage(url).addCallback(self.allanalVideoLink2, Tokens[-1][0], Token2).addErrback(self.dataError)
			else:
				message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def allanalVideoLink2(self, data, token1, token2):
		url = "http://www.linkbucksmedia.com/director/?t=%s" % token1
		getPage(url).addCallback(self.allanalVideoLink3, token1, token2).addErrback(self.dataError)

	def allanalVideoLink3(self, data, token1, token2):
		url = "http://www.allanalpass.com/intermission/loadTargetUrl?t=%s&aK=%s" % (token1, token2)
		reactor.callLater(6, self.allanalVideoLink4, url)
		message = self.session.open(MessageBoxExt, _("Stream starts in 6 sec."), MessageBoxExt.TYPE_INFO, timeout=6)

	def allanalVideoLink4(self, url):
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded','Referer':'http://www.allanalpass.com/ZRv2'}).addCallback(self.allanalVideoLink5).addErrback(self.dataError)

	def allanalVideoLink5(self, data):
		VideoUrl = re.findall('Url":"(.*?)"', data, re.S)
		if VideoUrl:
			url = VideoUrl[0]
			self.get_stream(url)
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def get_stream(self,url):
		self['name'].setText(self.streamName)
		get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		self['name'].setText(self.streamName)
		self.session.open(SimplePlayer, [(self.streamName, stream_url)], showPlaylist=False, ltype='megaskanks')