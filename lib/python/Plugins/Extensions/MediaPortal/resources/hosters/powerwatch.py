# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt

ck = {}
timeouttime = 15

def powerwatch(self, data, url):
	dataPost = {}
	r = re.findall('input type="hidden".*?name="(.*?)".*?value="(.*?)"', data, re.S)
	if r:
		for name, value in r:
			dataPost[name] = value
		reactor.callLater(5, self.powerwatchGetPage, url, timeout=timeouttime, method='POST', cookies=ck, postdata=urlencode(dataPost), headers={'Content-Type':'application/x-www-form-urlencoded'})
		message = self.session.open(MessageBoxExt, _("Stream starts in 5 sec."), MessageBoxExt.TYPE_INFO, timeout=3)
	else:
		self.stream_not_found()

def powerwatchGetPage(self, *args, **kwargs):
	getPage(*args, **kwargs).addCallback(self.powerwatch_postData).addErrback(self.errorload)

def powerwatch_postData(self, data):
	stream_url = re.search('file:"(.*?\.[mkv|avi|flv|mp4]+)"', data, re.I)
	if stream_url:
		self._callback(stream_url.group(1))
	else:
		self.stream_not_found()