# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

# Globals
suchCache = ""	# Letzte Sucheingabe
AdT = " "		# Default: Anzahl der Treffer/Clips/Sendungen
pageTrigger = 25# Max. Zeilen in Listfenster (25/50)
suchTrigger = 0	# pageTrigger OnTop: Die ZDF-Suche kann bis 100 (.../75/100)
BASE_URL = "http://www.zdf.de/ZDFmediathek"
isWeg = "Leider nicht (mehr) auf den ZDF-Servern vorhanden, oder Maximum erreicht!\n(gegebenenfalls Zeilenanzahl erhöhen)"
helpText2 = "Tipp: Die gelbe Taste legt die maximale Anzahl der zu listenden Zeilen (25 oder 50) fest. Für die Suche kann auf bis zu 100 erhöht werden. Für beides gilt: Je kleiner die Anzahl, desto geringer die Wartezeit. Allerdings liefern die ZDF-Server dann auch weniger Ergebnisse."
zdfPic = "http://www.zdf-werbefernsehen.de/typo3temp/pics/f2691d753e.jpg"

class ZDFGenreScreen(MPScreen):

	def __init__(self, session):
		self.keyLocked = True
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

		self['title'] = Label("ZDF Mediathek")
		self['ContentTitle'] = Label("Auswahl des Genres")

		self.genreliste = []
		self.bildchen = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "%s/xmlservice/web/senderliste" % BASE_URL
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		folgen = re.findall('<teaserimages>.*?key="173x120">(.*?)</te', data, re.S)
		if folgen:
			for image in folgen:
				self.bildchen.append(image)
		self.genreliste = []
		ZDFtiviPic = "%s/contentblob/2049596/timg485x273blob/8935329" % BASE_URL
		self.genreliste.append(("Suche (alle Sender)", "1", zdfPic))
		self.genreliste.append(("Sendungen A bis Z (alle Sender)", "2", zdfPic))
		self.genreliste.append(("Startseite (alle Sender)", "3", zdfPic))
		self.genreliste.append(("Nachrichten", "4", zdfPic))
		self.genreliste.append(("Sendung verpasst? (Wochenübersicht, alle Sender)", "5", zdfPic))
		self.genreliste.append(("Rubriken (grob, alle Sender)", "6", zdfPic))
		self.genreliste.append(("Themen (detaillierter, alle Sender)", "7", zdfPic))
		self.genreliste.append(("Podcasts (alle Sender)", "8", zdfPic))
		self.genreliste.append(("ZDF", "9", self.bildchen[0]))
		self.genreliste.append(("ZDFneo", "10", self.bildchen[1]))
		self.genreliste.append(("ZDF.kultur", "11", self.bildchen[2]))
		self.genreliste.append(("ZDFinfo", "12", self.bildchen[3]))
		self.genreliste.append(("ZDFtivi", "13", ZDFtiviPic))
		self.genreliste.append(("3sat (nur Anteile des ZDF)", "14", self.bildchen[4]))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		self['name'].setText(self['liste'].getCurrent()[0][0])
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		genreName = self['liste'].getCurrent()[0][0]
		genreFlag = self['liste'].getCurrent()[0][1]
		streamPic = self['liste'].getCurrent()[0][2]
		if genreFlag == "1": # Suche
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = suchCache, is_dialog=True)
		elif genreFlag == "13":	# ZDFtivi
			streamLink = "http://www.tivi.de/tiviVideos/navigation?view=flashXml"
			self.session.open(ZDFPostSelect,genreName,genreFlag,streamPic,streamLink,AdT)
		else:
			self.session.open(ZDFPreSelect,genreName,genreFlag,streamPic)

	def searchCallback(self, callbackStr):
		genreFlag = self['liste'].getCurrent()[0][1]
		self.keyLocked = False
		if callbackStr is not None:
			global suchCache
			suchCache = callbackStr
			genreName = "Suche... ' %s '" % suchCache
			self.session.open(ZDFPreSelect,genreName,genreFlag,self['liste'].getCurrent()[0][2])
		else:
			return

class ZDFPreSelect(MPScreen, ThumbsHelper):

	def __init__(self,session,genreName,genreFlag,prePic):
		self.keyLocked = True
		self.gN = genreName
		self.gF = genreFlag
		self.pP = prePic
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
			"yellow"	: self.keyYellow,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['F3'] = Label("Liste")
		self['title'] = Label("ZDF Mediathek")
		self['ContentTitle'] = Label("Auswahl der Kategorie")
		self['name'] = Label(_("Please wait..."))

		global suchTrigger
		suchTrigger = 0
		self.genreliste = []
		self.bildchen = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = ""
		self['name'].setText("Auswahl des Preselect")
		if self.gF == "1":
			self['handlung'].setText(helpText2+"\n\nZeilen: "+str(suchTrigger+pageTrigger)+" (25 / 50 / 75 / 100)")
		else:
			self['handlung'].setText(helpText2+"\n\nZeilen: "+str(pageTrigger)+" (25 / 50)")
		if self.gF == "6":
			url = "%s/xmlservice/web/rubriken" % BASE_URL
		elif self.gF == "7":
			url = "%s/xmlservice/web/themen" % BASE_URL
		elif self.gF == "8":
			url = "%s/xmlservice/web/podcasts" % BASE_URL
		elif int(self.gF) > 8 and int(self.gF) != 13:
			url = "%s/xmlservice/web/senderliste" % BASE_URL
		elif self.gF == "13":
			url = "http://www.tivi.de/tiviVideos/navigation?view=flashXml"
		if int(self.gF) <= 5:
			self.loadPageData(self.pP)
		else:
			getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.genreliste = []
		if self.gF == "1":
			self['ContentTitle'].setText("Auswahl der Suchergebnisse")
			self.genreliste.append(("Suchbegriff zu Sendungs-Name", "1"," ",self.pP,AdT))
			self.genreliste.append(("Suchbegriff zu Clip-Name / Info-Text / Verweis", "2"," ",self.pP,AdT))
		elif self.gF == "2":
			self['name'].setText("Auswahl des Buchstabens")
			self['ContentTitle'].setText("Auswahl des Buchstabens")
			d = -3
			for c in range(0,22,3): # ABC
				d += 3
				if c == 15 or c == 21:
					d += 1
					self.genreliste.append((chr(ord('A')+d-1)+chr(ord('A')+d)+chr(ord('A')+d+1)+chr(ord('A')+d+2)," "," ",self.pP,AdT))
				else:
					self.genreliste.append((chr(ord('A')+d)+chr(ord('A')+d+1)+chr(ord('A')+d+2)," "," ",self.pP,AdT))
			self.genreliste.insert(0, ('0-9'," "," ",self.pP,AdT))
		elif self.gF == "3":	# Startseite
			self.genreliste.append(("Tipps", "1"," ",self.pP,AdT))
			self.genreliste.append(("Meist gesehen", "2"," ",self.pP,AdT))
			self.genreliste.append(("Aktuellste", "3"," ",self.pP,AdT))
		elif self.gF == "4":	# Nachrichten
			self.genreliste.append(("Aktuellste", "1"," ",self.pP,AdT))
			self.genreliste.append(("Ganze Sendungen", "2"," ",self.pP,AdT))
			self.genreliste.append(("Meist gesehen", "3"," ",self.pP,AdT))
		elif self.gF == "5":	# Sendung verpasst?
			self['ContentTitle'].setText("Auswahl des Kalendertages")
			for q in range (0,7,1):
				if q == 0:
					s1 = " - Heute und im Voraus"
				elif q == 1:
					s1 = " - Gestern"
				else:
					s1 = ""
				s2 = (datetime.date.today()+datetime.timedelta(days=-q)).strftime("%d.%m.%y")
				s3 = (datetime.date.today()+datetime.timedelta(days=-q)).strftime("%d%m%y")
				self.genreliste.append((s2+s1,s3," ",self.pP,AdT))
		elif self.gF == "6" or self.gF == "7":	# Rubriken/Themen
			if self.gF == "6":
				self['ContentTitle'].setText("Auswahl der Rubrik")
			else:
				self['ContentTitle'].setText("Auswahl des Themas")
			folgen = re.findall('<teaserimages>.*?key="485x273">(.*?)</te.*?<title>(.*?)</ti.*?<detail>(.*?)</de.*?<assetId>(.*?)</as.*?<length>(.*?)</le.*?<vcmsUrl>(.*?)</vc', data, re.S)
			if folgen:
				for (image,themrubr,info,assetId,anzahl,url) in folgen:
					info = info.replace("\n"," ")
					decodeHtml(info)
					themrubr = decodeHtml(themrubr)
					if len(info) < 170:
						info = "\n"+info
					handlung = "Clips: %s\n%s" % (anzahl,info)
					self.genreliste.append((themrubr,assetId,handlung,image,anzahl))
				self.genreliste.sort(key=lambda t : t[0].lower())
		elif self.gF == "8":	# Podcasts
			self['ContentTitle'].setText("Auswahl des Podcasts")
			folgen = re.findall('key="94x65">(.*?)</te.*?<title>(.*?)</ti.*?<detail>(.*?)</de.*?<assetId>(.*?)</as.*?<length>(.*?)</le', data, re.S)
			if folgen:
				for (image,title,info,assetId,anzahl) in folgen:
					info = info.replace("\n"," ")
					decodeHtml(info)
					title = decodeHtml(title)
					self['name'].setText("Podcasts")
					if len(info) < 170:
						info = "\n"+info
					handlung = "Clips: %s\n%s" % (anzahl,info)
					self.genreliste.append((title,assetId,handlung,image,anzahl))
		elif self.gF == "9":	# ZDF
			self.genreliste.append(("Aktuellste", "1"," ",self.pP,AdT))
			self.genreliste.append(("Meist gesehen", "2"," ",self.pP,AdT))
		elif self.gF == "10":	# ZDFneo
			folgen = re.findall('<teaserimages>.*?key="173x120">(.*?)</te.*?<title>(.*?)</ti', data, re.S)
			if folgen:
				for (image,sender) in folgen:
					if "neo" in sender:
						self.bildchen.append(image)
			self.genreliste.append(("Aktuell im Programm", "1"," ",self.pP,AdT))
			self.genreliste.append(("Unsere Sendungen", "2"," ",self.pP,AdT))
		elif self.gF == "11":	# ZDF.kultur
			folgen = re.findall('<teaserimages>.*?key="173x120">(.*?)</te.*?<title>(.*?)</ti', data, re.S)
			if folgen:
				for (image,sender) in folgen:
					if "kultur" in sender:
						self.bildchen.append(image)
			self.genreliste.append(("Unsere Tipps", "1"," ",self.pP,AdT))
			self.genreliste.append(("Unsere Sendungen", "2"," ",self.pP,AdT))
			self.genreliste.append(("Meist gesehen", "3"," ",self.pP,AdT))
		elif self.gF == "12":	# ZDFinfo
			folgen = re.findall('<teaserimages>.*?key="173x120">(.*?)</te.*?<title>(.*?)</ti', data, re.S)
			if folgen:
				for (image,sender) in folgen:
					if "info" in sender:
						self.bildchen.append(image)
			self.genreliste.append(("Unsere Tipps", "1"," ",self.pP,AdT))
			self.genreliste.append(("Unsere Sendungen", "2"," ",self.pP,AdT))
			self.genreliste.append(("Meist gesehen", "3"," ",self.pP,AdT))
		elif self.gF == "14":	# 3sat
			folgen = re.findall('<teaserimages>.*?key="173x120">(.*?)</te.*?<title>(.*?)</ti', data, re.S)
			if folgen:
				for (image,sender) in folgen:
					if "sat" in sender:
						self.bildchen.append(image)
			self.genreliste.append(("Aktuelle Clips", "1"," ",self.pP,AdT))
			self.genreliste.append(("Unsere Sendungen", "2"," ",self.pP,AdT))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.genreliste, 0, 1, 3, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][3]
		if self.gF == "6" or  self.gF == "7":
			self['handlung'].setText(self['liste'].getCurrent()[0][2])
		self['name'].setText(self['liste'].getCurrent()[0][0])
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		passThru = 0
		auswahl = self['liste'].getCurrent()[0][0]
		extra = self['liste'].getCurrent()[0][1]
		if self.gF == "1": # Suche
			TrigCount = suchTrigger+pageTrigger
			sL = BASE_URL+"/xmlservice/web/detailsSuche?searchString="+suchCache.replace(' ', '+')+"&maxLength="+str(TrigCount)
			if extra == "1":
				streamLink = sL
			if extra == "2":
				streamLink = sL
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,"+")
		elif self.gF == "2": # ABC
			if auswahl == "0-9":
				streamLink = "%s/xmlservice/web/sendungenAbisZ?detailLevel=2&characterRangeStart=0-9&characterRangeEnd=0-9" % BASE_URL
			else:
				streamLink = "%s/xmlservice/web/sendungenAbisZ?characterRangeStart=%s&detailLevel=2&characterRangeEnd=%s" % (BASE_URL,auswahl[:1],auswahl[-1:])
		elif self.gF == "3":	# Startseite
			if extra == "1":
				streamLink = "%s/xmlservice/web/tipps?id=_STARTSEITE&maxLength=%s" % (BASE_URL,str(pageTrigger))
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
			elif extra == "2":
				streamLink = "%s/xmlservice/web/meistGesehen?id=_GLOBAL&maxLength=%s" % (BASE_URL,str(pageTrigger))
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
			elif  extra == "3":
				streamLink = "%s/xmlservice/web/aktuellste?id=_STARTSEITE&maxLength=%s" % (BASE_URL,str(pageTrigger))
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
		elif self.gF == "4":	# Nachrichten
			if extra == "1":
				streamLink = "%s/xmlservice/web/aktuellste?id=_NACHRICHTEN&maxLength=%s" % (BASE_URL,str(pageTrigger))
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
			elif extra == "2":
				streamLink = "%s/xmlservice/web/ganzeSendungen" % BASE_URL
			elif  extra == "3":
				streamLink = "%s/xmlservice/web/meistGesehen?id=_NACHRICHTEN&maxLength=%s" % (BASE_URL,str(pageTrigger))
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
		elif self.gF == "5":	# Sendung verpasst?
			streamLink = "%s/xmlservice/web/sendungVerpasst?startdate=%s&enddate=%s&maxLength=%s" % (BASE_URL,extra,extra,str(pageTrigger))
			passThru = 1
			self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
		elif self.gF == "6":	# Rubriken
			streamLink = "%s/xmlservice/web/aktuellste?id=%s&maxLength=%s" % (BASE_URL,extra,str(pageTrigger))
		elif self.gF == "7":	# Themen
			streamLink = "%s/xmlservice/web/aktuellste?id=%s&maxLength=%s" % (BASE_URL,extra,str(pageTrigger))
			passThru = 1
			self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
		elif self.gF == "8":	# Podcasts
			assetId = self['liste'].getCurrent()[0][1]
			image = self['liste'].getCurrent()[0][3]
			streamLink = "%s/podcast/%s?view=podcast,%s" % (BASE_URL,assetId,image)	# Schmuggle Image-URL unter, mit "," als Trenner
			passThru = 1
			self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,"-")
		elif self.gF == "9":	# ZDF
			if extra == "1":
				streamLink = "%s/xmlservice/web/tipps?id=_STARTSEITE&maxLength=%s" % (BASE_URL,str(pageTrigger))
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
			elif extra == "2":
				streamLink = "%s/xmlservice/web/meistGesehen?id=_GLOBAL&maxLength=%s" % (BASE_URL,str(pageTrigger))
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
			elif  extra == "3":
				streamLink = "%s" % BASE_URL
		elif self.gF == "10":	# ZDFneo
			if extra == "1":
				streamLink = "%s/senderstartseite/sst0/1209122?flash=off" % BASE_URL
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
			elif extra == "2":
				streamLink = "%s/senderstartseite/sst1/1209122?flash=off" % BASE_URL
		elif self.gF == "11":	# ZDF.kultur
			if extra == "1":
				streamLink = "%s/senderstartseite/sst0/1317640?flash=off" % BASE_URL
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
			elif extra == "2":
				streamLink = "%s/senderstartseite/sst1/1317640?flash=off" % BASE_URL
			elif  extra == "3":
				streamLink = "%s/senderstartseite/sst2/1317640?flash=off" % BASE_URL
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
		elif self.gF == "12":	# ZDFinfo
			if extra == "1":
				streamLink = "%s/senderstartseite/sst0/1209120?flash=off" % BASE_URL
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
			elif extra == "2":
				streamLink = "%s/senderstartseite/sst1/1209120?flash=off" % BASE_URL
			elif  extra == "3":
				streamLink = "%s/senderstartseite/sst2/1209120?flash=off" % BASE_URL
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
		elif self.gF == "14":	# 3sat
			if extra == "1":
				streamLink = "%s/senderstartseite/sst1/1209116?flash=off" % BASE_URL
				passThru = 1
				self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,AdT)
			elif extra == "2":
				streamLink = "%s/senderstartseite/sst2/1209116?flash=off" % BASE_URL
		else:
			return
		if passThru == 0 and self.gF == "1":
			self.session.open(ZDFPostSelect,self.gN,self.gF,self.pP,streamLink,"+")
		elif passThru == 0 and self.gF != "1":
			self.session.open(ZDFPostSelect,self.gN,self.gF,self.pP,streamLink,AdT)

	def keyYellow(self):
		if self.keyLocked:
			return
		if self.gF == "1":
			global suchTrigger
			suchTrigger += 25
			if pageTrigger+suchTrigger == 125:
				suchTrigger = 0
		else:
			global pageTrigger
			pageTrigger += 25
			if pageTrigger == 75:
				pageTrigger = 25
		self['name'].setText(_("Please wait..."))
		self.loadPage()

class ZDFPostSelect(MPScreen, ThumbsHelper):

	def __init__(self,session,genreName,genreFlag,prePic,streamLink,anzahl):
		self.keyLocked = True
		self.gN = genreName
		self.gF = genreFlag
		self.pP = prePic
		self.anzahl = anzahl
		self.streamLink = streamLink
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
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("ZDF Mediathek")
		self['ContentTitle'] = Label("Auswahl der Sendung")
		self['name'] = Label(_("Please wait..."))

		self.genreliste = []
		self.bildchen = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = self.streamLink
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if int(self.gF) > 9 and int(self.gF) != 13:	# ZDFneo, ZDFinfo, ZDF.kultur,3sat
			self.genreliste = []
			treffer = re.findall('<div class="image">.*?<img src="(.*?)" title="(.*?)".*?<div class="text">.*?<a href=".*?<a href=".*?">(.*?)<.*?a href=".*?">(.*?) B.*?</div>', data, re.S)
			for (image,info,title,anzahl) in treffer:
				info = info.replace("\n"," ")
				decodeHtml(info)
				handlung = "Clips: %s\n" % anzahl
				title = decodeHtml(title)
				asset = image.split('/')
				assetId = asset[3]
				anzahl = anzahl.strip()
				image = image.replace("94x65","485x273")
				image = "%s%s" % ("http://www.zdf.de",image)
				if len(info) < 170:
					info = "\n"+info
				handlung = "Clips: %s\n%s" % (anzahl,info)
				self.genreliste.append((title,assetId,handlung,image,anzahl))
			self.gN = "Sendung"	# Überschreibe den Wert als Kennung für Sendungen statt Clips

		elif self.gF == "13":	# ZDFtivi
			self.genreliste = []
			folgen = re.findall('<ns2:node.*?url=".*?".*?id=".*?".*?label="(.*?)".*?image="(.*?)".*?type=".*?">(.*?)</ns2:node>', data, re.S)
			if folgen:
				for (title,image,url) in folgen:
					title = decodeHtml(title)
					image = "http://www.tivi.de%s" % image
					image = image.replace("tiviNavBild","tiviTeaserbild")
					handlung = "Clips: Keine Angabe"
					self.genreliste.append((title,url,handlung,image,AdT))
		else:
			self.genreliste = []
			folgen = re.findall('<type>sendung</type>.*?<teaserimages>.*?key="485x273">(.*?)</te.*?<title>(.*?)</ti.*?<detail>(.*?)</de.*?<assetId>(.*?)</as.*?<length>(.*?)</le', data, re.S)
			if folgen:
				for (image,title,info,assetId,anzahl) in folgen:
					info = info.replace("\n"," ")
					decodeHtml(info)
					title = decodeHtml(title)
					if len(info) < 170:
						info = "\n"+info
					handlung = "Clips: %s\n%s" % (anzahl,info)
					self.genreliste.append((title,assetId,handlung,image,anzahl))
		# remove duplicates
		self.genreliste = list(set(self.genreliste))
		self.genreliste.sort(key=lambda t : t[0].lower())
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.genreliste, 0, 1, 3, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(self['liste'].getCurrent()[0][2])
		if self.gF == "1":
			self['name'].setText("' "+suchCache+" '")
		else:
			self['name'].setText(self['liste'].getCurrent()[0][0])
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		anzahl = self['liste'].getCurrent()[0][4]
		if self.gF == "13":
			streamLink = self['liste'].getCurrent()[0][1]
			self.session.open(ZDFStreamScreen,streamLink,self['liste'].getCurrent()[0][0],self.gF,anzahl)
		else:
			streamLink = "%s/xmlservice/web/aktuellste?id=%s&maxLength=%s" % (BASE_URL,self['liste'].getCurrent()[0][1],str(pageTrigger))
			self.session.open(ZDFStreamScreen,streamLink,self.gN,self.gF,anzahl)

class ZDFStreamScreen(MPScreen, ThumbsHelper):

	def __init__(self, session,streamLink,genreName,genreFlag,anzahl):
		self.keyLocked = True
		self.streamLink = streamLink
		self.gN = genreName
		self.gF = genreFlag
		self.anzahl = anzahl
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

		self['title'] = Label("ZDF Mediathek")
		self['ContentTitle'] = Label("Auswahl des Clips")
		self['name'] = Label(_("Please wait..."))

		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 1
		self.lastpageS = 1
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		if self.anzahl == " ": # Max. Seitenanzahl nicht ermittelbar
			if self.gF == "13":
				url = "%s%s" % ("http://www.tivi.de",self.streamLink)
				self['page'].setText(str(self.page)+' / 1')
			else:
				offset = "&offset="+str((self.page-1)*pageTrigger)
				url = "%s%s" % (self.streamLink,offset)
				self['page'].setText(str(self.page)+' / x')
		elif self.anzahl == "+": # Suchergebnis-Anzahl von Clips liefern <batch>
			self.lastpage = pageTrigger+suchTrigger
			if self.page > self.lastpage:
				self.page -= 1
			offset = "&offset="+str((self.page-1)*self.lastpage)
			url = "%s%s" % (self.streamLink,offset)
		elif self.anzahl == "-": # Podcasts
			par = self.streamLink.split(",")
			url = par[0]
		else:
			if self.page > self.lastpage:
				self.page -= 1
			self.lastpage = int(self.anzahl)/pageTrigger+1
			offset = "&offset="+str((self.page-1)*pageTrigger)
			self['page'].setText(str(self.page)+' / '+str(self.lastpage))
			url = "%s%s" % (self.streamLink,offset)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		typ,image,title,info,assetId,sender,sendung,dur = "","","","","","","",""
		if self.gF == "1" and self.anzahl == "+": # Anzahl der Treffer-Seiten (Clips) ermitteln, wenn gesucht wurde...
			anzahl = re.findall('<searchResult>.*?<batch>(.*?)</ba', data, re.S)
			if anzahl:
				for teiler in anzahl:
					self.lastpageS = (int(teiler)/(pageTrigger+suchTrigger))
					self['page'].setText(str(self.page) + ' / ' + str(self.lastpageS))
		if self.gF == "5": # Sendung verpasst?
			self['page'].setText('1 / 1')
			treffer = re.findall('<teaser member="(.*?)">.*?<type>video</type>.*?key="485x273">(.*?)</te.*?<title>(.*?)</ti.*?<detail>(.*?)</de.*?<assetId>(.*?)</as.*?<channel>(.*?)</ch.*?<length>(.*?)</le.*?<airtime>(.*?)</ai', data, re.S)
			if treffer:
				for (member,image,title,info,assetId,sender,dur,airtime) in treffer:
					info = info.replace("\n"," ")
					info = decodeHtml(info)
					title = decodeHtml(title)
					if "000" in dur:
						dur = dur[0:8]
					send = re.findall('originChannelTitle>(.*?)</ori', data, re.S)	# Diesen Tag extra lesen, da nicht immer an gleicher Stelle
					for sendung in send:
						sendung = decodeHtml(sendung)
					if len(info) < 170:
						info = "\n"+info
					handlung = "Sender: %s\nClip-Datum: %s\nDauer: %s\n%s" % (sender,airtime,dur,info)
					self.filmliste.append((member+": "+decodeHtml(title),assetId,handlung,image,sendung))
		elif self.gF == "8": # Podcasts
			self['page'].setText('1 / 1')
			par = self.streamLink.split(",")
			image = par[1] # Geschmuggelte Image-URL
			treffer = re.findall('<item>.*?<title>(.*?)</ti.*?<description>(.*?)</de.*?<enclosure url="(.*?)".*?<dc:date>(.*?)</dc', data, re.S)
			if treffer:
				for (title,info,streamLink,airtime) in treffer:
					info = info.replace("\n"," ")
					info = decodeHtml(info)
					streamLink = streamLink.split("?")
					airtime = airtime.split("-")
					y = airtime[2]
					airtime = y[:2]+"."+airtime[1]+"."+airtime[0]+" "+y[3:-4]
					title = decodeHtml(title)
					if len(info) < 170:
						info = "\n"+info
					handlung = "Sender: Podcast\nClip-Datum: %s\nDauer: ---\n%s" % (airtime,info)
					self.filmliste.append((title,streamLink[0],handlung,image,title))
		elif int(self.gF) > 9 and self.gN != "Sendung" and self.gF !="13":	# ZDFneo, ZDFinfo, ZDF.kultur,3sat
				getPage(self.streamLink).addCallback(self.videoPre).addErrback(self.dataError)
		elif self.gF == "13":	# ZDFtivi
			treffer = re.findall('<ns3:video-teaser>.*?<ns3:headline>(.*?)</ns3:he.*?<ns3:image>(.*?)</ns3:im.*?<ns3:page>(.*?)</ns3:pa.*?<ns3:text>(.*?)</ns3:te.*?<ns3:duration>.*?T(.*?)</ns3:du', data, re.S)
			if treffer:
				for (name,image,url,inf,dur) in treffer:
					info = ""
					if inf != None:
						info = inf.replace("\n"," ")
						info = decodeHtml(info)
					url = "http://www.tivi.de%s" % url
					image = "http://www.tivi.de%s" % image
					stdP = dur.split("H")
					minP = stdP[1].split("M")
					secP = minP[1].split(".")
					std = stdP[0]
					min = minP[0]
					sec = secP[0]
					if int(std) < 10:
						std = "0"+std
					if int(min) < 10:
						min = "0"+min
					if int(sec) < 10:
						sec = "0"+sec
					dur = "%s:%s:%s" % (std,min,sec)
					if len(info) < 170:
						info = "\n"+info
					handlung = "Sender: ZDFtivi (ZDF)\nDauer: %s\n%s" % (dur,info)
					self.filmliste.append((decodeHtml(name),url,handlung,image,self.gN))
		else:
			treffer = re.findall('<type>video</type>.*?key="485x273">(.*?)</te.*?<title>(.*?)</ti.*?<detail>(.*?)</de.*?<assetId>(.*?)</as.*?<channel>(.*?)</ch.*?<length>(.*?)</le.*?<airtime>(.*?)</ai', data, re.S)
			if treffer:
				for (image,title,info,assetId,sender,dur,airtime) in treffer:
					info = info.replace("\n"," ")
					info = decodeHtml(info)
					if "000" in dur:
						dur = dur[0:8]
					send = re.findall('originChannelTitle>(.*?)</ori', data, re.S)
					for sendung in send:
						sendung = decodeHtml(sendung)
					if len(info) < 170:
						info = "\n"+info
					handlung = "Sender: %s\nClip-Datum: %s\nDauer: %s\n%s" % (sender,airtime,dur,info)
					self.filmliste.append((decodeHtml(title),assetId,handlung,image,sendung))
			else:
				self.filmliste.append(("Einschränkung der ZDF-Server...",None,None,None))
				self['handlung'].setText("")
				self['name'].setText(isWeg)
				CoverHelper(self['coverArt']).getCover("")
		if not (int(self.gF) > 9 and self.gN != "Sendung" and self.gF !="13"):
			# remove duplicates
			self.filmliste = list(set(self.filmliste))
			self.filmliste.sort(key=lambda t : t[0].lower())
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 3, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def videoPre(self, data):
		preScan = re.findall('<img src="/ZDFmediathek/contentblob/(.*?)/', data, re.S)
		if preScan:
			x = 0
			y = len(preScan)
			for r in preScan:
				x = x + 1
				url = "http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?ak=web&id=%s" % r
				getPage(url).addCallback(self.addData,x,y).addErrback(self.dataError)

	def addData(self, data, pos, count):
		treffer = re.findall('key="485x273">(.*?)</te.*?<title>(.*?)</ti.*?<detail>(.*?)</de.*?<assetId>(.*?)</as.*?<channel>(.*?)</ch.*?<length>(.*?)</le.*?<airtime>(.*?)</ai', data, re.S)
		for (image,title,info,assetId,sender,dur,airtime) in treffer:
			info = info.replace("\n"," ")
			info = decodeHtml(info)
			title = decodeHtml(title)
			if "000" in dur:
				dur = dur[0:8]
			send = re.findall('originChannelTitle>(.*?)</ori', data, re.S)
			for sendung in send:
				sendung = decodeHtml(sendung)
			if len(info) < 170:
				info = "\n"+info
			handlung = "Sender: %s\nClip-Datum: %s\nDauer: %s\n%s" % (sender,airtime,dur,info)
			self.filmliste.append((title,assetId,handlung,image,sendung))
		if pos == count:
			# remove duplicates
			self.filmliste = list(set(self.filmliste))
			self.filmliste.sort(key=lambda t : t[0].lower())
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 3, None, None, self.page, self.lastpage)
			self.showInfos()

	def showInfos(self):
		if self['liste'].getCurrent()[0][3] == None:
			streamPic = zdfPic
			CoverHelper(self['coverArt']).getCover(streamPic)
		else:
			streamPic = self['liste'].getCurrent()[0][3]
			if self.gF == "1":
				self['name'].setText("Suche ' "+suchCache+" '\nSendung / Thema\n' "+self['liste'].getCurrent()[0][4]+" '")
			else:
				self['name'].setText("Sendung / Thema\n' "+self['liste'].getCurrent()[0][4]+" '")
			self['handlung'].setText(self['liste'].getCurrent()[0][2])
			CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		self['name'].setText(_("Please wait..."))
		streamName = self['liste'].getCurrent()[0][0]
		if streamName == isWeg:
			self.page -= 1
			self.loadPage()
		if self.gF == "8":
			streamName = self['liste'].getCurrent()[0][0]
			streamLink = self['liste'].getCurrent()[0][1]
			playlist = []
			playlist.append((streamName, streamLink))
			self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='zdf')
		else:
			if self.gF == "13":
				url = self['liste'].getCurrent()[0][1]
			else:
				url = "%s/xmlservice/web/beitragsDetails?ak=web&id=%s" % (BASE_URL,self['liste'].getCurrent()[0][1])
			if url:
				getPage(url).addCallback(self.get_Http).addErrback(self.dataError)

	def get_Http(self, data):
		self.keyLocked = True
		streamName = self['liste'].getCurrent()[0][0]
		streamQ = re.findall('basetype="h264_aac_mp4_http.*?quality>veryhigh</.*?quality>.*?url>(http://[nrodl|rodl|tvdl].*?)</.*?url>', data, re.S)
		if streamQ:
			stream = streamQ[0]
		self.keyLocked = False
		if stream:
			playlist = []
			playlist.append((streamName, stream))
			self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='zdf')
		if self.gF == "1":
			self['name'].setText("Sendung / Thema ("+suchCache+")\n' "+self['liste'].getCurrent()[0][4]+" '")
		else:
			self['name'].setText("Sendung / Thema\n' "+self['liste'].getCurrent()[0][4]+" '")