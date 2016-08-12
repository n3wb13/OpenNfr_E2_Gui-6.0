# -*- coding: utf-8 -*-

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.additions.fun.youtube import YT_ListScreen

MUSIC_Version = "MUSIC-Channels v1.00"

MUSIC_siteEncoding = 'utf-8'

class show_MUSIC_Genre(MPScreen):

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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(MUSIC_Version)
		self['ContentTitle'] = Label("Music Channels")
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label(_("Exit"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append((1,'Ultra Music', '/UltraRecords'))
		self.genreliste.append((2,'ArmadaMusic.TV', '/armadamusic'))
		self.genreliste.append((3,'YOU LOVE DANCE.TV', '/Planetpunkmusic'))
		self.genreliste.append((4,'Classical Music Only Channel', '/ClassicalMusicOnly'))
		#self.genreliste.append((5,'Music Channel Romania', '/1musicchannel'))
		self.genreliste.append((6,'50 Cent Music', '/50CentMusic'))
		self.genreliste.append((7,'GMC Schlager', '/BlueSilverstar'))
		self.genreliste.append((8,'Classical Music Channel / Klassische', '/BPanther'))
		self.genreliste.append((9,'EMI Music Germany', '/EMIMusicGermany'))
		self.genreliste.append((10,'Sony Music Germany', '/SMECatalogGermany'))
		self.genreliste.append((11,'Kanal von MyWorldCharts', '/MyWorldCharts'))
		self.genreliste.append((12,'CaptainCharts', '/CaptainCharts'))
		self.genreliste.append((13,'PowerCharts', '/PowerCharts'))
		self.genreliste.append((14,'Kontor.TV', '/kontor'))
		self.genreliste.append((15,'Scooter Official', '/scooter'))
		self.genreliste.append((16,'ATZEN MUSIK TV', '/atzenmusiktv'))
		self.genreliste.append((17,'BigCityBeats', '/HammerDontHurtEm'))
		self.genreliste.append((18,'The Best Of', '/alltimebestofmusic'))
		self.genreliste.append((19,'Tomorrowland', '/TomorrowlandChannel'))
		self.genreliste.append((20,'Electro House&Dance Music 2013', '/Ayonen1'))
		self.genreliste.append((21,'DrDoubleT', '/DrDoubleT'))
		self.genreliste.append((22,'►Techno, HandsUp & Dance◄', '/DJFlyBeatMusic'))
		self.genreliste.append((23,'Zooland Records', '/zoolandMusicGmbH'))
		self.genreliste.append((24,'Bazooka Records', '/bazookalabel'))
		self.genreliste.append((25,'Crystal Lake Music', '/CrystaLakeTV'))
		self.genreliste.append((26,'SKRILLEX', '/TheOfficialSkrillex'))
		self.genreliste.append((27,'AggroTV', '/aggroTV'))
		self.genreliste.append((28,'Bands & ART-Ellie Goulding', '/EllieGouldingEmpire'))
		self.genreliste.append((29,'Bands & ART-Psyche', '/thandewye'))
		self.genreliste.append((30,'Bands & ART-Joint Venture', '/srudlak'))
		self.genreliste.append((31,'Bands & ART-Madonna', '/madonna'))
		self.genreliste.append((32,'BB Sound Production', '/b0ssy007'))
		self.genreliste.append((33,'Chill-out,Lounge,Jazz,Electronic,Psy,Piano,Trance', '/aliasmike2002'))
		self.genreliste.append((34,'Gothic', '/AiratzuMusic'))
		self.genreliste.append((35,'Gothic', '/INM0R4L'))
		self.genreliste.append((36,'Gothic-Industrial Mix', '/noetek'))
		self.genreliste.append((37,'Wave & Gothic', '/MrBelorix'))
		self.genreliste.append((38,'Indie', '/curie78'))
		self.genreliste.append((39,'Indie', '/SoundIndieMusic'))
		self.genreliste.append((40,'Planetpunkmusic TV', '/Planetpunkmusic'))
		self.genreliste.append((41,'Selfmade Records', '/SelfmadeRecords'))
		self.genreliste.append((42,'UKF-DrumandBass', '/UKFDrumandBass'))
		self.genreliste.append((43,'UKF-Dubstep', '/UKFDubstep'))
		self.genreliste.append((44,'UKF-Music', '/UKFMusic'))
		self.genreliste.append((45,'UKF-Mixes', '/UKFMixes'))
		self.genreliste.append((46,'UKF-Live', '/UKFLive'))
		self.genreliste.append((47,'Smarty Music', '/smartymcfly'))
		self.genreliste.append((48,'MoMMusic Network', '/MrMoMMusic'))
		self.genreliste.append((49,'Schlager Affe', '/schlageraffe2011'))
		self.genreliste.append((50,'80sFlashbackVideos', '/80sFlashbackVideos'))
		self.genreliste.append((51,'Bee Gees', '/TheBeeGeesLive'))
#		self.genreliste.append((52,'elvis presley', '/vELVISv'))
		self.genreliste.append((52,'Elvis Presley', '/elvis'))
		self.genreliste.append((53,'Rock-Your-Body', '/RockYourBody2012'))
		self.genreliste.append((54,'Dj3P51LON', '/Dj3P51LON'))
		self.genreliste.append((55,'The Beatles Channel', '/TheBeatlesYears2'))
		self.genreliste.append((56,'HeadhunterzMedia', '/HeadhunterzMedia'))
		self.genreliste.append((57,'musicchannel888', '/musicchannel888'))
		self.genreliste.append((58,'GMC Volkstümlicher Schlager', '/gusbara'))
		self.genreliste.append((59,'GMC HQ Volkstümlicher Schlager', '/GMChq'))
		#self.genreliste.append((9,'', '/'))

		self.genreliste.sort(key=lambda t : t[1].lower())
		self.ml.setList(map(self.ChannelsListEntryLeft, self.genreliste))

	def keyOK(self):
		genreID = self['liste'].getCurrent()[0][0]
		genre = self['liste'].getCurrent()[0][1]
		stvLink = self['liste'].getCurrent()[0][2]
		url = "http://gdata.youtube.com/feeds/api/users"+stvLink+"/uploads?"
		self.session.open(YT_ListScreen, url, genre, title=MUSIC_Version)