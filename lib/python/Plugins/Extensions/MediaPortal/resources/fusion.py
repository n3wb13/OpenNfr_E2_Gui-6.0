# -*- coding: utf-8 -*-

import uuid
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

fusionConfig = {
	'dmax' : {
		'url': 'http://m.app.dmax.de',
		'token': 'XoVA15ecuocTY5wBbxNImXVFbQd72epyxxVcH3ZVmOA.',
		'logo': 'http://www.dmax.de/wp-content/themes/dni_wp_theme_dmax_de/img/logo-trans.png'
		},
	'tlc' : {
		'url': 'http://m.app.tlc.de',
		'token': 'XoVA15ecuocTY5wBbxNImXVFbQd72epyxxVcH3ZVmOA.',
		'logo': 'http://www.tlc.de/wp-content/themes/dni_wp_theme_tlc_de/img/logo.png'
		}
	}

class Client:
	USER_AGENT = 'stagefright/1.2 (Linux;Android 4.4.2)'

	def __init__(self, config):
		self.Config = config

	def _getJson(self, data):
		print '_getJson:'
		return json.loads(data)

	def _createUrl(self, url_path):
		url = self.Config.get('url', '')
		if not url.endswith('/') and not url_path.startswith('/'):
			url = url+'/'
		url = url+url_path

		return url

	def getVideoStreams(self, episode_id):
		print 'getVideoStreams:'
		params = {
			'video_id': episode_id,
			'video_fields': 'name,renditions',
			'command': 'find_video_by_id',
			'token': self.Config.get('token', '')
			}

		url = 'https://api.brightcove.com/services/library'
		url = url + '?' + urllib.urlencode(params)
		d = twAgentGetPage(url, agent=self.USER_AGENT)
		d.addCallback(self._getJson)

		return d

	def getEpisodes(self, series_id):
		print 'getEpisodes:'
		url = self._createUrl('/free-to-air/android/genesis/series/'+series_id+'/episodes/')
		d = twAgentGetPage(url, agent=self.USER_AGENT)
		d.addCallback(self._getJson)

		return d

	def getLibrary(self):
		print 'getLibrary:'
		url = self._createUrl('/free-to-air/android/genesis/series/')
		d = twAgentGetPage(url, agent=self.USER_AGENT)
		d.addCallback(self._getJson)

		return d

	def getHighlights(self):
		print 'getHighlights:'
		url = self._createUrl('/free-to-air/android/genesis/targets/featured/')
		d = twAgentGetPage(url, agent=self.USER_AGENT)
		d.addCallback(self._getJson)

		return d