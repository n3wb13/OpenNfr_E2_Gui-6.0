# -*- coding: utf-8 -*-
import base64
import re
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def zstream(self, data):
	stream_url = re.findall('file:"(.*?)"', data)
	if stream_url:
		self._callback(stream_url[0])
	else:
		self.stream_not_found()