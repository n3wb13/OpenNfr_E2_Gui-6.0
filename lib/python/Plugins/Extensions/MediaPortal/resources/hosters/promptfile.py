# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def promptfile(self, data, url):
	if re.search('http://www.promptfile.com/file', data):
		self.promptfilePost(data)
	else:
		chash = re.findall('type="hidden".*?"chash".*?name\s*=\s*"(.*?)"\s+value="(.*?)"', data, re.S)
		if chash:
			calcit = re.search('onclick=\'(.*?);', data, re.S)
			if calcit:
				calcData = calcit.group(1).replace('$("#chash").val()', chash[0][1]).replace('$("#chash")', chash[0][0]).replace('"','')
				calcData = re.sub(r'val\((.*?)\)', r'\1' ,  calcData).split('.')
				if len(calcData) == 2:
					cval = calcData[1]
					while '+' in cval:
						cval = re.sub(r'(\w+)\+(\w+)', r'\1\2' , cval)
					dataPost = {calcData[0]: cval}
					twAgentGetPage(url, method='POST', postdata=urlencode(dataPost), agent=std_headers['User-Agent'], headers={'Accept':'*/*', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.promptfilePost).addErrback(self.errorload)
					return
		self.stream_not_found()

def promptfilePost(self, data):
	stream_url = re.findall('src:\s*"(.*?)"', data, re.S)
	if stream_url:
		self._callback(stream_url[0])
	else:
		self.stream_not_found()