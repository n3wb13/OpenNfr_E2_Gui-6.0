# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def streamin(self, data):
	final = None
	file = re.search('file:\s"(.*?)"', data)
	if file:
		final = file.group(1)
	if final:
		self._callback(final)
	else:
		self.stream_not_found()