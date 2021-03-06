# Libreoffice-divvun: Linguistic extension for LibreOffice
# Copyright (C) 2015 Harri Pitkänen <hatapitk@iki.fi>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
# 
# Alternatively, the contents of this file may be used under the terms of
# the GNU General Public License Version 3 or later (the "GPL"), in which
# case the provisions of the GPL are applicable instead of those above.

import logging
import unohelper		# type:ignore
import os
import sys
import locale
import uno			# type:ignore
from LODivvun.DivvunHandlePool import DivvunHandlePool
from com.sun.star.beans import XPropertyChangeListener, UnknownPropertyException, PropertyValue	 # type:ignore
from com.sun.star.linguistic2 import LinguServiceEvent	# type:ignore
from com.sun.star.linguistic2.LinguServiceEventFlags import SPELL_CORRECT_WORDS_AGAIN, SPELL_WRONG_WORDS_AGAIN, HYPHENATE_AGAIN, PROOFREAD_AGAIN  # type:ignore
from typing import Set, List, Tuple, Dict, Any     # flake8: noqa

class PropertyManager(unohelper.Base, XPropertyChangeListener):

	def __init__(self):
		self.__messageLanguage = "en_US"
		DivvunHandlePool.getInstance().setInstallationPath(self.__getInstallationPath())
		logging.debug("PropertyManager.__init__")
		self.__linguPropSet = None
		self.__hyphMinLeading = 2
		self.__hyphMinTrailing = 2
		self.__hyphMinWordLength = 5
		self.__hyphWordParts = False
		self.__hyphUnknownWords = True
		self.__linguEventListeners = {}	 # type: Dict[int, Any]
		try:
			dictVariant = self.readFromRegistry("/no.divvun.gramcheck.Config/dictionary", "variant")
			DivvunHandlePool.getInstance().setPreferredGlobalVariant(dictVariant)
			logging.debug("Initial dictionary variant '" + dictVariant + "'")
		except UnknownPropertyException as e:
			logging.debug("Setting initial dictionary variant to default")
			DivvunHandlePool.getInstance().setPreferredGlobalVariant("")
		self.initialize()

	def propertyChange(self, evt):
		logging.debug("PropertyManager.propertyChange")
		self.__setProperties(self.__linguPropSet)
		event = LinguServiceEvent()
		event.nEvent = SPELL_CORRECT_WORDS_AGAIN | SPELL_WRONG_WORDS_AGAIN | HYPHENATE_AGAIN | PROOFREAD_AGAIN
		self.__sendLinguEvent(event);

	def __setUiLanguage(self):
		try:
			lang = self.readFromRegistry("org.openoffice.Office.Linguistic/General", "UILocale")
			logging.debug("Specified UI locale = '" + lang + "'")
			if lang is not None and len(lang) > 0:
				self.__messageLanguage = lang
			else:
				# Use system default language
				lang = locale.getdefaultlocale()[0]
				if lang is not None:
					logging.debug("Locale language = '" + lang + "'")
					self.__messageLanguage = lang
		except UnknownPropertyException:
			logging.error("PropertyManager.initialize caught UnknownPropertyException")

	def initialize(self):
		logging.debug("PropertyManager.initialize: starting")
		self.__setUiLanguage()

		DivvunHandlePool.getInstance().setGlobalBooleanOption(PropertyManager.DIVVUN_OPT_IGNORE_DOT, True)
		DivvunHandlePool.getInstance().setGlobalBooleanOption(PropertyManager.DIVVUN_OPT_NO_UGLY_HYPHENATION, True)

		# Set these options globally until OOo bug #97945 is resolved.
		DivvunHandlePool.getInstance().setGlobalBooleanOption(PropertyManager.DIVVUN_OPT_ACCEPT_TITLES_IN_GC, True)
		DivvunHandlePool.getInstance().setGlobalBooleanOption(PropertyManager.DIVVUN_OPT_ACCEPT_BULLETED_LISTS_IN_GC, True)

		DivvunHandlePool.getInstance().setGlobalBooleanOption(PropertyManager.DIVVUN_OPT_ACCEPT_UNFINISHED_PARAGRAPHS_IN_GC, True)

		compContext = uno.getComponentContext()
		servManager = compContext.ServiceManager
		self.__linguPropSet = servManager.createInstanceWithContext("com.sun.star.linguistic2.LinguProperties", compContext)
		self.__linguPropSet.addPropertyChangeListener("IsSpellWithDigits", self)
		self.__linguPropSet.addPropertyChangeListener("IsSpellUpperCase", self)
		logging.debug("PropertyManager.initialize: property manager initalized")

		# synchronize the local settings from global preferences
		self.__setProperties(self.__linguPropSet)
		self.readDivvunSettings()
		# request that all users of linguistic services run the spellchecker and hyphenator
		# again with updated settings
		event = LinguServiceEvent()
		event.nEvent = SPELL_CORRECT_WORDS_AGAIN | SPELL_WRONG_WORDS_AGAIN | HYPHENATE_AGAIN | PROOFREAD_AGAIN
		self.__sendLinguEvent(event)

	def getHyphMinLeading(self):
		return self.__hyphMinLeading

	def getHyphMinTrailing(self):
		return self.__hyphMinTrailing

	def getHyphMinWordLength(self):
		return self.__hyphMinWordLength

	def addLinguServiceEventListener(self, xLstnr):
		logging.debug("PropertyManager.addLinguServiceEventListener")
		if id(xLstnr) in self.__linguEventListeners:
			return False
		self.__linguEventListeners[id(xLstnr)] = xLstnr
		return True

	def removeLinguServiceEventListener(self, xLstnr):
		logging.debug("PropertyManager.removeLinguServiceEventListener")
		if id(xLstnr) in self.__linguEventListeners:
			del self.__linguEventListeners[id(xLstnr)]
			return True
		return False

	def readDivvunSettings(self):
		try:
			self.__hyphWordParts = self.readFromRegistry("/no.divvun.gramcheck.Config/hyphenator", "hyphWordParts")
			self.__hyphUnknownWords = self.readFromRegistry("/no.divvun.gramcheck.Config/hyphenator", "hyphUnknownWords")
		except UnknownPropertyException as e:
			logging.exception("PropertyManager.readDivvunSettings")
		self.__syncHyphenatorSettings()

	def __getInstallationPath(self):
		dname = os.path.dirname(sys.modules[__name__].__file__)
		expectedSuffix = "pythonpath/LODivvun"
		if dname.endswith(expectedSuffix):
			dname = dname[:-len(expectedSuffix )]
			logging.debug("PropertyManager.getInstallationPath: '" + dname + "'")
			return dname
		else:
			logging.debug("PropertyManager.getInstallationPath: not using unexpect '" + dname + "'")
			return None

	def readFromRegistry(self, group, key):
		rootView = PropertyManager.getRegistryProperties(group)
		if rootView is None:
			logging.error("PropertyManager.readFromRegistry: failed to obtain rootView " + group)
			raise UnknownPropertyException()
		return rootView.getHierarchicalPropertyValue(key)

	def getMessageLanguage(self):
		return self.__messageLanguage

	def reloadDivvunSettings(self):
		divvun = DivvunHandlePool.getInstance()
		event = LinguServiceEvent()
		event.nEvent = 0
		try:
			hyphWordParts = self.readFromRegistry("/no.divvun.gramcheck.Config/hyphenator", "hyphWordParts")
			if hyphWordParts != self.__hyphWordParts:
				event.nEvent = event.nEvent | HYPHENATE_AGAIN
				self.__hyphWordParts = hyphWordParts

			hyphUnknownWords = self.readFromRegistry("/no.divvun.gramcheck.Config/hyphenator", "hyphUnknownWords")
			if hyphUnknownWords != self.__hyphUnknownWords:
				event.nEvent = event.nEvent | HYPHENATE_AGAIN
				self.__hyphUnknownWords = hyphUnknownWords

			dictVariant = self.readFromRegistry("/no.divvun.gramcheck.Config/dictionary", "variant")
			if dictVariant is None or dictVariant == "":
				dictVariant = divvun.getPreferredGlobalVariant()
			if dictVariant != divvun.getPreferredGlobalVariant():
				event.nEvent =  event.nEvent | SPELL_CORRECT_WORDS_AGAIN | SPELL_WRONG_WORDS_AGAIN | PROOFREAD_AGAIN
				divvun.setPreferredGlobalVariant(dictVariant)
		except UnknownPropertyException as e:
			logging.exception("PropertyManager.reloadDivvunSettings")
		self.__syncHyphenatorSettings()
		self.__sendLinguEvent(event)

	def __setProperties(self, properties):
		for p in ["IsSpellWithDigits", "IsSpellUpperCase", "HyphMinLeading", "HyphMinTrailing", "HyphMinWordLength"]:
			pValue = PropertyValue()
			pValue.Name = p
			try:
				pValue.Value = properties.getPropertyValue(p)
				self.setValue(pValue)
			except Exception as e:
				logging.exception("Exception setting property value '%s'", p)

	def setValues(self, values):
		for v in values:
			self.setValue(v)

	def resetValues(self, values):
		for v in values:
			globalV = PropertyValue()
			globalV.Name = v.Name
			globalV.Value = self.__linguPropSet.getPropertyValue(v.Name)
			self.setValue(globalV)

	def setValue(self, value):
		if value.Name == "IsSpellWithDigits":
			DivvunHandlePool.getInstance().setGlobalBooleanOption(PropertyManager.DIVVUN_OPT_IGNORE_NUMBERS, not value.Value)
		elif value.Name == "IsSpellUpperCase":
			DivvunHandlePool.getInstance().setGlobalBooleanOption(PropertyManager.DIVVUN_OPT_IGNORE_UPPERCASE, not value.Value)
		elif value.Name == "HyphMinLeading":
			if value.Value is not None:
				self.__hyphMinLeading = value.Value
				self.__syncHyphenatorSettings()
		elif value.Name == "HyphMinTrailing":
			if value.Value is not None:
				self.__hyphMinTrailing = value.Value
				self.__syncHyphenatorSettings()
		elif value.Name == "HyphMinWordLength":
			if value.Value is not None:
				self.__hyphMinWordLength = value.Value
				self.__syncHyphenatorSettings()

	def __syncHyphenatorSettings(self):
		if self.__hyphWordParts:
			DivvunHandlePool.getInstance().setGlobalIntegerOption(PropertyManager.DIVVUN_MIN_HYPHENATED_WORD_LENGTH, self.__hyphMinWordLength)
		else:
			DivvunHandlePool.getInstance().setGlobalIntegerOption(PropertyManager.DIVVUN_MIN_HYPHENATED_WORD_LENGTH, 2)
		DivvunHandlePool.getInstance().setGlobalBooleanOption(PropertyManager.DIVVUN_OPT_HYPHENATE_UNKNOWN_WORDS, self.__hyphUnknownWords)

	def __sendLinguEvent(self, event):
		logging.debug("PropertyManager.sendLinguEvent")
		for key, lstnr in self.__linguEventListeners.items():
			logging.debug("PropertyManager.sendLinguEvent sending event")
			lstnr.processLinguServiceEvent(event)

	@staticmethod
	def getRegistryProperties(group):
		logging.debug("PropertyManager.getRegistryProperties: " + group)
		compContext = uno.getComponentContext()
		servManager = compContext.ServiceManager
		provider = servManager.createInstanceWithContext("com.sun.star.configuration.ConfigurationProvider", compContext)
		pathArgument = PropertyValue()
		pathArgument.Name = "nodepath"
		pathArgument.Value = group
		aArguments = (pathArgument,)
		rootView = provider.createInstanceWithArguments("com.sun.star.configuration.ConfigurationUpdateAccess", aArguments)
		return rootView

	@staticmethod
	def getInstance():
		if PropertyManager.instance is None:
			PropertyManager.instance = PropertyManager()
		return PropertyManager.instance

PropertyManager.instance = None
PropertyManager.loadingFailed = False
PropertyManager.DIVVUN_OPT_IGNORE_NUMBERS = 1
PropertyManager.DIVVUN_OPT_IGNORE_UPPERCASE = 3
PropertyManager.DIVVUN_MIN_HYPHENATED_WORD_LENGTH = 9
PropertyManager.DIVVUN_OPT_HYPHENATE_UNKNOWN_WORDS = 15
PropertyManager.DIVVUN_OPT_IGNORE_DOT = 0
PropertyManager.DIVVUN_OPT_NO_UGLY_HYPHENATION = 4
PropertyManager.DIVVUN_OPT_ACCEPT_TITLES_IN_GC = 13
PropertyManager.DIVVUN_OPT_ACCEPT_BULLETED_LISTS_IN_GC = 16
PropertyManager.DIVVUN_OPT_ACCEPT_UNFINISHED_PARAGRAPHS_IN_GC = 14
