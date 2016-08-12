# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt

def vodlocker(self, data, url):
	dataPost = {}
	r = re.findall('input type="hidden".*?name="(.*?)".*?value="(.*?)"', data, re.S)
	if r:
		for name, value in r:
			dataPost[name] = value
		dataPost.update({'imhuman':'Proceed to video'})
		reactor.callLater(2, self.vodlockerGetPage, url, method='POST', postdata=urlencode(dataPost), headers={'Content-Type':'application/x-www-form-urlencoded'})
		message = self.session.open(MessageBoxExt, _("Stream starts in 2 sec."), MessageBoxExt.TYPE_INFO, timeout=2)
	else:
		stream_url = re.findall('setup\(\{\s*file:\s*[\'|"](.*?)[\'|"]', data, re.S)
		if stream_url:
			self._callback(stream_url[0])
		else:
			self.stream_not_found()

def vodlockerGetPage(self, *args, **kwargs):
	getPage(*args, **kwargs).addCallback(self.vodlockerData).addErrback(self.errorload)

def vodlockerData(self, data):
	stream_url = re.search('file:\s"(http://.*?)"', data)
	if stream_url:
		self._callback(stream_url.group(1))
	else:
		self.stream_not_found()