# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def google(self, data):
	stream_url = re.search('"fmt_stream_map".*?\|(.*?)\|', data, re.S)
	if stream_url:
		self._callback(stream_url.group(1).replace("\u003d","=").replace("\u0026","&"))
	else:
		self.stream_not_found()