# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.additions.fun.youtube import YT_ListScreen

HSC_Version = "HÖRSPIEL-Channels v0.94"

HSC_siteEncoding = 'utf-8'

class show_HSC_Genre(MPScreen):

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


		self['title'] = Label(HSC_Version)
		self['ContentTitle'] = Label("Hörspiel Channels")
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label(_("Exit"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		#self.genreliste.append((2,'', '/))
		self.genreliste.append((1,'Audible Hörbücher', '/audibletrailer'))
		self.genreliste.append((2,'audilust - Hörspiele und Hörbücher', '/audilust'))
		self.genreliste.append((3,'Björns Hörspiel-TV', '/BjoernsHoerspielTV'))
		self.genreliste.append((4,'Der Lauscher Treff', '/pokermen001'))
		self.genreliste.append((5,'Die guten alten Zeiten', '/EstrellasTube'))
		self.genreliste.append((6,'Edgar Allan Poe´s Kaminzimmer', '/EAPoeProductions'))
		self.genreliste.append((7,'felix auris', '/mercuriius'))
		self.genreliste.append((8,'FRUITY - SOUND - DISASTER', '/MrFruitylooper'))
		self.genreliste.append((9,'Für Jung & Alt!', '/Bussard79'))
		self.genreliste.append((10,'Hein Bloed', '/Heinbloedful'))
		self.genreliste.append((11,'Hörbücher, Hörspiele und mehr', '/BestSound1000'))
		self.genreliste.append((12,'Hörbücher2013', '/Hoerbuecher2013'))
		self.genreliste.append((13,'Hörspiele und Klassik', '/scyliorhinus'))
		self.genreliste.append((14,'Hörspielprojekt', '/Hoerspielprojekt'))
		self.genreliste.append((15,'KonzertfürFlügel', '/KonzertfuerFluegel'))
		self.genreliste.append((16,'LAUSCH - Phantastische Hörspiele', '/merlausch'))
		self.genreliste.append((17,'Lauschgoldladen', '/Lauschgoldladen'))
		self.genreliste.append((18,'Multipolizei2', '/Multipolizei2'))
		self.genreliste.append((19,'Multipolizei3', '/Multipolizei3'))
		self.genreliste.append((20,'Nostalgiekanal - Hörspielkiste', '/Hoerspielkiste'))
		self.genreliste.append((21,'Soundtales Productions', '/SoundtalesProduction'))
		self.ml.setList(map(self.ChannelsListEntryCenter, self.genreliste))

	def keyOK(self):
		genreID = self['liste'].getCurrent()[0][0]
		genre = self['liste'].getCurrent()[0][1]
		stvLink = self['liste'].getCurrent()[0][2]
		url = "http://gdata.youtube.com/feeds/api/users"+stvLink+"/uploads?"
		self.session.open(YT_ListScreen, url, genre, title=HSC_Version)