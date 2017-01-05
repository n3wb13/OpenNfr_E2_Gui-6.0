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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import TwAgentHelper
import base64

baseurl = "http://streamxxxfree.com"
basename = "WTFvideofree"

class wtfvideofreeGenreScreen(MPScreen):

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
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.filmliste.append(("--- Search ---", None))
		self.filmliste.append(("Latest", baseurl))
		self.filmliste.append(("Categories", "categories"))
		self.filmliste.append(("Genres", "genres"))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(wtfvideofreeListScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Latest":
			self.session.open(wtfvideofreeListScreen, Link, Name)
		else:
			self.session.open(wtfvideofreeSubGenreScreen, Link, Name)

class wtfvideofreeSubGenreScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("%s:" % self.Name)
		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.parseData(None)

	def parseData(self, data):
		if self.Link == "categories":
			categorie = {'Brazzers': '/watch/category/brazzers', 'Bangbros': '/watch/category/bangbros', 'Realitykings': '/watch/category/realitykings',
						'Mofos': '/watch/category/mofos', 'Naughtyamerica': '/watch/category/naughtyamerica', 'Digitalplayground': '/?s=Digitalplayground',
						'Kink': '/?s=kink', 'EvilAngel': '/?s=EvilAngel', 'Digital Sin': '/?s=Digital%20Sin'}
			for item in categorie:
				self.filmliste.append((item, "%s%s" % (baseurl,categorie[item])))
		else:
			categorie = {'Ass': 'ass', 'Ass-to-Mouth': 'ass-to-mouth', 'Anal': 'anal', 'Asian': 'asian', 'Behind-the-Scene': 'behind-the-scene', 'Big-Dick': 'big-dick',
						'Big-Tits': 'big-tits', 'Black': 'black', 'Blonde': 'blonde', 'Blowjob': 'blowjob', 'Brunette': 'brunette', 'Bubble Butt': 'bubble-butt',
						'Butt': 'butt', 'College': 'college', 'Creampie': 'creampie', 'Cute': 'cute', 'Deepthroating': 'deepthroating', 'Hardcore': 'hardcore',
						'Interracial': 'interracial', 'Kink': 'kink', 'Lesbian': 'lesbian', 'Natural-Tits': 'natural-tits', 'Pornstarslikeitbig': 'pornstarslikeitbig',
						'Pov': 'pov', 'Realwifestories':'realwifestories', 'Shaved': 'shaved', 'Squirt': 'squirt', 'Sweet': 'sweet', 'Teen': 'teen','Threesome': 'threesome'}
			for item in categorie:
				self.filmliste.append((item, "%s/watch/tag/%s" % (baseurl,categorie[item])))
			self.filmliste.sort()
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No movies found!"), ''))
		self.filmliste = list(set(self.filmliste))
		self.filmliste.sort()
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(wtfvideofreeListScreen, Link, Name)

class wtfvideofreeListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "%s/page/%s/?s=%s" % (baseurl, str(self.page), self.Link)
		elif re.search("\?s=", self.Link):
			url = "%s/page/%s/?s=%s" % (baseurl, str(self.page), self.Link.split('?s=')[-1])
		else:
			url = self.Link + "/page/" + str(self.page) + "/"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, '', '<span>Page\s\d+\sof\s(.*?)</span>')
		preparse = re.search('"home-cont(ain\srelative|ent-out)">(.*?)</ul>', data, re.S)
		if preparse:
			if self.Name == 'Latest':
				raw = re.findall('<a\shref="(.*?)".*?src="(.*?)".*?<h2>(.*?)</h2>.*?<!--read-share-overlay-->', preparse.group(2), re.S)
			else:
				raw = re.findall('<a\shref="(http.*?)".*?src="(.*?)".*?widget-full-list-text.*?"\s*rel="bookmark">(.*?)<', preparse.group(2), re.S)
			x = []
			if raw:
				for (url, image, title) in raw:
					if url not in x:
						self.filmliste.append((decodeHtml(title).strip(), url, image))
						x.append(url)
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), '', None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		cover = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(cover)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][0]
		if Link == None:
			return
		Title = self['liste'].getCurrent()[0][1]
		self.session.open(StreamAuswahl, Link, Title)

class StreamAuswahl(MPScreen):

	def __init__(self, session, Title, Link):
		self.Link = Link
		self.Title = Title
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("%s" %self.Title)

		self.filmliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = self.Link
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('class="wordpress-post-tabs(.*?)class="wpts_cr', data, re.S)
		if parse:
			streamsids = re.findall('#tabs-(.*?)".*?(><a href="\s*(http[s]?://(.*?)\/.*?)" target="_blank"|)>((?!<s).*?)<', parse.group(1), re.S)
			if streamsids:
				for (id, x, link, hoster, quality) in streamsids:
					if not link:
						stream = re.findall('id="tabs-'+id+'.*?="\s*(http[s]?://(.*?)\/.*?)"', parse.group(1), re.S)
						if stream:
							if "streamdefence" in stream[0][1]:
								hoster = '%s - %s' % (quality, 'WTFCrypt')
								self.filmliste.append((hoster, stream[0][0]))
							elif "wtf-zone.xyz" in stream[0][1]:
								hoster = '%s - %s' % (quality, 'WTFZONE')
								self.filmliste.append((hoster, stream[0][0]))
							elif isSupportedHoster(stream[0][1], True):
								hoster = '%s - %s' % (quality, stream[0][1].replace('wtf-is-this.xyz', 'WTFISTHIS'))
								self.filmliste.append((hoster, stream[0][0]))
					else:
						if hoster != 'wtf-videos.xyz':
							hoster = '%s - %s' % (quality, hoster.replace('wtf-is-this.xyz', 'WTFISTHIS').replace('wtf-zone.xyz', 'WTFZONE'))
							self.filmliste.append((hoster, link.split(' ')[0]))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamHoster = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if url == None:
			return
		if re.search('WTFZONE', streamHoster):
			getPage(url).addCallback(self.wtfzoneembed).addErrback(self.dataError)
		elif re.search('WTFISTHIS', streamHoster):
			getPage(url).addCallback(self.wtfisthis).addErrback(self.dataError)
		elif re.search('WTFCrypt', streamHoster):
			getPage(url, headers={'Referer': self.Link}).addCallback(self.wtfcrypt).addErrback(self.dataError)
		else:
			get_stream_link(self.session).check_link(url, self.got_link)

	def wtfcrypt(self, data):
		key = re.search('document.write.*?\("(.*?)"', data)
		if key:
			wtfcode = re.sub('[^A-Za-z0-9\+\/\=]', '', key.group(1))
			mycode = base64.b64decode(base64.b64decode(wtfcode))
			key = re.search('document.write.*?\("(.*?)"', mycode)
			if key:
				wtfcode = re.sub('[^A-Za-z0-9\+\/\=]', '', key.group(1))
				mycode2 = base64.b64decode(base64.b64decode(wtfcode))
				stream_url = re.search('src="(http.*?)"', mycode2)
				if stream_url:
					stream_url = stream_url.group(1)
					get_stream_link(self.session).check_link(str(stream_url), self.got_link)
					return
		message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def wtfisthis(self, data):
		url = re.search('<a href="(http://wtf-is-this.xyz/\?r=.*?)"', data, re.S)
		if url:
			url = url.group(1)
			self.tw_agent_hlp = TwAgentHelper()
			self.tw_agent_hlp.getRedirectedUrl(url).addCallback(self.wtfisthisdata).addErrback(self.dataError)
		else:
			self.adfly(data)

	def wtfisthisdata(self, data):
		getPage(data).addCallback(self.adfly).addErrback(self.dataError)

	def wtfisthisembed(self, data):
		getPage(data).addCallback(self.adfly).addErrback(self.dataError)

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
			if re.search('wtf-zone\.xyz', url, re.S):
				self.wtfzone(str(url))
				return
			else:
				get_stream_link(self.session).check_link(str(url), self.got_link)
				return
		else:
			link = re.findall('="(http://wtf-zone\.xyz/view.*?)"', data, re.S)
			if link:
				self.wtfzone(link[0])
				return
		message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def wtfzone(self, url):
		if re.search('wtf-zone\.xyz/embed', url, re.S):
			link = url
		else:
			id = re.search('wtf-zone\.xyz/view/.*?/(.*?)$', url)
			if id:
				link = "http://wtf-zone.xyz/embed/%s" % str(id.group(1))
		getPage(link).addCallback(self.wtfzonelink).addErrback(self.dataError)

	def wtfzoneembed(self, data):
		link = re.search('embedURL"\scontent="(.*?)"', data)
		if link:
			getPage(link.group(1)).addCallback(self.wtfzonelink).addErrback(self.dataError)

	def wtfzonelink(self, data):
		stream_url = re.findall('\s+src="(http://[^wtf\-zone\.xyz].*?)"', data)
		if stream_url:
			stream_url = stream_url[-1]
			get_stream_link(self.session).check_link(str(stream_url), self.got_link)
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def got_link(self, stream_url):
		title = self.Title
		self.session.open(SimplePlayer, [(self.Title, stream_url)], showPlaylist=False, ltype='wtfvideofree')