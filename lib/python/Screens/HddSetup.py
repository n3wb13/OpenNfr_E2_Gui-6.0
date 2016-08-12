from enigma import *
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from Components.Button import Button
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Screens.HddPartitions import HddPartitions
from Screens.HddInfo import HddInfo
from Components.Disks import Disks
from Components.ExtraMessageBox import ExtraMessageBox
from Components.ExtraActionBox import ExtraActionBox
from Components.MountPoints import MountPoints

import os
import sys

def DiskEntry(model, size, removable):
	if removable:
		picture = LoadPixmap(cached = True, path = resolveFilename(SCOPE_CURRENT_SKIN, "/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/icons/diskusb.png"));
	else:
		picture = LoadPixmap(cached = True, path = resolveFilename(SCOPE_CURRENT_SKIN, "/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/icons/disk.png"));
		
	return (picture, model, size)
	
class HddSetup(Screen):

	skin = """
                   <screen name="HddSetup" position="center,115" size="900,530" title="HddSetup" flags="wfBorder">
                      <widget source="menu" render="Listbox" position="10,10" size="880,450" scrollbarMode="showOnDemand" transparent="1">
                         <convert type="TemplatedMultiContent">
				{"template": [
					MultiContentEntryPixmapAlphaTest(pos = (5, 0), size = (48, 48), png = 0),
					MultiContentEntryText(pos = (70, 3), size = (430, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),
					MultiContentEntryText(pos = (515, 3), size = (135, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 2),
					],
					"fonts": [gFont("Regular", 22)],
					"itemHeight": 50
				}
                        </convert>
                    </widget>
                   <ePixmap position="10,497" size="35,27" pixmap="skin_default/buttons/red.png" alphatest="blend" />
                   <ePixmap position="230,497" size="35,27" pixmap="skin_default/buttons/green.png" alphatest="blend" />
                   <ePixmap position="695,497" size="35,27" pixmap="skin_default/buttons/blue.png" alphatest="blend" />
                   <widget name="key_red" position="48,498" zPosition="2" size="150,22" valign="center" halign="center" font="Regular; 20" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
                   <widget name="key_green" position="273,499" zPosition="2" size="150,22" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" backgroundColor="foreground" />
                   <widget name="key_blue" position="736,499" zPosition="3" size="150,22" valign="center" halign="center" font="Regular; 21" transparent="1" backgroundColor="foreground" />
                   </screen>"""

	def __init__(self, session, args = 0):
		self.session = session
		
		Screen.__init__(self, session)
		self.disks = list ()
		
		self.mdisks = Disks()
		for disk in self.mdisks.disks:
			capacity = "%d MB" % (disk[1] / (1024 * 1024))
			self.disks.append(DiskEntry(disk[3], capacity, disk[2]))
		
		self["menu"] = List(self.disks)
		self["key_red"] = Button(_("Mounts"))
		self["key_green"] = Button(_("Info"))
		#self["key_yellow"] = Button(_("Initialize"))
		self["key_blue"] = Button(_("Exit"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"blue": self.quit,
		#	"yellow": self.yellow,
			"green": self.green,
			"red": self.red,
			"cancel": self.quit,
		}, -2)
	
	def isExt4Supported(self):
		return "ext4" in open("/proc/filesystems").read()
		
	def mkfs(self):
		self.formatted += 1
		return self.mdisks.mkfs(self.mdisks.disks[self.sindex][0], self.formatted, self.fsresult)
		
	def refresh(self):
		self.disks = list ()
		
		self.mdisks = Disks()
		for disk in self.mdisks.disks:
			capacity = "%d MB" % (disk[1] / (1024 * 1024))
			self.disks.append(DiskEntry(disk[3], capacity, disk[2]))
			
		self["menu"].setList(self.disks)
		
	def checkDefault(self):
		mp = MountPoints()
		mp.read()
		if not mp.exist("/hdd"):
			mp.add(self.mdisks.disks[self.sindex][0], 1, "/media/hdd")
			mp.write()
			mp.mount(self.mdisks.disks[self.sindex][0], 1, "/media/hdd")
			os.system("/bin/mkdir /media/hdd/movie")
			os.system("/bin/mkdir /media/hdd/music")
			os.system("/bin/mkdir /media/hdd/picture")
		
	def green(self):
		if len(self.mdisks.disks) > 0:
			self.sindex = self['menu'].getIndex()
			self.session.open(HddInfo, self.mdisks.disks[self.sindex][0])
		
	def red(self):
		if len(self.mdisks.disks) > 0:
			self.sindex = self['menu'].getIndex()
			if len(self.mdisks.disks[self.sindex][5]) == 0:
				self.session.open(MessageBox, _("You need to initialize your storage device first"), MessageBox.TYPE_ERROR)
			else:
				self.session.open(HddPartitions, self.mdisks.disks[self.sindex])
		
	def quit(self):
		self.close()
