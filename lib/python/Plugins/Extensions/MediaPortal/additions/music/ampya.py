# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.ampyalink import AmpyaLink
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.simple_lru_cache import SimpleLRUCache
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

ampya_session = None
json_headers = {
	'Accept':'application/json',
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/json',
	}
agent='Mozilla/5.0 (Windows NT 6.1; rv:44.0) Gecko/20100101 Firefox/44.0'
search_headers = None
glob_stagLRUCache = SimpleLRUCache(50, config.mediaportal.watchlistpath.value + 'mp_ampya_stags')

class ampyaGenreScreen(MPScreen):

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
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("AMPYA")
		self['ContentTitle'] = Label("Kanal Auswahl:")

		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onClose.append(glob_stagLRUCache.saveCache)
		glob_stagLRUCache.readCache()

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		# http://www.putpat.tv/ws.xml?client=miniplayer&method=Channel.all
		self.genreliste.append(("--- Artist Search ---", "callSuchen"))
		self.genreliste.append(("--- Video Search ---", "callSuchen"))
		self.genreliste.append(("--- My Last Search Tags ---", "callSuchen"))
		self.genreliste.append(("Charts", "2"))
		self.genreliste.append(("Heimat", "3"))
		self.genreliste.append(("Retro", "4"))
		self.genreliste.append(("2Rock", "5"))
		self.genreliste.append(("Vibes", "6"))
		self.genreliste.append(("Hooray!", "7"))
		self.genreliste.append(("INTRO TV", "9"))
		self.genreliste.append(("JAZZthing.TV", "11"))
		self.genreliste.append(("Festival Guide", "12"))
		self.genreliste.append(("studiVZ", "15"))
		self.genreliste.append(("meinVZ", "16"))
		self.genreliste.append(("MELT Festival", "29"))
		self.genreliste.append(("Splash! Festival", "30"))
		self.genreliste.append(("Berlin Festival", "31"))
		self.genreliste.append(("Flux TV", "34"))
		self.genreliste.append(("Introducing", "36"))
		self.genreliste.append(("Pop10", "39"))
		self.genreliste.append(("Rock Hard", "41"))
		self.genreliste.append(("Sneakerfreaker", "43"))
		self.genreliste.append(("Paradise TV", "45"))
		self.genreliste.append(("PUTPAT one", "46"))
		self.genreliste.append(("detektor.fm", "47"))
		self.genreliste.append(("Party", "48"))
		self.genreliste.append(("HD-Kanal", "49"))
		self.genreliste.append(("Chiemsee Festival", "50"))
		self.genreliste.append(("Hurricane/Southside Festival", "51"))
		self.genreliste.append(("Highfield Festival", "52"))
		self.genreliste.append(("M'era Luna", "53"))
		self.genreliste.append(("FazeMag", "54"))
		self.genreliste.append(("AMPYA one", "56"))
		self.genreliste.append(("AMPYA Charts", "57"))
		self.genreliste.append(("Purified", "58"))
		self.genreliste.append(("AMPYA Testspiel", "59"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][1]
		Image = 'http://files.ampya.com/artwork/channelgraphics/%s/channelteaser_500.png' % Image
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		if streamGenreName == "--- Artist Search ---":
			#self.suchen()
			self.session.openWithCallback(self.SuchenCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True, auto_text_init=False, suggest_func=self.getArtistSuggestions)
		elif streamGenreName == "--- Video Search ---":
			self.session.openWithCallback(self.SuchenCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True, auto_text_init=False, suggest_func=self.getVideoSuggestions)
		elif streamGenreName == "--- My Last Search Tags ---":
			if glob_stagLRUCache.cache:
				self.tagSearch()
		else:
			streamGenreLink = self['liste'].getCurrent()[0][1]
			self.session.open(ampyaFilmScreen, streamGenreLink, streamGenreName)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback.strip()):
			global glob_stagLRUCache
			stagKey = callback.translate(None,"+- *?_;,()&<>'\"!").lower()
			glob_stagLRUCache[stagKey] = callback.strip()
			callback = re.sub('\(.+?\)', '', callback).strip()
			streamGenreLink = urllib.quote_plus(callback)
			selfGenreName = "--- Search ---"
			self.session.open(ampyaFilmScreen, streamGenreLink, selfGenreName)

	def getSessiondata(self):
		import uuid
		uid = uuid.uuid4()
		content = '{"app":{"token":"ampya_web","version":"3.0.0","partner_id":1},"viewer":"%s"}' % uid
		url = 'http://ampya.com/webservice/v1/putpat/init'
		return twAgentGetPage(url, method="POST", postdata=content, agent=agent, headers=json_headers, timeout=10).addCallback(self.gotSessiondata)

	def gotSessiondata(self, data):
		global ampya_session, search_headers
		ampya_session = json.loads(data)
		search_headers = json_headers.copy()
		search_headers.update((('X-Putpat-Session-Id',str(ampya_session["session"]["session_id"])),('X-CSRF-TOKEN',str(ampya_session["session"]["csrf_token"]))))
		return ampya_session

	def getArtistSuggestions(self, text, max_res):
		return self.getSuggestions(text, max_res, 'artists')

	def getVideoSuggestions(self, text, max_res):
		return self.getSuggestions(text, max_res, 'videos')

	def getSuggestions(self, text, max_res, sugg_type):
		if ampya_session == None:
			return self.getSessiondata().addCallback(lambda ign: self.getSuggestions(text, max_res, sugg_type)).addErrback(self.gotSuggestions, max_res, err=True)
		else:
			url = "http://ampya.com/webservice/v1/search?term=%s" % urllib.quote_plus(text)
			d = twAgentGetPage(url, agent=agent, headers=search_headers, timeout=5)
			d.addCallback(self.gotSuggestions, max_res, sugg_type=sugg_type)
			d.addErrback(self.gotSuggestions, max_res, err=True)
			return d

	def gotSuggestions(self, suggestions, max_res, err=False, sugg_type='artists'):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions[sugg_type]:
				li = item['title'] if sugg_type == 'artists' else "%s - %s" % (item['artist'], item['title'])
				list.append(str(li))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

	def tagSearch(self):
		list = []
		for key, val in glob_stagLRUCache.cache:
			list.insert(0,(val, key))
		if list:
			self.session.openWithCallback(self.gotSearchTag, ChoiceBoxExt, title=_("Search Tag Selection"), list = list)

	def gotSearchTag(self, answer):
		stag = answer and answer[0]
		if stag:
			self.SuchenCallback(callback = stag)

class ampyaFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, catName):
		self.CatLink = CatLink
		self.catName = catName
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
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Titel Auswahl")
		self['ContentTitle'] = Label("Genre: %s" % self.catName)
		self['F2'] = Label(_("Page"))

		self.keyLocked = True
		self.page = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(self.catName)
		self.filmliste = []
		if self.catName == '--- Search ---':
			url = "http://www.putpat.tv/ws.xml?limit=100&client=putpatplayer&partnerId=1&searchterm=%s&method=Asset.quickbarSearch" % (self.CatLink)
		else:
			url = "http://www.putpat.tv/ws.xml?method=Channel.clips&partnerId=1&client=putpatplayer&maxClips=500&channelId=%s&streamingId=tvrl&streamingMethod=http" % (self.CatLink)
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if self.catName == '--- Search ---':
			Search = re.findall('<video-file-id\stype="integer">(.*?)</video-file-id>.*?<token>(.*?)</token>.*?<description>(.*?)</description>', data, re.S)
			if Search:
				for (Image, Token, Title) in Search:
					if len(Image) == 6:
						Image = '0' + Image
					elif len(Image) == 5:
						Image = '00' + Image
					elif len(Image) == 4:
						Image = '000' + Image
					Image = 'http://files.ampya.com/artwork/posterframes/%s/%s/v%s_posterframe_putpat_large.jpg' % (Image[:5], Image, Image)
					self.filmliste.append((decodeHtml(Title), None, Token, Image))
		else:
			Movies = re.findall('<clip>.*?<medium>(.*?)</medium>.*?<title>(.*?)</title>.*?<display-artist-title>(.*?)</display-artist-title>.*?<video-file-id\stype="integer">(.*?)</video-file-id>', data, re.S)
			if Movies:
				for (Url, Title, Artist, Image) in Movies:
					Title = Artist + ' - ' + Title
					Url = Url.replace('&amp;','&')
					if len(Image) == 6:
						Image = '0' + Image
					elif len(Image) == 5:
						Image = '00' + Image
					elif len(Image) == 4:
						Image = '000' + Image
					Image = 'http://files.ampya.com/artwork/posterframes/%s/%s/v%s_posterframe_putpat_large.jpg' % (Image[:5], Image, Image)
					if not (re.search('pop10_trenner.*?', Title, re.S) or re.search('Pop10 Trenner', Title, re.S) or re.search('pop10_pspot', Title, re.S) or re.search('pop10_opn_neu', Title, re.S) or re.search('PutPat Top Ten', Title, re.S)):
						self.filmliste.append((decodeHtml(Title), Url, None, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No songs found!"),'','',''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 3, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Image = self['liste'].getCurrent()[0][3]
		CoverHelper(self['coverArt']).getCover(Image)
		title = self['liste'].getCurrent()[0][0]
		if not re.match('.*?----------------------------------------', title):
			self['name'].setText(title)
		else:
			self['name'].setText('')

	def keyOK(self):
		if self.keyLocked:
			return
		self.session.open(
			AmpyaPlayer,
			self.filmliste,
			playIdx = self['liste'].getSelectedIndex(),
			playAll = True,
			listTitle = self.catName,
			ltype='ampya',
			useResume=False
			)

class AmpyaPlayer(SimplePlayer):

	def getVideo(self):
		url = self.playList[self.playIdx][1]
		Title = self.playList[self.playIdx][0]
		token = self.playList[self.playIdx][2]
		Image = self.playList[self.playIdx][3]
		AmpyaLink(self.session).getLink(self.playStream, self.dataError, Title, url, token, Image)