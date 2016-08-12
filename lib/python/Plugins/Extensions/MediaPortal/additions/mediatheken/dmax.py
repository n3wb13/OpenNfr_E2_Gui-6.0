# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources import fusion

if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/TMDb/plugin.pyo'):
	from Plugins.Extensions.TMDb.plugin import *
	TMDbPresent = True
elif fileExists('/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo'):
	TMDbPresent = False
	IMDbPresent = True
	from Plugins.Extensions.IMDb.plugin import *
else:
	IMDbPresent = False
	TMDbPresent = False

DMAX_Version = " v0.93"

DMAX_siteEncoding = 'utf-8'


"""
Sondertastenbelegung:

Genre Auswahl:
	KeyCancel		: Menu Up / Exit
	KeyOK			: Menu Down / Select

Doku Auswahl:
	Bouquet +/-				: Seitenweise blättern in 1er Schritten Up/Down
	'1', '4', '7',
	'3', 6', '9'			: blättern in 2er, 5er, 10er Schritten Down/Up
	Rot/Blau				: Die Beschreibung Seitenweise scrollen

Stream Auswahl:
	Rot/Blau				: Die Beschreibung Seitenweise scrollen
"""

glob_portal_nm = None
glob_fusion_client = None
glob_portal_logo = None

class show_DMAX_Genre(MenuHelper):

	def __init__(self, session, fusion_cfg, portal_nm, genre_title='Auswahl', series_id=None, series_nm=None):
		if fusion_cfg:
			global glob_portal_nm
			global glob_fusion_client
			global glob_portal_logo
			glob_portal_nm = portal_nm
			glob_fusion_client = fusion.Client(fusion.fusionConfig[fusion_cfg])
			glob_portal_logo = fusion.fusionConfig[fusion_cfg]['logo']
		self.genre_title = genre_title
		self.series_id = series_id
		self.series_nm = series_nm

		MenuHelper.__init__(self, session, 0, None, None, "", self._defaultlistleft, skin_name='defaultListWideScreen.xml')

		self["dmax_actions"] = ActionMap(['MP_Actions'], {
			"blue" :  self.keyTxtPageDown,
			"yellow" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label(glob_portal_nm + DMAX_Version)
		self['ContentTitle'] = Label(self.genre_title)
		self['F3'] = Label('Text-')
		self['F4'] = Label('Text+')
		self.mh_On_setGenreStrTitle.append((self.showInfos,()))
		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_initMenu(self):
		self.d_print("mh_initMenu:")
		self.mh_menuListe.append((_('Please wait...'),None))
		self.ml.setList(map(self.mh_menuListentry, self.mh_menuListe))
		self.mh_parseCategorys(None)

	def mh_parseCategorys(self, data):
		print 'mh_parseCategorys:'
		menu = []
		if self.series_id and self.series_nm:
			d = glob_fusion_client.getEpisodes(self.series_id)
			d.addCallback(self.parseEpisodes, menu, 0, False)
			d.addCallback(self.mh_genMenu2)
			d.addErrback(self.mh_dataError)
		else:
			d = glob_fusion_client.getHighlights()
			d.addCallback(self.parseEpisodes, menu, (0, ('',glob_portal_logo,''), 'Highlights'), 1, sortList=False)
			d.addCallback(self.getSeriesData)
			d.addErrback(self.mh_dataError)

	def getSeriesData(self, menu):
		print 'getSeries'
		d = glob_fusion_client.getLibrary()
		d.addCallback(self.parseSeries, menu, (0, ('',glob_portal_logo,''), 'Serien'), 1)
		d.addCallback(self.mh_genMenu2)
		d.addErrback(self.mh_dataError)

	def parseSeries(self, jsonData, menu, me=None, mlev=0):
		print 'parseSeries:'
		series = jsonData.get('series', None)
		if series != None:
			list = self.getSeries(series)
			if list:
				if me: menu.append(me)
				for nm, id, thumb, infos in list:
					menu.append((mlev, (id, thumb, infos), nm))

		return menu

	def parseEpisodes(self, jsonData, menu, me=None, mlev=0, showSeriesTitle=True, sortList=False):
		print 'parseEpisodes:'
		episodes = jsonData.get('episodes', None)
		if episodes != None:
			list = self.getEpisodes(episodes, showSeriesTitle)
			if list:
				if sortList:
					list.sort(key=lambda x: x[0].lower())
				if me: menu.append(me)
				for nm, id, thumb, infos in list:
					menu.append((mlev, (id, thumb, infos), nm))

		return menu

	def getSeries(self, series):
		print 'getSeries:'
		def _sort_key(d):
			return d.get('series-title', "").lower()

		series_list = series.get('series-list', {})
		series_list = sorted(series_list, key=_sort_key, reverse=False)
		list = []
		for series in series_list:
			name = series.get('series-title', None)
			id = series.get('series-id', None)

			if name != None and id != None:
				thumbnail = series.get('series-cloudinary-image', None)
				if thumbnail!=None:
					thumbnail =  'http://res.cloudinary.com/db79cecgq/image/upload/c_fill,g_faces,h_270,w_480/'+thumbnail

				infos = series.get('series-long-description', "")

				list.append((name.encode('utf-8'), str(id), str(thumbnail), infos.encode('utf-8')))

		return list

	def getEpisodes(self, episodes, showSeriesTitle=True):
		print 'getEpisodes:'
		episodes_list = episodes.get('episodes-list', {})
		list=[]
		for episode in episodes_list:
			id = episode.get('episode-additional-info', None)
			if id != None:
				id = id.get('episode-brightcove-id', None)

			if id != None:
				title = episode.get('episode-title', "")
				subtitle = episode.get('episode-subtitle', "")
				if showSeriesTitle:
					name = title
					if len(subtitle):
						name += " - " + subtitle
				else:
					if len(subtitle):
						name = subtitle
					else:
						name = title

				thumbnail = episode.get('episode-cloudinary-image', None)
				if thumbnail != None:
					thumbnail =  'http://res.cloudinary.com/db79cecgq/image/upload/c_fill,g_faces,h_270,w_480/'+thumbnail

				infos = episode.get('episode-long-description', "")

				list.append((name.encode('utf-8'), str(id), str(thumbnail), infos.encode('utf-8')))

		return list

	def mh_callGenreListScreen(self):
		id = self.mh_genreUrl[self.mh_menuLevel][0]
		if 'Highlights' in self.mh_genreTitle or self.series_id:
			self.play(self['liste'].getCurrent()[0][0], id)
		else:
			self.session.open(show_DMAX_Genre, None, None, 'Episoden:' + self['liste'].getCurrent()[0][0], id, self['liste'].getCurrent()[0][0])

	def play(self, title, episode_id):
		print 'play:',episode_id
		d = glob_fusion_client.getVideoStreams(episode_id)
		d.addCallback(self.playBestVideoUrl, title)
		d.addCallback(self.mh_dataError)

	def showInfos(self):
		infos = self.mh_genreUrl[self.mh_menuLevel]
		if len(infos) == 3:
			self['handlung'].setText(self.mh_genreUrl[self.mh_menuLevel][2])
			ImageUrl = self.mh_genreUrl[self.mh_menuLevel][1]
			CoverHelper(self['coverArt']).getCover(ImageUrl)

	def _getVideoResolution(self):
		videoPrio = int(config.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			resolution=1280
		elif videoPrio == 1:
			resolution=720
		else:
			resolution=480

		return resolution

	def playBestVideoUrl(self, jsonData, title):
		url = None
		resolution = self._getVideoResolution()
		last_resolution=0
		for stream in jsonData.get('renditions', []):
			test_resolution = stream.get('frameWidth', 0)
			if test_resolution >= last_resolution and test_resolution <= resolution:
				last_resolution = test_resolution
				url = stream.get('url', None)

		if url:
			self.session.open(SimplePlayer, [(title, str(url))], cover=False, showPlaylist=False, ltype='dmax.de', useResume=False)
		else:
			message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)