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

class pornosharePlaylist():

	def __init__(self):
		self.sbox = {}
		self.mykey = {}

	def decrypt(self, string, passid):
		_local3 = self.hexToChars(string)
		_local4 = self.strToChars(passid)
		_local5 = self.calculate(_local3, _local4)
		final = "".join([chr(c) for c in _local5])
		return final

	def calculate(self, _arg1, _arg2):
		self.initialize(_arg2)
		_local3 = 0
		_local4 = 0
		_local5 = []
		_local9 = 0
		while _local9 < len(_arg1):
			_local3 = ((_local3 + 1) % 0x0100)
			_local4 = ((_local4 + self.sbox[_local3]) % 0x0100)
			_local7 = self.sbox[_local3]
			self.sbox[_local3] = self.sbox[_local4]
			self.sbox[_local4] = _local7
			_local10 = ((self.sbox[_local3] + self.sbox[_local4]) % 0x0100)
			_local6 = self.sbox[_local10]
			_local8 = (_arg1[_local9] ^ _local6)
			_local5.append(_local8)
			_local9 += 1
		return _local5

	def initialize(self, _arg1):
		_local2 = 0
		_local4 = len(_arg1)
		_local5 = 0
		while _local5 <= 0xFF:
			self.mykey[_local5] = _arg1[(_local5 % _local4)]
			self.sbox[_local5] = _local5
			_local5 += 1
		_local6 = 0
		while _local6 <= 0xFF:
			_local2 = (((_local2 + self.sbox[_local6]) + self.mykey[_local6]) % 0x0100)
			_local3 = self.sbox[_local6]
			self.sbox[_local6] = self.sbox[_local2]
			self.sbox[_local2] = _local3
			_local6 += 1

	def strToChars(self,_arg1):
		_local2 = []
		for i in range(0, len(_arg1)):
			_local2.append(ord(_arg1[i]))
		return _local2

	def hexToChars(self,_arg1):
		_local2 = []
		for i in range(0, len(_arg1), 2):
			_local2.append(int(_arg1[i:i+2], 16))
		return _local2