# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt

def flashx(self, data, id):
	p1 = re.search('type="hidden" name="op" value="(.+?)"', data)
	p3 = re.search('type="hidden" name="id" value="(.+?)"', data)
	p4 = re.search('type="hidden" name="fname" value="(.+?)"', data)
	p6 = re.search('type="hidden" name="hash" value="(.+?)"', data)
	if p1 and p3 and p4 and p6:
		info = urlencode({'op': p1.group(1),
						'usr_login': '',
						'id': p3.group(1),
						'fname': p4.group(1),
						'referer':  '',
						'hash': p6.group(1),
						'imhuman': 'Proceed+to+video'})
		url = re.findall('src="(http://www.flashx.tv/code.js[^"]+)"', data)
		if url:
			twAgentGetPage(url[0], agent=None, headers=std_headers).addCallback(self.flashxCheckUrl, id, info).addErrback(self.errorload)
			return
	self.stream_not_found()

def flashxCheckUrl(self, data, id, info):
	link = 'http://www.flashx.tv/dl?%s' % id
	reactor.callLater(6, self.flashxCalllater, link, method='POST', postdata=info, agent=std_headers['User-Agent'], headers={'Content-Type': 'application/x-www-form-urlencoded'})
	message = self.session.open(MessageBoxExt, _("Stream starts in 6 sec."), MessageBoxExt.TYPE_INFO, timeout=6)

def flashxCalllater(self, *args, **kwargs):
	twAgentGetPage(*args, **kwargs).addCallback(self.flashxdata).addErrback(self.errorload)

def flashxdata(self, data):
	get_packedjava = re.findall("<script type=.text.javascript.>(eval.function.*?)</script>", data, re.S)
	if get_packedjava:
		sJavascript = get_packedjava[0]
		sUnpacked = unpack(sJavascript)
		if sUnpacked:
			best = 0
			links = re.findall('file:"(http.*?)",label:"(\d+)', sUnpacked, re.S)
			if links:
				for stream in links:
					if stream[1] > best:
						best = stream[1]
						bestlink = stream[0]
				if bestlink:
					self._callback(bestlink)
					return
			else:
				links = re.findall('file:"(http.*?)",label:"(Low|Middle|High)"', sUnpacked, re.S|re.I)
				if links:
					res = ['high', 'middle', 'low']
					for best in res:
						for url, qua in links:
							if best == qua.lower():
								self._callback(url)
								return
	self.stream_not_found()