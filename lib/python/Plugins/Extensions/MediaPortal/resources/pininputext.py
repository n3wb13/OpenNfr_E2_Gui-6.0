# -*- coding: utf-8 -*-
from imports import *
import mp_globals
from Screens.InputBox import PinInput, InputBox

class PinInputExt(PinInput, InputBox):

	def __init__(self, session, service = "", triesEntry = None, pinList = [], *args, **kwargs):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/PinInput.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/PinInput.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		InputBox.__init__(self, session = session, text="    ", maxSize=True, type=Input.PIN, *args, **kwargs)
		PinInput.__init__(self, session = session, service = service, triesEntry = triesEntry, pinList = pinList, *args, **kwargs)
		self["title"] = Label(kwargs.get('windowTitle', ''))

		self.onShow.append(self.__onShow)

	def __onShow(self):
		try:
			self._closeHelpWindow()
		except:
			pass