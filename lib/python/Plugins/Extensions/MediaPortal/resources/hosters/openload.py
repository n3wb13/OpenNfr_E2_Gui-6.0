# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt
import cStringIO, base64

def openload(self, data):
	openloadNumbers = "https://openload.co/assets/js/obfuscator/n.js"
	twAgentGetPage(openloadNumbers, agent=None, headers=std_headers).addCallback(self.openloadData, data).addErrback(self.errorload)
	
def openloadData(self, openloadNumbers, data):
	openimg = re.search('src=\"data:image/png;base64,([A-Za-z0-9+/=]+?)\"', data, re.S)
	if openimg:
		opensign = re.search("window.signatureNumbers='([a-z]+?)'",openloadNumbers, re.S)
		if opensign:
			try:
				import Image
				opensign = opensign.group(1)
				imgdata = base64.b64decode(openimg.group(1))
				img = Image.open(cStringIO.StringIO(imgdata))
				width, height = img.size
			except:
				message = self.session.open(MessageBoxExt, _("Error module Image"), MessageBoxExt.TYPE_INFO, timeout=5)
				return

			output = ''
			for y in range(0,height):
				for x in range(0,width):
					r, g, b = img.getpixel((x, y))
					if r==0 and g == 0 and b == 0:
						break
					else:
						output += str(unichr(r))
						output += str(unichr(g))
						output += str(unichr(b))
			ImgStrLength = len(output)/200
			ImgStr = [[0 for x in range(ImgStrLength)] for y in range(10)]
			SigStrLength = len(opensign)/260
			SigStr = [[0 for x in range(SigStrLength)] for y in range(10)]

			for i in range(10):
				for j in range(ImgStrLength):
					begin = i*ImgStrLength*20+j*20
					ImgStr[i][j] = output[ begin : begin + 20]
				for j in range(SigStrLength):
					begin = i*SigStrLength*26+j*26
					SigStr[i][j] = opensign[begin : begin + 26]

			Parts = []
			Str = ''
			for i in [2, 3, 5, 7]:
				Str = ''
				Sum = float(99)
				for j in range(len(SigStr[i])):
					for ChrIdx in range(len(ImgStr[i][j])):
						if Sum > float(122):
							Sum = float(98)
						Chr = unichr(int(math.floor(Sum)))
						if SigStr[i][j][ChrIdx] == Chr and j >= len(Str):
							Sum += float(2.5);
							Str += ImgStr[i][j][ChrIdx];
				Parts.append(Str.replace(",", ""));
			url = 'https://openload.co/stream/' + Parts[3] + '~' + Parts[1] + '~' + Parts[2] + '~' + Parts[0] + '?mime=true'
			self.tw_agent_hlp = TwAgentHelper()
			self.tw_agent_hlp.getRedirectedUrl(url).addCallback(self.openloadRedirect).addErrback(self.errorload)
			return
	self.stream_not_found()

def openloadRedirect(self, data):
	mp_globals.player_agent = std_headers['User-Agent']
	if data:
		self._callback(str(data))
	else:
		self.stream_not_found()