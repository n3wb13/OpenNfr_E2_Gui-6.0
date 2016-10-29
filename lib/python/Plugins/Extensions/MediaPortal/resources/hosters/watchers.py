# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def watchers(self, data):
	get_packedjava = re.findall("<script type=.text.javascript.>(eval.function.*?)</script>", data, re.S)
	if get_packedjava:
		sJavascript = get_packedjava[0].replace('eval (function','eval(function').replace("\'","'").replace("\n","")
		sUnpacked = unpack(sJavascript)
		if sUnpacked:
			stream_url = re.findall('file:"(.*?)"', sUnpacked)
			if stream_url:
				self._callback(stream_url[1])
				return
	self.stream_not_found()