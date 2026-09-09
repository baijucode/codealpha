[app]
title = Language Translator
package.name = translator
package.domain = org.codealpha

source.dir = .
source.main = Mobile_app.py
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

requirements = python3,kivy,requests,urllib3,certifi,charset-normalizer,idna,deep-translator,beautifulsoup4,soupsieve,gTTS,click

orientation = portrait

android.permissions = INTERNET

[buildozer]
log_level = 2
