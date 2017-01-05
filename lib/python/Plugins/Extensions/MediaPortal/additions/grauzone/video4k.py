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
from Components.ProgressBar import ProgressBar
from datetime import datetime, timedelta

glob_agent = getUserAgent()
base_apiurl = "http://video4k.to/request"

def postData(filter, type, page):
	post = urllib.urlencode({'bRegex': 'false',
							'bRegex_0': 'false',
							'bRegex_1': 'false',
							'bRegex_2': 'false',
							'bRegex_3': 'false',
							'bRegex_4': 'false',
							'bSearchable_0': 'true',
							'bSearchable_1': 'true',
							'bSearchable_2': 'true',
							'bSearchable_3': 'true',
							'bSearchable_4': 'true',
							'bSortable_0': 'false',
							'bSortable_1': 'true',
							'bSortable_2': 'false',
							'bSortable_3': 'false',
							'bSortable_4': 'true',
							'filter': filter,
							'iColumns': '5',
							'iDisplayLength': '100',
							'iDisplayStart': page,
							'iSortCol_0': '0',
							'iSortingCols': '1',
							'mDataProp_0': '0',
							'mDataProp_1': '1',
							'mDataProp_2': '1',
							'mDataProp_3': '3',
							'mDataProp_4': '4',
							'sColumns': '',
							'sEcho': '1',
							'sSearch': '',
							'sSearch_0': '',
							'sSearch_1': '',
							'sSearch_2': '',
							'sSearch_3': '',
							'sSearch_4': '',
							'sSortDir_0': 'asc',
							'type': type})
	return post

class video4kMain(MPScreen):

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

		self['title'] = Label("Video4K")
		self['ContentTitle'] = Label(_("Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(("Last Updates","updates"))
		self.streamList.append(("Cinema","cinema"))
		self.streamList.append(("All","ALL"))
		self.streamList.append(("#","#"))
		self.streamList.append(("A","A"))
		self.streamList.append(("B","B"))
		self.streamList.append(("C","C"))
		self.streamList.append(("D","D"))
		self.streamList.append(("E","E"))
		self.streamList.append(("F","F"))
		self.streamList.append(("G","G"))
		self.streamList.append(("H","H"))
		self.streamList.append(("I","I"))
		self.streamList.append(("J","J"))
		self.streamList.append(("K","K"))
		self.streamList.append(("L","L"))
		self.streamList.append(("M","M"))
		self.streamList.append(("N","N"))
		self.streamList.append(("O","O"))
		self.streamList.append(("P","P"))
		self.streamList.append(("Q","Q"))
		self.streamList.append(("R","R"))
		self.streamList.append(("S","S"))
		self.streamList.append(("T","T"))
		self.streamList.append(("U","U"))
		self.streamList.append(("V","V"))
		self.streamList.append(("W","W"))
		self.streamList.append(("X","X"))
		self.streamList.append(("Y","Y"))
		self.streamList.append(("Z","Z"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		genre = self['liste'].getCurrent()[0][0]
		type = self['liste'].getCurrent()[0][1]
		if genre == "Cinema" or genre == "Last Updates":
			self.session.open(video4kParsing, genre, type, '')
		else:
			self.session.open(video4kParsing, genre, 'movies', type)

class video4kParsing(MPScreen):

	def __init__(self, session, genre, type, filter):
		self.genre = genre
		self.type = type
		self.filter = filter
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		widgets_files = ('cover_widgets.xml',)
		self.skin = self.skin.replace('</screen>', '')
		for wf in widgets_files:
			path = "%s/%s/%s" % (self.skin_path, config.mediaportal.skin.value, wf)
			if not fileExists(path):
				path = self.skin_path + mp_globals.skinFallback + "/%s" % wf

			f = open(path, "r")
			for widget in f:
				self.skin += widget
			f.close()
		self.skin += '</screen>'

		MPScreen.__init__(self, session)

		self["hdpic"] = Pixmap()
		self['rating10'] = ProgressBar()
		self['rating0'] = Pixmap()
		self["hdpic"].hide()

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label("Video4K")
		self['ContentTitle'] = Label("")
		self['Page'] = Label(_("Page:"))
		self['F1'] = Label(_("Text-"))
		self['F2'] = Label(_("Page"))
		self['F4'] = Label(_("Text+"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 999
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['rating10'].setValue(0)
		self.streamList = []
		if self.page == 1:
			pageint = 0
		else:
			pageint = self.page * 100
		if self.type == "updates":
			dates = []
			sum = 0
			i = 0
			while i < 7:
				date_x_days_ago = datetime.now() - timedelta(days=i)
				dates.append(date_x_days_ago.strftime('%d.%m.%Y'))
				i += 1

			ds = defer.DeferredSemaphore(tokens=1)
			downloads = [ds.run(self.download, datum).addCallback(self.parseData2).addErrback(self.dataError) for datum in dates]
			finished = defer.DeferredList(downloads).addErrback(self.dataError)
		else:
			getPage(base_apiurl, method='POST', postdata=postData(self.filter, self.type, str(pageint)), agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest', 'Accept-Language':'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4,id;q=0.2,ru;q=0.2,tr;q=0.2'}).addCallback(self.parseData).addErrback(self.dataError)

	def download(self, datum):
		return getPage(base_apiurl, method='POST', postdata=postData(datum, self.type, '0'), agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest', 'Accept-Language':'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4,id;q=0.2,ru;q=0.2,tr;q=0.2'})

	def parseData(self, data):
		getLastpage = re.findall('"iTotalDisplayRecords":(\d+),', data, re.S|re.I)
		if getLastpage:
			if int(getLastpage[0]) < 100:
				self.lastpage = 1
			else:
				self.lastpage = int(getLastpage[0]) / 100
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self['page'].setText(str(self.page))
		movies = re.findall('title=."(.*?).".*?<span data-language=.*?rel=."#tt(.*?).">(.*?)<.*?flags./de.png." style=."opacity: (.*?);.".*?flags./en.png." style=."opacity: (.*?);.".*?.*?"IMDB\sRating:\s(.*?)."', data)
		if movies:
			for type,id,title,langDE,landEN,imdb in movies:
				if langDE != '0.3':
					lang = '1'
				else:
					lang = '2'
				self.streamList.append((decodeHtml(title),id,type,lang,imdb))
			if len(self.streamList) == 0:
				self.streamList.append((_('No movies found!'), None, None, None, None))
			else:
				self.ml.setList(map(self.kinoxlistleftflagged, self.streamList))
				self.keyLocked = False
				self.showInfos()

	def parseData2(self, data):
		getLastpage = re.findall('"iTotalDisplayRecords":(\d+),', data, re.S|re.I)
		if getLastpage:
			if int(getLastpage[0]) < 100:
				self.lastpage = 1
			else:
				self.lastpage = int(getLastpage[0]) / 100
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self['page'].setText(str(self.page))
		movies = re.findall('<img class=.*?title=."(Cinema|Movie).".*?<span data-language=."(.*?).".*?rel=."#tt(.*?).">(.*?)<.*?"IMDB\sRating:\s(.*?)."', data, re.S)
		if movies:
			for type,lang,id,title,imdb in movies:
				if lang == 'DE':
					lang = '1'
				else:
					lang = '2'
				self.streamList.append((decodeHtml(title),id,type,lang,imdb))
			if len(self.streamList) == 0:
				self.streamList.append((_('No movies found!'), None, None, None, None))
			else:
				self.ml.setList(map(self.kinoxlistleftflagged, self.streamList))
				self.keyLocked = False
				self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		id = self['liste'].getCurrent()[0][1]
		lang = self['liste'].getCurrent()[0][3]
		rate = self['liste'].getCurrent()[0][4]
		if lang == '1':
			lang = "de"
		else:
			lang = "en"
		rating = int(rate)*10 if rate else 0
		if rating > 100:
			rating = 100
		self['rating10'].setValue(rating)
		post = urllib.urlencode({'mID': id, 'language': lang})
		getPage(base_apiurl, method='POST', postdata=post, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest', 'Accept-Language':'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4,id;q=0.2,ru;q=0.2,tr;q=0.2'}).addCallback(self.getCover).addErrback(self.dataError)

	def getCover(self, data):
		cover = re.findall('"cover":"(.*?)",', data)
		if cover:
			self.coverurl = 'http:'+cover[0].replace('\/','/')
			CoverHelper(self['coverArt']).getCover(self.coverurl)
		else:
			self.coverurl = None
		handlung = re.findall('"plot":"(.*?)"}', data)
		if handlung:
			handlung = decodeHtml(handlung[0].replace('\\"','"'))
			self['handlung'].setText(handlung)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		id = self['liste'].getCurrent()[0][1]
		lang = self['liste'].getCurrent()[0][3]
		if lang == '1':
			lang = "de"
		else:
			lang = "en"
		self.session.open(video4kStreams, title, id, self.coverurl, lang)

class video4kStreams(MPScreen):

	def __init__(self, session, title, id, cover, lang):
		self.movietitle = title
		self.id = id
		self.cover = cover
		self.lang = lang
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
		}, -1)

		self['title'] = Label("Video4K")
		self['leftContentTitle'] = Label(_("Stream Selection"))
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.movietitle)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		post = urllib.urlencode({'language': self.lang, 'mID': self.id, 'raw': 'true'})
		getPage(base_apiurl, method='POST', postdata=post, agent=glob_agent, headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest', 'Accept-Language':'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4,id;q=0.2,ru;q=0.2,tr;q=0.2'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		streams_raw = re.findall('"name":"(.*?)".*?links":\[(.*?)\]', data, re.S)
		if streams_raw:
			for hostername,hosterraw in streams_raw:
				streams = re.findall('"URL":"(.*?)"',hosterraw , re.S)
				if streams:
					for hosterlink in streams:
						self.streamList.append((hostername.lower(), hosterlink.replace('\/','/')))
			if len(self.streamList) == 0:
				self.streamList.append((_('No supported streams found!'), None))
			else:
				self.keyLocked = False
			self.ml.setList(map(self._defaultlisthoster, self.streamList))
			CoverHelper(self['coverArt']).getCover(self.cover)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_url = self['liste'].getCurrent()[0][1]
		get_stream_link(self.session).check_link(stream_url, self.got_link)

	def got_link(self, stream_url):
		self.session.open(SimplePlayer, [(self.movietitle, stream_url, self.cover)], showPlaylist=False, ltype='video4k', cover=True)