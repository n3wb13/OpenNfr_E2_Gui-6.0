# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

MozillaAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'

class filmON(MPScreen, ThumbsHelper):

	def __init__(self, session):
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
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmOn")

		self.keyLocked = True
		self.filmliste = []
		self.datarange = ""
		self.keckse = CookieJar()
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.filmon.com/tv/live"
		twAgentGetPage(url, agent=MozillaAgent, cookieJar=self.keckse).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		parse = re.search('var groups = \[(.*?)groups\[i\]', data, re.S)
		if parse:
			self.datarange = parse.group(1)
			data = re.findall('\{"group_id":"(\d+)","id":"(\d+)","title":"(.*?)"', self.datarange, re.S)
			if data:
				for (id, nr, title) in data:
					image = "http://static.filmon.com/couch/groups/%s/big_logo.png" % id
					self.filmliste.append((decodeHtml(title), id, image))
		if len(self.filmliste) == 0:
			self.filmliste.append(("No channels found.", "",""))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		alldata = []
		id = self['liste'].getCurrent()[0][1]
		name = self['liste'].getCurrent()[0][0]
		data = re.findall('\{"id":(.*?)\}', self.datarange, re.S)
		if data:
			for sublink in data:
				data1 = re.findall('^(.*?)group_id":%s,' % id, sublink, re.S)
				if data1:
					data1 = re.findall('^(.*?),.*?"title":"(.*?)".*?"description":"(.*?)"', data1[0], re.S)
					alldata = alldata + data1
		if alldata:
			self.session.open(filmONFilm, name, alldata, self.keckse)

class filmONFilm(MPScreen, ThumbsHelper):

	def __init__(self, session, Name, Data, keckse):
		self.Name = Name
		self.Data = Data
		self.keckse = keckse
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
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmOn - %s" % self.Name)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.pageData)

	def pageData(self):
		for (id, title, desc) in self.Data:
			image = "http://static.filmon.com/couch/channels/%s/big_logo.png" % id
			self.filmliste.append((decodeHtml(title).replace('\/','/'), id, image, decodeHtml(desc)))
		if len(self.filmliste) == 0:
			self.filmliste.append(("No channels found.", "","",""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		handlung = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(handlung)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		id = self['liste'].getCurrent()[0][1]
		info = urlencode({
		'channel_id': id,
		'quality': "low"
		})
		import cookielib
		ck = cookielib.Cookie(version=0, name='xheader', value='1', port=None, port_specified=False, domain='www.filmon.com', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
		self.keckse.set_cookie(ck)
		ck = cookielib.Cookie(version=0, name='return_url', value='/tv/live', port=None, port_specified=False, domain='www.filmon.com', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
		self.keckse.set_cookie(ck)
		url = "http://www.filmon.com/ajax/getChannelInfo"
		twAgentGetPage(url, agent=MozillaAgent, cookieJar=self.keckse, method='POST', postdata=info, headers={'Accept':'application/json, text/javascript, */*; q=0.01','Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.streamData).addErrback(self.dataError)

	def streamData(self, data):
		title = self['liste'].getCurrent()[0][0]
		streamDaten = re.findall('"serverURL":"(.*?)","streamName":"(.*?)"', data, re.S)
		if streamDaten:
			(rtmpServer, rtmpFile) = streamDaten[0]
			url = "%s" % rtmpServer.replace('\/','/')
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='filmon')