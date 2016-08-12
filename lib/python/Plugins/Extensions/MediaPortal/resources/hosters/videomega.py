# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def videomega(self, data):
	get_packedjava = re.findall("<script\stype=.text.javascript.>.*?(eval.function.*?)</script>", data, re.S)
	if get_packedjava and detect(get_packedjava[0]):
		try:
			sJavascript = re.search("(.*?,)(\d\d)(,\d\d.*?)$", get_packedjava[0], re.S)
			if sJavascript:
				sJavascript = "%s62%s" % (sJavascript.group(1), sJavascript.group(3))
				sUnpacked = unpack(sJavascript)
				if sUnpacked:
					stream_url = re.findall('["|\']src["|\'],["|\'](http.*?)["|\']\)', sUnpacked)
					if stream_url:
						self._callback(stream_url[0])
						return
					else:
						self.stream_not_found()
				else:
					self.stream_not_found()
		except:
			pass
	unescape = re.findall('unescape."(.*?)"', data, re.S)
	if len(unescape) == 3:
		javadata = urllib2.unquote(unescape[2])
		if javadata:
			stream_url = re.findall('file:"(http.*?)"', javadata, re.S)
			if stream_url:
				self._callback(stream_url[0])
			else:
				self.stream_not_found()
		else:
			self.stream_not_found()
	else:
		stream_url = re.findall('<source src="(.*?)" type="video/mp4"/>', data)
		if stream_url:
			self._callback(stream_url[0])
			return
		else:
			self.stream_not_found()