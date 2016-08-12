# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def mailru(self, data, ck):
	print data
	print ck
	stream_url = None
	js_data = json.loads(data)
	best_quality = 0
	for video in js_data['videos']:
		if int(video['key'][:-1]) > best_quality:
			stream_url = video['url']
			best_quality = int(video['key'][:-1])
	if stream_url:
		config.mediaplayer.extraHeaders = NoSave(ConfigText(default=""))
		headersString = '|'.join([(key + ':' + value) for key, value in ck.iteritems()])
		config.mediaplayer.extraHeaders.setValue(headersString)
		stream_url = urllib.unquote(stream_url)
		print stream_url
		self._callback(stream_url)
	else:
		self.stream_not_found()