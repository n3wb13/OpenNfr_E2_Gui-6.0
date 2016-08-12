# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def trollvid(self, data):
	stream_url = re.findall('url:\s"(.*?)"', data)
	if stream_url:
		url = urllib.unquote(stream_url[-1])
		self._callback(url)
	else:
		self.stream_not_found()