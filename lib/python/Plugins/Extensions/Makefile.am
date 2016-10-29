installdir = $(pkglibdir)/python/Plugins/Extensions

SUBDIRS = TuxboxPlugins CutListEditor PicturePlayer MediaScanner MediaPlayer SocketMMI DVDBurn Modem Infopanel MenuSort bmediacenter MediaPortal MainMenu2 e2speedtest

if SPARK
SUBDIRS +=  NFR4XBoot-sh4
else
SUBDIRS +=  NFR4XBoot
endif

if HAVE_LIBDDVD
SUBDIRS += DVDPlayer
endif

if VUSOLO4K
SUBDIRS += MiniTV
endif

install_PYTHON = __init__.py
