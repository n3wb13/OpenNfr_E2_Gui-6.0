# -*- coding: utf-8 -*-
from imports import *
from debuglog import printlog as printl
from messageboxext import MessageBoxExt
import mechanize

class CannaLink:
	def __init__(self, session):
		print "CannaLink:"
		self.session = session
		self._errback = None
		self._callback = None

	def getLink(self, cb_play, cb_err, sc_title, sc_artist, sc_album, url, imgurl):
		self._errback = cb_err
		self._callback = cb_play

		stream_url = self.getDLurl(url)
		if stream_url:
			cb_play(sc_title, stream_url, album=sc_album, artist=sc_artist, imgurl=imgurl)
		else:
			cb_err('stream_url not found!')

	def getDLurl(self, url):
		try:
			content = self.getUrl(url)
			match = re.findall('flashvars.playlist = \'(.*?)\';', content)
			if match:
				for url in match:
					url = 'http://ua.canna.to/canna/'+url
					content = self.getUrl(url)
					match = re.findall('<location>(.*?)</location>', content)
					if match:
						for url in match:
							url = 'http://ua.canna.to/canna/'+url
							req = mechanize.Request('http://ua.canna.to/canna/single.php')
							response = mechanize.urlopen(req)
							req = mechanize.Request(url)
							req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
							response = mechanize.urlopen(req)
							response.close()
							code=response.info().getheader('Content-Location')
							url='http://ua.canna.to/canna/avzt/'+code
							return url

		except urllib2.HTTPError, error:
			printl(error,self,"E")
			message = self.session.open(MessageBoxExt, ("Fehler: %s" % error), MessageBoxExt.TYPE_INFO, timeout=3)
			return False

		except urllib2.URLError, error:
			printl(error.reason,self,"E")
			message = self.session.open(MessageBoxExt, ("Fehler: %s" % error), MessageBoxExt.TYPE_INFO, timeout=3)
			return False

	def getUrl(self,url):
		req = mechanize.Request(url)
		req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = mechanize.urlopen(req)
		link = response.read()
		response.close()
		return link