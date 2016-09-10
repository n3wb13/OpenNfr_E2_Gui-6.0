# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def thevideo(self, data):
	token = re.findall("tkn='(.*?)'", data, re.S)
	stream_url = re.findall("file['|\"|\s|:]*['|\"](.*?)['|\"]\s*}", data)
	if token:
		url = "http://thevideo.me/jwv/" + token[0]
		if stream_url:
			twAgentGetPage(url, agent=None, headers=std_headers).addCallback(self.thevideotoken, stream_url[-1]).addErrback(self.errorload)
		else:
			self.stream_not_found()
	else:
		self.stream_not_found()

def thevideotoken(self, data, url):
	token = re.findall('jwConfig\|(.*?)\|', data, re.S)
	if token:
		if token[0] != "false":
			stream_url = url + "?direct=false&ua=1&vt=" + token[0]
			self._callback(stream_url)
		else:
			self.stream_not_found()		
	else:
		self.stream_not_found()