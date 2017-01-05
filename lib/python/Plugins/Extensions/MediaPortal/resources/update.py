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
from imports import *
import mp_globals
from messageboxext import MessageBoxExt
from twagenthelper import twAgentGetPage
import random
gLogFile = None

class checkupdate:

	def __init__(self, session):
		self.session = session

	def checkforupdate(self):
		update_agent = getUserAgent()
		update_url = getUpdateUrl()
		twAgentGetPage(update_url, agent=update_agent, timeout=60).addCallback(self.gotUpdateInfo).addErrback(self.gotError)

	def gotError(self, error=""):
		printl(error,self,"E")
		return

	def gotUpdateInfo(self, html):
		if re.search(".*?<html", html):
			return
		self.html = html
		tmp_infolines = html.splitlines()
		remoteversion_ipk = re.sub('\D', '', tmp_infolines[0])
		remoteversion_deb = re.sub('\D', '', tmp_infolines[2])
		try:
			mirrors = self.updateurl = tmp_infolines[5].split(';')
			mirror_rand = random.choice(mirrors)
			printl('Random update mirror selected: %s' % mirror_rand,self,'A')
		except:
			mirror_rand = None
		if mp_globals.isDreamOS:
			self.updateurl = tmp_infolines[3]
			remoteversion = remoteversion_deb
		else:
			self.updateurl = tmp_infolines[1]
			remoteversion = remoteversion_ipk
		printl('Found update url: %s' % self.updateurl,self,'A')
		if mirror_rand:
			mirror_replace = re.search('(sourceforge.net.*)', self.updateurl)
			if mirror_replace:
				self.updateurl = 'http://' + mirror_rand + '.dl.' + mirror_replace.group(1)
				printl('Generated update url: %s' % self.updateurl,self,'A')
		if config.mediaportal.version.value < remoteversion:
			self.session.openWithCallback(self.startUpdate,MessageBoxExt,_("An update is available for the MediaPortal Plugin!\nDo you want to download and install it now?"), MessageBoxExt.TYPE_YESNO)
			return
		else:
			return

	def startUpdate(self,answer):
		if answer is True:
			self.session.open(MPUpdateScreen,self.updateurl)
		else:
			return

class MPUpdateScreen(Screen):

	def __init__(self, session, updateurl):
		self.session = session
		self.updateurl = updateurl

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/MPUpdate.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/MPUpdate.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["mplog"] = ScrollLabel()

		Screen.__init__(self, session)
		self['title'] = Label("MediaPortal Update")
		self.setTitle("MediaPortal Update")

		self.onLayoutFinish.append(self.__onLayoutFinished)

	def __onLayoutFinished(self):
		sl = self["mplog"]
		sl.instance.setZPosition(1)
		self["mplog"].setText(_("Starting update, please wait..."))
		self.startPluginUpdate()

	def startPluginUpdate(self):
		self.container=eConsoleAppContainer()
		if mp_globals.isDreamOS:
			self.container.appClosed_conn = self.container.appClosed.connect(self.finishedPluginUpdate)
			self.container.stdoutAvail_conn = self.container.stdoutAvail.connect(self.mplog)
			self.container.execute("apt-get update ; wget -q -O /tmp/foobar %s ; dpkg --install /tmp/foobar ; apt-get -y -f install" % str(self.updateurl))
		else:
			self.container.appClosed.append(self.finishedPluginUpdate)
			self.container.stdoutAvail.append(self.mplog)
			#self.container.stderrAvail.append(self.mplog)
			#self.container.dataAvail.append(self.mplog)
			self.container.execute("opkg update ; opkg install " + str(self.updateurl))

	def finishedPluginUpdate(self,retval):
		self.container.kill()
		if retval == 0:
			config.mediaportal.filter.value = "ALL"
			config.mediaportal.filter.save()
			configfile.save()
			self.session.openWithCallback(self.restartGUI, MessageBoxExt, _("MediaPortal successfully updated!\nDo you want to restart the Enigma2 GUI now?"), MessageBoxExt.TYPE_YESNO)
		elif retval == 2:
			self.session.openWithCallback(self.returnGUI, MessageBoxExt, _("MediaPortal update failed! Please check free space on your root filesystem, at least 16MB are required for installation.\nCheck the update log carefully!"), MessageBoxExt.TYPE_ERROR)
		else:
			self.session.openWithCallback(self.returnGUI, MessageBoxExt, _("MediaPortal update failed! Check the update log carefully!"), MessageBoxExt.TYPE_ERROR)

	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

	def returnGUI(self, answer):
		self.close()

	def mplog(self,str):
		self["mplog"].setText(str)
		self.writeToLog(str)

	def writeToLog(self, log):
		global gLogFile

		if gLogFile is None:
			self.openLogFile()

		now = datetime.datetime.now()
		gLogFile.write(str(log) + "\n")
		gLogFile.flush()

	def openLogFile(self):
		global gLogFile
		baseDir = "/tmp"
		logDir = baseDir + "/mediaportal"

		now = datetime.datetime.now()

		try:
			os.makedirs(baseDir)
		except OSError, e:
			pass

		try:
			os.makedirs(logDir)
		except OSError, e:
			pass

		gLogFile = open(logDir + "/MediaPortal_update_%04d%02d%02d_%02d%02d.log" % (now.year, now.month, now.day, now.hour, now.minute, ), "w")