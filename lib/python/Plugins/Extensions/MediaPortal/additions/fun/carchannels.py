# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.additions.fun.youtube import YT_ListScreen

CAR_Version = "CARS & BIKES-Channels v0.93"

CAR_siteEncoding = 'utf-8'

class show_CAR_Genre(MPScreen):

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

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)


		self['title'] = Label(CAR_Version)
		self['ContentTitle'] = Label("Car Channels")
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label(_("Exit"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		#self.genreliste.append((2,'', '/'))
		self.genreliste.append((1,'Alfa Romeo Deutschland', '/AlfaRomeoDE'))
		self.genreliste.append((2,'Audi Deutschland', '/Audi'))
		self.genreliste.append((3,'BMW Deutschland', '/BMWDeutschland'))
		self.genreliste.append((4,'BMW Motorrad', '/bmwmotorrad'))
		self.genreliste.append((5,'CITROËN Deutschland', '/CitroenDeutschland'))
		self.genreliste.append((6,'Ducati Motor Official Channel', '/DucatiMotorHolding'))
		self.genreliste.append((7,'Fiat Deutschland', '/FiatDeutschland'))
		self.genreliste.append((8,'Ford Deutschland', '/fordindeutschland'))
		self.genreliste.append((9,'Harley-Davidson Europe', '/HarleyDavidsonEurope'))
		self.genreliste.append((10,'Honda Deutschland', '/HondaDeutschlandGmbH'))
		self.genreliste.append((11,'Kawasaki Motors Europe', '/Kawasakimotors'))
		self.genreliste.append((12,'Land Rover Deutschland', '/experiencegermany'))
		self.genreliste.append((13,'Mazda Deutschland', '/MazdaDeutschland'))
		self.genreliste.append((14,'Mercedes-Benz', '/mercedesbenz'))
		self.genreliste.append((15,'MITSUBISHI MOTORS Deutschland', '/MitsubishiMotorsDE'))
		self.genreliste.append((16,'Moto Guzzi', '/motoguzziofficial'))
		self.genreliste.append((17,'Nissan Deutschland', '/NissanDeutsch'))
		self.genreliste.append((18,'Porsche Channel', '/Porsche'))
		self.genreliste.append((19,'SEAT Deutschland', '/SEATde'))
		self.genreliste.append((20,'ŠKODA AUTO Deutschland', '/skodade'))
		self.genreliste.append((21,'WAYOFLIFE SUZUKI', '/GlobalSuzukiChannel'))
		self.genreliste.append((22,'Toyota Deutschland', '/toyota'))
		self.genreliste.append((23,'Official Triumph Motorcycles', '/OfficialTriumph'))
		self.genreliste.append((24,'Volkswagen', '/myvolkswagen'))
		self.genreliste.append((25,'Yamaha Motor Europe', '/YamahaMotorEurope'))
		self.genreliste.append((26,'AUTO BILD TV', '/Autobild'))
		self.genreliste.append((27,'autotouring-TV', '/autotouring'))
		self.genreliste.append((28,'ADAC e.V.', '/adac'))
		self.genreliste.append((29,'MOTORVISION BIKE', '/motorvisionbike'))
		self.genreliste.append((30,'www.MOTORRADonline.de', '/motorrad'))
		self.genreliste.append((31,'TOURENFAHRER', '/Tourenfahrer'))
		self.genreliste.append((32,'DEKRA Automobil GmbH', '/DEKRAAutomobil'))
		self.genreliste.append((33,'Motorvision', '/MOTORVISIONcom'))
		self.genreliste.append((34,'Auto Motor & Sport', '/automotorundsport'))
		self.genreliste.append((35,'1000PS Motorradvideos', '/1000ps'))
		self.genreliste.append((36,'Motorrad Online', '/motorrad'))
		self.genreliste.append((37,'DMAX MOTOR', '/DMAX'))

		self.genreliste.sort(key=lambda t : t[1].lower())
		self.ml.setList(map(self.ChannelsListEntryCenter, self.genreliste))

	def keyOK(self):
		genreID = self['liste'].getCurrent()[0][0]
		genre = self['liste'].getCurrent()[0][1]
		stvLink = self['liste'].getCurrent()[0][2]
		url = "http://gdata.youtube.com/feeds/api/users"+stvLink+"/uploads?"
		self.session.open(YT_ListScreen, url, genre, title=CAR_Version)