# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def okru(self, data):
	print data
	stream_url = None
	stream_url = re.findall('name":".*?","url":"(.*?)"', data, re.S)
	if stream_url:
		print stream_url
		stream_url = stream_url[-1].replace('\u0026','&')
		print stream_url
		self._callback(stream_url)
	else:
		self.stream_not_found()