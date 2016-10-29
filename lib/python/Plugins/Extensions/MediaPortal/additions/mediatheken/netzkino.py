# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class netzKinoGenreScreen(MPScreen):

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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Netzkino.de")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(('Neu bei Netzkino', 'neu'))
		self.genreliste.append(('HD-Kino', 'hdkino'))
		self.genreliste.append(('Animekino', 'animekino'))
		self.genreliste.append(('Actionkino', 'actionkino'))
		self.genreliste.append(('Dramakino', 'dramakino'))
		self.genreliste.append(('Thrillerkino', 'thrillerkino'))
		self.genreliste.append(('Liebesfilmkino', 'liebesfilmkino'))
		self.genreliste.append(('Scifikino', 'scifikino'))
		self.genreliste.append(('Arthousekino', 'arthousekino'))
		self.genreliste.append(('Queerkino', 'queerkino'))
		self.genreliste.append(('Spaßkino', 'spasskino'))
		self.genreliste.append(('Asiakino', 'asiakino'))
		self.genreliste.append(('Horrorkino', 'horrorkino'))
		self.genreliste.append(('Kinderkino', 'kinderkino'))
		self.genreliste.append(('Prickelkino', 'prickelkino'))
		self.genreliste.append(('Kino ab 18', 'kinoab18'))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		genreID = self['liste'].getCurrent()[0][1]
		self.session.open(netzKinoFilmeScreen, genreID, Name)

class netzKinoFilmeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreID, Name):
		self.genreID = genreID
		self.Name = Name
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
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

		self['title'] = Label("Netzkino.de")
		self['ContentTitle'] = Label("Film Auswahl: %s" % self.Name)
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://api.netzkino.de.simplecache.net/capi-2.0a/categories/%s.json" % self.genreID
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('"posts"(.*)', data)
		Daten = re.findall('"id".*?title":"(.*?)".*?"featured_img_all":\["(.*?)".*?Streaming":\["(.*?)"', parse.group(1), re.S|re.I)
		if Daten:
			for (Title,Image,Stream) in Daten:
				Url = "http://pmd.netzkino-seite.netzkino.de/%s.mp4" % Stream
				self.filmliste.append((decodeHtml(Title),Image,Url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 2, 1, None, None, 1, 1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][1]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][2]
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Title, Link)], showPlaylist=False, ltype='netzkino')