# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

basename = "Pokerstars.tv"
baseurl ="http://www.pokerstars.tv"

class pokerGenreScreen(MPScreen):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		u = "%s/en/tv/channels/" %(baseurl)
		getPage(u).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.findall('class="channel-list-item-box".*?href="(.*?)".*?src=.*?alt="(.*?)"', data, re.S)
		if parse:
			for (url,title) in parse:
				url = baseurl + url
				self.genreliste.append((decodeHtml(title),url))
			self.genreliste.sort()
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self['name'].setText("")

	def subnavcheck(self, data, name, url):
		check = re.findall('class="subNav">.*?<li class="cat-item">', data, re.S)
		if check:
			self.session.open(subnav, name, url)
		else:
			self.session.open(vids, name, url)

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if self.keyLocked:
			return
		getPage(url).addCallback(self.subnavcheck, name, url).addErrback(self.dataError)

class subnav(MPScreen):

	def __init__(self, session,name,url):
		self.url = url
		self.name = name
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

		self.keyLocked = True
		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "%s" %(self.url)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.findall('<li\sclass="cat-item">.*?<a\shref="(.*?)">(.*?)</a>', data, re.S)
		if parse:
			for (url,title) in parse:
				title = title.strip()
				url = baseurl + url
				self.filmliste.append((decodeHtml(title),url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self['name'].setText("")

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(vids, name, url)

class vids(MPScreen):

	def __init__(self, session,name,url):
		self.url = url
		self.name = name
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
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "%s" %(self.url)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.findall('summary">.*?href="(.*?)"\stitle="(.*?)".*?src="(.*?)"\s/>.*?class="play-icon">', data, re.S)
		if parse:
			for (url,title,pic) in parse:
				if pic.startswith("//"):
					pic = "http:"+pic
				self.filmliste.append((decodeHtml(title),url,pic))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		self['name'] = Label(_("Please wait..."))
		url = baseurl + self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.getID).addErrback(self.dataError)

	def getID(self, data):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		akamai=re.findall('itemprop="contentURL" content="(.*?)"', data, re.S)[0]
		if akamai:
			url = akamai + "&affiliateId=&v=3.4.0&fp=WIN%2017,0,0,169&r=BQWUO&g=EVXYCIPEUCIC"
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='pokerstars')
		else:
			message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)

	def noVideoError(self, error):
		try:
			if error.value.status == '404':
				message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)
		except:
			pass
		self.keyLocked = False
		raise error