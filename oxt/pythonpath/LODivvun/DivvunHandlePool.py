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
import os
import platform
from collections import defaultdict
from threading import RLock
from com.sun.star.lang import Locale

try:
	from typing import Set, List, Tuple, Dict, Any     # flake8: noqa
except ImportError:
	pass

import libdivvun

class Bcp47ToLoMapping:

	def __init__(self, bcpTag, loLanguage, loRegion):
		self.bcpTag = bcpTag
		self.loLanguage = loLanguage
		self.loRegion = loRegion

# This list should contain all the languages that either
# 1) need to be mapped from BCP 47 tag to legacy LibreOffice locale
# OR
# 2) where a speller without country code should also be used for
#    checking text that has language and some specific country specified
BCP_TO_LO_MAPPING = [
	Bcp47ToLoMapping("af",	"af",	"NA"), \
	Bcp47ToLoMapping("af",	"af",	"ZA"), \
	Bcp47ToLoMapping("alq",	"alq",	"CA"), \
	Bcp47ToLoMapping("am",	"am",	"ET"), \
	Bcp47ToLoMapping("an",	"an",	"ES"), \
	Bcp47ToLoMapping("ar",	"ar",	"AE"), \
	Bcp47ToLoMapping("ar",	"ar",	"BH"), \
	Bcp47ToLoMapping("ar",	"ar",	"DJ"), \
	Bcp47ToLoMapping("ar",	"ar",	"DZ"), \
	Bcp47ToLoMapping("ar",	"ar",	"EG"), \
	Bcp47ToLoMapping("ar",	"ar",	"ER"), \
	Bcp47ToLoMapping("ar",	"ar",	"IL"), \
	Bcp47ToLoMapping("ar",	"ar",	"IQ"), \
	Bcp47ToLoMapping("ar",	"ar",	"JO"), \
	Bcp47ToLoMapping("ar",	"ar",	"KM"), \
	Bcp47ToLoMapping("ar",	"ar",	"KW"), \
	Bcp47ToLoMapping("ar",	"ar",	"LB"), \
	Bcp47ToLoMapping("ar",	"ar",	"LY"), \
	Bcp47ToLoMapping("ar",	"ar",	"MA"), \
	Bcp47ToLoMapping("ar",	"ar",	"MR"), \
	Bcp47ToLoMapping("ar",	"ar",	"OM"), \
	Bcp47ToLoMapping("ar",	"ar",	"PS"), \
	Bcp47ToLoMapping("ar",	"ar",	"QA"), \
	Bcp47ToLoMapping("ar",	"ar",	"SA"), \
	Bcp47ToLoMapping("ar",	"ar",	"SD"), \
	Bcp47ToLoMapping("ar",	"ar",	"SO"), \
	Bcp47ToLoMapping("ar",	"ar",	"SY"), \
	Bcp47ToLoMapping("ar",	"ar",	"TD"), \
	Bcp47ToLoMapping("ar",	"ar",	"TN"), \
	Bcp47ToLoMapping("ar",	"ar",	"YE"), \
	Bcp47ToLoMapping("as",	"as",	"IN"), \
	Bcp47ToLoMapping("as-BT",	"as",	"BT"), \
	Bcp47ToLoMapping("ast",	"ast",	"ES"), \
	Bcp47ToLoMapping("atj",	"atj",	"CA"), \
	Bcp47ToLoMapping("av",	"av",	"RU"), \
	Bcp47ToLoMapping("av-AZ",	"av",	"AZ"), \
	Bcp47ToLoMapping("av-GE",	"av",	"GE"), \
	Bcp47ToLoMapping("av-KZ",	"av",	"KZ"), \
	Bcp47ToLoMapping("azj",	"azj",	"AZ"), \
	Bcp47ToLoMapping("azj-RU",	"azj",	"RU"), \
	Bcp47ToLoMapping("bak",	"bak",	"RU"), \
	Bcp47ToLoMapping("bak-KZ",	"bak",	"KZ"), \
	Bcp47ToLoMapping("be",	"be",	"BY"), \
	Bcp47ToLoMapping("bg",	"bg",	"BG"), \
	Bcp47ToLoMapping("bla",	"bla",	"CA"), \
	Bcp47ToLoMapping("bla-US",	"bla",	"US"), \
	Bcp47ToLoMapping("bn",	"bn",	"BD"), \
	Bcp47ToLoMapping("bn",	"bn",	"IN"), \
	Bcp47ToLoMapping("br",	"br",	"FR"), \
	Bcp47ToLoMapping("bxr",	"bxr",	"RU"), \
	Bcp47ToLoMapping("ca",	"ca",	"AD"), \
	Bcp47ToLoMapping("ca",	"ca",	"ES"), \
	Bcp47ToLoMapping("ce",	"ce",	"RU"), \
	Bcp47ToLoMapping("ceb",	"ceb",	"PH"), \
	Bcp47ToLoMapping("chp",	"chp",	"CA"), \
	Bcp47ToLoMapping("chr",	"chr",	"US"), \
	Bcp47ToLoMapping("ciw",	"ciw",	"US"), \
	Bcp47ToLoMapping("cos",	"cos",	"FR"), \
	Bcp47ToLoMapping("crj",	"crj",	"CA"), \
	Bcp47ToLoMapping("crk",	"crk",	"CA"), \
	Bcp47ToLoMapping("crk-US",	"crk",	"US"), \
	Bcp47ToLoMapping("crl",	"crl",	"CA"), \
	Bcp47ToLoMapping("crm",	"crm",	"CA"), \
	Bcp47ToLoMapping("cs",	"cs",	"CZ"), \
	Bcp47ToLoMapping("csb",	"csb",	"PL"), \
	Bcp47ToLoMapping("csw",	"csw",	"CA"), \
	Bcp47ToLoMapping("cv",	"cv",	"RU"), \
	Bcp47ToLoMapping("cwd",	"cwd",	"CA"), \
	Bcp47ToLoMapping("cy",	"cy",	"GB"), \
	Bcp47ToLoMapping("da",	"da",	"DK"), \
	Bcp47ToLoMapping("de",	"de",	"DE"), \
	Bcp47ToLoMapping("de-AT",	"de",	"AT"), \
	Bcp47ToLoMapping("de-BE",	"de",	"BE"), \
	Bcp47ToLoMapping("de-CH",	"de",	"CH"), \
	Bcp47ToLoMapping("de-LU",	"de",	"LU"), \
	Bcp47ToLoMapping("dsb",	"dsb",	"DE"), \
	Bcp47ToLoMapping("el",	"el",	"GR"), \
	Bcp47ToLoMapping("en-US",	"en",	"US"), \
	Bcp47ToLoMapping("en-US",	"en",	"ZA"), \
	Bcp47ToLoMapping("eo",	"eo",	""), \
	Bcp47ToLoMapping("es",	"es",	"ES"), \
	Bcp47ToLoMapping("es-MX",	"es",	"MX"), \
	Bcp47ToLoMapping("et",	"et",	"EE"), \
	Bcp47ToLoMapping("eu",	"eu",	""), \
	Bcp47ToLoMapping("eve",	"eve",	"RU"), \
	Bcp47ToLoMapping("evn",	"evn",	"CN"), \
	Bcp47ToLoMapping("evn-RU",	"evn",	"RU"), \
	Bcp47ToLoMapping("fa",	"fa",	"IR"), \
	Bcp47ToLoMapping("fi",	"fi",	"FI"), \
	Bcp47ToLoMapping("fkv",	"fkv",	"NO"), \
	Bcp47ToLoMapping("fo",	"fo",	"FO"), \
	Bcp47ToLoMapping("fr",	"fr",	"FR"), \
	Bcp47ToLoMapping("fr-BE",	"fr",	"BE"), \
	Bcp47ToLoMapping("fr-CA",	"fr",	"CA"), \
	Bcp47ToLoMapping("fr-CH",	"fr",	"CH"), \
	Bcp47ToLoMapping("fr-LU",	"fr",	"LU"), \
	Bcp47ToLoMapping("fr-MC",	"fr",	"MC"), \
	Bcp47ToLoMapping("fry",	"fry",	"NL"), \
	Bcp47ToLoMapping("fur",	"fur",	"IT"), \
	Bcp47ToLoMapping("fy",	"fy",	"NL"), \
	Bcp47ToLoMapping("ga",	"ga",	"IE"), \
	Bcp47ToLoMapping("gd",	"gd",	"GB"), \
	Bcp47ToLoMapping("gl",	"gl",	"ES"), \
	Bcp47ToLoMapping("glk",	"glk",	"IR"), \
	Bcp47ToLoMapping("gn",	"gug",	"PY"), \
	Bcp47ToLoMapping("grn",	"grn",	"PY"), \
	Bcp47ToLoMapping("gu",	"gu",	"IN"), \
	Bcp47ToLoMapping("guc",	"guc",	"CO"), \
	Bcp47ToLoMapping("guc-VE",	"guc",	"VE"), \
	Bcp47ToLoMapping("gv",	"gv",	"IM"), \
	Bcp47ToLoMapping("hax",	"hax",	"CA"), \
	Bcp47ToLoMapping("hdn",	"hdn",	"CA"), \
	Bcp47ToLoMapping("hdn-US",	"hdn",	"US"), \
	Bcp47ToLoMapping("he",	"he",	"IL"), \
	Bcp47ToLoMapping("hi",	"hi",	"IN"), \
	Bcp47ToLoMapping("hr",	"hr",	"BA"), \
	Bcp47ToLoMapping("hr",	"hr",	"HR"), \
	Bcp47ToLoMapping("hsb",	"hsb",	"DE"), \
	Bcp47ToLoMapping("hu",	"hu",	"HU"), \
	Bcp47ToLoMapping("hy",	"hy",	"AM"), \
	Bcp47ToLoMapping("ia",	"ia",	""), \
	Bcp47ToLoMapping("id",	"id",	"ID"), \
	Bcp47ToLoMapping("ik",	"ik",	"US"), \
	Bcp47ToLoMapping("is",	"is",	"IS"), \
	Bcp47ToLoMapping("it",	"it",	"CH"), \
	Bcp47ToLoMapping("it",	"it",	"IT"), \
	Bcp47ToLoMapping("izh",	"izh",	"RU"), \
	Bcp47ToLoMapping("kaa",	"kaa",	"UZ"), \
	Bcp47ToLoMapping("kaa-RU",	"kaa",	"RU"), \
	Bcp47ToLoMapping("kaz",	"kaz",	"KZ"), \
	Bcp47ToLoMapping("kca",	"kca",	"RU"), \
	Bcp47ToLoMapping("khk",	"khk",	"MN"), \
	Bcp47ToLoMapping("khk-CN",	"khk",	"CN"), \
	Bcp47ToLoMapping("khk-KG",	"khk",	"KG"), \
	Bcp47ToLoMapping("khk-RU",	"khk",	"RU"), \
	Bcp47ToLoMapping("kk",	"kk",	"KZ"), \
	Bcp47ToLoMapping("kl",	"kl",	"GL"), \
	Bcp47ToLoMapping("koi",	"koi",	"RU"), \
	Bcp47ToLoMapping("kpv",	"kpv",	"RU"), \
	Bcp47ToLoMapping("ku",	"ku",	"SY"), \
	Bcp47ToLoMapping("ku",	"ku",	"TR"), \
	Bcp47ToLoMapping("kum",	"kum",	"RU"), \
	Bcp47ToLoMapping("kw",	"kw",	"UK"), \
	Bcp47ToLoMapping("ky",	"ky",	"CN"), \
	Bcp47ToLoMapping("ky",	"ky",	"KG"), \
	Bcp47ToLoMapping("la",	"la",	"VA"), \
	Bcp47ToLoMapping("liv",	"liv",	"LV"), \
	Bcp47ToLoMapping("liv",	"liv",	"RU"), \
	Bcp47ToLoMapping("ln",	"ln",	"CD"), \
	Bcp47ToLoMapping("lt",	"lt",	"LT"), \
	Bcp47ToLoMapping("ltz",	"ltz",	"LU"), \
	Bcp47ToLoMapping("lv",	"lv",	"LV"), \
	Bcp47ToLoMapping("mdf",	"mdf",	"RU"), \
	Bcp47ToLoMapping("mhr",	"mhr",	"RU"), \
	Bcp47ToLoMapping("mis",	"mis",	"XX"), \
	Bcp47ToLoMapping("mk",	"mk",	"MK"), \
	Bcp47ToLoMapping("ml",	"ml",	"IN"), \
	Bcp47ToLoMapping("ml",	"ml",	"IN"), \
	Bcp47ToLoMapping("moe",	"moe",	"CA"), \
	Bcp47ToLoMapping("mr",	"mr",	"IN"), \
	Bcp47ToLoMapping("mrj",	"mrj",	"RU"), \
	Bcp47ToLoMapping("ms",	"ms",	""), \
	Bcp47ToLoMapping("ms",	"ms",	"BN"), \
	Bcp47ToLoMapping("ms",	"ms",	"MY"), \
	Bcp47ToLoMapping("mt",	"mt",	"MT"), \
	Bcp47ToLoMapping("myv",	"myv",	"RU"), \
	Bcp47ToLoMapping("nb",	"nb",	"NO"), \
	Bcp47ToLoMapping("ndl",	"ndl",	"CD"), \
	Bcp47ToLoMapping("ne",	"ne",	"IN"), \
	Bcp47ToLoMapping("ne",	"ne",	"NP"), \
	Bcp47ToLoMapping("nio",	"nio",	"RU"), \
	Bcp47ToLoMapping("nl",	"nl",	"BE"), \
	Bcp47ToLoMapping("nl",	"nl",	"NL"), \
	Bcp47ToLoMapping("nn",	"nn",	"NO"), \
	Bcp47ToLoMapping("nog",	"nog",	"RU"), \
	Bcp47ToLoMapping("nr",	"nr",	"ZA"), \
	Bcp47ToLoMapping("nsk",	"nsk",	"CA"), \
	Bcp47ToLoMapping("nso",	"ns",	"ZA"), \
	Bcp47ToLoMapping("nso",	"nso",	"ZA"), \
	Bcp47ToLoMapping("ny",	"ny",	"MW"), \
	Bcp47ToLoMapping("oc",	"oc",	"FR"), \
	Bcp47ToLoMapping("ojb",	"ojb",	"CA"), \
	Bcp47ToLoMapping("ojc",	"ojc",	"CA"), \
	Bcp47ToLoMapping("ojg",	"ojg",	"CA"), \
	Bcp47ToLoMapping("ojs",	"ojs",	"CA"), \
	Bcp47ToLoMapping("ojw",	"ojw",	"CA"), \
	Bcp47ToLoMapping("olo",	"olo",	"RU"), \
	Bcp47ToLoMapping("or",	"or",	"IN"), \
	Bcp47ToLoMapping("otw",	"otw",	"CA"), \
	Bcp47ToLoMapping("pa",	"pa",	"IN"), \
	Bcp47ToLoMapping("pa",	"pa",	"PK"), \
	Bcp47ToLoMapping("pap-BQ",	"pap",	"BQ"), \
	Bcp47ToLoMapping("pap-CW",	"pap",	"CW"), \
	Bcp47ToLoMapping("pjt",	"pjt",	"AU"), \
	Bcp47ToLoMapping("pl",	"pl",	"PL"), \
	Bcp47ToLoMapping("pt",	"pt",	"PT"), \
	Bcp47ToLoMapping("pt-BR",	"pt",	"BR"), \
	Bcp47ToLoMapping("qu",	"qu",	"BO"), \
	Bcp47ToLoMapping("qu",	"qu",	"EC"), \
	Bcp47ToLoMapping("qu",	"qu",	"PE"), \
	Bcp47ToLoMapping("quz",	"quz",	"PE"), \
	Bcp47ToLoMapping("qve",	"qve",	"PE"), \
	Bcp47ToLoMapping("ro",	"ro",	"MD"), \
	Bcp47ToLoMapping("ro",	"ro",	"RO"), \
	Bcp47ToLoMapping("ru",	"ru",	"RU"), \
	Bcp47ToLoMapping("rup",	"rup",	"MK"), \
	Bcp47ToLoMapping("rup-GR",	"rup",	"GR"), \
	Bcp47ToLoMapping("rup-RO",	"rup",	"RO"), \
	Bcp47ToLoMapping("rw",	"rw",	"RW"), \
	Bcp47ToLoMapping("sc",	"sc",	"IT"), \
	Bcp47ToLoMapping("se",	"se",	"FI"), \
	Bcp47ToLoMapping("se",	"se",	"NO"), \
	Bcp47ToLoMapping("se",	"se",	"SE"), \
	Bcp47ToLoMapping("sel",	"sel",	"RU"), \
	Bcp47ToLoMapping("si",	"si",	"LK"), \
	Bcp47ToLoMapping("sid",	"sid",	"ET"), \
	Bcp47ToLoMapping("sjd",	"sjd",	"RU"), \
	Bcp47ToLoMapping("sje",	"sje",	"SE"), \
	Bcp47ToLoMapping("sk",	"sk",	"SK"), \
	Bcp47ToLoMapping("sl",	"sl",	"SI"), \
	Bcp47ToLoMapping("sma",	"sma",	"NO"), \
	Bcp47ToLoMapping("sma",	"sma",	"SE"), \
	Bcp47ToLoMapping("smj",	"smj",	"NO"), \
	Bcp47ToLoMapping("smj",	"smj",	"SE"), \
	Bcp47ToLoMapping("smn",	"smn",	"FI"), \
	Bcp47ToLoMapping("sms",	"sms",	"FI"), \
	Bcp47ToLoMapping("so",	"so",	"SO"), \
	Bcp47ToLoMapping("sq",	"sq",	"AL"), \
	Bcp47ToLoMapping("srs",	"srs",	"CA"), \
	Bcp47ToLoMapping("ss",	"ss",	"ZA"), \
	Bcp47ToLoMapping("st",	"st",	"ZA"), \
	Bcp47ToLoMapping("sto",	"sto",	"CA"), \
	Bcp47ToLoMapping("sv",	"sv",	"FI"), \
	Bcp47ToLoMapping("sv",	"sv",	"SE"), \
	Bcp47ToLoMapping("sw",	"sw",	"KE"), \
	Bcp47ToLoMapping("sw",	"sw",	"TZ"), \
	Bcp47ToLoMapping("ta",	"ta",	"IN"), \
	Bcp47ToLoMapping("tau",	"tau",	"US"), \
	Bcp47ToLoMapping("te",	"te",	"IN"), \
	Bcp47ToLoMapping("tet",	"tet",	"ID"), \
	Bcp47ToLoMapping("tet",	"tet",	"TL"), \
	Bcp47ToLoMapping("tg",	"tg",	"TJ"), \
	Bcp47ToLoMapping("tg-UZ",	"tg",	"UZ"), \
	Bcp47ToLoMapping("tk",	"tk",	"TM"), \
	Bcp47ToLoMapping("tku",	"tku",	"MX"), \
	Bcp47ToLoMapping("tl",	"tl",	"PH"), \
	Bcp47ToLoMapping("tl",	"tl",	"PH"), \
	Bcp47ToLoMapping("tn",	"tn",	"BW"), \
	Bcp47ToLoMapping("tn",	"tn",	"ZA"), \
	Bcp47ToLoMapping("ts",	"ts",	"ZA"), \
	Bcp47ToLoMapping("tt",	"tt",	"RU"), \
	Bcp47ToLoMapping("tus",	"tus",	"CA"), \
	Bcp47ToLoMapping("tyv",	"tyv",	"RU"), \
	Bcp47ToLoMapping("udm",	"udm",	"RU"), \
	Bcp47ToLoMapping("uk",	"uk",	"UA"), \
	Bcp47ToLoMapping("ur",	"ur",	"PK"), \
	Bcp47ToLoMapping("uz",	"uz",	"UZ"), \
	Bcp47ToLoMapping("uz-KG",	"uz",	"KG"), \
	Bcp47ToLoMapping("vep",	"vep",	"RU"), \
	Bcp47ToLoMapping("vi",	"vi",	"VN"), \
	Bcp47ToLoMapping("vro",	"vro",	"EE"), \
	Bcp47ToLoMapping("xh",	"xh",	"ZA"), \
	Bcp47ToLoMapping("yrk",	"yrk",	"RU"), \
	Bcp47ToLoMapping("zu",	"zu",	"ZA"), \
	Bcp47ToLoMapping("zu-LS",	"zu",	"LS"), \
	Bcp47ToLoMapping("zu-SZ",	"zu",	"SZ")
]

# This list should contain language codes that should be used for checking
# text without country code even when the language is listed in BCP_TO_LO_MAPPING
BCP_ADVERTISE_WITHOUT_COUNTRY = [
	"alq",
	"atj",
	"chr",
	"crj",
	"crl",
	"crm",
	"csw",
	"cwd",
	"hax",
	"mis",
	"moe",
	"nsk",
	"ojb",
	"ojc",
	"ojg",
	"ojs",
	"ojw",
	"srs",
	"sto",
	"tau"
]

class DivvunHandlePool:
	instance = None
	mutex = RLock()

	def __init__(self):
		self.__supportedSpellingLocales = []         # type: List[Locale]
		self.__supportedHyphenationLocales = []      # type: List[Locale]
		self.__supportedGrammarCheckingLocales = []  # type: List[Locale]
		self.__installationPath = None
		self.__handles = {}  # type: List[libdivvun.CheckerUniquePtr]
		self.__initializationErrors = {}
		self.__globalBooleanOptions = {}
		self.__globalIntegerOptions = {}
		self.__preferredGlobalVariant = None
		self.__bcpToOOoMap = defaultdict(list)
		for m in BCP_TO_LO_MAPPING:
			self.__bcpToOOoMap[m.bcpTag].append(m)
		self.__bcpAdvertiseWithoutCountry = set(BCP_ADVERTISE_WITHOUT_COUNTRY)

	@classmethod
	def getInstance(cls):
		if DivvunHandlePool.instance is None:
			DivvunHandlePool.instance = DivvunHandlePool()
		return DivvunHandlePool.instance

	def getInstallationPath(self):
		return self.__installationPath

	def getDictionaryPath(self):
		return os.path.join(self.getInstallationPath(), "divvun")

	def __openHandleWithVariant(self, language, fullVariant):
		logging.debug("DivvunHandlePool.__openHandleWithVariant")
		try:
			extraPath = self.getDictionaryPath()
			logging.info("Listing langs including getDictionaryPath={}".format(extraPath))
			allLangs = libdivvun.listLangs(extraPath)
			logging.info("Found {} languages: {}".format(len(allLangs), allLangs.keys()))
			if not language in allLangs:
				msg = "Couldn't find data for language {}".format(language)
				logging.info(msg)
				raise Exception(msg)
			# We assume the first matching spec for a language is the preferred (e.g. from user dir)
			logging.info("len: {}".format(len(allLangs[language])))
			specpath = allLangs[language][0]
			logging.info("specpath="+specpath)
			logging.info("Loading language {} with spec from {}".format(language, specpath))
			# TODO: Any reason to support non-archive specs here?
			spec = libdivvun.ArCheckerSpec(specpath)
			# TODO: Use preferences
			pipename = spec.defaultPipe()
			verbose = True
			divvunHandle = spec.getChecker(pipename, verbose)
			self.__handles[language] = divvunHandle
			for booleanOpt, booleanValue in self.__globalBooleanOptions.items():
				pass
				# divvunHandle.setBooleanOption(booleanOpt, booleanValue)
			for integerOpt, integerValue in self.__globalIntegerOptions.items():
				# divvunHandle.setIntegerOption(integerOpt, integerValue)
				pass
			return divvunHandle;
		except Exception as e:
			self.__initializationErrors[language] = e.args[0]
			return None

	def __openHandle(self, language):
		if self.__preferredGlobalVariant is not None:
			languageWithVariant = language + "-x-" + self.__preferredGlobalVariant
			handle = self.__openHandleWithVariant(language, languageWithVariant)
			if handle is not None:
				return handle
		return self.__openHandleWithVariant(language, language)

	def getOpenHandles(self):
		return self.__handles

	def getHandle(self, locale):
		language = None
		if locale.Language == "qlt":
			language = locale.Variant
		else:
			language = locale.Language
		if language in self.__handles:
			return self.__handles[language]
		if language in self.__initializationErrors:
			return None
		return self.__openHandle(language)

	def closeAllHandles(self):
		for key, value in self.__handles.items():
			value.terminate()
		self.__handles.clear()
		self.__initializationErrors.clear()

	def setGlobalBooleanOption(self, option, value):
		if option in self.__globalBooleanOptions and self.__globalBooleanOptions[option] == value:
			return
		self.__globalBooleanOptions[option] = value
		for lang, handle in self.__handles.items():
			handle.setBooleanOption(option, value)

	def setGlobalIntegerOption(self, option, value):
		if option in self.__globalIntegerOptions and self.__globalIntegerOptions[option] == value:
			return
		self.__globalIntegerOptions[option] = value
		for lang, handle in self.__handles.items():
			handle.setIntegerOption(option, value)

	def __addLocale(self, locales, language):
		matchingMappings = self.__bcpToOOoMap[language]
		for bcpMapping in matchingMappings:
			locales.append(Locale(bcpMapping.loLanguage, bcpMapping.loRegion, ""))
		if language in self.__bcpAdvertiseWithoutCountry:
			locales.append(Locale(language, "", ""))
			return
		if len(matchingMappings) == 0:
			if len(language) <= 3:
				# assume this is ISO 639-1 or ISO 639-3 code
				locales.append(Locale(language, "", ""))
			else:
				locales.append(Locale("qlt", "", language))

	def __getSupportedLocalesForOperation(self, localeList, localeOperation):
		# optimization: if we already have found some locales, don't search for more
		if len(localeList) == 0:
			logging.info("dictionary path %s", self.getDictionaryPath())
			languages = localeOperation(self.getDictionaryPath())
			for lang in languages:
				self.__addLocale(localeList, lang)
		return tuple(localeList)

	def getSupportedSpellingLocales(self):
		def listLangs(path):  # TODO: get from libdivvun? Need function to check for pure speller pipelines though.
			return []
		res = self.__getSupportedLocalesForOperation(self.__supportedSpellingLocales, listLangs)
		logging.info("supported spelling locales: %s", res)
		return res

	def getSupportedHyphenationLocales(self):
		def listLangs(path):  # TODO: get from libdivvun? We don't do plain hyphenation though, might not make sense.
			return []
		res = self.__getSupportedLocalesForOperation(self.__supportedHyphenationLocales, listLangs)
		logging.info("supported hyphenation locales: %s", res)
		return res

	def getSupportedGrammarLocales(self):
		res = self.__getSupportedLocalesForOperation(self.__supportedGrammarCheckingLocales, libdivvun.listLangs)
		logging.info("supported gc locales: %s", res)
		return res

	def getInitializationStatus(self):
		"""Returns initialization status diagnostics"""
		status = "Init OK:["
		for key, value in self.__handles.items():
			status = status + key + " "
		status = status + "] FAILED:["
		for key, value in self.__initializationErrors.items():
			status = status + key + ":'" + value + "' "
		status = status + "]"
		return status

	def setPreferredGlobalVariant(self, variant):
		if variant != self.__preferredGlobalVariant:
			self.__preferredGlobalVariant = variant
			self.closeAllHandles()

	def setInstallationPath(self, path):
		self.__installationPath = path
		if path is None:
			logging.debug("DivvunHandlePool.setInstallationPath(None)")
		else:
			searchPath = os.path.join(path, "divvun", platform.system() + "-" + "-".join(platform.architecture()))
			logging.debug("DivvunHandlePool.setInstallationPath: library search path is " + searchPath)
			# We do this here in the extension instead, in LO.LibLoad.loadLibs:
			# libdivvun.setLibrarySearchPath(searchPath)

	def getPreferredGlobalVariant(self):
		return self.__preferredGlobalVariant

	def __containsLocale(self, localeToFind, locales):
		for locale in locales:
			if locale.Language == localeToFind.Language and locale.Country == localeToFind.Country:
				return True
			if locale.Language == "qlt" and \
			   (locale.Variant == localeToFind.Language or (localeToFind.Language == "qlt" and locale.Variant == localeToFind.Variant)):
				return True
		if localeToFind.Language == "qlt":
			# See if we can try again with a trimmed tag: some tags may contain extra
			# components that can be skipped while matching such as country in crk-Cans-CN
			tagToFind = localeToFind.Variant
			tagLen = len(tagToFind)
			if tagLen > 9 and tagToFind[tagLen - 3] == "-":
				loc = Locale("qlt", "", tagToFind[0:-3])
				return self.__containsLocale(loc, locales)
		return False

	def supportsSpellingLocale(self, locale):
		return self.__containsLocale(locale, self.getSupportedSpellingLocales())

	def supportsHyphenationLocale(self, locale):
		return self.__containsLocale(locale, self.getSupportedHyphenationLocales())

	def supportsGrammarLocale(self, locale):
		return self.__containsLocale(locale, self.getSupportedGrammarLocales())

