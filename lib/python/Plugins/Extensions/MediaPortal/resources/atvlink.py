# -*- coding: utf-8 -*-

import re
from twagenthelper import twAgentGetPage
agent="Mozilla/5.0 (Windows NT 6.1; rv:40.0) Gecko/20100101 Firefox/40.0"

class ATVLink(object):
	def getATVStream(self, station):
		if station == "atv":
			self.url = 'http://www.atv.com.tr/webtv/secure?url=http://trkvz-live.ercdn.net/atvhd/atvhd.m3u8'
		elif station == "aspor":
			self.url = 'http://www.aspor.com.tr/webtv/secure?url=http://trkvz-live.ercdn.net/asporhd/asporhd.m3u8'
		elif station == "ahaber":
			self.url = 'http://www.ahaber.com.tr/webtv/secure?url=http://trkvz-live.ercdn.net/ahaberhd/ahaberhd.m3u8'
		elif station == "atvavrupa":
			self.url = 'http://www.atv.com.tr/webtv/secure?url=http://trkvz-live.ercdn.net/atvavrupa/atvavrupa.m3u8'
		elif station == "minikacocuk":
			self.url = 'http://www.minikacocuk.com.tr/webtv/secure?url=http://trkvz-live.ercdn.net/minikagococuk/minikagococuk.m3u8'
		elif station == "minikago":
			self.url = 'http://www.minikago.com.tr/webtv/secure?url=http://trkvz-live.ercdn.net/minikago/minikago.m3u8'
		return twAgentGetPage(self.url, timeout=10, agent=agent).addCallback(self.getATVAuthUrl).addErrback(self.getATVAuthUrl, True)

	def getATVAuthUrl(self, jdata, err=False):
		try:
			auth_url = re.search('url":"(.*?)"', jdata).group(1)
			print auth_url
			stream_url = auth_url.replace('\u0026','&')
			print stream_url
		except:
			raise Exception('Cannot get ATV authUrl!')
		else:
			return stream_url