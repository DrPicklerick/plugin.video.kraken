# -*- coding: utf-8 -*-
"""
	Kraken Add-on
"""

from resources.lib.modules import control
from resources.lib.modules import log_utils

window = control.homeWindow
plugin = 'plugin://plugin.video.kraken/'
LOGNOTICE = 2 if control.getKodiVersion() < 19 else 1 # (2 in 18, deprecated in 19 use LOGINFO(1))


class CheckSettingsFile:
	def run(self):
		try:
			control.log('[ plugin.video.kraken ]  CheckSettingsFile Service Starting...', LOGNOTICE)
			window.clearProperty('kraken_settings')
			profile_dir = control.dataPath
			if not control.existsPath(profile_dir):
				success = control.makeDirs(profile_dir)
				if success: control.log('%s : created successfully' % profile_dir, LOGNOTICE)
			else: control.log('%s : already exists' % profile_dir, LOGNOTICE)
			settings_xml = control.joinPath(profile_dir, 'settings.xml')
			if not control.existsPath(settings_xml):
				control.setSetting('trakt.message1', '')
				control.log('%s : created successfully' % settings_xml, LOGNOTICE)
			else: control.log('%s : already exists' % settings_xml, LOGNOTICE)
			return control.log('[ plugin.video.kraken ]  Finished CheckSettingsFile Service', LOGNOTICE)
		except:
			log_utils.error()


class SettingsMonitor(control.monitor_class):
	def __init__ (self):
		control.monitor_class.__init__(self)
		control.log('[ plugin.video.kraken ]  Settings Monitor Service Starting...', LOGNOTICE)


	def onSettingsChanged(self):
		# Kodi callback when the addon settings are changed
		window.clearProperty('kraken_settings')
		control.sleep(50)
		refreshed = control.make_settings_dict()


class SyncMyAccounts:
	def run(self):
		control.log('[ plugin.video.kraken ]  Sync "My Accounts" Service Starting...', LOGNOTICE)
		control.syncMyAccounts(silent=True)
		return control.log('[ plugin.video.kraken ]  Finished Sync "My Accounts" Service', LOGNOTICE)


class ReuseLanguageInvokerCheck:
	def run(self):
		if control.getKodiVersion() < 18: return
		control.log('[ plugin.video.kraken ]  ReuseLanguageInvokerCheck Service Starting...', LOGNOTICE)
		try:
			import xml.etree.ElementTree as ET
			addon_xml = control.joinPath(control.addonPath('plugin.video.kraken'), 'addon.xml')
			tree = ET.parse(addon_xml)
			root = tree.getroot()
			current_addon_setting = control.addon('plugin.video.kraken').getSetting('reuse.languageinvoker')
			try: current_xml_setting = [str(i.text) for i in root.iter('reuselanguageinvoker')][0]
			except: return control.log('[ plugin.video.kraken ]  ReuseLanguageInvokerCheck failed to get settings.xml value', LOGNOTICE)
			if current_addon_setting == '':
				current_addon_setting = 'true'
				control.setSetting('reuse.languageinvoker', current_addon_setting)
			if current_xml_setting == current_addon_setting:
				return control.log('[ plugin.video.kraken ]  ReuseLanguageInvokerCheck Service Finished', LOGNOTICE)
			control.okDialog(message='%s\n%s' % (control.lang(33023), control.lang(33020)))
			for item in root.iter('reuselanguageinvoker'):
				item.text = current_addon_setting
				hash_start = control.gen_file_hash(addon_xml)
				tree.write(addon_xml)
				hash_end = control.gen_file_hash(addon_xml)
				control.log('[ plugin.video.kraken ]  ReuseLanguageInvokerCheck Service Finished', LOGNOTICE)
				if hash_start != hash_end:
					current_profile = control.infoLabel('system.profilename')
					control.execute('LoadProfile(%s)' % current_profile)
				else: control.okDialog(title='default', message=33022)
			return
		except:
			log_utils.error()


class AddonCheckUpdate:
	def run(self):
		control.log('[ plugin.video.kraken ]  Addon checking available updates', LOGNOTICE)
		try:
			import re
			import requests
			repo_xml = requests.get('https://raw.githubusercontent.com/DrPicklerick/zips/master/addons.xml')
			if not repo_xml.status_code == 200:
				control.log('[ plugin.video.kraken ]  Could not connect to remote repo XML: status code = %s' % repo_xml.status_code, LOGNOTICE)
				return
			repo_version = re.findall(r'<addon id=\"plugin.video.kraken\".+version=\"(\d*.\d*.\d*)\"', repo_xml.text)[0]
			local_version = control.getKrakenVersion()
			if control.check_version_numbers(local_version, repo_version):
				while control.condVisibility('Library.IsScanningVideo'):
					control.sleep(10000)
				control.log('[ plugin.video.kraken ]  A newer version is available. Installed Version: v%s, Repo Version: v%s' % (local_version, repo_version), LOGNOTICE)
				control.notification(message=control.lang(35523) % repo_version)
			return control.log('[ plugin.video.kraken ]  Addon update check complete', LOGNOTICE)
		except:
			log_utils.error()


class LibraryService:
	def run(self):
		control.log('[ plugin.video.kraken ]  Library Update Service Starting (Update check every 6hrs)...', LOGNOTICE)
		control.execute('RunPlugin(%s?action=library_service)' % plugin) # library_service contains control.monitor().waitForAbort() while loop every 6hrs


class SyncTraktCollection:
	def run(self):
		control.log('[ plugin.video.kraken ]  Trakt Collection Sync Starting...', LOGNOTICE)
		control.execute('RunPlugin(%s?action=library_tvshowsToLibrarySilent&url=traktcollection)' % plugin)
		control.execute('RunPlugin(%s?action=library_moviesToLibrarySilent&url=traktcollection)' % plugin)
		control.log('[ plugin.video.kraken ]  Trakt Collection Sync Complete', LOGNOTICE)


class SyncTraktWatched:
	def run(self):
		control.log('[ plugin.video.kraken ]  Trakt Watched Sync Service Starting (sync check every 15min)...', LOGNOTICE)
		control.execute('RunPlugin(%s?action=tools_syncTraktWatched)' % plugin) # trakt.sync_watched() contains control.monitor().waitForAbort() while loop every 15min


class SyncTraktProgress:
	def run(self):
		control.log('[ plugin.video.kraken ]  Trakt Progress Sync Service Starting (sync check every 15min)...', LOGNOTICE)
		control.execute('RunPlugin(%s?action=tools_syncTraktProgress)' % plugin) # trakt.sync_progress() contains control.monitor().waitForAbort() while loop every 15min


try:
	AddonVersion = control.addon('plugin.video.kraken').getAddonInfo('version')
	RepoVersion = control.addon('repository.kraken').getAddonInfo('version')
	log_utils.log('#####   CURRENT VENOM VERSIONS REPORT   #####', level=log_utils.LOGNOTICE)
	log_utils.log('########   VENOM PLUGIN VERSION: %s   ########' % str(AddonVersion), level=log_utils.LOGNOTICE)
	log_utils.log('#####   VENOM REPOSITORY VERSION: %s   #######' % str(RepoVersion), level=log_utils.LOGNOTICE)
except:
	log_utils.log('################# CURRENT Kraken VERSIONS REPORT ################', level=log_utils.LOGNOTICE)
	log_utils.log('# ERROR GETTING Kraken VERSION - Missing Repo of failed Install #', level=log_utils.LOGNOTICE)


def getTraktCredentialsInfo():
	username = control.setting('trakt.username').strip()
	token = control.setting('trakt.token')
	refresh = control.setting('trakt.refresh')
	if (username == '' or token == '' or refresh == ''): return False
	return True


def main():
	while not control.monitor.abortRequested():
		control.log('[ plugin.video.kraken ]  Service Started', LOGNOTICE)
		syncWatched = None
		syncProgress = None
		schedTrakt = None
		libraryService = None
		CheckSettingsFile().run()
		SyncMyAccounts().run()
		ReuseLanguageInvokerCheck().run()
		if control.setting('library.service.update') == 'true':
			libraryService = True
			LibraryService().run()
		if control.setting('general.checkAddonUpdates') == 'true':
			AddonCheckUpdate().run()
		if getTraktCredentialsInfo():
			if control.setting('indicators.alt') == '1':
				syncWatched = True
				SyncTraktWatched().run()
			if control.setting('bookmarks') == 'true' and control.setting('resume.source') == '1':
				syncProgress = True
				SyncTraktProgress().run()
			if control.setting('autoTraktOnStart') == 'true':
				SyncTraktCollection().run()
			if int(control.setting('schedTraktTime')) > 0:
				import threading
				log_utils.log('#################### STARTING TRAKT SCHEDULING ################', level=log_utils.LOGNOTICE)
				log_utils.log('#################### SCHEDULED TIME FRAME '+ control.setting('schedTraktTime')  + ' HOURS ###############', level=log_utils.LOGNOTICE)
				timeout = 3600 * int(control.setting('schedTraktTime'))
				schedTrakt = threading.Timer(timeout, SyncTraktCollection().run) # this only runs once at the designated interval time to wait...not repeating
				schedTrakt.start()
		break
	SettingsMonitor().waitForAbort()
	control.log('[ plugin.video.kraken ]  Settings Monitor Service Stopping...', LOGNOTICE)
	if syncWatched:
		control.log('[ plugin.video.kraken ]  Trakt Watched Sync Service Stopping...', LOGNOTICE)
	if syncProgress:
		control.log('[ plugin.video.kraken ]  Trakt Progress Sync Service Stopping...', LOGNOTICE)
	if libraryService:
		control.log('[ plugin.video.kraken ]  Library Update Service Stopping...', LOGNOTICE)
	if schedTrakt:
		schedTrakt.cancel()
		# control.log('[ plugin.video.kraken ]  Library Update Service Stopping...', LOGNOTICE)
	control.log('[ plugin.video.kraken ]  Service Stopped', LOGNOTICE)

main()
