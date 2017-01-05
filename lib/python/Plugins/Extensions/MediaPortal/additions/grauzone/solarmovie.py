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
import gzip

BASE_URL = 'http://www.solarmovie.fm/'

def gzipToRaw(data):
    data = StringIO.StringIO(data)
    gzipper = gzip.GzipFile(fileobj=data)
    data = gzipper.read()
    gzipper.close()
    return data

class solarMovieMain(MPScreen):

    def __init__(self, session):
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
            "0": self.closeAll,
            "ok" : self.keyOK,
            "cancel": self.keyCancel
        }, -1)

        self['title'] = Label("SolarMovie")
        self['ContentTitle'] = Label("Choose Genre:")

        self.streamList = []
        self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
        self['liste'] = self.ml

        self.keyLocked = False
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.keyLocked = True
        self.streamList.append(("Latest Movies", "/?page="))
        self.streamList.append(("Action Movies", "/?genre=Action&page="))
        self.streamList.append(("Musical Movies", "/?genre=Musical&page="))
        self.streamList.append(("Mystery Movies", "/?genre=Mystery&page="))
        self.streamList.append(("Reality-TV Movies", "/?genre=Reality-TV&page="))
        self.streamList.append(("Romance Movies", "/?genre=Romance&page="))
        self.streamList.append(("Sci-Fi Movies", "/?genre=Sci-Fi&page="))
        self.streamList.append(("Short Movies", "/?genre=Short&page="))
        self.streamList.append(("Sport Movies", "/?genre=Sport&page="))
        self.streamList.append(("Talk-Show Movies", "/?genre=Talk-Show&page="))
        self.streamList.append(("Thriller Movies", "/?genre=Thriller&page="))
        self.streamList.append(("War Movies", "/?genre=War&page="))
        self.streamList.append(("Western Movies", "/?genre=Western&page="))
        self.streamList.append(("Zombies Movies", "/?genre=Zombies&page="))
        self.streamList.append(("Music Movies", "/?genre=Music&page="))
        self.streamList.append(("Korean Movies", "/?genre=Korean&page="))
        self.streamList.append(("Animation Movies", "/?genre=Animation&page="))
        self.streamList.append(("Biography Movies", "/?genre=Biography&page="))
        self.streamList.append(("Comedy Movies", "/?genre=Comedy&page="))
        self.streamList.append(("Crime Movies", "/?genre=Crime&page="))
        self.streamList.append(("Documentary Movies", "/?genre=Documentary&page="))
        self.streamList.append(("Drama Movies", "/?genre=Drama&page="))
        self.streamList.append(("Family Movies", "/?genre=Family&page="))
        self.streamList.append(("Fantasy Movies", "/?genre=Fantasy&page="))
        self.streamList.append(("Game-Show Movies", "/?genre=Game-Show&page="))
        self.streamList.append(("History Movies", "/?genre=History&page="))
        self.streamList.append(("Horror Movies", "/?genre=Horror&page="))
        self.streamList.append(("Japanese Movies", "/?genre=Japanese&page="))
        self.streamList.append(("Adventure Movies", "/?genre=Adventure&page="))
        self.ml.setList(map(self._defaultlistcenter, self.streamList))
        self.keyLocked = False

    def keyOK(self):
        exist = self['liste'].getCurrent()
        if self.keyLocked or exist == None:
            return
        auswahl = self['liste'].getCurrent()[0][0]
        url = BASE_URL + self['liste'].getCurrent()[0][1]
        self.session.open(solarMovieParsing, auswahl, url)

class solarMovieParsing(MPScreen, ThumbsHelper):

    def __init__(self, session, genre, url):
        self.genre = genre
        self.url = url
        self.plugin_path = mp_globals.pluginPath
        self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
        path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
        if not fileExists(path):
            path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
        with open(path, "r") as f:
            self.skin = f.read()
            f.close()
        MPScreen.__init__(self, session)
        ThumbsHelper.__init__(self)

        self["actions"] = ActionMap(["MP_Actions"], {
            "0": self.closeAll,
            "5" : self.keyShowThumb,
            "ok" : self.keyOK,
            "cancel": self.keyCancel,
            "up" : self.keyUp,
            "down" : self.keyDown,
            "right" : self.keyRight,
            "left" : self.keyLeft,
            "nextBouquet" : self.keyPageUp,
            "prevBouquet" : self.keyPageDown
        }, -1)

        self['title'] = Label("SolarMovie")
        self['ContentTitle'] = Label("%s" % self.genre)

        self['Page'] = Label(_("Page:"))

        self.page = 1
        self.lastpage = 1
        self.streamList = []
        self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
        self['liste'] = self.ml

        self.keyLocked = True
        self.onLayoutFinish.append(self.loadPage)

    def loadPage(self):
        self.streamList = []
        url = self.url+str(self.page)
        getPage(url).addCallback(self.parseData).addErrback(self.dataError)

    def parseData(self, data):
        # try:
        # 	data = gzipToRaw(data)
        # except IOError:
        # 	print "source: kein gzip"
        # except:
        # 	print "source: gzip"

        self.getLastPage(data, 'class="pagination"(.*?)</div>', '(\d+)">>>')
        parse = re.search('<div class="js-tab" id="tab-popular">((.|\s)*?)>>>', data, re.S)
        if parse:
            movies = re.findall('<a class="coverImage" href="(.*?)" title="(.*?)"><img src="(.*?)"', parse.group(1), re.S)
            if movies:
                for (Url, Title, Image) in movies:
                    self.streamList.append((decodeHtml(Title), Url, Image))
                self.ml.setList(map(self._defaultlistleft, self.streamList))
                self.ml.moveToIndex(0)
                self.keyLocked = False
                self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page, self.lastpage)
                self.showInfos()
            else:
                print "No movie has been found"
        print "No movie found in category"

    def showInfos(self):
        filmName = self['liste'].getCurrent()[0][0]
        self['name'].setText(filmName)
        coverUrl = self['liste'].getCurrent()[0][2]
        CoverHelper(self['coverArt']).getCover(coverUrl)

    def keyOK(self):
        exist = self['liste'].getCurrent()
        if self.keyLocked or exist == None:
            return
        stream_name = self['liste'].getCurrent()[0][0]
        movie_url = self['liste'].getCurrent()[0][1]
        cover = self['liste'].getCurrent()[0][2]
        self.session.open(solarMovieStreams, stream_name, movie_url, cover)

class solarMovieStreams(MPScreen):

    def __init__(self, session, stream_name, url, cover):
        self.stream_name = stream_name
        self.url = url
        self.cover = cover
        self.plugin_path = mp_globals.pluginPath
        self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
        path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
        if not fileExists(path):
            path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
        with open(path, "r") as f:
            self.skin = f.read()
            f.close()

        MPScreen.__init__(self, session)

        self["actions"] = ActionMap(["MP_Actions"], {
            "0": self.closeAll,
            "ok" : self.keyOK,
            "cancel": self.keyCancel
        }, -1)

        self['title'] = Label("SolarMovie")
        self['ContentTitle'] = Label("Streams:")


        self.streamList = []
        self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
        self['liste'] = self.ml

        self.keyLocked = True
        self.onLayoutFinish.append(self.loadPage)

    def loadPage(self):
        self.streamList = []
        getPage(self.url).addCallback(self.parseData).addErrback(self.dataError)

    def parseData(self, data):
        # try:
        # 	data = gzipToRaw(data)
        # except IOError:
        # 	print "source: kein gzip"
        # except:
        # 	print "source: gzip"

        self.streamList = []
        streams = re.findall('<span\sclass="movie_version_link"><a\shref="%splay/(.*?).html"\stitle="(?:(.|\s)*?)<span\sclass="version_host"\sstyle="font-size:13px;">(.*?)</span></td>' % BASE_URL, data, re.S)
        if streams:
            for (Id, Garbage, Hoster) in streams:
                if isSupportedHoster(Hoster, True):
                    Hoster = Hoster.replace('www.','')
                    self.streamList.append((Hoster, Id))
            self.ml.setList(map(self._defaultlisthoster, self.streamList))
            CoverHelper(self['coverArt']).getCover(self.cover)
            self.keyLocked = False
        else:
            print "No stream found"

    def keyOK(self):
        exist = self['liste'].getCurrent()
        if self.keyLocked or exist == None:
            return
        id = self['liste'].getCurrent()[0][1]
        get_url = BASE_URL + "play/%s.html" % id
        # print "Url: %s" % get_url
        getPage(get_url).addCallback(self.getStreamLink).addErrback(self.dataError)

    def getStreamLink(self, data):
        # try:
        # 	data = gzipToRaw(data)
        # except IOError:
        # 	print "source: kein gzip"
        # except:
        # 	print "source: gzip"


        stream = re.search('<a rel="nofollow" href="(.*?)" target="_blank" title="(?:.*?)" class="img_1"></a>', data, re.S|re.I)
        # print "stream: %s" % stream
        if stream:
            streamUrl = stream.group(1)
            get_stream_link(self.session).check_link(streamUrl, self.playfile)
        else:
            print "Stream not found"

    def playfile(self, stream_url):
        if stream_url != None:
            self.session.open(SimplePlayer, [(self.stream_name, stream_url, self.cover)], showPlaylist=False, ltype='solarmovie', cover=True)