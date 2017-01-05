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
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.pininputext import PinInputExt
from cookielib import CookieJar, Cookie
import base64

keckse = CookieJar()
SOURCE_STREAMER = ''
ALLUC_MODE = ''
special_agent = 'Mozilla/5.0 (Windows NT 6.1; rv:23.0) Gecko/20131011 Firefox/23.0'
alluc_header = {
			'Accept': '*/*'
			}

ALLUCFILMURL = 'http://www.alluc.ee'
ALLUCPORNURL = 'http://pron.tv'
ALLUCURL = ''

config.mediaportal.allucsearch_lang = ConfigText(default="all Languages", fixed_size=False)
config.mediaportal.allucsearch_timerange = ConfigText(default="no Timelimit", fixed_size=False)
config.mediaportal.allucsearch_sort = ConfigText(default="relevance", fixed_size=False)
config.mediaportal.allucsearch_hoster = ConfigText(default="all Hosters", fixed_size=False)

class manageListElement(MPScreen):

	def __init__(self, session, listname='MP_globallist'):
		self.listname = listname
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
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyRed,
			"green" : self.keyGreen,
			"yellow" : self.keyYellow
		}, -1)

		self['title'] = Label('ManageListElement')
		self['name'] = Label("Your Search Requests")
		self['ContentTitle'] = Label("Annoyed, typing in your search-words again and again?")

		self['F1'] = Label(_("Delete"))
		self['F2'] = Label(_("Add"))
		self['F3'] = Label(_("Edit"))
		self.keyLocked = True
		self.suchString = ''

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.Searches)

	def Searches(self):
		self.genreliste = []
		self['liste'] = self.ml
		if not fileExists(config.mediaportal.watchlistpath.value+self.listname):
			open(config.mediaportal.watchlistpath.value+self.listname,"w").close()
		if fileExists(config.mediaportal.watchlistpath.value+self.listname):
			fobj = open(config.mediaportal.watchlistpath.value+self.listname,"r")
			for line in fobj:
				self.genreliste.append((line, None))
			fobj.close()
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False

	def SearchAdd(self):
		suchString = ""
		self.session.openWithCallback(self.SearchAdd1, VirtualKeyBoardExt, title = (_("Enter Search")), text = suchString, is_dialog=True, auto_text_init=True)

	def SearchAdd1(self, suchString):
		if suchString is not None and suchString != "":
			self.genreliste.append((suchString,None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.saveWatchList()

	def SearchEdit(self):
		if len(self.genreliste) > 0:
			suchString = self['liste'].getCurrent()[0][0].rstrip()
			self.session.openWithCallback(self.SearchEdit1, VirtualKeyBoardExt, title = (_("Enter Search")), text = suchString, is_dialog=True, auto_text_init=True)

	def SearchEdit1(self, suchString):
		if suchString is not None and suchString != "":
			pos = self['liste'].getSelectedIndex()
			self.genreliste.pop(pos)
			self.genreliste.insert(pos,(suchString,None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.saveWatchList()

	def keyOK(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			search = self['liste'].getCurrent()[0][0].rstrip()
			self.close(search)

	def keyRed(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			self.genreliste.pop(self['liste'].getSelectedIndex())
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.saveWatchList()

	def keyGreen(self):
		if self.keyLocked:
			return
		self.SearchAdd()

	def keyYellow(self):
		if self.keyLocked:
			return
		self.SearchEdit()

	def keyCancel(self):
		if self.keyLocked:
			return
		self.saveWatchList()
		self.close()

	def saveWatchList(self):
		self.genreliste.sort(key=lambda t : t[0].lower())
		fobj_out = open(config.mediaportal.watchlistpath.value+self.listname,"w")
		x = len(self.genreliste)
		if x > 0:
			for c in range(x):
				writeback = self.genreliste[c][0].rstrip()+"\n"
				fobj_out.write(writeback)
			fobj_out.close()
		else:
			os.remove(config.mediaportal.watchlistpath.value+self.listname)

class searchAllucHelper():

	def keyTimeRange(self):
		if self.keyLocked:
			return
		rangelist = ['no Timelimit', 'last24h', 'lastweek', 'lastmonth']
		for x in rangelist:
			if self.timeRange == x:
				self.timeRange = rangelist[rangelist.index(x)-len(rangelist)+1]
				break
		config.mediaportal.allucsearch_timerange.value = self.timeRange
		config.mediaportal.allucsearch_timerange.save()
		configfile.save()
		self['F3'].setText(self.timeRange.title())
		self.loadFirstPage()

	def keyLanguage(self):
		if self.keyLocked:
			return
		rangelist = [
					['all Languages', 'all Languages'],
					['German', 'DE'],
					['English', 'EN'],
					['Spanish', 'ES'],
					['French', 'FR'],
					['Italian', 'IT'],
					['Hebrew', 'HE'],
					['Russian', 'RU'],
					['Finnish', 'FI'],
					['Norwegian', 'NO'],
					['Swedish', 'SE'],
					['Turkish', 'TR'],
					['Polish', 'PL'],
					['Slovakian', 'SK'],
					['Czech', 'CZ'],
					['Slovenian', 'SI'],
					['Lithuanian', 'LT'],
					['Latvian', 'LV'],
					['Estonian', 'EE'],
					['Bulgarian', 'BG'],
					['Hungarian', 'HU'],
					['Croatian', 'HR'],
					['Romanian', 'RO']
					]
		self.session.openWithCallback(self.returnLanguage, ChoiceBoxExt, title=_('Select Language'), list = rangelist)

	def returnLanguage(self, data):
		if data:
			self.lang = data[1]
			config.mediaportal.allucsearch_lang.value = self.lang
			config.mediaportal.allucsearch_lang.save()
			configfile.save
			self['F4'].setText(self.lang)
			self.loadFirstPage()

	def keySort(self):
		if self.keyLocked:
			return
		rangelist = ['relevance', 'newlinks']
		for x in rangelist:
			if self.sort == x:
				self.sort = rangelist[rangelist.index(x)-len(rangelist)+1]
				break
		config.mediaportal.allucsearch_sort.value = self.sort
		config.mediaportal.allucsearch_sort.save()
		configfile.save()
		self['F2'].setText(self.sort.title())
		self.loadFirstPage()

	def keyHoster(self):
		if self.keyLocked:
			return
		rangelist =[]
		helper = mp_globals.hosters[1].replace('\\','')
		if not helper:
			return
		rangehelper = list(set(helper.split('|')))
		for x in rangehelper:
			rangelist.append([x])
		rangelist.sort()
		rangelist.insert(0, (['all Hosters']))
		self.session.openWithCallback(self.returnHoster, ChoiceBoxExt, title=_('Select Hoster'), list = rangelist)

	def returnHoster(self, data):
		if data:
			self.hoster = data[0]
			config.mediaportal.allucsearch_hoster.value = self.hoster
			config.mediaportal.allucsearch_hoster.save()
			configfile.save()
			self['F1'].setText(self.hoster)
			self.loadFirstPage()

	def keySaveStreamer(self):
		source = self['liste'].getCurrent()[0][3]
		searchAllucStreamerFile = config.mediaportal.watchlistpath.value+'mp_searchalluc_streamer'+ALLUC_MODE
		if not fileExists(searchAllucStreamerFile):
			open(searchAllucStreamerFile,"w").close()
		if fileExists(searchAllucStreamerFile):
			with open(searchAllucStreamerFile, "a+") as myfile:
				if not any(source == x.rstrip('\r\n') for x in myfile):
					message = self.session.open(MessageBoxExt, _("Source Hoster saved in list."), MessageBoxExt.TYPE_INFO, timeout=3)
					myfile.write(source + '\n')
				else:
					message = self.session.open(MessageBoxExt, _("Source Hoster already in list."), MessageBoxExt.TYPE_INFO, timeout=3)

	def keyStreamer(self):
		global SOURCE_STREAMER
		if self.keyLocked:
			return
		try:
			source = self['liste'].getCurrent()[0][3]
			if SOURCE_STREAMER[:4] == "all@":
				SOURCE_STREAMER = ""
				self['ContentTitle'].setText("Search Streams for %s" % self.searchfor)
			elif source == '' or source == SOURCE_STREAMER:
				source = SOURCE_STREAMER
				SOURCE_STREAMER = "all@%s" % source
				self['ContentTitle'].setText("Search Streams all / Source: %s " % SOURCE_STREAMER)
			elif source != SOURCE_STREAMER:
				SOURCE_STREAMER = source
				self['ContentTitle'].setText("Search Streams for %s / Source: %s " % (self.searchfor, SOURCE_STREAMER))
			self.loadFirstPage()
		except:
			pass

	def loadFirstPage(self):
		try:
			self.filmliste = []
			self.loadPage()
		except:
			pass

	def errCancelDeferreds(self, error):
		myerror = error.getErrorMessage()
		if myerror:
			raise error

	def dataError(self, error):
		printl(error,self,"E")
		self.keyLocked = False

class searchAllucMenueScreen(searchAllucHelper, MPScreen):

	def __init__(self, session, mode=False):
		global ALLUC_MODE
		global SOURCE_STREAMER
		global ALLUCURL
		SOURCE_STREAMER = ''
		if mode == "porn":
			ALLUC_MODE = "porn"
			ALLUCURL = ALLUCPORNURL
		else:
			ALLUC_MODE = ""
			ALLUCURL = ALLUCFILMURL
		if SOURCE_STREAMER:
			self.Name = "--- Multi " + ALLUC_MODE.capitalize() +"Search Engine --- / Source: %s" % SOURCE_STREAMER
		else:
			self.Name = "--- Multi " + ALLUC_MODE.capitalize() +"Search Engine ---"
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
			"cancel" : self.keyCancel,
			"0" : self.closeAll,
			"2" : self.manageStreamerFilter,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"red" : self.keyHoster,
			"green" : self.keySort,
			"yellow" : self.keyTimeRange,
			"blue" : self.keyLanguage
		}, -1)

		self.timeRange = config.mediaportal.allucsearch_timerange.value
		self.sort = config.mediaportal.allucsearch_sort.value
		self.lang = config.mediaportal.allucsearch_lang.value
		self.hoster = config.mediaportal.allucsearch_hoster.value
		self['title'] = Label("2SearchAlluc")
		self['ContentTitle'] = Label("%s / Searchlimit 100!" % self.Name)
		self['F1'] = Label(self.hoster)
		self['F2'] = Label(self.sort.title())
		self['F3'] = Label(self.timeRange.title())
		self['F4'] = Label(self.lang)
		self.keyLocked = True
		self.suchString = ''
		self.pin = False

		self.genreliste = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def manageStreamerFilter(self):
		self.session.openWithCallback(self.manageStreamerFilter_set, manageListElement, listname='mp_searchalluc_streamer'+ALLUC_MODE)

	def manageStreamerFilter_set(self, source=''):
		global SOURCE_STREAMER
		SOURCE_STREAMER = source
		self['ContentTitle'].setText("--- Multi " + ALLUC_MODE.capitalize() +"Search Streams all / Source: %s " % SOURCE_STREAMER)

	def pincheck(self):
		self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config.mediaportal.pincode.value)], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def pincheckok(self, pincode):
		if pincode:
			self.pin = True
			self.keyOK()

	def genreData(self):
		if ALLUC_MODE == "porn":
			self.genreliste.append(("Search for Streams", "callSuchen"))
			self.genreliste.append(("Search for all Streams", "callSuchenall"))
			self.genreliste.append(("Search Streams use 2Search4Porn List", "callPornSearchList"))
		else:
			self.genreliste.append(("Search for Streams", "callSuchen"))
			self.genreliste.append(("Search for all Streams", "callSuchenall"))
			self.genreliste.append(("Search using Keyword List", "callKeywordList"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Pick = self['liste'].getCurrent()[0][1]
		if config.mediaportal.pornpin.value and not ALLUC_MODE == 'porn' and not self.pin:
			self.pincheck()
		else:
			if Pick == "callSuchen":
				self.suchen()
			elif Pick == "callSuchenall":
				self.SuchenCallback('')
			elif Pick == "callKeywordList":
				self.session.openWithCallback(self.SuchenCallback, manageListElement, listname="mp_keywords")
			else:
				self.session.openWithCallback(self.SuchenCallback, manageListElement, listname="mp_2s4p")

	def SuchenCallback(self, callback = None, entry = None):
		Name = self['liste'].getCurrent()[0][0]
		Pick = self['liste'].getCurrent()[0][1]
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = "%s" % self.suchString
			self.session.openWithCallback(self.cancelSetValue, searchAllucListScreen, Link, Name, self.suchString, self.timeRange, self.lang, self.sort, self.hoster)
		elif Pick != "callSuchen":
			Link = ""
			self.session.openWithCallback(self.cancelSetValue, searchAllucListScreen, Link, Name, '', self.timeRange, self.lang, self.sort, self.hoster)

	def cancelSetValue(self):
		self.hoster = config.mediaportal.allucsearch_hoster.value
		self.sort = config.mediaportal.allucsearch_sort.value
		self.timeRange = config.mediaportal.allucsearch_timerange.value
		self.lang = config.mediaportal.allucsearch_lang.value
		self['F1'].setText(self.hoster)
		self['F2'].setText(self.sort.title())
		self['F3'].setText(self.timeRange.title())
		self['F4'].setText(self.lang)

class searchAllucListScreen(searchAllucHelper, MPScreen):

	def __init__(self, session, Link, Name, searchfor, timeRange='no Timelimit', lang='all Languages', sort='newlinks', hoster='all Hosters'):
		self.Link = Link.replace(' ', '%20')
		self.Name = Name
		self.searchfor = searchfor
		self.timeRange = timeRange
		self.sort = sort
		self.lang = lang
		self.hoster = hoster
		global keckse
		global SOURCE_STREAMER
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self.dsUrl = ""

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"0" : self.closeAll,
			"2" : self.keySaveStreamer,
			"8" : self.keyStreamer,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyHoster,
			"green" : self.keySort,
			"yellow" : self.keyTimeRange,
			"blue" : self.keyLanguage
		}, -1)

		self['title'] = Label("2SearchAlluc")
		self.myLabel = self.Name
		if self.searchfor:
			self.myLabel = "%s / Search for: %s" % (self.myLabel, self.searchfor)
		if SOURCE_STREAMER:
			self.myLabel = "%s / Streamer: %s" % (self.myLabel, SOURCE_STREAMER)
		self['ContentTitle'] = Label(self.myLabel)
		self['F1'] = Label(self.hoster)
		self['F2'] = Label(self.sort.title())
		self['F3'] = Label(self.timeRange.title())
		self['F4'] = Label(self.lang)

		self.keyLocked = True
		self.autoload = True
		self.getPageProc = 0
		self.filmliste = []
		self.Cover = ''
		self.moviecounter = 0
		self.movieallcounter = 0

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.deferreds = []
		self.deferreds2 = []
		self.ds = defer.DeferredSemaphore(tokens=1)
		self.ds2 = defer.DeferredSemaphore(tokens=1)
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.getPageProc = 0
		self.moviecounter = 0
		self.movieallcounter = 0
		self.filmliste = []
		self.ml.setList(map(self.searchallucMultiListEntry, self.filmliste))
		self['handlung'].setText('')
		self['name'].setText(_('Please wait...'))
		Url = self.Link
		if SOURCE_STREAMER != '':
			if "all@" == SOURCE_STREAMER[:4]:
				if Url and Url[0] != "+":
					if "+" in Url:
						Url = "+%s+src:%s" % (Url.split('+', 1)[-1], SOURCE_STREAMER[4:])
					else:
						Url = "+src:%s" % SOURCE_STREAMER[4:]
				else:
					Url = "%s+src:%s" % (Url, SOURCE_STREAMER[4:])
			else:
				Url = "%s+src:%s" % (Url, SOURCE_STREAMER)
		if self.hoster != 'all Hosters':
				Url = "host:%s+%s" % (self.hoster, Url)
		if self.timeRange != 'no Timelimit':
			Url = "%s+#%s" % (Url,self.timeRange)
		if self.lang != 'all Languages':
			Url = "%s+lang:%s" % (Url, self.lang.lower())
		if self.sort != 'relevance':
			Url = "%s+#%s" % (Url, self.sort)
		if Url:
			if Url[0] == '+':
				Url = Url[1:]
		for items in self.deferreds:
			items.cancel()
		if not Url:
			Url = "#lastmonth"
		Url = Url.replace('#','%23').replace(':','%3A')
		for getPageNr in range(1,14):
			if getPageNr != 1:
				self.dsUrl = "%s/stream/%s?page=%s" % (ALLUCURL, Url, getPageNr)
			else:
				self.dsUrl = ALLUCURL + "/stream/" + Url
			d = self.ds.run(twAgentGetPage, self.dsUrl, cookieJar=keckse, followRedirect=False, redirectLimit=1, gzip_decoding=True, agent=special_agent, headers=alluc_header).addCallback(self.loadPageData).addErrback(self.dataError)
			self.deferreds.append(d)
		self.deferreds.append(d)

	def errorNoVideo(self, error):
		try:
			if error.getErrorMessage():
				self.getPageProc += 8
				if self.getPageProc != 100:
					self['Page'].setText("%s%%" % str(self.getPageProc))
				else:
					self['Page'].setText("")
					self.allFinish()
		except:
			pass
		raise error

	def loadPageData(self, data):
		if not re.search('No exact matches found', data):
			preparse = re.search('<div class="found"(.*?)resultitems"', data, re.S)
			if preparse:
				filme = data.split('resblock">')
				for film in filme[1:]:
					Movies = re.search('\shref="(/l/.*?)"\s+title="Watch\s(.*?)on.*?(src="([^"]+thumbnail/.*?)".*?)?class="hoster topstar(.*?)".*?</a>\s+(.*?)</div>.*?class="source"\s*>(.*?)<.*?alt="(.*?)"/></a>\s*(<div class="tagged">(.*?)<)?', film, re.S)
					if Movies:
						self.movieallcounter += 1
						if isSupportedHoster(Movies.group(5), True):
							self.moviecounter += 1
							Url = "%s%s" % (ALLUCURL, Movies.group(1).replace('&amp;','&'))
							if Movies.group(9):
								quali = Movies.group(10)
							else:
								quali = '?'
							self.filmliste.append((decodeHtml(Movies.group(2)), Url, Movies.group(5), Movies.group(7), Movies.group(6)[2:], quali, Movies.group(8), Movies.group(4)))
		else:
			for items in self.deferreds:
				items.cancel()
			self.getPageProc = 100
		self.getPageProc += 8
		if self.getPageProc < 100:
			self['Page'].setText("%s%%" % str(self.getPageProc))
		else:
			self['Page'].setText("")
			self.allFinish()
		if len(self.filmliste) > 0:
			self.ml.setList(map(self.searchallucMultiListEntry, self.filmliste))
			self.keyLocked = False
			if self.autoload:
				self.autoload = False
				self.showInfos()

	def allFinish(self):
		self.filmliste.append(("found %s movies / %s with MP supported hosters!" % (self.movieallcounter,self.moviecounter), None, '', '', '', '','',''))
		self.filmliste.append(('', None, '', '', '', '','',''))
		if SOURCE_STREAMER == '':
			Url = '%s%s%s%s' % (ALLUCURL,'/ajax.php?ajax=%7B%22clientVersion%22%3A%220.9%22%2C%22params%22%3A%5B%22', self.searchfor, '%22%2C%22stream%22%5D%2C%22func%22%3A%22fetchHosterFacets%22%7D')
			twAgentGetPage(Url, cookieJar=keckse, gzip_decoding=True, agent=special_agent, headers=alluc_header).addCallback(self.loadCounterInfo).addErrback(self.dataError)
		self.ml.setList(map(self.searchallucMultiListEntry, self.filmliste))
		self['name'].setText('')
		self.keyLocked = False
		self.showInfos()

	def loadCounterInfo(self, data):
		parse = re.search('"response":"\{(.*?)\}', data, re.S)
		if parse:
			linkcount = re.findall('(.*?):(.*?),', parse.group(1).replace('\\','').replace('"','')+',', re.S)
			if linkcount:
				for (hoster, links) in linkcount:
					if isSupportedHoster(hoster, True):
						if links[-1:] == 'k':
							try:
								links = str(int(links[:-1])*1000)
							except: pass
						self.filmliste.append(("found %s movies for hoster..." % links, None, hoster, '', '', '','',''))
				self.ml.setList(map(self.searchallucMultiListEntry, self.filmliste))
		self.keyLocked = False

	def showInfos(self):
		for items in self.deferreds2:
			try:
				items.cancel()
			except:
				pass
		self.deferreds2 = []
		image = self['liste'].getCurrent()[0][7]
		if image:
			if re.match('//', image):
				image = 'http:' + image
			else:
				image = '%s%s' % (ALLUCURL, self['liste'].getCurrent()[0][7])
		CoverHelper(self['coverArt']).getCover(image)
		if self['liste'].getCurrent()[0][1] != None:
			Title = self['liste'].getCurrent()[0][0]
			Url = self['liste'].getCurrent()[0][1]
			self['name'].setText(Title)
			d = self.ds2.run(twAgentGetPage, Url, cookieJar=keckse, gzip_decoding=True, agent=special_agent, headers=alluc_header).addCallback(self.loadPageInfos).addErrback(self.dataError)
			self.deferreds2.append(d)

	def loadPageInfos(self, data):
		Description = re.search('<td><b>Description</b></td>.*?<td>(.*?)</td>', data, re.S)
		Title = self['liste'].getCurrent()[0][0]
		Hoster = self['liste'].getCurrent()[0][2]
		Source = self['liste'].getCurrent()[0][3]
		Size = self['liste'].getCurrent()[0][4]
		Date = self['liste'].getCurrent()[0][5]
		Lang = self['liste'].getCurrent()[0][6]
		if Description:
			if re.match('.*?alluc.ee', Description.group(1)):
				Handlung = 'There is no description for this movie yet'
			else:
				Handlung = decodeHtml(Description.group(1).strip())
		else:
			Handlung = 'No Description found.'
		Handlung = "Language: %s  Quali: %s  Date-Size: %s  Hoster: %s  Source: %s\n%s:\n%s" % (Lang.upper(), Date, Size, Hoster, Source, Title, Handlung)
		self['handlung'].setText(Handlung)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link == None:
			Name = self['liste'].getCurrent()[0][0]
			if re.match('found\s\d+', Name):
				Hoster = self['liste'].getCurrent()[0][2]
				self.returnHoster(Hoster.split())
			return
		self.keyLocked = True
		twAgentGetPage(Link, cookieJar=keckse, gzip_decoding=True, agent=special_agent, headers=alluc_header).addCallback(self.getHosterLink).addErrback(self.noVideoError).addErrback(self.dataError)

	def getHosterLink(self, data):
		streamcode = re.search('<div\sclass="linktitleurl.*?decrypt\(\'(.*?)\',\s+\'(.*?)\'', data, re.S|re.I)
		if streamcode:
			stream = ''
			streamdecode = base64.b64decode(streamcode.group(1))
			for mycounter in range(len(streamdecode)):
				varA = streamdecode[mycounter]
				varB = streamcode.group(2)[mycounter % len(streamcode.group(2))-1]
				varA = int(ord(varA) - ord(varB))
				varA = chr(varA)
				stream = stream + varA

			Hoster = self['liste'].getCurrent()[0][2]
			if Hoster == 'youtube.com':
				m2 = re.search('//www.youtube.com/(embed/|v/|watch.v=)(.*?)(\?|" |&amp|\&|$)', stream)
				if m2:
					Title = self['liste'].getCurrent()[0][0]
					dhVideoId = m2.group(2)
					self.session.open(YoutubePlayer, [(Title, dhVideoId, None)], showPlaylist=False)
			else:
				self.get_redirect(stream.replace('&amp;','&'))
		else:
			streams = re.search('contains adult material', data, re.S)
			if streams:
				message = self.session.open(MessageBoxExt, "This video contains adult material and has been moved", MessageBoxExt.TYPE_INFO, timeout=5)
			else:
				message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)
		self.keyLocked = False

	def noVideoError(self, error):
		try:
			if error.value.status == '404':
				message = self.session.open(MessageBoxExt, _("No link found."), MessageBoxExt.TYPE_INFO, timeout=3)
		except:
			pass
		self.keyLocked = False
		raise error

	def keyCancel(self):
		for items in self.deferreds:
			items.cancel()
		self.close()

	def get_redirect(self, url):
		get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		self.keyLocked = False
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Title, stream_url)], showPlaylist=False, ltype='searchalluc')