# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.additions.fun.youtube import YT_ListScreen

GAME_Version = "GAME-Channels v0.93"

GAME_siteEncoding = 'utf-8'

class show_GAME_Genre(MPScreen):

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
			"ok"    : self.keyOK,
			"0"		: self.closeAll,
			"cancel": self.keyCancel
		}, -1)


		self['title'] = Label(GAME_Version)
		self['ContentTitle'] = Label("Game Channels")
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label(_("Exit"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		#self.genreliste.append((2,'', '/'))
		self.genreliste.append((1,'High definition GAMING!', '/JohnsGameChannel'))
		self.genreliste.append((2,'... weiß, wer der Babo ist!', '/THCsGameChannel'))
		self.genreliste.append((3,'Game Tube', '/GameTube'))
		self.genreliste.append((4,'Electronic Arts GmbH', '/ElectronicArtsDE'))
		self.genreliste.append((5,'Ubisoft', '/ubisoft'))
		self.genreliste.append((6,'PlayStation', '/PlayStation'))
		self.genreliste.append((7,'Game Star', '/GameStarDE'))
		self.genreliste.append((8,'Assassins Creed DE', '/AssassinsCreedDE'))
		self.genreliste.append((9,'XboxDE\'s channel', '/XboxDE'))
		self.genreliste.append((10,'Disney Deutschland', '/WaltDisneyStudiosDE'))
		self.genreliste.append((11,'GIGA', '/giga'))
		self.genreliste.append((12,'GronkhDE | Gronkh', '/Gronkh'))
		self.genreliste.append((13,'GronkhDE | Sarazar', '/SarazarLP'))
		self.genreliste.append((14,'RANDOM ENCOUNTER', '/thegeekmythology'))
		self.genreliste.append((15,'gameinside tv', '/gameinsideshow'))
		self.genreliste.append((16,'Comedy Gaming mit Pink Panter', '/WartimeDignity'))
		self.genreliste.append((17,'CommanderKrieger - Baff Disch', '/CommanderKrieger'))
		self.genreliste.append((18,'Danny Burnage - Darauf ein Snickers-Eis!', '/TheDannyBurnage'))
		self.genreliste.append((19,'m4xFPS - Keks mit ♥', '/m4xFPS'))
		self.genreliste.append((20,'Kanal von xTheSolution', '/xTheSolution'))
		self.genreliste.append((21,'TheDoctorKaboom', '/TheDoctorKaboom'))

		self.genreliste.sort(key=lambda t : t[1].lower())
		self.ml.setList(map(self.ChannelsListEntryCenter, self.genreliste))

	def keyOK(self):
		genreID = self['liste'].getCurrent()[0][0]
		genre = self['liste'].getCurrent()[0][1]
		stvLink = self['liste'].getCurrent()[0][2]
		url = "http://gdata.youtube.com/feeds/api/users"+stvLink+"/uploads?"
		self.session.open(YT_ListScreen, url, genre, title=GAME_Version)