# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def zettahost(self, data):
	stream_url = None
	get_packedjava = re.findall('<div id="player_code".*?javascript.>(eval.function.*?)</script>', data, re.S)
	if get_packedjava and detect(get_packedjava[0]):
		sJavascript = get_packedjava[0]
		sUnpacked = unpack(sJavascript)
		if sUnpacked:
			stream_url = re.search('file:"(.*?)"', sUnpacked, re.S)
			if stream_url:
				print stream_url.group(1)
				self._callback(stream_url.group(1))
				return
			else:
				stream_url = re.search('type="video/divx"src="(.*?)"', sUnpacked, re.S)
				if stream_url:
					print stream_url.group(1)
					self._callback(stream_url.group(1))
					return
	self.stream_not_found()
