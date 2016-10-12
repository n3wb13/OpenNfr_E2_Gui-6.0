# -*- coding: utf-8 -*-
from enigma import gFont, addFont, eTimer, eConsoleAppContainer, ePicLoad, loadPNG, getDesktop, eServiceReference, iPlayableService, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, eListbox, gPixmapPtr, getPrevAsciiCode, eBackgroundFileEraser

from Plugins.Plugin import PluginDescriptor

from twisted import __version__
from twisted.internet import reactor, defer
from twisted.web.http_headers import Headers
from twisted.internet.defer import Deferred, succeed
from twisted.web import http
from twisted.python import failure

#from twisted.web.client import downloadPage, getPage, error
from twisted.web import error as weberror

from cookielib import CookieJar

from zope.interface import implements

from twagenthelper import TwAgentHelper, twAgentGetPage
from tw_util import downloadPage, getPage
from sepg.mp_epg import SimpleEPG, mpepg, mutex
from sepg import log

from Components.ActionMap import NumberActionMap, ActionMap, HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.Button import Button
from Components.config import config, ConfigInteger, ConfigSelection, getConfigListEntry, ConfigText, ConfigDirectory, ConfigYesNo, configfile, ConfigSelection, ConfigSubsection, ConfigPIN, NoSave, ConfigNothing, ConfigIP
try:
	from Components.config import ConfigPassword
except ImportError:
	ConfigPassword = ConfigText
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
from Components.Pixmap import Pixmap, MovingPixmap
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.Boolean import Boolean
from Components.Input import Input

from Screens.InfoBar import MoviePlayer, InfoBar
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarNotifications
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Screens.HelpMenu import HelpableScreen

from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN, SCOPE_CURRENT_SKIN, createDir
from Tools.LoadPixmap import LoadPixmap
from Tools.NumericalTextInput import NumericalTextInput

import re, httplib, urllib, urllib2, os, cookielib, socket, sha, shutil, datetime, math, hashlib, random, json, md5, string, xml.etree.cElementTree, StringIO, Queue, threading, sys

from urllib2 import Request, URLError, urlopen as urlopen2
from socket import gaierror, error
from urllib import quote, unquote_plus, unquote, urlencode
from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException
from binascii import unhexlify, hexlify
from urlparse import parse_qs
from time import time, localtime, strftime, mktime


# MediaPortal Imports
from debuglog import printlog as printl
FuturesSession = None
print '[MP imports] Try to import "FuturesSession"'
if sys.version_info[:3] >= (2,7,9):
	try:
		from .requests_futures.sessions import FuturesSession
		print '[MP imports] "FuturesSession" successfull imported'
	except:
		print '[MP imports] Error: cannot import "FuturesSession"'
else:
	print '[MP imports] Wrong python version to import "FuturesSession": %s' % sys.version

class InsensitiveKey(object):
	def __init__(self, key):
		self.key = key
	def __hash__(self):
		return hash(self.key.lower())
	def __eq__(self, other):
		return self.key.lower() == other.key.lower()
	def __str__(self):
		return self.key

class InsensitiveDict(dict):
	def __setitem__(self, key, value):
		key = InsensitiveKey(key)
		super(InsensitiveDict, self).__setitem__(key, value)
	def __getitem__(self, key):
		key = InsensitiveKey(key)
		return super(InsensitiveDict, self).__getitem__(key)

def r_getPage(url, *args, **kwargs):
	if FuturesSession != None:
		session = FuturesSession()
		method = kwargs.pop('method', 'GET')
		user_agent = kwargs.pop('agent', None)
		if user_agent:
			headers = kwargs.pop('headers', {})
			headers['User-Agent'] = user_agent
			kwargs['headers'] = headers
		def cb_err_ret(err):
			return err

		d = Deferred()
		d.addErrback(cb_err_ret)
		try:
			def bg_cb(sess, resp):
				c = resp.content
				d.callback(c)

			if method == 'GET':
				session.get(url, background_callback=bg_cb, *args, **kwargs)
			elif method == 'POST':
				kwargs['data'] = kwargs.pop('postdata')
				session.post(url, background_callback=bg_cb, *args, **kwargs)
			return d
		except Exception, err:
			printl('Error: '+str(err),None,'E')
			d.errback(failure.Failure())
	else:
		return getPage(url.replace('https:','http:'), *args, **kwargs)

import mp_globals
from mp_globals import std_headers
from streams import isSupportedHoster, get_stream_link
from mpscreen import MPScreen, SearchHelper
from simpleplayer import SimplePlayer
from coverhelper import CoverHelper
from showAsThumb import ThumbsHelper
from messageboxext import MessageBoxExt

def registerFont(file, name, scale, replacement):
		try:
				addFont(file, name, scale, replacement)
		except Exception, ex: #probably just openpli
				addFont(file, name, scale, replacement, 0)

def getUserAgent():
	userAgents = [
		"Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
		"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; de) Presto/2.9.168 Version/11.52",
		"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20120101 Firefox/35.0",
	    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0",
	    "Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0",
	    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
	    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)",
	    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
	    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
	    "Mozilla/5.0 (compatible; Konqueror/4.5; FreeBSD) KHTML/4.5.4 (like Gecko)",
	    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",
	]
	return random.choice(userAgents)

def getUpdateUrl():
	updateurls = [
		'http://master.dl.sourceforge.net/project/e2-mediaportal/version.txt',
		'http://dhwz.github.io/e2-mediaportal/version.txt'
	]
	return random.choice(updateurls)

def bstkn(url):
	urlpart = re.search('https://bs.to/api/(.*?)$', url)
	if urlpart:
		import hmac, base64
		urlpart = urlpart.group(1)
		datelong = int(round(time()))
		public_key = base64.b64decode('UGdmTGEzY0dOWTVuRE4zaXNpYnp1R3NvbVNXc3BqQXM=')
		resultD = mp_globals.bsp
		myurlpart = '%s/%s' % (datelong, urlpart)
		myHmac = hmac.new(resultD, myurlpart,digestmod=hashlib.sha256).hexdigest()
		token = '{"public_key":"'+public_key+'","timestamp":'+str(datelong)+',"hmac":"'+ myHmac+'"}'
		retval = base64.b64encode(token)
		return retval
	else:
		return None

def testWebConnection():
	conn = httplib.HTTPConnection("www.google.com", timeout=15)
	try:
		conn.request("GET", "/")
		data = conn.getresponse()
		conn.close()
		return True
	except:
		conn.close()
	return False

def decodeHtml(text):
	text = text.replace('&auml;','ä')
	text = text.replace('\u00e4','ä')
	text = text.replace('&#228;','ä')

	text = text.replace('&Auml;','Ä')
	text = text.replace('\u00c4','Ä')
	text = text.replace('&#196;','Ä')

	text = text.replace('&ouml;','ö')
	text = text.replace('\u00f6','ö')
	text = text.replace('&#246;','ö')

	text = text.replace('&ouml;','Ö')
	text = text.replace('&Ouml;','Ö')
	text = text.replace('\u00d6','Ö')
	text = text.replace('&#214;','Ö')

	text = text.replace('&uuml;','ü')
	text = text.replace('\u00fc','ü')
	text = text.replace('&#252;','ü')

	text = text.replace('&Uuml;','Ü')
	text = text.replace('\u00dc','Ü')
	text = text.replace('&#220;','Ü')

	text = text.replace('&szlig;','ß')
	text = text.replace('\u00df','ß')
	text = text.replace('&#223;','ß')

	text = text.replace('&copy;','©')
	text = text.replace('&pound;','£')
	text = text.replace('&fnof;','ƒ')
	text = text.replace('&Atilde;','Ã')
	text = text.replace('&atilde;','ã')
	text = text.replace('&Egrave;','È')
	text = text.replace('&egrave;','è')
	text = text.replace('&Yacute;','Ý')
	text = text.replace('&yacute;','ý')
	text = text.replace('&amp;','&')
	text = text.replace('&quot;','\"')
	text = text.replace('&gt;','>')
	text = text.replace('&lt;','<')
	text = text.replace('&apos;',"'")
	text = text.replace('&acute;','\'')
	text = text.replace('&comma;',',')
	text = text.replace('&commat;','@')
	text = text.replace('&period;','.')
	text = text.replace('&colon;',':')
	text = text.replace('&semi;',';')
	text = text.replace('&infin;','∞')
	text = text.replace('&excl;','!')
	text = text.replace('&quest;','?')
	text = text.replace('&num;','#')
	text = text.replace('&equals;','=')
	text = text.replace('&lpar;','(')
	text = text.replace('&rpar;',')')
	text = text.replace('&lsqb;','[')
	text = text.replace('&lbrack;','[')
	text = text.replace('&rsqb;',']')
	text = text.replace('&rbrack;',']')
	text = text.replace('&ndash;','-')
	text = text.replace('&lowbar;','_')
	text = text.replace('&bdquo;','"')
	text = text.replace('&rdquo;','"')
	text = text.replace('&ldquo;','"')
	text = text.replace('&lsquo;','\'')
	text = text.replace('&rsquo;','\'')
	text = text.replace('&#034;','"')
	text = text.replace('&#34;','"')
	text = text.replace('&#038;','&')
	text = text.replace('&#039;','\'')
	text = text.replace('&#39;','\'')
	text = text.replace('&#160;',' ')
	text = text.replace('\u00a0',' ')
	text = text.replace('\u00b4','\'')
	text = text.replace('\u003d','=')
	text = text.replace('\u0026','&')
	text = text.replace('&#174;','')
	text = text.replace('&#215;','×')
	text = text.replace('&#225;','a')
	text = text.replace('&#233;','e')
	text = text.replace('&#243;','o')
	text = text.replace('&#8211;',"-")
	text = text.replace('&#8212;',"—")
	text = text.replace('&mdash;','—')
	text = text.replace('\u2013',"–")
	text = text.replace('&#8216;',"'")
	text = text.replace('&#8217;',"'")
	text = text.replace('&#8220;',"'")
	text = text.replace('&#8221;','"')
	text = text.replace('&#8222;',',')
	text = text.replace('&#124;','|')
	text = text.replace('\u014d','ō')
	text = text.replace('\u016b','ū')
	text = text.replace('\u201a','\"')
	text = text.replace('\u2018','\"')
	text = text.replace('\u201e','\"')
	text = text.replace('\u201c','\"')
	text = text.replace('\u201d','\'')
	text = text.replace('\u2019','’')
	text = text.replace('\u2019s','’')
	text = text.replace('\u2606','*')
	text = text.replace('\u266a','♪')
	text = text.replace('\u00e0','à')
	text = text.replace('\u00d7','×')
	text = text.replace('\u00e7','ç')
	text = text.replace('\u00e8','é')
	text = text.replace('\u00e9','é')
	text = text.replace('\u00f2','ò')
	text = text.replace('\u00f4','ô')
	text = text.replace('\u00c1','Á')
	text = text.replace('\u00c6','Æ')
	text = text.replace('\u00e1','á')
	text = text.replace('\u00b0','°')
	text = text.replace('\u00e6','æ')

	text = text.replace('&#xC4;','Ä')
	text = text.replace('&#xD6;','Ö')
	text = text.replace('&#xDC;','Ü')
	text = text.replace('&#xE4;','ä')
	text = text.replace('&#xF6;','ö')
	text = text.replace('&#xFC;','ü')
	text = text.replace('&#xDF;','ß')
	text = text.replace('&#xE9;','é')
	text = text.replace('&#xB7;','·')
	text = text.replace("&#x27;","'")
	text = text.replace("&#x26;","&")
	text = text.replace("&#xFB;","û")
	text = text.replace("&#xF8;","ø")
	text = text.replace("&#x21;","!")
	text = text.replace("&#x3f;","?")

	text = text.replace('&#8230;','...')
	text = text.replace('\u2026','...')
	text = text.replace('&hellip;','...')

	text = text.replace('&#8234;','')
	text = text.replace('&nbsp;','')
	return text

def iso8859_Decode(txt):
	txt = txt.replace('\xe4','ä').replace('\xf6','ö').replace('\xfc','ü').replace('\xdf','ß')
	txt = txt.replace('\xc4','Ä').replace('\xd6','Ö').replace('\xdc','Ü')
	return txt

def decodeHtml2(txt):
	txt = iso8859_Decode(txt)
	txt = decodeHtml(txt).strip()
	return txt

def stripAllTags(html):
	cleanr = re.compile('<.*?>')
	cleantext = re.sub(cleanr,'', html.replace('\n',''))
	return cleantext