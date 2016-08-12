# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def vidxden(self, data, link):
	p1 = re.search('type="hidden" name="op" value="(.*?)"', data)
	p2 = re.search('type="hidden" name="file_code" value="(.*?)"', data)
	p3 = re.search('type="hidden" name="embed_width" value="(.*?)"', data)
	p4 = re.search('type="hidden" name="embed_height" value="(.*?)"', data)
	p6 = re.search('type="hidden" name="referer" value="(.*?)"', data)
	if p1 and p2 and p3 and p4 and p6:
		info = urlencode({'op': p1.group(1),
						'file_code': p2.group(1),
						'embed_width': p3.group(1),
						'embed_height': p4.group(1),
						'pass': '1',
						'referer': p6.group(1)})
	getPage(link, method='POST', postdata=info, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self.vidxdenPostdata).addErrback(self.errorload)

def vidxdenPostdata(self, data):
	get_packedjava = re.findall("<script type=.text.javascript.>(eval.function.*?)</script>", data, re.S)
	if get_packedjava and detect(get_packedjava[0]):
		sJavascript = get_packedjava[0]
		sUnpacked = unpack(sJavascript)
		if sUnpacked:
			print "sUnpacked found", sUnpacked
			stream_url = re.search('"file","(.*?)"', sUnpacked)
			if stream_url:
				self._callback(stream_url.group(1))
				return
			else:
				stream_url = re.search('type="video/divx"src="(.*?)"', sUnpacked)
				if stream_url:
					self._callback(stream_url.group(1))
					return
	self.stream_not_found()