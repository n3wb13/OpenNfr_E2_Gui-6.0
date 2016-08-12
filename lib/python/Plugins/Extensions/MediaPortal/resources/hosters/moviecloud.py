# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def moviecloud(self, data):
	parse = re.search('jwPlayerContainer".*?file:\s+"(.*?)"', data, re.S)
	if parse:
		self._callback(parse.group(1))
	else:
		self.stream_not_found()