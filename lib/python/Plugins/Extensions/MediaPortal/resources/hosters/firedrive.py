# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def firedrive(self, data, url):
	valkey = re.findall('name="confirm"\svalue="(.*?)"', data)
	if valkey:
		postdata = {'confirm': valkey[0]}
		getPage(url, method='POST', postdata=urlencode(postdata), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.firedriveData).addErrback(self.errorload)
	else:
		self.stream_not_found()

def firedriveData(self, data):
	stream_url = re.findall("file:.*?'(.*?)'", data, re.S)
	if stream_url and stream_url[-1] != '':
		self._callback(stream_url[-1])
		return
	stream_url = re.findall('"ad_button"\shref="(.*?)"', data, re.S)
	if stream_url:
		self._callback(stream_url[0])
		return
	else:
		self.stream_not_found()