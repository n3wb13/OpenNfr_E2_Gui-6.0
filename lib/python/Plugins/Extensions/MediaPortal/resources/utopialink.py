# -*- coding: utf-8 -*-

import re
from twagenthelper import twAgentGetPage

class UtopiaLink(object):
	def getNTStream(self, country):
		if country == "nl":
			self.base_url = "utopiatv.nl"
		else:
			self.base_url = "utopya.com.tr"
		auth_url = 'https://token.%s/api/2/GetLongLivedAuthToken/?callback=&authToken=&_=' % self.base_url
		return twAgentGetPage(auth_url, timeout=10).addCallback(self.getNTAuth).addErrback(self.getNTAuth, True)

	def getNTAuth(self, jdata, err=False):
		try:
			auth_token = re.search('authToken":"(.*?)"', jdata).group(1)
			stream_url = 'https://token.%s/api/2/GetToken/?callback=&authToken=%s&streamKey=stream_live_1&platform=web&_=' % (self.base_url, auth_token)
		except:
			raise Exception('Cannot get utopia authToken!')
		else:
			return twAgentGetPage(stream_url, timeout=10).addCallback(self.getNTM3U8URL)

	def getNTM3U8URL(self, jdata):
		try:
			url = re.search('"url":"(.*?)"', jdata).group(1)
		except:
			raise Exception('Cannot get utopia stream url!')
		else:
			return url