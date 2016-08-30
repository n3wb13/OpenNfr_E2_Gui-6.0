# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2016
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding execution on hardware, you are permitted to execute this plugin on VU+ hardware
#  which is licensed by satco europe GmbH, if the VTi image is used on that hardware.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
#############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

class UrknallFilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Urknall, Weltall und das Leben")
		self['ContentTitle'] = Label("Videos:")
		self['name'] = Label("Video Auswahl")
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		url = "https://www.urknall-weltall-leben.de/videos"
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		movies = re.findall('class="itemContainer".*?<a\shref="(.*?)".*?<img\ssrc="(.*?)".*?catItemTitle">(.*?)</a>.*?catItemIntroText">(.*?)</div>.*?ampel.\.png">\s-\s(.*?)</span.*?Dauer.*?(\d+).*?</span>', data, re.S)
		if movies:
			self.filmliste = []
			for (url,image,title,descr,severity,length) in movies:
				image = 'https://www.urknall-weltall-leben.de' + image
				url = 'https://www.urknall-weltall-leben.de' + url
				title = decodeHtml(title).strip()
				descr = decodeHtml(descr).strip()
				self.filmliste.append((title,url,image,length,severity,descr))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		length = self['liste'].getCurrent()[0][3]
		severity = self['liste'].getCurrent()[0][4]
		descr = self['liste'].getCurrent()[0][5]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)
		self['handlung'].setText('Länge: %s min\nSchwierigkeit: %s\n\n%s' % (length,severity,descr))

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			self.keyLocked = True
			getPage(url).addCallback(self.getlink).addErrback(self.dataError)

	def getlink(self, data):
		parse = re.findall('www.youtube.com/(v|embed)/(.*?)\?.*?"', data, re.S)
		if parse:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(YoutubePlayer,[(title, parse[0][1], None)],playAll= False,showPlaylist=False,showCover=False)
		else:
			message = self.session.open(MessageBoxExt, _("This video is not available."), MessageBoxExt.TYPE_INFO, timeout=5)
		self.keyLocked = False