# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def vivo(self, data, url):
	p1 = re.search('type="hidden" name="hash".*?value="(.*?)"', data)
	p2 = re.search('type="hidden" name="timestamp".*?value="(.*?)"', data)
	if p1 and p2:
		if mp_globals.isDreamOS or not mp_globals.requests:
			post = urllib.urlencode({'hash': p1.group(1), 'timestamp': p2.group(1)})
			twAgentGetPage(url, method='POST', postdata=post, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vivoPostData).addErrback(self.errorload)
		else:
			post = {'hash': p1.group(1), 'timestamp': p2.group(1)}
			data = self.grabpage(url, method='POST', postdata=post)
			self.vivoPostData(data)
	else:
		self.stream_not_found()

def vivoPostData(self, data):
	stream_url = re.search('class="stream-content" data-url="(.*?)"', data)
	if stream_url:
		self._callback(stream_url.group(1))
	else:
		self.stream_not_found()