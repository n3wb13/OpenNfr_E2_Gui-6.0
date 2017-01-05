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

class myspassGenreScreen(MPScreen):

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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("MySpass.de")
		self['ContentTitle'] = Label("Sendungen A-Z:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://www.myspass.de/ganze-folgen/"
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		ganze = re.findall('class="myspassTeaser _seasonId seasonlistItem.*?<a\shref="(/shows/.*?)".*?\s(?:data-original|img\ssrc)="(.*?\.jpg)".*?title="(.*?)"', data, re.S)
		if ganze:
			self.genreliste = []
			for (link, image, name) in ganze:
				link = "http://www.myspass.de%s" % link
				image = "http://www.myspass.de%s" % image
				self.genreliste.append((decodeHtml(name), link, image))
			# remove duplicates
			self.genreliste = list(set(self.genreliste))
			self.genreliste.sort()
		if len(self.genreliste) == 0:
			self.genreliste.append((_("No shows found!"), None, None))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		Title = self['liste'].getCurrent()[0][0]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Url = self['liste'].getCurrent()[0][1]
		if Url:
			self.session.open(myspassStaffelListeScreen, Name, Url)

class myspassStaffelListeScreen(MPScreen):

	def __init__(self, session, myspassName, myspassUrl):
		self.myspassName = myspassName
		self.myspassUrl = myspassUrl
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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("MySpass.de")
		self['ContentTitle'] = Label("Staffeln:")

		self.staffelliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.myspassUrl).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('data-category="full_episode".*?data-target="#episodes_season__category_">(.*?)</ul>', data, re.S)
		if parse:
			staffeln = re.findall('data-query=".*?.*?formatId=(\d+).*?seasonId=(\d+)&amp(.*?)data-target.*?>\t{0,5}\s{0,15}(.*?)</li', parse.group(1), re.S)
			if staffeln:
				self.staffelliste = []
				for (formatid, seasonid, pages, name) in staffeln:
					page = re.search('data-maxpages="(.*?)"', pages, re.S)
					if page:
						pages = page.group(1)
					else:
						pages = 0
					link = "http://www.myspass.de/frontend/php/ajax.php?ajax=true&query=getEpisodeListFromSeason&formatId=%s&seasonId=%s&category=full_episode&sortBy=episode_desc" % (formatid, seasonid)
					self.staffelliste.append((decodeHtml(name).strip(), link, pages))
		if len(self.staffelliste) == 0:
			self.staffelliste.append((_('No seasons found!'), None, 0))
		self.ml.setList(map(self._defaultlistleft, self.staffelliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Pages = self['liste'].getCurrent()[0][2]
		if Link:
			self.session.open(myspassFolgenListeScreen, Name, Link, Pages)

class myspassFolgenListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, myspassName, myspassUrl, myspassPages):
		self.myspassName = myspassName
		self.myspassUrl = myspassUrl
		self.myspassPages = myspassPages
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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label("MySpass.de")
		self['ContentTitle'] = Label("Folgen:")
		self['Page'] = Label(_("Page:"))

		self.page = 0
		self.lastpage = 0

		self.folgenliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.folgenliste = []
		url = "%s%s" % (self.myspassUrl, str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.lastpage = int(self.myspassPages)
		self['page'].setText(str(self.page+1) + ' / ' + str(self.lastpage+1))
		folgen = re.findall('data-original="(.*?)".\s{0,25}alt="(.*?)".*?--\/(\d+)\/">(.*?)</a>', data, re.S|re.I)
		if folgen:
			for (image, title, id, description) in folgen:
				link = "http://www.myspass.de/includes/apps/video/getvideometadataxml.php?id=%s" % id
				image = "http:" + image
				description = description.replace('\t','').replace('\n','')
				self.folgenliste.append((decodeHtml(title), link, image, description))
			self.ml.setList(map(self._defaultlistleft, self.folgenliste))
			self.keyLocked = False
			self.showInfos()
			self.th_ThumbsQuery(self.folgenliste, 0, 1, 2, None, None, self.page+1, self.lastpage+1, mode=1, pagefix=-1)

	def showInfos(self):
		streamTitle = self['liste'].getCurrent()[0][0]
		streamPic = self['liste'].getCurrent()[0][2]
		streamHandlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(streamTitle)
		self['handlung'].setText(streamHandlung)
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		self.myname = self['liste'].getCurrent()[0][0]
		self.mylink = self['liste'].getCurrent()[0][1]
		getPage(self.mylink).addCallback(self.get_link).addErrback(self.dataError)

	def get_link(self, data):
		stream_url = re.search('<url_flv><.*?CDATA\[(.*?)\]\]></url_flv>', data, re.S)
		if stream_url:
			self.session.open(SimplePlayer, [(self.myname, stream_url.group(1))], showPlaylist=False, ltype='myspass')

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 1:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.keyLocked:
			return
		if self.page < self.lastpage:
			self.page += 1
			self.loadPage()