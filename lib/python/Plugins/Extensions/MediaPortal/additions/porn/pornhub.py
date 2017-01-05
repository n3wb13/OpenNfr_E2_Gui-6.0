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
from Plugins.Extensions.MediaPortal.resources.configlistext import ConfigListScreenExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

config.mediaportal.pornhub_username = ConfigText(default="pornhubUserName", fixed_size=False)
config.mediaportal.pornhub_password = ConfigPassword(default="pornhubPassword", fixed_size=False)
config.mediaportal.pornhub_cdnfix = ConfigYesNo(default=False)

ck = {}
phLoggedIn = False
phAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"
json_headers = {
	'Accept':'application/json',
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/x-www-form-urlencoded',
	}

class pornhubGenreScreen(MPScreen):

	def __init__(self, session):
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue": self.keySetup
		}, -1)

		self.username = str(config.mediaportal.pornhub_username.value)
		self.password = str(config.mediaportal.pornhub_password.value)

		self['title'] = Label("Pornhub.com")
		self['ContentTitle'] = Label("Genre:")
		self['F4'] = Label(_("Setup"))
		self.keyLocked = True
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		if self.username != "pornhubUserName" and self.password != "pornhubPassword":
			if phLoggedIn:
				self.onLayoutFinish.append(self.layoutFinished)
			else:
				self.onLayoutFinish.append(self.Login)
		else:
			self.onLayoutFinish.append(self.layoutFinished)

	def Login(self):
		url = "http://www.pornhub.com"
		getPage(url, agent=phAgent, cookies=ck).addCallback(self.Login2).addErrback(self.dataError)

	def Login2(self, data):
		parse = re.findall('name="redirect"\svalue="(.*?)".*?id="token"\svalue="(.*?)"', data, re.S)
		if parse:
			loginUrl = "http://www.pornhub.com/front/authenticate"
			loginData = {
				'redirect' : str(parse[0][0]),
				'token' : str(parse[0][1]),
				'remember_me' : '1',
				'from' : 'pc_login_modal_:index',
				'username' : self.username,
				'password' : self.password
				}
			getPage(loginUrl, agent=phAgent, method='POST', postdata=urlencode(loginData), cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.Login3).addErrback(self.dataError)
		else:
			self.layoutFinished()

	def Login3(self, data):
		self.layoutFinished()

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.pornhub.com/categories"
		getPage(url, agent=phAgent, cookies=ck).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		self.filmliste = []
		global phLoggedIn
		if re.findall('class="(logged-in)"', data):
			phLoggedIn = True
		else:
			phLoggedIn = False
		Cats = re.findall('<div\sclass="category-wrapper">.*?<a\shref="(.*?)".*?<img\ssrc="(.*?)".*?alt="(.*?)"', data, re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				if re.match(".*\?",Url):
					Url = "http://www.pornhub.com" + Url + "&page="
				else:
					Url = "http://www.pornhub.com" + Url + "?page="
				self.filmliste.append((Title, Url, Image))
			self.filmliste.sort()
		if phLoggedIn:
			self.filmliste.insert(0, (400 * "—", None, None))
			#self.filmliste.insert(0, ("Previously Viewed", "http://www.pornhub.com/users/%s/videos/recent?page=" % self.username, None))
			self.filmliste.insert(0, ("My Feed", "http://www.pornhub.com/feeds?section=videos&page=", None))
			self.filmliste.insert(0, ("Recommended", "http://www.pornhub.com/recommended?page=", None))
			self.filmliste.insert(0, ("Member Subscriptions", "http://www.pornhub.com/users/%s/subscriptions?page=" % self.username, None))
			self.filmliste.insert(0, ("Channel Subscriptions", "http://www.pornhub.com/users/%s/channel_subscriptions?page=" % self.username, None))
			self.filmliste.insert(0, ("Pornstar Subscriptions", "http://www.pornhub.com/users/%s/pornstar_subscriptions?page=" % self.username, None))
			self.filmliste.insert(0, ("Favourite Playlists", "http://www.pornhub.com/users/%s/playlists/favorites?page=" % self.username, None))
			self.filmliste.insert(0, ("Favourite Videos", "http://www.pornhub.com/users/%s/videos/favorites?page=" % self.username, None))
		self.filmliste.insert(0, (400 * "—", None, None))
		self.filmliste.insert(0, ("Playlists", "http://www.pornhub.com/playlists?page=", None))
		self.filmliste.insert(0, ("Channels", "http://www.pornhub.com/channels?page=", None))
		self.filmliste.insert(0, ("Pornstars", "http://www.pornhub.com/pornstars?page=", None))
		self.filmliste.insert(0, ("Longest", "http://www.pornhub.com/video?o=lg&page=", None))
		self.filmliste.insert(0, ("Hottest", "http://www.pornhub.com/video?o=ht&page=", None))
		self.filmliste.insert(0, ("Top Rated", "http://www.pornhub.com/video?o=tr&page=", None))
		self.filmliste.insert(0, ("Most Viewed", "http://www.pornhub.com/video?o=mv&page=", None))
		self.filmliste.insert(0, ("Community Feed", "http://www.pornhub.com/community?content=videos&page=", None))
		if not phLoggedIn:
			self.filmliste.insert(0, ("Recommended", "http://www.pornhub.com/recommended?page=", None))
		self.filmliste.insert(0, ("Featured Recently", "http://www.pornhub.com/video?o=mr&page=", None))
		self.filmliste.insert(0, ("Newest", "http://www.pornhub.com/video?o=cm&page=", None))
		self.filmliste.insert(0, ("--- Search ---", "callSuchen", None))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.session.openWithCallback(self.SuchenCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.suchString, is_dialog=True, auto_text_init=False, suggest_func=self.getSuggestions)
		elif re.match(".*Subscriptions", Name):
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornhubSubscriptionsScreen, Link, Name)
		elif re.match(".*Pornstars", Name):
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornhubPornstarScreen, Link, Name)
		elif re.match(".*Channels", Name):
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornhubChannelScreen, Link, Name)
		elif re.match(".*Playlists", Name):
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornhubPlayListScreen, Link, Name)
		else:
			Link = self['liste'].getCurrent()[0][1]
			if Link:
				self.session.open(pornhubFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = 'http://www.pornhub.com/video/search?search=%s&page=' % self.suchString.replace(' ', '+')
			self.session.open(pornhubFilmScreen, Link, Name)

	def getSuggestions(self, text, max_res):
		url = "http://www.pornhub.com/video/search_autocomplete?pornstars=true&orientation=straight&q=%s" % urllib.quote_plus(text)
		d = twAgentGetPage(url, agent=phAgent, headers=json_headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, err=True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions['queries']:
				li = item
				list.append(str(li))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

	def keySetup(self):
		if mp_globals.isDreamOS:
			self.session.openWithCallback(self.setupCallback, pornhubSetupScreen, is_dialog=True)
		else:
			self.session.openWithCallback(self.setupCallback, pornhubSetupScreen)

	def setupCallback(self, answer=False):
		if answer:
			ck.clear()
			global phLoggedIn
			phLoggedIn = False
			self.username = str(config.mediaportal.pornhub_username.value)
			self.password = str(config.mediaportal.pornhub_password.value)
			self.Login()

class pornhubSetupScreen(Screen, ConfigListScreenExt):

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
		self['title'] = Label("Pornhub.com " + _("Setup"))
		self['F4'] = Label('')
		self.setTitle("Pornhub.com " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		self.list.append(getConfigListEntry(_("Username:"), config.mediaportal.pornhub_username))
		self.list.append(getConfigListEntry(_("Password:"), config.mediaportal.pornhub_password))
		self.list.append(getConfigListEntry(_("CDN fix (please don't use this option as default):"), config.mediaportal.pornhub_cdnfix))

		self["config"].setList(self.list)

		self["setupActions"] = ActionMap(["MP_Actions"],
		{
			"ok"    : self.keySave,
			"cancel": self.keyCancel
		}, -1)

	def keySave(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		self.close(True)

class pornhubPlayListScreen(MPScreen, ThumbsHelper):

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
			"green" : self.keyPageNumber,
			"yellow" : self.keySort,
			"blue" : self.keyFavourite
		}, -1)

		self['title'] = Label("Pornhub.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Sort"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.lock = False
		self.page = 1
		self.lastpage = 1
		self.sort = 'tr'
		self.sortname = "Top Rated"
		self.reload = False

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self.keyLocked = True
		url = self.Link + str(self.page) + "&o=%s" % self.sort
		getPage(url, agent=phAgent, cookies=ck).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		countprofile = re.findall('class="showingInfo">Showing up to (\d+) playlists.</div>', data, re.S)
		if countprofile:
			self.lastpage = int(round((float(countprofile[0].replace(',','')) / 30) + 0.5))
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self.getLastPage(data, 'class="pagination3">(.*?)</div>')
		preparse = re.search('class="sectionWrapper(.*?)class="pagination3"', data, re.S)
		if not preparse:
			preparse = re.search('class="sectionWrapper(.*?)id="profileInformation"', data, re.S)
		Cats = re.findall('class="playlist-videos">.*?class="number"><span>(.*?)</span>.*?src="(.*?jpg)".*?href="(/view_video.php.*?)".*?class="viewPlaylistLink"\shref="(.*?)".*?class="title"\stitle="(.*?)"', preparse.group(1), re.S)
		if Cats:
			for Videos, Image, PlayUrl, Url, Title in Cats:
				Url = "http://www.pornhub.com" + Url
				PlayUrl = "http://www.pornhub.com" + PlayUrl
				self.filmliste.append((decodeHtml(Title), Videos, Image, Url, PlayUrl))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No playlists found!'), "", None, None, None))
		self.ml.setList(map(self.pornhubPlayListEntry, self.filmliste))
		if not self.reload:
			self.ml.moveToIndex(0)
		self.reload = False
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 3, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		submsg = ""
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)
		if phLoggedIn:
			if self.Name == "Favourite Playlists":
				submsg = ""
				self['F4'].setText(_("Remove Favourite"))
			else:
				url = self['liste'].getCurrent()[0][3]
				self.lock = True
				self['F4'].setText('')
				getPage(url, agent=phAgent, cookies=ck).addCallback(self.showInfos2).addErrback(self.dataError)
		self['handlung'].setText("%s: %s" % (_("Sort order"), self.sortname) + submsg)

	def showInfos2(self, data):
		fav = re.findall('var\salreadyAddedToFav\s=\s(\d);', data, re.S)
		isfav = str(fav[0])
		if isfav == "1":
			submsg = "\nFavourite"
			self['F4'].setText(_("Remove Favourite"))
		else:
			submsg = ""
			self['F4'].setText(_("Add Favourite"))
		self.lock = False
		self['handlung'].setText("%s: %s" % (_("Sort order"), self.sortname) + submsg)

	def keyOK(self):
		CatLink = self['liste'].getCurrent()[0][3]
		NameLink = self['liste'].getCurrent()[0][0]
		self.session.open(pornhubFilmScreen, CatLink, NameLink)

	def keySort(self):
		if self.keyLocked:
			return
		if self.Name == "Favourite Playlists":
			rangelist = [['Top Rated', 'tr'], ['Most Viewed','mv'], ['Most Recent','mr']]
		else:
			rangelist = [['Top Rated', 'tr'], ['Most Favorited', 'mf'], ['Most Viewed','mv'], ['Most Recent','mr']]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sortname = result[0]
			self.loadPage()

	def keyFavourite(self):
		if self.keyLocked:
			return
		if self.lock:
			return
		if phLoggedIn:
			self.playurl = self['liste'].getCurrent()[0][3]
			if self.playurl:
				getPage(self.playurl, agent=phAgent, cookies=ck).addCallback(self.parseFavourite).addErrback(self.dataError)

	def parseFavourite(self, data):
		parse = re.findall('var\stoken\s=\s"(.*?)";.*?var\salreadyAddedToFav\s=\s(\d);.*?var\splaylistId\s=\s"(\d+)";', data, re.S)
		if parse:
			isfav = str(parse[0][1])
			favtoken = str(parse[0][0])
			id = str(parse[0][2])
			if isfav == "1":
				FavUrl = "http://www.pornhub.com/playlist/remove_favourite?playlist_id=%s&token=%s" % (id, favtoken)
			else:
				FavUrl = "http://www.pornhub.com/playlist_json/favourite?playlist_id=%s&token=%s" % (id, favtoken)
			getPage(FavUrl, agent=phAgent, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded','Referer':self.playurl}).addCallback(self.ok).addErrback(self.dataError)
			self.reload = True
			self.loadPage()

	def ok(self, data):
		#print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
		#print data
		#print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
		pass

class pornhubSubscriptionsScreen(MPScreen, ThumbsHelper):

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
			"red" : self.keySubscribe,
			"green" : self.keyPageNumber,
			"yellow" : self.keySort
		}, -1)

		self['title'] = Label("Pornhub.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F1'] = Label(_("Unsubscribe"))
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Sort"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		if self.Name == "Pornstar Subscriptions":
			self.sort = ''
			self.sortname = ''
		else:
			self.sort = '&orderby=recent_subscribers'
			self.sortname = 'Recent Subscriptions'
		self.reload = False

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self.keyLocked = True
		if self.page > 1 and self.Name == "Member Subscriptions":
			url = self.Link.replace('/subscriptions','/subscriptions/ajax') + str(self.page) + self.sort
			getPage(url, agent=phAgent, method='POST', cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)
		else:
			url = self.Link + str(self.page) + self.sort
			getPage(url, agent=phAgent, cookies=ck).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if self.page == 1 and self.Name == "Member Subscriptions":
			countprofile = re.findall('class="showingInfo">Showing up to (\d+) subscriptions.</div>', data, re.S)
			if countprofile:
				self.lastpage = int(round((float(countprofile[0].replace(',','')) / 100) + 0.5))
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
			else:
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
			parse = re.search('(.*?)class="profileContentRight', data, re.S)
			parsedata = parse.group(1)
		else:
			if self.Name == "Member Subscriptions":
				parsedata = data
			else:
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
				parse = re.search('(.*?)class="profileContentRight', data, re.S)
				parsedata = parse.group(1)
		Cats = re.findall('class="pornStarLink.*?href="(.*?)".*?img\sclass="avatar.*?src="(.*?)".*?alt="(.*?)"', parsedata, re.S)
		if not Cats:
			Cats = re.findall('class="userLink.*?\shref="(.*?)".*?img\sclass="avatar.*?src="(.*?)".*?alt="(.*?)"', parsedata, re.S)
			if not Cats:
				Cats = re.findall('class="channelSubChannel.*?a\shref="(.*?)".*?img\ssrc="(.*?)".*?wtitle">.*?>(.*?)</a.', parsedata, re.S)
		if Cats:
			for Url, Image, Title in Cats:
				if self.Name == "Member Subscriptions":
					Url = Url + '/videos/public?page='
				elif self.Name == "Pornstar Subscriptions":
					Url = Url + '?o=cm&page='
				else:
					Url = Url + '/videos?o=da&page='
				Url = 'http://www.pornhub.com' + Url
				self.filmliste.append((decodeHtml(Title), Url, Image))
			if self.Name == "Pornstar Subscriptions" and self.sortname == "Pornstar Name":
				self.filmliste.sort()
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No subscriptions found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		if not self.reload:
			self.ml.moveToIndex(0)
		self.reload = False
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		self['handlung'].setText("%s: %s" % (_("Sort order"), self.sortname))
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(pornhubFilmScreen, Link, Name)

	def keySort(self):
		if self.keyLocked:
			return
		if self.Name == "Channel Subscriptions":
			rangelist = [['Recent Subscriptions', '&orderby=recent_subscribers'], ['Channel Name','&orderby=channel_title'], ['Channel Rank','&orderby=channel_rank']]
		elif self.Name == "Member Subscriptions":
			rangelist = [['Recent Subscriptions', '&orderby=recent_subscribers'], ['Username','&orderby=username'], ['Recent Users','&orderby=recent_users'], ['Recent Loggged In','&orderby=recent_logins']]
		elif self.Name == "Pornstar Subscriptions":
			rangelist = [['Recent Subscriptions', ''], ['Pornstar Name','']]
		else:
			return
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sortname = result[0]
			self.loadPage()

	def keySubscribe(self):
		if self.keyLocked:
			return
		if phLoggedIn:
			url = self['liste'].getCurrent()[0][1]
			if url:
				url = url + "1"
				getPage(url, agent=phAgent, cookies=ck).addCallback(self.parseSubscribe).addErrback(self.dataError)

	def parseSubscribe(self, data):
		subs = re.findall('data-unsubscribe-url="(.*?)"', data, re.S)
		if subs:
			url = 'http://www.pornhub.com' + subs[0].replace('&amp;','&')
			getPage(url, agent=phAgent, cookies=ck).addCallback(self.parseSubscribe2).addErrback(self.dataError)

	def parseSubscribe2(self, data):
		unsub = re.findall('(Subscription removed.*?PASS)', data, re.S)
		if unsub:
			self.reload = True
			self.loadPage()
		else:
			self.session.open(MessageBoxExt, _("Unknown error."), MessageBoxExt.TYPE_INFO)

class pornhubPornstarScreen(MPScreen, ThumbsHelper):

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
			"red" : self.keySubscribe,
			"green" : self.keyPageNumber,
			"yellow" : self.keySort
		}, -1)

		self['title'] = Label("Pornhub.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Sort"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.sort = 'mp'
		self.sortname = "Most Popular"
		self.reload = False

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self.keyLocked = True
		url = self.Link + str(self.page) + "&o=%s" % self.sort
		getPage(url, agent=phAgent, cookies=ck).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.getLastPage(data, 'class="pagination3">(.*?)</div>')
		parse = re.search('class="textFilter">.*?</span>(.*)', data, re.S)
		Cats = re.findall('rank_number">(.*?)<.*?src="(.*?)".*?href="(.*?)".*?class="title.*?>(.*?)<.*?videosNumber">(.*?)\sVideos', parse.group(1), re.S)
		if Cats:
			for Rank, Image, Url, Title, Videos in Cats:
				Url = 'http://www.pornhub.com' + Url + "?page="
				self.filmliste.append((decodeHtml(Title), Url, Image, Rank.strip(), Videos))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No pornstars found!'), None, None, "", ""))
		self.ml.setList(map(self.pornhubPornstarListEntry, self.filmliste))
		if not self.reload:
			self.ml.moveToIndex(0)
		self.reload = False
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		self['handlung'].setText("%s: %s" % (_("Sort order"), self.sortname))
		CoverHelper(self['coverArt']).getCover(Image)
		if phLoggedIn:
			url = self['liste'].getCurrent()[0][1] + "1"
			getPage(url, agent=phAgent, cookies=ck).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		subs = re.findall('data-subscribed="(\d)"', data, re.S)
		Subscribed = str(subs[0])
		if Subscribed == "1":
			submsg = "\nSubscribed"
			self['F1'].setText(_("Unsubscribe"))
		else:
			submsg = ""
			self['F1'].setText(_("Subscribe"))
		self['handlung'].setText("%s: %s" % (_("Sort order"), self.sortname) + submsg)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Count = self['liste'].getCurrent()[0][4]
		self.session.open(pornhubFilmScreen, Link, Name, Count)

	def keySort(self):
		if self.keyLocked:
			return
		rangelist = [['Most Popular', 'mp'], ['Most Subscribed', 'ms'], ['Most Viewed','mv'], ['Top Trending','t'], ['Number Of Videos','nv']]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sortname = result[0]
			self.loadPage()

	def keySubscribe(self):
		if self.keyLocked:
			return
		if phLoggedIn:
			url = self['liste'].getCurrent()[0][1] + "1"
			getPage(url, agent=phAgent, cookies=ck).addCallback(self.parseSubscribe).addErrback(self.dataError)

	def parseSubscribe(self, data):
		subs = re.findall('data-subscribe-url="(.*?)"\sdata-unsubscribe-url="(.*?)"\sdata-subscribed="(.*?)"', data, re.S)
		if subs:
			Subscribed = subs[0][2]
			if Subscribed == "1":
				url = 'http://www.pornhub.com' + subs[0][1].replace('&amp;','&')
			else:
				url = 'http://www.pornhub.com' + subs[0][0].replace('&amp;','&')
			getPage(url, agent=phAgent, cookies=ck).addCallback(self.parseSubscribe2).addErrback(self.dataError)

	def parseSubscribe2(self, data):
		unsub = re.findall('(Subscription removed.*?PASS)', data, re.S)
		if unsub:
			self.reload = True
			self.loadPage()
		else:
			sub = re.findall('(Subscription added.*?PASS)', data, re.S)
			if sub:
				self.reload = True
				self.loadPage()
			else:
				self.session.open(MessageBoxExt, _("Unknown error."), MessageBoxExt.TYPE_INFO)

class pornhubChannelScreen(MPScreen, ThumbsHelper):

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
			"red" : self.keySubscribe,
			"green" : self.keyPageNumber,
			"yellow" : self.keySort
		}, -1)

		self['title'] = Label("Pornhub.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Sort"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.sort = 'rk'
		self.sortname = "Most Popular"
		self.reload = False

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self.keyLocked = True
		url = self.Link + str(self.page) + "&o=%s" % self.sort
		getPage(url, agent=phAgent, cookies=ck).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.getLastPage(data, 'class="pagination3">(.*?)</div>')
		Cats = re.findall('class="channelsWrapper.*?ref="(.*?)".*?class="rank"><span>Rank<br/>\s{0,1}(\d+)</span>.*?img\salt="(.*?)"\ssrc="(.*?)".*?Subscribers.*?<li><span>(.*?)</span>\s{0,1}Videos</li>.*?.*?data-subscribe-url="(.*?)"\sdata-unsubscribe-url="(.*?)"\sdata-subscribed="(.*?)"', data, re.S)
		if Cats:
			for Url, Rank, Title, Image, Videos, Reg, Unreg, Subscribed in Cats:
				Url = 'http://www.pornhub.com' + Url + "/videos?o=da&page="
				Reg = 'http://www.pornhub.com' + Reg.replace('&amp;','&')
				Unreg = 'http://www.pornhub.com' + Unreg.replace('&amp;','&')
				Videos = Videos.replace(',','')
				self.filmliste.append((decodeHtml(Title), Url, Image, Rank.strip(), Videos, Reg, Unreg, Subscribed))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No channels found!'), None, None, "", "", None, None, ""))
		self.ml.setList(map(self.pornhubPornstarListEntry, self.filmliste))
		if not self.reload:
			self.ml.moveToIndex(0)
		self.reload = False
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		submsg = ""
		Image = self['liste'].getCurrent()[0][2]
		if phLoggedIn:
			Subscribed = self['liste'].getCurrent()[0][7]
			if Subscribed == "1":
				submsg = "\nSubscribed"
				self['F1'].setText(_("Unsubscribe"))
			else:
				submsg = ""
				self['F1'].setText(_("Subscribe"))
		self['handlung'].setText("%s: %s" % (_("Sort order"), self.sortname) + submsg)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Count = self['liste'].getCurrent()[0][4]
		self.session.open(pornhubFilmScreen, Link, Name, Count)

	def keySort(self):
		if self.keyLocked:
			return
		rangelist = [['Most Popular', 'rk'], ['Trending', 'tr'], ['Most Recent','mr']]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sortname = result[0]
			self.loadPage()

	def keySubscribe(self):
		if self.keyLocked:
			return
		if phLoggedIn:
			Subscribed = self['liste'].getCurrent()[0][7]
			if Subscribed == "1":
				url = self['liste'].getCurrent()[0][6]
			else:
				url = self['liste'].getCurrent()[0][5]
			getPage(url, agent=phAgent, cookies=ck).addCallback(self.parseSubscribe).addErrback(self.dataError)

	def parseSubscribe(self, data):
		unsub = re.findall('(Subscription removed.*?PASS)', data, re.S)
		if unsub:
			self.reload = True
			self.loadPage()
		else:
			sub = re.findall('(Subscription added.*?PASS)', data, re.S)
			if sub:
				self.reload = True
				self.loadPage()
			else:
				self.session.open(MessageBoxExt, _("Unknown error."), MessageBoxExt.TYPE_INFO)

class pornhubFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Count=None):
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
			"red" : self.keySubscribe,
			"green" : self.keyPageNumber,
			"yellow" : self.keyRelated,
			"blue" : self.keyFavourite
		}, -1)

		self['title'] = Label("Pornhub.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.lock = False
		self.page = 1
		self.lastpage = 999
		self.count = None
		self.reload = False
		self.favourited = ""
		self.suburl = ""
		self.unsuburl = ""
		self.subscribed = ""
		self.id = ""
		self.favkey = ""
		self.favhash = ""

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*Feed",self.Name):
			url = self.Link + str(self.page)
		elif re.match(".*\/playlist\/",self.Link):
			self.lastpage = 1
			url = "%s" % self.Link
		else:
			url = "%s%s" % (self.Link, str(self.page))
		if re.match(".*Feed",self.Name):
			getPage(url, agent=phAgent, cookies=ck).addCallback(self.loadFeedData).addErrback(self.dataError)
		else:
			getPage(url, agent=phAgent, cookies=ck).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		countprofile = re.findall('class="showingInfo">Showing up to (?:<span class="totalSpan">)(\d+)(?:</span>) videos.</div>', data, re.S)
		if countprofile:
			self.lastpage = int(round((float(countprofile[0].replace(',','')) / 48) + 0.5))
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			countprofile = re.findall('id="stats".*?SUBSCRIBERS.*?floatRight">(.*?)\s{0,1}<br/', data, re.S)
			if countprofile:
				self.lastpage = int(round((float(countprofile[0].replace(',','')) / 36) + 0.5))
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
			else:
				if self.Count:
					self.lastpage = int(round((float(self.Count) / 36) + 0.5))
					self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
				else:
					if self.lastpage == 1:
						self['page'].setText('1 / 1')
					else:
						if self.Name == "Related":
							self.lastpage = 6
							self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
						else:
							self.getLastPage(data, 'class="pagination3">(.*?)</div>')
		parse = re.search('class="nf-videos(.*?)class="pagination3">', data, re.S)
		if not parse:
			parse = re.search('class="videos\srow-5-thumbs(.*?)id="cmtWrapper">', data, re.S)
			if not parse:
				parse = re.search('class="videos\srow-5-thumbs(.*?)class="pagination3">', data, re.S)
				if not parse:
					parse = re.search('class="videos\srecommendedContainerLoseOne(.*?)class="pagination3">', data, re.S)
					if not parse:
						parse = re.search('class="profileVids">(.*?)class="profileContentRight', data, re.S)
						if not parse:
							parse = re.search('id="lrelateRecommendedItems"(.*?)</ul>', data, re.S)

		if parse:
			Movies = re.findall('class="videoblock.*?<a\shref="(.*?)".*?title="(.*?)".*?class="duration">(.*?)</var>.*?data-mediumthumb="(.*?)".*?<span\sclass="views"><var>(.*?)<.*?<var\sclass="added">(.*?)</var>', parse.group(1), re.S)
		if Movies:
			for (Url, Title, Runtime, Image, Views, Added) in Movies:
				Url = 'http://www.pornhub.com' + Url
				Title = Title.replace('&amp;amp;','&')
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views, Added))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None, "", "", ""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		if not self.reload:
			self.ml.moveToIndex(0)
		self.reload = False
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def loadFeedData(self, data):
		parse = re.findall('feedItemSection"(.*?)</section', data, re.S)
		if parse:
			for each in parse:
				Movies = re.findall('class="videoblock.*?<a\shref="(.*?)".*?title="(.*?)".*?class="duration">(.*?)</var>.*?data-mediumthumb="(.*?)".*?<span\sclass="views"><var>(.*?)<.*?<var\sclass="added">(.*?)</var>', each, re.S)
				if Movies:
					for (Url, Title, Runtime, Image, Views, Added) in Movies:
						Url = 'http://www.pornhub.com' + Url
						Title = Title.replace('&amp;amp;','&')
						self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views, Added))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None, "", "", ""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		if not self.reload:
			self.ml.moveToIndex(0)
		self.reload = False
		self.keyLocked = False
		self['page'].setText(str(self.page))
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		self.count = 0
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)
		if phLoggedIn:
			self.url = self['liste'].getCurrent()[0][1]
			if self.url:
				self.lock = True
				self['F1'].setText('')
				self['F3'].setText('')
				self['F4'].setText('')
				getPage(self.url, agent=phAgent, cookies=ck).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		added = self['liste'].getCurrent()[0][5]
		self.favourited = ""
		self.suburl = ""
		self.unsuburl = ""
		self.subscribed = ""
		favparse = re.findall('favouriteUrl.*?token.*?:\s\'(.*?)\',.*?itemId.*?:\s\'(\d+)\',.*?isFavourite.*?:\s(\d),', data, re.S)
		if favparse:
			self.favtoken = str(favparse[0][0])
			self.id = str(favparse[0][1])
			self.favourited = str(favparse[0][2])
		userinfo = re.findall('From:.*?data-type="(.*?)".*?bolded">(.*?)</', data, re.S)
		if userinfo:
			usertype = userinfo[0][0].title()
			username = userinfo[0][1]
		else:
			username = "unknown"
			usertype = ""
		if not username == "unknown":
			subparse = re.findall('data-subscribe-url="(.*?)"\sdata-unsubscribe-url="(.*?)"\sdata-subscribed="(.*?)"', data, re.S)
			if subparse:
				self.suburl = 'http://www.pornhub.com' + subparse[0][0].replace('&amp;','&')
				self.unsuburl = 'http://www.pornhub.com' + subparse[0][1].replace('&amp;','&')
				self.subscribed = str(subparse[0][2])
		if self.subscribed == "1":
			submsg = "\n" + usertype + ": " + username + " - Subscribed"
			self['F1'].setText(_("Unsubscribe"))
		elif self.subscribed == "0":
			submsg = "\n" + usertype + ": " + username
			self['F1'].setText(_("Subscribe"))
		else:
			submsg = ""
			self['F1'].setText("")
		if self.favourited == "1":
			if self.Name == "Favourite Videos":
				favmsg = ""
			else:
				favmsg = "\nFavourited"
			self['F4'].setText(_("Remove Favourite"))
		elif self.favourited == "0":
			favmsg = ""
			self['F4'].setText(_("Add Favourite"))
		else:
			favmsg = ""
			self['F4'].setText("")
		if not self.id == '':
			self['F3'].setText(_("Show Related"))
		else:
			self['F3'].setText("")
		self.lock = False
		self['handlung'].setText("Runtime: %s\nViews: %s\nAdded: %s%s%s" % (runtime, views, added, submsg, favmsg))

	def keyOK(self):
		if self.keyLocked:
			return
		self.url = self['liste'].getCurrent()[0][1]
		if self.url:
			getPage(self.url, agent=phAgent, cookies=ck).addCallback(self.parseData).addErrback(self.dataError)

	def keyFavourite(self):
		if self.keyLocked:
			return
		if self.lock:
			return
		if phLoggedIn:
			FavUrl = "http://www.pornhub.com/video/favourite"
			toggle = self.favourited
			if toggle == "0":
				toggle = "1"
			elif toggle == "1":
				toggle = "0"
			FavData = {
				'id' : self.id,
				'token' : self.favtoken,
				'toggle' : toggle
				}
			getPage(FavUrl, agent=phAgent, method='POST', postdata=urlencode(FavData), cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded','Referer':self.url}).addCallback(self.ok).addErrback(self.dataError)
			if self.Name == "Favourite Videos":
				self.reload = True
				self.loadPage()
			else:
				self.showInfos()

	def keyRelated(self):
		if self.keyLocked:
			return
		if self.lock:
			return
		if self.id == '':
			return
		if phLoggedIn:
			RelatedUrl = "http://www.pornhub.com/video/relateds?ajax=1&id=%s&num_per_page=10&page=" % self.id
			self.session.open(pornhubFilmScreen, RelatedUrl, "Related")

	def keySubscribe(self):
		if self.keyLocked:
			return
		if self.lock:
			return
		if phLoggedIn:
			if self.subscribed == "1":
				url = self.unsuburl
			else:
				url = self.suburl
			if not self.suburl == "" and not self.unsuburl == "":
				getPage(url, agent=phAgent, cookies=ck).addCallback(self.parseSubscribe).addErrback(self.dataError)

	def parseSubscribe(self, data):
		unsub = re.findall('(Subscription removed.*?PASS)', data, re.S)
		if unsub:
			if re.match(".*Feed",self.Name):
				self.reload = True
				self.loadPage()
			else:
				self.showInfos()
		else:
			sub = re.findall('(Subscription added.*?PASS)', data, re.S)
			if sub:
				self.showInfos()
			else:
				self.session.open(MessageBoxExt, _("Unknown error."), MessageBoxExt.TYPE_INFO)

	def parseData(self, data):
		# retry till we get working cdn-d-vid-public.pornhub.com streamurl, cdn2b.video.pornhub.phncdn.com is not working properly
		if config.mediaportal.pornhub_cdnfix.value:
			if re.match('.*?cdn2b.video.pornhub.phncdn.com', data, re.S):
				self.count += 1
				if self.count < 20:
					self.keyOK()
				return
		Title = self['liste'].getCurrent()[0][0]
		match = re.findall('quality_720p.[=|:].\'{0,1}(.*?)["|\';]', data, re.S)
		if not match:
			match = re.findall('quality_480p.[=|:].\'{0,1}(.*?)["|\';]', data, re.S)
		if not match:
			match = re.findall('quality_240p.[=|:].\'{0,1}(.*?)["|\';]', data, re.S)
		fetchurl = urllib2.unquote(match[0]).replace('\/','/')
		vcserverurl = re.findall('vcServerUrl":"(.*?)"', data, re.S)
		vcserverurl = urllib2.unquote(vcserverurl[0])
		if fetchurl:
			if phLoggedIn:
				if vcserverurl.startswith('//'):
					vcserverurl = 'http:' + vcserverurl
					getPage(vcserverurl, agent=phAgent, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded','Referer':self.url}).addCallback(self.ok).addErrback(self.dataError)
			if fetchurl.startswith('//'):
				fetchurl = 'http:' + fetchurl
			mp_globals.player_agent = phAgent
			self.session.open(SimplePlayer, [(Title, fetchurl)], showPlaylist=False, ltype='pornhub')

	def ok(self, data):
		#print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
		#print data
		#print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
		pass