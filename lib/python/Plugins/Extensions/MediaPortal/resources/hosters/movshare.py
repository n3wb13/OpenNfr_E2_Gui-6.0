# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def movshare(self, data, url, hostername, loop=False):
	print "movshare:", hostername
	print data
	m = re.search('flashvars.filekey=(.*?);', data, re.S)
	if not m:
		keyvar = filecode = None
		l = re.search('\}\(\'(.*?)\',\'(.*?)\',\'(.*?)\',\'(.*?)\'\)\);', data)
		if l:
			w = l.group(1)
			i = l.group(2)
			s = l.group(3)
			e = l.group(4)
			crypt1 = self.movshare_code1(w,i,s,e)
			print "crypt1", crypt1
			m = re.search('\}\(\'(.*?)\',\'(.*?)\',\'(.*?)\',\'(.*?)\'\)', crypt1)
			if m:
				w = m.group(1)
				i = m.group(2)
				s = m.group(3)
				e = m.group(4)
				crypt2 = self.movshare_code1(w,i,s,e)
				print "crypt2", crypt2
				n = re.search('\}\(\'(.*?)\',\'(.*?)\',\'(.*?)\',\'(.*?)\'.*?return.*?\}\(\'(.*?)\',\'(.*?)\',\'(.*?)\',\'(.*?)\'\)', crypt2)
				print "n", n
				if n:
					w2 = n.group(5)
					i2 = n.group(6)
					s2 = n.group(7)
					e2 = n.group(8)
					crypt3 = self.movshare_code1(w2,i2,s2,e2)
					print "crypt3", crypt3
					m = re.search('flashvars.file="(.*?)"', crypt3, re.S)
					if m:
						filecode = m.group(1)
						print filecode
						key = re.search('flashvars.filekey="(.*?)"', crypt3)
						if key:
							print "11111111111111111111111111111"
							keyvar = key.group(1)
							print "key 1:", keyvar
						else:
							print "code3 - 222222222222222222222222222"
							t = re.search('(\d+.\d+.\d+.\d+-\w+)', crypt3, re.S)
							keyvar = t and t.group(1)
							print keyvar
					elif crypt3:
						sUnpacked = unpack(crypt3)
						print sUnpacked
						print "code mit crypt"
						m = re.search('flashvars.file="(.*?)"', sUnpacked, re.S)
						filecode = m and m.group(1)

						key = re.search('flashvars.filekey=".*?"', sUnpacked)
						if key:
							print "11111111111111111111111111111"
							keyvar = key.group(1)
							print "key 1:", keyvar
						else:
							print "sUnpacked - 222222222222222222222222222"
							print filecode
							t = re.search('flashvars.filekey=(.*?);', sUnpacked, re.S)
							key = t and t.group(1)
							t = re.search(';var %s=(.*?);' % key, sUnpacked, re.S)
							key1 = t and t.group(1)
							t = re.search(';var %s=(.*?);' % key1, sUnpacked, re.S)
							key2 = t and t.group(1)
							t = re.search(';var %s=(.*?);' % key2, sUnpacked, re.S)
							key3 = t and t.group(1)
							t = re.search(';var %s="(.*?)";' % key3, sUnpacked, re.S)
							keyvar = t and t.group(1)
		else:
			stepkey = re.findall('method="post"\s*action="".*?name="stepkey"\s*value="(.*?)"', data, re.S)
			if stepkey and not loop:
				postdata = {'stepkey': stepkey[0], 'submit': 'submit'}
				getPage(url, method='POST', postdata=urlencode(postdata), headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self.movshare, url, hostername, True).addErrback(self.errorload)
				return
	else:
		fk = m.group(1)
		m = re.search('var %s="(.*?)";.*?flashvars.file="(.*?)";' % fk, data, re.S)
		if m:
			filecode = m and m.group(2)
			keyvar = m and m.group(1)
			print "filecode:",filecode,"keyvar:",keyvar
		else:
			m = re.search('flashvars.filekey=(.*?);', data, re.S)
			if m:
				fk = m.group(1)
				m = re.search('flashvars.file="(.*?)".*?%s' %fk, data, re.S)
				filecode = m.group(1)
				keyvar = fk.replace('.', '%2E').replace('-', '%2D')
				print "filecode:",filecode,"keyvar:",keyvar
	if filecode and keyvar:
		if hostername == "wholecloud":
			print "wholecloud"
			url = "http://www.wholecloud.net/api/player.api.php?cid3=undefined&key=%s&user=undefined&numOfErrors=0&cid=undefined&file=%s&cid2=undefined" % ( keyvar, filecode)
		elif hostername == "nowvideo":
			print "nowvideo"
			url = "http://www.nowvideo.sx/api/player.api.php?cid3=undefined&key=%s&user=undefined&numOfErrors=0&cid=undefined&file=%s&cid2=undefined" % ( keyvar, filecode)
		elif hostername == "novamov":
			print "novamov"
			url = "http://www.novamov.com/api/player.api.php?cid3=undefined&key=%s&user=undefined&numOfErrors=0&cid=undefined&file=%s&cid2=undefined" % ( keyvar, filecode)
		elif hostername == "videoweed":
			print "videoweed"
			url = "http://www.videoweed.es/api/player.api.php?cid3=undefined&key=%s&user=undefined&numOfErrors=0&cid=undefined&file=%s&cid2=undefined" % ( keyvar, filecode)
		elif hostername == "cloudtime":
			print "cloudtime"
			url = "http://www.cloudtime.to/api/player.api.php?cid3=undefined&key=%s&user=undefined&numOfErrors=0&cid=undefined&file=%s&cid2=undefined" % ( keyvar, filecode)
		elif hostername == "vidgg":
			print "vidgg"
			url = "http://www.vidgg.to/api/player.api.php?pass=undefined&key=%s&numOfErrors=0&cid2=undefined&cid=undefined&user=undefined&file=%s&cid3=undefined" % ( keyvar, filecode)
		else:
			self.stream_not_found()
		print url
		getPage(url, method='GET').addCallback(self.movshare_xml).addErrback(self.errorload)
	else:
		self.stream_not_found()

def movshare_code1(self,w,i,s,e):
	lIll=0
	ll1I=0
	Il1l=0
	ll1l=[]
	l1lI=[]
	while not len(w)+len(i)+len(s)+len(e)==len(ll1l)+len(l1lI)+len(e):
		if lIll < 5:
			l1lI.append(w[lIll])
		elif lIll < len(w):
			ll1l.append(w[lIll])
		lIll += 1
		if ll1I < 5:
			l1lI.append(i[ll1I])
		elif ll1I < len(i):
			ll1l.append(i[ll1I])
		ll1I += 1
		if Il1l < 5:
			l1lI.append(s[Il1l])
		elif Il1l < len(s):
			ll1l.append(s[Il1l])
		Il1l += 1
	str1 = ''
	lI1l = str1.join( ll1l )
	I1lI = str1.join( l1lI )
	ll1I = 0
	l1ll = []
	lIll = 0
	while lIll < len(ll1l):
		ll11 = -1
		if ord(I1lI[ll1I])%2:
			ll11 = 1
		l1ll.append(chr(self.movshare_base36decode(lI1l[lIll:lIll+2]) - ll11))
		ll1I += 1
		if ll1I >= len(l1lI):
			ll1I = 0
		lIll += 2
	return str1.join(l1ll)

def movshare_base36decode(self, number):
	return int(number,36)

def movshare_xml(self, data):
	file_link = re.search('url=(.+?)&title=', data)
	if file_link:
		stream_url = urllib.unquote(file_link.group(1))
		self._callback(stream_url)
	else:
		self.stream_not_found()