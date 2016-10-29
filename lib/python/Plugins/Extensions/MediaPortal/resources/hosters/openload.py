# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt

def openloadApi(self, data):
	if re.search('IP address not authorized', data):
		message = self.session.open(MessageBoxExt, _("IP address not authorized. Visit https://openload.co/pair"), MessageBoxExt.TYPE_ERROR)
	else:
		stream_url = re.findall('"url":"(.*?)"', data)
		if stream_url:
			self._callback(stream_url[0].replace('\\',''))
		else:
			self.stream_not_found()