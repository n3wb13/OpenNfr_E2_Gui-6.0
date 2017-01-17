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
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

config.mediaportal.vporn_username = ConfigText(default="vpornUserName", fixed_size=False)
config.mediaportal.vporn_password = ConfigPassword(default="vpornPassword", fixed_size=False)
config.mediaportal.vporn_hd = ConfigText(default="SD/HD", fixed_size=False)
config.mediaportal.vporn_date = ConfigText(default="all time", fixed_size=False)

ck = {}

class vpornGenreScreen(MPScreen):

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
			"left" : self.keyLeft,
			"green"	: self.keyHD,
			"yellow": self.keyDate,
			"blue": self.keySetup
		}, -1)

		self.hd = config.mediaportal.vporn_hd.value
		self.date = config.mediaportal.vporn_date.value
		self.username = str(config.mediaportal.vporn_username.value)
		self.password = str(config.mediaportal.vporn_password.value)

		self['title'] = Label("Vporn.com")
		self['ContentTitle'] = Label("Genre:")
		self['F2'] = Label(self.hd)
		self['F3'] = Label(self.date)
		self['F4'] = Label(_("Setup"))
		self.keyLocked = True
		self.loggedin = False
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		if self.username != "vpornUserName" and self.password != "vpornPassword":
			self.onLayoutFinish.append(self.Login)
		else:
			self.onLayoutFinish.append(self.layoutFinished)

	def Login(self):
		loginUrl = "http://www.vporn.com/login"
		loginData = {'backto': "", 'password': self.password, 'submit': 'Login', 'username': self.username}
		getPage(loginUrl, method='POST', postdata=urlencode(loginData), cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.Login2).addErrback(self.dataError)

	def Login2(self, data):
		if 'alt="Logout"' in data:
			self.loggedin = True
		self.layoutFinished()

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.vporn.com"
		getPage(url, cookies=ck).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		if not self.loggedin:
			message = self.session.open(MessageBoxExt, _("Login data is required for HD video playback!"), MessageBoxExt.TYPE_INFO, timeout=5)
		parse = re.search('<div\sclass="catslist(.*?)</div>', data, re.S)
		Cats = re.findall('<li\s{0,1}><a\shref="/cat/(.*?)">.*?>(.*?)</a></li>', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://www.vporn.com/cat/" + Url
				Title = Title.title()
				self.genreliste.append((Title, Url, None, False))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Longest", "http://www.vporn.com/longest/", None, True))
			self.genreliste.insert(0, ("Most Votes", "http://www.vporn.com/votes/", None, True))
			self.genreliste.insert(0, ("Most Comments", "http://www.vporn.com/comments/", None, True))
			self.genreliste.insert(0, ("Most Favorited", "http://www.vporn.com/favorites/", None, True))
			self.genreliste.insert(0, ("Most Viewed", "http://www.vporn.com/views/", None, True))
			self.genreliste.insert(0, ("Top Rated", "http://www.vporn.com/rating/", None, True))
			self.genreliste.insert(0, ("Newest", "http://www.vporn.com/newest/", None, True))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", None, False))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			Main = self['liste'].getCurrent()[0][3]
			self.session.open(vpornFilmScreen, Link, Name, self.hd, self.date, Main)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			self.session.open(vpornFilmScreen, Link, Name, self.hd, self.date, False)

	def keySetup(self):
		if mp_globals.isDreamOS:
			self.session.openWithCallback(self.setupCallback, vpornSetupScreen, is_dialog=True)
		else:
			self.session.openWithCallback(self.setupCallback, vpornSetupScreen)

	def setupCallback(self):
		pass

	def keyHD(self):
		if self.hd == "SD/HD":
			self.hd = "HD"
			config.mediaportal.vporn_hd.value = "HD"
		elif self.hd == "HD":
			self.hd = "SD/HD"
			config.mediaportal.vporn_hd.value = "SD/HD"

		config.mediaportal.vporn_hd.save()
		configfile.save()
		self['F2'].setText(self.hd)

	def keyDate(self):
		if self.date == "all time":
			self.date = "last 24h"
			config.mediaportal.vporn_date.value = "last 24h"
		elif self.date == "last 24h":
			self.date = "last week"
			config.mediaportal.vporn_date.value = "last week"
		elif self.date == "last week":
			self.date = "last month"
			config.mediaportal.vporn_date.value = "last month"
		elif self.date == "last month":
			self.date = "all time"
			config.mediaportal.vporn_date.value = "all time"

		config.mediaportal.vporn_date.save()
		configfile.save()
		self['F3'].setText(self.date)

class vpornSetupScreen(Screen, ConfigListScreenExt):

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
		self['title'] = Label("Vporn.com " + _("Setup"))
		self['F4'] = Label('')
		self.setTitle("Vporn.com " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		self.list.append(getConfigListEntry(_("Username:"), config.mediaportal.vporn_username))
		self.list.append(getConfigListEntry(_("Password:"), config.mediaportal.vporn_password))

		self["config"].setList(self.list)

		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"ok":		self.saveConfig,
			"cancel":	self.exit
		}, -1)

	def saveConfig(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close()

	def exit(self):
		self.close()

class vpornFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, HD, Date, Main):
		self.Link = Link
		self.Name = Name
		self.Main = Main
		if HD == "HD":
			self.hd = "hd/"
		else:
			self.hd = ""
		if Date == "last 24h":
			self.date = "today/"
		elif Date == "last week":
			self.date = "week/"
		elif Date == "last month":
			self.date = "month/"
		else:
			self.date = ""
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
			"blue" : self.keySort
		}, -1)

		self['title'] = Label("Vporn.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F4'] = Label(_("Sort"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.sort = 'newest'
		self.sortname = 'Newest'

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://www.vporn.com/search/?q=%s&page=%s&time=%s" % (self.Link, str(self.page), self.date)
		else:
			if self.Main:
				sort = ""
			else:
				sort = self.sort
			if self.page == 1:
				url = "%s%s/%s%s" % (self.Link, sort , self.date, self.hd)
			else:
				url = "%s%s/%s%s%s" % (self.Link, sort , self.date, self.hd, str(self.page))
		getPage(url, cookies=ck).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pager">(.*?)</div>')
		Movies = re.findall('thumbsArr\[.*?<a\shref="(.*?)"\sclass="thumb"><img\ssrc="(.*?)"\salt="(.*?)".*?class="time">(.*?)</span>.*?class="ileft">(.*?)\sviews', data, re.S)
		if Movies:
			for (Url, Image, Title, Runtime, Views) in Movies:
				Runtime = stripAllTags(Runtime).strip()
				Views = Views.replace(",","")
				self.filmliste.append((decodeHtml(Title).strip(), Url, Image, Runtime, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"), None, None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		if self['liste'].getCurrent()[0][1] != None:
			title = self['liste'].getCurrent()[0][0]
			pic = self['liste'].getCurrent()[0][2]
			runtime = self['liste'].getCurrent()[0][3]
			views = self['liste'].getCurrent()[0][4]
			self['name'].setText(title)
			self['handlung'].setText("Runtime: %s\nViews: %s\nSort order: %s" % (runtime, views, self.sortname))
			CoverHelper(self['coverArt']).getCover(pic)
		else:
			self['name'].setText('')

	def keySort(self):
		if self.keyLocked:
			return
		rangelist = [['Newest', 'newest'], ['Views','views'], ['Rating','rating'], ['Favorites','favorites']
					, ['Comments','comments'], ['Votes','votes'], ['Duration','longest']]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sortname = result[0]
			self.sort = result[1]
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url != None:
			self.keyLocked = True
			getPage(url, cookies=ck).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('flashvars.videoUrl(?:Low|Low2|Medium|Medium2|HD|HD2)\s=\s"(http.*?.mp4)"', data, re.S)
		if videoPage:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			url = videoPage[-1].replace('https://','http://')
			self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='vporn')