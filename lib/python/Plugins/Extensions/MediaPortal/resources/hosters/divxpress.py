# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def divxpress(self, data, link):
	p1 = re.search('type="hidden" name="op" value="(.*?)"', data)
	p2 = re.search('type="hidden" name="id" value="(.*?)"', data)
	p3 = re.search('type="hidden" name="rand" value="(.*?)"', data)
	p4 = re.search('type="hidden" name="referer" value="(.*?)"', data)
	p5 = re.search('type="hidden" name="method_free" value="(.*?)"', data)
	p6 = re.search('type="hidden" name="method_premium" value="(.*?)"', data)
	if p1 and p2 and p3 and p4 and p5 and p6:
		info = urlencode({'op': p1.group(1),
						'id': p2.group(1),
						'rand': p3.group(1),
						'referer': p4.group(1),
						'method_free': p5.group(1),
						'method_premium': p6.group(1),
						'down_direct': '1'})
		print info
		getPage(link, method='POST', postdata=info, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self.divxpressPostdata).addErrback(self.errorload)
	else:
		self.stream_not_found()

def divxpressPostdata(self, data):
	stream_url = re.search('<a href="(http://.*?)">Download the file</a>', data, re.I)
	if stream_url:
		self._callback(stream_url.group(1))
	else:
		self.stream_not_found()