# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
	
def filenuke(self, data):
	nextid = re.search('id="go-next"\s*href="(.*?)">', data)
	if nextid:
		spezialagent = 'Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/BuildID) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'
		link = "http://filenuke.com%s" % nextid.group(1)
		getPage(link, agent=spezialagent).addCallback(self.filenuke_data).addErrback(self.errorload)

def filenuke_data(self, data):
	stream_url = re.findall("var\slnk.*?=\s*'(.*?)'", data, re.S)
	if stream_url:
		mp_globals.player_agent = 'Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/BuildID) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'
		stream_url = stream_url[0]
		self._callback(stream_url)
	else:
		self.stream_not_found()