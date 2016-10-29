# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def nowvideo(self, data):
	print "post",
	print data
	stream_url = re.findall('<source src="(.*?)" type=\'video/mp4\'>', data)
	if stream_url:
		self._callback(stream_url[0])
	else:
		self.stream_not_found()