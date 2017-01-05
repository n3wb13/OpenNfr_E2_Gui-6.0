# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2017
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
###############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

CONFIG = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/additions/additions.xml"

class toSearchForPorn(MPScreen, SearchHelper):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self.skin = self.skin.replace('</screen>', '')
		path = "%s/%s/search_widgets.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/search_widgets.xml"
		with open(path, "r") as f:
			self.skin += f.read()
			f.close()
		self.skin += '</screen>'

		MPScreen.__init__(self, session)
		SearchHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyRed,
			"green" : self.keyGreen,
			"yellow" : self.keyYellow
		}, -1)

		self['title'] = Label("2Search4Porn")
		self['name'] = Label("Your Search Requests")
		self['ContentTitle'] = Label("Annoyed, typing in your search-words for each Porn-Site again and again?")

		self['F1'] = Label(_("Delete"))
		self['F2'] = Label(_("Add"))
		self['F3'] = Label(_("Edit"))
		self.keyLocked = True
		self.suchString = ''

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.Searches)

	def goToLetter(self, num):
		self.keyNumberGlobal(num, self.genreliste)
		self.showSearchkey(num)

	def Searches(self):
		self.genreliste = []
		self['liste'] = self.ml
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_2s4p"):
			open(config.mediaportal.watchlistpath.value+"mp_2s4p","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_2s4p"):
			fobj = open(config.mediaportal.watchlistpath.value+"mp_2s4p","r")
			for line in fobj:
				self.genreliste.append((line, None))
			fobj.close()
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False

	def SearchAdd(self):
		suchString = ""
		self.session.openWithCallback(self.SearchAdd1, VirtualKeyBoardExt, title = (_("Enter Search")), text = suchString, is_dialog=True)

	def SearchAdd1(self, suchString):
		if suchString is not None and suchString != "":
			self.genreliste.append((suchString,None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def SearchEdit(self):
		if len(self.genreliste) > 0:
			suchString = self['liste'].getCurrent()[0][0].rstrip()
			self.session.openWithCallback(self.SearchEdit1, VirtualKeyBoardExt, title = (_("Enter Search")), text = suchString, is_dialog=True)

	def SearchEdit1(self, suchString):
		if suchString is not None and suchString != "":
			pos = self['liste'].getSelectedIndex()
			self.genreliste.pop(pos)
			self.genreliste.insert(pos,(suchString,None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def SearchCallback(self, suchString):
		if suchString is not None and suchString != "":
			self.session.open(toSearchForPornBrowse,suchString)

	def keyOK(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			self.SearchCallback(self['liste'].getCurrent()[0][0].rstrip())

	def keyRed(self):
		if self.keyLocked:
			return
		if len(self.genreliste) > 0:
			self.genreliste.pop(self['liste'].getSelectedIndex())
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyGreen(self):
		if self.keyLocked:
			return
		self.SearchAdd()

	def keyYellow(self):
		if self.keyLocked:
			return
		self.SearchEdit()

	def keyCancel(self):
		if self.keyLocked:
			return
		self.genreliste.sort(key=lambda t : t[0].lower())
		fobj_out = open(config.mediaportal.watchlistpath.value+"mp_2s4p","w")
		x = len(self.genreliste)
		if x > 0:
			for c in range(x):
				writeback = self.genreliste[c][0].rstrip()+"\n"
				fobj_out.write(writeback)
			fobj_out.close()
		else:
			os.remove(config.mediaportal.watchlistpath.value+"mp_2s4p")
		self.close()

class toSearchForPornBrowse(MPScreen):

	def __init__(self, session, suchString):
		self.suchString = suchString
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("2Search4Porn")
		self['ContentTitle'] = Label("Select Site")
		self['name'] = Label(_("Selection:"))
		self.keyLocked = True
		self.pornscreen = None
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadsites)

	def loadsites(self):
		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					if x.get("confcat") == "porn" and x.get("search") == "1":
						gz = x.get("gz")
						if not config.mediaportal.showgrauzone.value and gz == "1":
							pass
						else:
							mod = eval("config.mediaportal." + x.get("confopt") + ".value")
							if mod:
								exec("self.genreliste.append((\""+x.get("name").replace("&amp;","&")+"\", None))")

		self.genreliste.sort(key=lambda t : t[0].lower())
		self.keyLocked = False
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		if self.keyLocked:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		self.suchString = self.suchString.rstrip()

		conf = xml.etree.cElementTree.parse("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/additions/additions.xml")
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					if x.get("confcat") == "porn" and x.get("search") == "1":
							if auswahl == x.get("name").replace("&amp;","&"):
								modfile = x.get("modfile")
								modfile = "Plugins.Extensions.MediaPortal.additions.%s.%s" % (modfile.split(".")[0], modfile.split(".")[1])
								exec("from "+modfile+" import *")
								exec("self.suchString = self.suchString.replace(\" \",\""+x.get("delim")+"\")")
								exec("Name = \"2Search4Porn - %s\" % (self.suchString)")
								exec("Link = \""+x.get("searchurl").replace("&amp;","&")+"\" % (self.suchString)")
								print "Name: "+ Name
								print "Link: "+ Link
								exec("self.session.open("+x.get("searchscreen")+", Link, Name"+x.get("searchparam").replace("&quot;","\"")+")")