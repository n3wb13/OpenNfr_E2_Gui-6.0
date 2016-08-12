# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt

ck = {}
timeouttime = 15

def cloudyvideosEmbed(self, data, url):
	dataPost = {}
	r = re.findall('input type="hidden".*?name="(.*?)".*?value="(.*?)"', data, re.S)
	if r:
		for name, value in r:
			dataPost[name] = value
		getPage(url, method='POST', postdata=urlencode(dataPost), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.cloudyvideos_postDataEmbed).addErrback(self.errorload)
	else:
		self.stream_not_found()
		
def cloudyvideos_postDataEmbed(self, data):
	stream_url = re.search("file: '(.*?)'", data, re.I)
	if stream_url:
		self._callback(stream_url.group(1))
	else:
		self.stream_not_found()

def cloudyvideos(self, data, url):
	dataPost = {}
	r = re.findall('input type="hidden".*?name="(.*?)".*?value="(.*?)"', data, re.S)
	if r:
		for name, value in r:
			dataPost[name] = value
		reactor.callLater(3, self.cloudyvideosGetPage, url, timeout=timeouttime, method='POST', cookies=ck, postdata=urlencode(dataPost), headers={'Content-Type':'application/x-www-form-urlencoded'})
		message = self.session.open(MessageBoxExt, _("Stream starts in 3 sec."), MessageBoxExt.TYPE_INFO, timeout=3)
	else:
		self.stream_not_found()

def cloudyvideosGetPage(self, *args, **kwargs):
	getPage(*args, **kwargs).addCallback(self.cloudyvideos_postData).addErrback(self.errorload)

def cloudyvideos_postData(self, data):
	stream_url = re.search('<a href="(.*?\.[mkv|avi|flv|mp4]+)"><input type="submit"', data, re.I)
	if stream_url:
		self._callback(stream_url.group(1))
	else:
		self.stream_not_found()