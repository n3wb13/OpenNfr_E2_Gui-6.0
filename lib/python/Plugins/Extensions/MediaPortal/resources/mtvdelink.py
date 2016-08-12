# -*- coding: utf-8 -*-
from imports import *
from twagenthelper import TwAgentHelper

class MTVdeLink:

	tw_agent_hlp = TwAgentHelper()

	def __init__(self, session):
		print "MTVdeLink:"
		self.session = session
		self._callback = None

	def getLink(self, cb_play, cb_err, title, artist, token, imgurl):
		self._callback = cb_play
		self._errback = cb_err
		self.title = title
		self.artist = artist
		self.imgurl = imgurl
		url = "http://media-utils.mtvnservices.com/services/MediaGenerator/mgid:arc:video:mtv.de:%s?accountOverride=esperanto.mtvi.com&acceptMethods=hls,phttp" % token
		getPage(url, timeout=15).addCallback(self._parseData).addErrback(cb_err)

	def _parseData(self, data):
		print "_parseData:"
		rtmplink = re.findall('<src>(.*?)</src>', data)
		if rtmplink:
			videourl = rtmplink[0].replace('&amp;','&')
		else:
			self._errback('MTVdeLink: Cannot get link!')
			videourl = None

		self._callback(self.title, videourl, imgurl=self.imgurl, artist=self.artist)