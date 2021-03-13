# -*- coding: utf-8 -*-
"""
	Kraken Add-on
"""

from resources.lib.modules import control

kraken_path = control.addonPath(control.addonId())
kraken_version = control.addonVersion(control.addonId())


def get(file):
	helpFile = control.joinPath(kraken_path, 'resources', 'help', file + '.txt')
	r = open(helpFile)
	text = r.read()
	r.close()
	control.dialog.textviewer('[COLOR red]Kraken[/COLOR] -  v%s - %s' % (kraken_version, file), text)
