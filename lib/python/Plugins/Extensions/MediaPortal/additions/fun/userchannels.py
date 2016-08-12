# -*- coding: utf-8 -*-
from os.path import exists
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.additions.fun.youtube import YT_ListScreen

USER_Version = "USER-Channels v0.97"

USER_siteEncoding = 'utf-8'

class show_USER_Genre(MPScreen):

	def __init__(self, session):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"

		print path
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"green"	: self.keyGreen
		}, -1)


		self['title'] = Label(USER_Version)
		self['ContentTitle'] = Label("User Channels")
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label(_("Exit"))
		self['F2'] = Label("Load")

		self.user_path = config.mediaportal.watchlistpath.value + "mp_userchan.xml"
		self.show_help = config.mediaportal.show_userchan_help.value
		self.keyLocked = True
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		if not exists(self.user_path):
			self.getUserFile(fInit=True)

		if self.show_help:
			self.genreliste.append((0, "Mit dieser Erweiterung kannst Du deine Lieblings Youtubekanäle selber hinzufügen.", ""))
			self.genreliste.append((0, "Für jeden Kanal müssen nur zwei Einträge hinzugefügt werden:", ""))
			self.genreliste.append((0, "'<name> Kanal Bezeichnung </name>' und '<user> Besitzername </user>'", ""))
			self.genreliste.append((0, " ", ""))
			self.genreliste.append((0, "Mit der Taste 'Grün' wird die Datei:", ""))
			self.genreliste.append((0, "'"+self.user_path+"' geladen.", ""))
			self.genreliste.append((0, " ", ""))
			self.genreliste.append((0, "With this extension you can add your favorite Youtube channels themselves.", ""))
			self.genreliste.append((0, "For each channel, only two entries are added:", ""))
			self.genreliste.append((0, "'<name> channel name </name>' and '<user> owner name </ user>'", ""))
			self.genreliste.append((0, " ", ""))
			self.genreliste.append((0, "With the 'Green' button the user file:", ""))
			self.genreliste.append((0, "'"+self.user_path+"' is loaded.", ""))
			self.ml.setList(map(self.ChannelsListEntryCenter, self.genreliste))
		else:
			self.getUserFile()

	def getUserFile(self, fInit=False):
		fname = self.plugin_path + "/userfiles/userchan.xml"

		print "fname: ",fname
		try:
			if fInit:
				shutil.copyfile(fname, self.user_path)
				return

			fp = open(self.user_path)
			data = fp.read()
			fp.close()
		except IOError, e:
			print "File Error: ",e
			self.genreliste = []
			self.genreliste.append((0, str(e), ""))
			self.ml.setList(map(self.ChannelsListEntryCenter, self.genreliste))
		else:
			self.userData(data)

	def userData(self, data):
		list = re.findall('<name>(.*?)</name>.*?<user>(.*?)</user>', data, re.S)

		self.genreliste = []
		if list:
			i = 1
			for (name, user) in list:
				self.genreliste.append((i, name.strip(), '/'+user.strip()))
				i += 1

			self.genreliste.sort(key=lambda t : t[1].lower())
			self.keyLocked = False
		else:
			self.genreliste.append((0, "Keine User Channels gefunden !", ""))

		self.ml.setList(map(self.ChannelsListEntryLeft, self.genreliste))

	def keyGreen(self):
		self.getUserFile()

	def keyOK(self):
		if self.keyLocked:
			return

		genreID = self['liste'].getCurrent()[0][0]
		genre = self['liste'].getCurrent()[0][1]
		stvLink = self['liste'].getCurrent()[0][2]
		if stvLink == '/':
			return
		url = "http://gdata.youtube.com/feeds/api/users"+stvLink+"/uploads?"
		self.session.open(YT_ListScreen, url, genre, title=USER_Version)