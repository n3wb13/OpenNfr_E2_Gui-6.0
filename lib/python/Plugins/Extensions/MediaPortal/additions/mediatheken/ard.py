# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

# Globals
suchCache = ""
dm = "dummy"
mainLink = "http://www.ardmediathek.de"
tDef = "Keine Informationen/Angaben"
isWeg = "Nicht (oder nicht mehr) auf den ARD-Servern vorhanden!"
helpText = "Tipps:\
\t- 'INFO' zeigt Inhaltsangaben bei gefundenen Inhalten.\n\n\
\t- 'BLAU' listet einige passende Clips zur aktiven Auswahl.\n\n\
\t- 'GELB' bei der Suche: Relevanz/Datum (Default=Datum)."
alienFound = "Kann nicht abgespielt werden! Entweder ist der Content...  \n\n\
- in der Zukunft liegend, und noch nicht vorhanden, oder...\n\
- nicht mehr vorhanden, oder...\n\
- die Stream-Links werden auf Seiten der ARD-Server nun\n   anders zusammengesetzt.\n\n\
In letzterem Fall muss auf ein Update dieses Plugins gewartet werden!"
placeHolder = ("---","99")
ardPic = ""

class ARDGenreScreen(MPScreen):

	ARDPICURL = "http://www.ardmediathek.de/image/00/13/82/72/58/1995897458/16x9/512"

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
		self['title'] = Label("ARD-Mediathek")
		self['ContentTitle'] = Label("Auswahl des Genres")
		self['name'] = Label("Auswahl des Sub-Genres")

		self['handlung'] = Label(helpText)
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.checkARDPicURL)

	def checkARDPicURL(self):
		#global ardPic
		if ardPic == "":
			getPage(self.ARDPICURL, method='HEAD').addCallback(self.cb_checkARDPicURL, True).addErrback(self.cb_checkARDPicURL)
		else:
			self.loadPage()

	def cb_checkARDPicURL(self, response, found=False):
		if found:
			global ardPic
			ardPic = self.ARDPICURL
		self.loadPage()

	def loadPage(self):
		self.genreliste = []
		self.genreliste.append(("Suche  -  TV", "1"))
		self.genreliste.append(("A bis Z  -  TV", "2"))
		self.genreliste.append(("Sendung verpasst!?  -  TV", "3"))
		self.genreliste.append(("Kategorien  -  TV", "4"))
		self.genreliste.append(placeHolder)
		self.genreliste.append(("Suche  -  Radio", "6"))
		self.genreliste.append(("A bis Z  -  Radio", "7"))
		self.genreliste.append(("Kategorien  -  Radio", "8"))
		self.genreliste.append(placeHolder)
		self.genreliste.append(("Dossiers  -  TV & Radio", "10"))
		self.genreliste.append(("Tagesschau  -  TV", "11"))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		if ardPic != "":
			CoverHelper(self['coverArt']).getCover(ardPic)

	def keyOK(self):
		if self.keyLocked:
			return
		self.gN = self['liste'].getCurrent()[0][0]
		self.gF = self['liste'].getCurrent()[0][1]
		if self.gF == "99":
			return
		elif self.gF == "1" or self.gF == "6": # Suche TV oder Radio
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_(self.gN)), text = suchCache, is_dialog=True)
		elif self.gF == "10": # Dossiers
			self.session.open(ARDPostSelect,dm,self.gN,self.gF, dm)
		else:
			self.session.open(ARDPreSelect,self.gN,self.gF)

	def searchCallback(self, callbackStr):
		self.gF = self['liste'].getCurrent()[0][1]
		if callbackStr is not None:
			global suchCache
			suchCache = callbackStr
			self.searchStr = callbackStr
			self.gN = "Suche... ' %s '" % self.searchStr
			self.searchStr = self.searchStr.replace(' ', '+')
			self.searchStr = self.searchStr.replace('ä', '%C3%A4')	#	Umlaute URI-konform wandeln, sonst Fehler zB. beim Suchen nach "Börse".
			self.searchStr = self.searchStr.replace('ö', '%C3%B6')
			self.searchStr = self.searchStr.replace('ü', '%C3%BC')
			self.searchStr = self.searchStr.replace('Ä', '%C3%84')
			self.searchStr = self.searchStr.replace('Ö', '%C3%96')
			self.searchStr = self.searchStr.replace('Ü', '%C3%9C')
			self.searchStr = self.searchStr.replace('ß', '%C3%9F')
			if self.gF == "1":
				url = mainLink+"/suche?searchText="+self.searchStr+"&source=tv&sort="	#	Hier kein "%s" verwenden! Fehler, wenn "%" in URI landet!
			elif self.gF == "6":
				url = mainLink+"/suche?searchText="+self.searchStr+"&source=radio&sort="
			self.session.open(ARDStreamScreen,url,self.gN,self.gF)

class ARDPreSelect(MPScreen):

	def __init__(self,session,genreName,genreFlag):
		self.gN = genreName
		self.gF = genreFlag
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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("ARD-Mediathek")
		self['ContentTitle'] = Label("Auswahl des Genres")

		self['handlung'] = Label(helpText)
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		if self.gF == "2" or self.gF == "7":
			if self.gF == "2":
				self['name'].setText(self.gN+"\n\nAuswahl des Buchstabens")
			else:
				self['name'].setText(self.gN+"\n\nAuswahl des Buchstabens")
			self.genreliste = []
			for c in xrange(26): # ABC, Radio & TV
				self.genreliste.append((chr(ord('A') + c), None))
			self.genreliste.insert(0, ('0-9', None))
		elif self.gF == "4" or self.gF == "8":
			self.genreliste = []
			if self.gF == "4": # Extra-Kategorien, Radio & TV
				self['name'].setText(self.gN+"\n\nAuswahl der Kategorie")
				self.genreliste.append(("TOP von Seite 1 - TV", "1"))
				self.genreliste.append(("Neueste Clips", "2"))
				self.genreliste.append(("Am besten bewertete Clips", "3"))
				self.genreliste.append(("EINSLIKE", "4"))
				self.genreliste.append(placeHolder)
				self.genreliste.append(("Film-Highlights", "5"))	# Ab hier (incl.) Standard-Kategorien, Radio & TV
				self.genreliste.append(("Reportage & Doku", "6"))
				self.genreliste.append(("Kinder & Familie", "7"))
				self.genreliste.append(("Satire & Unterhaltung ", "8"))
				self.genreliste.append(("Kultur", "9"))
				self.genreliste.append(("Serien & Soaps ", "10"))
				self.genreliste.append(("Wissen", "11"))
			if self.gF == "8": # Extra-Kategorien, nur Radio
				self['name'].setText(self.gN+"\n\nAuswahl der Kategorie")
				self.genreliste.append(("Neueste Clips", "1"))
				self.genreliste.append(("Meistabgerufene Clips", "2"))
				self.genreliste.append(placeHolder)
				self.genreliste.append(("Tipps der Redaktion", "3"))
				self.genreliste.append(("Hörspiel", "4"))
		elif self.gF == "3":	# Sendung verpasst?
			self['name'].setText("Sendung verpasst!?\n\nAuswahl des Kalendertages")
			for q in range (0, 7):
				if q == 0:
					s1 = " - Heute und im Voraus"
				elif q == 1:
					s1 = " - Gestern"
				else:
					s1 = ""
				s2 = (datetime.date.today()+datetime.timedelta(days=-q)).strftime("%d.%m.%y")
				s3 = str(q)
				self.genreliste.append((s2+s1,s3,dm,dm))
		elif self.gF == "11":
			self.genreliste = []
			self['name'].setText(self.gN+"\n\nAuswahl der Kategorie")
			self.genreliste.append(("Tagesschau", "1"))
			self.genreliste.append(("Tagesschau mit Gebärdensprache", "2"))
			self.genreliste.append(("Tagesthemen", "3"))
			self.genreliste.append(("Tagesschau24", "4"))

		self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		if ardPic != "":
			CoverHelper(self['coverArt']).getCover(ardPic)

	def keyOK(self):
		if self.keyLocked:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		extra = self['liste'].getCurrent()[0][1]
		if extra == "99":
			return
		elif self.gF == "3":
			self.session.open(ARDPreSelectSender,auswahl,self.gF,extra,dm)
		elif self.gF == "4":	# Kategorien TV
			if extra == '1': # TOP von Seite 1 - TV
				streamLink = "%s/tv" % mainLink
			elif extra == '2': # Neueste Clips
				streamLink = "%s/tv/Neueste-Videos/mehr?documentId=21282466" % mainLink
			elif extra == '3': # Am besten bewertete Clips
				streamLink = "%s/tv/Am-besten-bewertet/mehr?documentId=21282468" % mainLink
			elif extra == '4': # EINSLIKE
				self.session.open(ARDPreSelectSender,auswahl,self.gF,"EINSLIKE",dm)
			elif extra == '5': # Film-Highlights
				streamLink = "%s/tv/Film-Highlights/mehr?documentId=21301808" % mainLink
			elif extra == '6': # Reportage & Doku
				streamLink = "%s/tv/Reportage-Doku/mehr?documentId=21301806" % mainLink
			elif extra == '7': # Kinder & Familie
				streamLink = "%s/tv/Kinder-Familie/mehr?documentId=21282542" % mainLink
			elif extra == '8': # Satire & Unterhaltung
				streamLink = "%s/tv/Satire-Unterhaltung/mehr?documentId=21282544" % mainLink
			elif extra == '9': # Kultur
				streamLink = "%s/tv/Kultur/mehr?documentId=21282546" % mainLink
			elif extra == '10': # Serien & Soaps
				streamLink = "%s/tv/Serien-Soaps/mehr?documentId=21282548" % mainLink
			elif extra == '11': # Wissen
				streamLink = "%s/tv/Wissen/mehr?documentId=21282530" % mainLink
			if extra != "4":
				self.session.open(ARDStreamScreen,streamLink,auswahl,self.gF)
		elif self.gF == "8": # Kategorien Radio
			if extra == '1': # Neueste Clips
				streamLink = "%s/radio/Neueste-Audios/mehr?documentId=21282450" % mainLink
			elif extra == '2': # Meistabgerufene Clips
				streamLink = "%s/radio/Meistabgerufene-Audios/mehr?documentId=21282452" % mainLink
			elif extra == '3': # Tipps der Redaktion
				streamLink = "%s/radio/Tipps-der-Redaktion/mehr?documentId=21301892" % mainLink
			elif extra == '4': # Hörspiel
				streamLink = "%s/radio/Hörspiele/mehr?documentId=21301890" % mainLink
			self.session.open(ARDStreamScreen,streamLink,auswahl,self.gF)
		elif self.gF == "11": # Tagesschau
			if extra == '1': # Tagesschau
				streamLink = "%s/tv/Tagesschau/Sendung?documentId=4326&bcastId=4326" % mainLink
			elif extra == '2': # Tagesschau mit Gebärdensprache
				streamLink = mainLink+"/tv/Tagesschau-mit-Geb%C3%A4rdensprache/Sendung?documentId=12722002&bcastId=12722002"
			elif extra == '3': # Tagesthemen
				streamLink = "%s/tv/Tagesthemen/Sendung?documentId=3914&bcastId=3914" % mainLink
			elif extra == '4': # Tagesschau24
				streamLink = "%s/tv/tagesschau24/Sendung?documentId=6753968&bcastId=6753968" % mainLink
			self.session.open(ARDStreamScreen,streamLink,auswahl,self.gF)
		else:
			if self.gF == "2" or self.gF == "7": # ABC (TV oder Radio)
				self.gN = auswahl
			else:
				self.gN = auswahl
				auswahl = extra
			self.session.open(ARDPostSelect,auswahl,self.gN,self.gF, dm)

class ARDPreSelectSender(MPScreen):

	def __init__(self,session,genreName,genreFlag,sender,such):
		self.gN = genreName
		self.gF = genreFlag
		self.sender = sender
		self.such = such
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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("ARD-Mediathek")
		self['ContentTitle'] = Label("Auswahl des Genres")

		self['handlung'] = Label(helpText)
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		if self.gF == "3":	# Sendung verpasst!?
			self['name'].setText("Sendung verpasst!?\n\nAuswahl des Senders")
			self.genreliste.append(("Das Erste", "208"))
			self.genreliste.append(("BR", "2224"))
			self.genreliste.append(("HR", "5884"))
			self.genreliste.append(("MDR", "5882"))
			self.genreliste.append(("MDR Thüringen", "1386988"))
			self.genreliste.append(("MDR Sachsen-Anhalt", "1386898"))
			self.genreliste.append(("MDR Sachsen", "1386804"))
			self.genreliste.append(("NDR", "5906"))
			self.genreliste.append(("NDR Hamburg", "21518348"))
			self.genreliste.append(("NDR Mecklenburg-Vorpommern", "21518350"))
			self.genreliste.append(("NDR Niedersachsen", "21518352"))
			self.genreliste.append(("NDR Schleswig-Holstein", "21518354"))
			self.genreliste.append(("RB", "5898"))
			self.genreliste.append(("RBB", "5874"))
			self.genreliste.append(("RBB Brandenburg", "21518356"))
			self.genreliste.append(("RBB Berlin", "21518358"))
			self.genreliste.append(("SR", "5870"))
			self.genreliste.append(("SWR", "5310"))
			self.genreliste.append(("SWR Rheinland-Pfalz", "5872"))
			self.genreliste.append(("SWR Baden-Württemberg", "5904"))
			self.genreliste.append(("WDR", "5902"))
			self.genreliste.append(("tagesschau24", "5878"))
			self.genreliste.append(("EinsPlus", "4178842"))
			self.genreliste.append(("EinsFestival", "673348"))
			self.genreliste.append(("DW-TV", "5876"))

		if self.gF == "4" and self.sender == "EINSLIKE":
			self['name'].setText("EINSLIKE")
			self.genreliste.append(("TOP von Seite 1 - EINSLIKE", "20"))
			self.genreliste.append(("Neueste Clips", "21"))
			self.genreliste.append(("Meistabgerufene Clips", "22"))
			self.genreliste.append(placeHolder)
			self.genreliste.append(("Leben", "23"))
			self.genreliste.append(("Netz & Tech", "24"))
			self.genreliste.append(("Info", "25"))
			self.genreliste.append(("Spaß & Fiktion", "26"))
			self.genreliste.append(("Musik", "27"))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		if ardPic != "":
			CoverHelper(self['coverArt']).getCover(ardPic)

	def keyOK(self):
		if self.keyLocked:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		extra = self['liste'].getCurrent()[0][1]
		if extra == "99":
			return
		if self.gF == "3":
			url = "%s/tv/sendungVerpasst?tag=%s&kanal=%s" % (mainLink,self.sender,extra)	# "self.sender" kein Tippfehler!
		if self.gF == "4":
			if extra == "20":
				url = mainLink+"/einslike"
			elif extra == "21":
				url = mainLink+"/einslike/Neueste-Videos/mehr?documentId=21282466"
			elif extra == "22":
				url = mainLink+"/einslike/Meistabgerufene-Videos/mehr?documentId=21282464"
			elif extra == "23":
				url = mainLink+"/einslike/Leben/mehr?documentId=21301896"
			elif extra == "24":
				url = mainLink+"/einslike/Netz-Tech/mehr?documentId=21301898"
			elif extra == "25":
				url = mainLink+"/einslike/Info/mehr?documentId=21301900"
			elif extra == "26":
				url = mainLink+"/einslike/Spaß-Fiktion/mehr?documentId=21301902"
			elif extra == "27":
				url = mainLink+"/einslike/Musik/mehr?documentId=21301894"
		self.session.open(ARDStreamScreen,url,auswahl,self.gF)

class ARDPostSelect(MPScreen, ThumbsHelper):

	def __init__(self,session,auswahl,genreName,genreFlag,mediaFlag):
		self.auswahl = auswahl
		self.gN = genreName
		self.gF = genreFlag
		self.mF = mediaFlag
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
			"info" : self.keyInfo,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("ARD-Mediathek")
		self['ContentTitle'] = Label("Auswahl der Inhalte")

		self['Page'] = Label(_("Page:"))
		self['handlung'] = Label(helpText)
		self.genreliste = []
		self.textTrigger = 0
		self.page = 1
		self.sendungen = ""
		self.lastpage = 1	# Alles hier hat nur 1 Seite
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		if self.gF == "2":	# ABC - TV
			url = "%s/tv/sendungen-a-z?buchstabe=%s&mcontent=page.1" % (mainLink,self.auswahl)
		if self.gF == "7":	# ABC - Radio
			url = "%s/radio/sendungen-a-z?buchstabe=%s&mcontent=page.1" % (mainLink,self.auswahl)
		if self.gF == "10":	# Dossiers
			url = mainLink+"/tv"
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.genreliste = []
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		if self.gF == "10":	# Dossiers
			sub = re.findall('<a class="more" aria-labelledby.*? href="(.*?)".*?morebutton">(.+?)<', data,re.S)
			if sub:
				for url, title in sub:
					url = mainLink+url+"&mcontent=page.".replace("&amp;","&")	#	Dossier innerhalb vom Dossier
					if not re.search('.*?(TV-Livestreams|Themen|Rubriken)', title):
						sub = decodeHtml(title),url
						self.genreliste.append((sub))
		else: # Alles andere
			self.sendungen = re.findall('<div class="box" .*?textWrapper.*?<a\shref="(.*?)".*?headline">(.*?)<', data, re.S)
			if self.sendungen:
				for (url,title) in self.sendungen:
					url = mainLink+url.replace("&amp;","&")
					if "|" in title:
						title = title.replace("|","-")
					self.genreliste.append((decodeHtml(title),url))
			else:
				self.genreliste.append((isWeg,None,None,None))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.genreliste, 0, 1, None, None, '<meta name="gsaimg512" content="(.*?)"', self.page, self.lastpage, mode=1)
		if self['liste'].getCurrent()[0][0] != isWeg:
			self.showInfos()

	def showInfos(self):
		if self.gF != "10":
			url = self['liste'].getCurrent()[0][1]
			getPage(url).addCallback(self.handlePicAndTxt).addErrback(self.dataError)

	def handlePicAndTxt(self, data):
		handlung = ''
		streamPic = None
		gefunden = re.findall('<meta name="description" content="(.*?)"/.*?<meta name="author" content="(.*?)".*?<meta name="gsaimg512" content="(.*?)"/>.*?<div class="box">.*?textWrapper.*?dachzeile">(.*?)[<|\s]', data, re.S)
		if gefunden:
			for (itxt,sender,streamPic,ausgaben) in gefunden:
				itxttmp = itxt.split("|")
				itxt = itxttmp[-1]
				itxt = decodeHtml(itxt)
				itxt = itxt.lstrip()
				if itxt == "":
					itxt = tDef
				if not ausgaben:
					ausgaben = tDef
				url = self['liste'].getCurrent()[0][1]
				if "/tv/" in url:
					media = "TV"
				elif "/radio/" in url:
					media = "Radio"
				else:
					media = "?"
				handlung = "Media:\t%s\nGenre:\t%s\nSender:\t%s\nClips:\t%s" % (media,self.gN,sender,ausgaben)
		if self.textTrigger == 1:
			streamHandlung = itxt
		elif self.textTrigger == 0:
			streamHandlung = handlung
		self['handlung'].setText(streamHandlung)
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText("Sendung / Thema\n\n' "+streamName+" '")
		self.keyLocked = False
		if streamPic:
			CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		if self['liste'].getCurrent()[0][0] == isWeg:
			self.close()
		streamLink = self['liste'].getCurrent()[0][1]
		if streamLink == None:
			return
		self.session.open(ARDStreamScreen,streamLink,self.gN,self.gF)

	def keyInfo(self):
		if self.keyLocked:
			return
		if self.textTrigger == 0:
			self.textTrigger = 1
		elif self.textTrigger == 1:
			self.textTrigger = 0
		self.showInfos()

class ARDStreamScreen(MPScreen, ThumbsHelper):

	def __init__(self, session,streamLink,genreName,genreFlag):
		self.streamLink = streamLink
		self.gN = genreName
		self.gF = genreFlag
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
			"yellow" : self.keyYellow,
			"blue" : self.keyBlue,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"info" : self.keyInfo
			}, -1)

		self.keyLocked = True
		self['title'] = Label("ARD-Mediathek")
		self['ContentTitle'] = Label("Auswahl des Clips")
		self['name'] = Label(_("Please wait..."))
		if self.gF == "1" or self.gF == "6":
			self['F3'] = Label("Relevanz")
		else:
			self['F4'] = Label("Mehr...")

		self['Page'] = Label(_("Page:"))
		self.future = 0
		self.page = 1
		self.lastpage = 1
		self.textTrigger = 0
		self.suchTrigger = "date"
		self.blueTrigger = 0
		self.blueURL = ""
		self.blueMemory = [0,0,0]
		self.blueIdx = 0
		self.folgen = ""
		self.filmliste = []
		self.sendung = ""
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		if self.blueTrigger == 0:
			if self.gF == "1" or self.gF =="6":	# Suche
				url = self.streamLink+self.suchTrigger+"&mresults=page."+str(self.page)	# Kein "%s" hier verwenden!! Gewandelte Umlaute aus searchCallBack enthalten "%"!
			elif self.gF == "10" and not "mcontent" in self.streamLink:	# Dossiers
				url = self.streamLink+"&mquelle=quelle.all&mall=page.%s" % (self.page)
			elif self.gF == "10" and "mcontent" in self.streamLink:	#	Dossier innerhalb vom Dossier
				url = self.streamLink+str(self.page)
			elif self.gF == "4" or self.gF == "8":	# Kategorien
				url = "%s&mcontent=page.%s" % (self.streamLink,self.page)
			elif self.gF == "3":
				url = self.streamLink
			else:
				url = "%s&mcontents=page.%s" % (self.streamLink,self.page)
			if self.gN == "TOP von Seite 1 - TV" or self.gN == "TOP von Seite 1 - EINSLIKE":	#	self.gF == 4 überschreiben
				url = self.streamLink
		else:	# Zweiter Durchlauf, wenn "Mehr.." gedrückt wurde (StreamLink wird zur StreamLink-Liste)
			self['F4'].setText("Zurück")
			self.blueMemory[0] = self.page
			self.page = 1
			url = self.blueURL+"&mpage=page.moreclips"
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		if self.blueTrigger == 0:
			if self.page == 1:	# Gleich bei Seite 1 die maximale Seite merken. Danach nicht nochmal berechnen
				if "Loader-source" in data:
					try:
						max = re.findall('Loader-source.*?<a.*?>\s+(.*?)\s+</a>', data, re.S)[-2]	# Der vorletzte Treffer ist die letzte Seite
					except IndexError:	#	Gab kein [-2]
						max = "x"
					max = filter(lambda x: x.isdigit(), max)	#	Ziffer enthalten?
					if max == "":	# Keine Ziffer gefunden
						self.lastpage = 1
					else:
						self.lastpage = int(max)
				else: # Kein "Loader-source"; ergo: Gibt nur eine Seite
					self.lastpage = 1
		else:	#	"Mehr..."
			self.blueMemory[1] = self.lastpage
			self.lastpage = 1
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))

		if self.blueTrigger == 1:
			self.blueIdx = 0
		else:
			self.blueIdx = self.blueMemory[2]
			self.blueMemory[2] = 0
		if (self.gF == "4" and self.gN == "TOP von Seite 1 - TV") or (self.gF == "4" and self.gN == "TOP von Seite 1 - EINSLIKE"): # TOP von Seite 1
			if self.blueTrigger == 0:
				self.folgen = re.findall('ModStageMediaPanel.*?textWrapper.*?href="(.*?)" class="textLink">.*?headline">(.*?)</', data, re.S)
			else:	#	"Mehr..." im 2. Durchlauf
				self.folgen = re.findall('<div class="teaser" data-ctrl-.*?textWrapper.*?href="(.*?)" class="textLink">.*?headline">(.*?)</', data, re.S)
		elif self.gF == "11":	#	Tagesschau/themen
			self.folgen = re.findall('data-ctrl-contentsoptionalLayouter-entry.*?textWrapper.*?href="(.*?)" class="textLink">.*?headline">(.*?)</', data, re.S)
		else:
			self.folgen = re.findall('<div class="teaser" data-ctrl-.*?textWrapper.*?href="(.*?)" class="textLink">.*?headline">(.*?)</', data, re.S)
		if self.folgen:
			for (url,title) in self.folgen:
				if not "Livestream" in url and not "Dossier" in url and not "http:" in url and "bcastId" in url:
					url = mainLink+url.replace("&amp;","&")
					sub = re.search('documentId=(.*?)($|&)', url, re.S)
					if sub:
						iD = sub.group(1)
						self.filmliste.append((decodeHtml(title),url,iD))
						self.ml.setList(map(self._defaultlistleft, self.filmliste))
						self.ml.moveToIndex(self.blueIdx)
		else:
			self.filmliste.append((isWeg, None, None, None))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, None, None, '<meta name="gsaimg512" content="(.*?)"', self.page,self.lastpage, mode=1)
		if self['liste'].getCurrent()[0][0] != isWeg:
			self.showInfos()

	def showInfos(self):
		self['name'].setText('')
		self.blueURL = self['liste'].getCurrent()[0][1]
		getPage(self.blueURL).addCallback(self.handlePicAndTxt).addErrback(self.dataError)

	def handlePicAndTxt(self, data):
		handlung = ''
		streamPic = None
		self.future = 0
		if not "dcterms.date" in data:
			self.future = 1
			ergebnis = re.findall('<meta name="description" content="(.*?)"/>.*?author" content="(.*?)"/.*?<meta name="gsaimg512" content="(.*?)"/>.*?dcterms.title" content="(.*?)"/>.*?og:site_name" content="(.*?)"/>.*?<p class="subtitle">(.*?)</', data, re.S)
		if "dcterms.isPartOf" in data and self.future == 0:
			ergebnis = re.findall('<meta name="description" content="(.*?)"/>.*?author" content="(.*?)"/.*?<meta name="gsaimg512" content="(.*?)"/>.*?dcterms.isPartOf" content="(.*?)"/>.*?dcterms.date" content="(.*?)"/>.*?<p class="subtitle">(.*?)</', data, re.S)
		else:
			if self.future == 0:
				ergebnis = re.findall('<meta name="description" content="(.*?)"/>.*?author" content="(.*?)"/.*?<meta name="gsaimg512" content="(.*?)"/>.*?dcterms.title" content="(.*?)"/>.*?dcterms.date" content="(.*?)"/>.*?<p class="subtitle">(.*?)</', data, re.S)
		if ergebnis:
			for (itxt,sender,streamPic,sendung,uhr,meta) in ergebnis:
				self.sendung = sendung
				if not itxt or len(itxt) == 0:
					itxt = tDef
				else:
					title = self['liste'].getCurrent()[0][0]
					if title in itxt:
						itxttmp = itxt.split(title+":")
						itxt = itxttmp[-1].lstrip()
						itxt = decodeHtml(itxt)
						if itxt == "":
							itxt = tDef
					else:
						itxt = decodeHtml(itxt)
				if "ARD" in uhr:	#	Fakeeintrag um Absturz zu verhindern
					uhr = " - Liegt in der Zukunft!"
				else:
					uhr = uhr.split("T")
					uhr = uhr[-1]
					uhr = ", "+uhr[:5]+" Uhr"
				meta = meta.split(" | ")
				airtime = meta[0]
				dur = meta[1]
			url = self['liste'].getCurrent()[0][1]
			if "/tv/" in url:
				media = "TV"
			elif "/einslike/" in url:
				media = "TV & Radio (EINSLIKE)"
			elif "/radio/" in url:
				media = "Radio"
			else:
				media = "?"
			handlung = "Media:\t%s\nGenre:\t%s\nSender:\t%s\nClip-Datum:\t%s%s\nDauer:\t%s" % (media,self.gN,sender,airtime,uhr,dur)
		if self.textTrigger == 1:
			streamHandlung = itxt
		elif self.textTrigger == 0:
			streamHandlung = handlung
		self['handlung'].setText(streamHandlung)
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText("Sendung / Thema\n\n' "+decodeHtml(self.sendung)+" '")
		self.keyLocked = False
		if streamPic:
			CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		if self.streamName == isWeg:
			self.close()
		self['name'].setText(_("Please wait..."))
		url = self['liste'].getCurrent()[0][1]
		if url == None:
			streamName = self['liste'].getCurrent()[0][0]
			self['name'].setText(streamName)
			return
		else:
			getPage(url).addCallback(self.get_Link).addErrback(self.dataError)

	def get_Link(self, data):
		fsk = re.search('<div class="box fsk.*?"teasertext">\s+(.*?)\s+</p>', data, re.S)
		if fsk:
			message = self.session.open(MessageBoxExt, _(fsk.group(1)), MessageBoxExt.TYPE_INFO, timeout=7)
			streamName = self['liste'].getCurrent()[0][0]
			self['name'].setText(streamName)
			return
		else:
			qualiSub = self['liste'].getCurrent()[0][2]
			url = mainLink+"/play/media/"+qualiSub
			getPage(url).addCallback(self.QCnGO).addErrback(self.dataError)

	def QCnGO(self, data):
		rtH = ""
		rtP = ""
		htP = ""
		r_qUp = 0
		h_qUp = 0
		qualitycheck = re.findall('"_quality":(.*?),.*?"_server":"(.*?)",.*?"_stream":"(.*?)"', data, re.S)
		if qualitycheck:
			for (a,c,d) in qualitycheck:
				if "?sen=" in d:	# Für ARD-Links, sonst wird von rtmp auf http geschwenkt - "?sen=[...]" vermutlich wegen Untertitel für Hörgeschädigte in PC-Browser
					d = d.split("?")[0]
				if a != '"auto"':
					if int(a) == r_qUp and c != "":
						rtH = c
						rtP = d
						r_qUp += 1
					elif int(a) == h_qUp and c == "":
						htP = d
						h_qUp += 1

			m = re.search('"_quality":%s,"_stream":\[".*?","(.*?)"\]' % (h_qUp - 1), data)
			if m:
				htP = m.group(1)
				if "?sen=" in htP:	# Für ARD-Links, sonst wird von rtmp auf http geschwenkt - "?sen=[...]" vermutlich wegen Untertitel für Hörgeschädigte in PC-Browser
					htP = htP.split("?")[0]

			if len(rtH+rtP+htP) == 0:	# Hier stimmt gar nichts!
				message = self.session.open(MessageBoxExt, "\n' -----------| "+decodeHtml(self.streamName)+" |----------- '\n\n"+alienFound, MessageBoxExt.TYPE_INFO, timeout=15)
				streamName = self['liste'].getCurrent()[0][0]
				self['name'].setText(streamName)
				return

			# Sonderlocken
			htP = htP.replace(" ","%20")	#	URI-Konformität: Es gibt einige Streams mit Leerzeichen im Link
			rtP = rtP.replace(" ","%20")
			rtH = rtH.replace(" ","%20")

			if htP == "" and rtH != "":	# Wenn kein einziger http-Link vorhanden (ausschliesslich rtmp-Links), umgehe nachfolgende http-Abfrage, und "vertraue darauf" dass Content existiert.
				self.playStream(None, rtP, rtH, htP)
			elif htP != "":	# http-Abfrage, ob Content existiert. Wenn ja, und es werden ebenfalls rtmp-Links angeboten, dann existieren immer beide Contents! Eine rtmp-Abfrage wäre zu kompliziert.
				getPage(htP, method='HEAD').addCallback(self.playStream, rtP, rtH, htP).addErrback(self.httpURLError)
			else:
				message = self.session.open(MessageBoxExt, "\n' -----------| "+decodeHtml(self.streamName)+" |----------- '\n\n"+alienFound, MessageBoxExt.TYPE_INFO, timeout=15)
				streamName = self['liste'].getCurrent()[0][0]
				self['name'].setText(streamName)

	def httpURLError(self, error):
		message = self.session.open(MessageBoxExt, "\n' "+decodeHtml(self.streamName)+" '\n\n"+isWeg, MessageBoxExt.TYPE_INFO, timeout=7)
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)

	def playStream(self, response, rtP, rtH, htP):
		self['name'].setText("Sendung / Thema\n\n' "+decodeHtml(self.sendung)+" '")
		if htP != "":	# Neu: Bevorzuge http, statt zuvor rtmp
			playpath = htP
			playlist = []
			playlist.append((self.streamName, playpath))
			self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='ard')
		else:
			if "fc-ondemand.radiobremen.de" in rtH:	# Sonderlocken
				host = rtH.split('mediabase/')[0]
				playpath1 = rtH.split('/mediabase/')[1]
				playpath2 = rtP[4:]
				playpath = "mp4:mediabase/"+playpath1+"/"+playpath2	#	Hier kein "%s" verwenden, da "%" im String vorkommen kann
			elif "fm-ondemand.einsplus.de" in rtH:
				host = rtH
				playpath = "mp4:"+rtP
			else:
				host = rtH
				playpath = rtP
			playpath = playpath.replace('&amp;','&')
			final = host+" playpath="+playpath	#	Hier kein "%s" verwenden, da "%" im String  vorkommen kann
			playlist = []
			playlist.append((self.streamName, final))
			self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='ard')

	def keyInfo(self):
		if self.keyLocked:
			return
		if self.textTrigger == 0:
			self.textTrigger = 1
		elif self.textTrigger == 1:
			self.textTrigger = 0
		self.showInfos()

	def keyYellow(self):
		if self.keyLocked:
			return
		if self.gF == "1" or self.gF =="6":
			if self.suchTrigger == "date":
				self['F3'].setText("Datum")
				self.suchTrigger = "score"
			elif self.suchTrigger == "score":
				self['F3'].setText("Relevanz")
				self.suchTrigger = "date"
		else:
			return
		self.loadPage()

	def keyBlue(self):
		if self.keyLocked:
			return
		if self.blueTrigger == 0:
			self.blueMemory[2] = self['liste'].getSelectedIndex()
			self.blueTrigger = 1
		elif self.blueTrigger == 1:
			self['F4'].setText("Mehr...")
			self.page = self.blueMemory[0]
			self.lastpage = self.blueMemory[1]
			self.blueTrigger = 0
		self.loadPage()