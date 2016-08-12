# E2Speedtest - Test your internetspeed
# for OpenATV
# by Alex-2.5
from Screens.Screen import Screen
from Screens.Console import Console
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Plugins.Plugin import PluginDescriptor

###########################################################################

class E2Speedtest(Screen):
	skin = """
		<screen position="center,center" size="460,200" title="E2Speedtest" >
			<widget name="myMenu" position="10,10" size="420,180" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args = 0):
		self.session = session
		
		list = []
		list.append(("Start Speedtest", "com_one"))
		list.append((_("Exit"), "exit"))
		
		Screen.__init__(self, session)
		self["myMenu"] = MenuList(list)
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.cancel
		}, -1)

	def go(self):
		returnValue = self["myMenu"].l.getCurrentSelection()[1]
		print "\n[E2Speedtest] returnValue: " + returnValue + "\n"
		
		if returnValue is not None:
			if returnValue is "com_one":
				self.prombt("/usr/lib/enigma2/python/Plugins/Extensions/e2speedtest/speedtest-cli")
		
			else:
				print "\n[E2Speedtest] cancel\n"
				self.close(None)

	def prombt(self, com):
		self.session.open(Console,_("Internet-Speed: %s") % (com), ["%s" % com])
		
	def cancel(self):
		print "\n[E2Speedtest] cancel\n"
		self.close(None)

###########################################################################

def main(session, **kwargs):
	print "\n[E2Speedtest] start\n"	
	session.open(E2Speedtest)

###########################################################################

def Plugins(**kwargs):
	return PluginDescriptor(
			name="E2Speedtest",
			description="Test your internetspeed",
			where = PluginDescriptor.WHERE_PLUGINMENU,
			icon="pluginLogo.png",
			fnc=main)
