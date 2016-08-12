# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def vidbull(self, data):
	stream_url = re.search('<source\s+src="(.*?)"', data)
	if stream_url:
		self._callback(stream_url.group(1))
	else:
		self.stream_not_found()