# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def sharesix(self, data):
	if re.search('type="video/divx', data):
		stream_url = re.findall('type="video/divx"src="(.*?)"', data)
		if stream_url:
			print stream_url[0].replace('0://','http://')
			self._callback(stream_url[0].replace('0://','http://'))
			return
	elif re.search("file", data):
		stream_url = re.findall("var lnk1 = '(.*?)'", data)
		if stream_url:
			url = stream_url[0]
			print url
			self._callback(url)
			return
	self.stream_not_found()