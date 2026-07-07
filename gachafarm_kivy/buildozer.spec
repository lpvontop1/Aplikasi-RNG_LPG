[app]

# ═══════════════════════════════════════════════════════════════
#  Application Metadata
# ═══════════════════════════════════════════════════════════════

# (str) Title of your application
title = GachaFarm Simulator

# (str) Package name
package.name = gachafarm

# (str) Package domain (needed for Android package: org.gachafarm.simulator)
package.domain = org.gachafarm

# (str) Source code root directory (where main.py lives)
source.dir = .

# (list) Source files to include in the APK
# shop.json WAJIB disertakan sebagai aset aplikasi
source.include_exts = py,png,jpg,kv,atlas,json,ttf

# (list) Source files to exclude
source.exclude_exts = spec,md,txt

# (list) List of directory to exclude (let buildozer auto-exclude others)
source.exclude_dirs = tests, bin, __pycache__, .git, app_data

# (list) List of exclusions using pattern matching
source.exclude_patterns = license*,README*,*_test.py,validate_*

# (str) Application versioning (manual — bump this for each release)
version = 1.0.0

# (str) Application versioning using git tag
# version.regex = initial
# version.filename = %(source.dir)s/data/version.txt

# (list) Application requirements
# Hanya Kivy dan pustaka standar Python. Tidak ada numpy / pillow / dll.
# python3 dan hostpython3 recipe sudah di-patch ke 3.12.10 (kompatibel dengan Kivy 2.3.0)
# FIX: tambah libbz2 dan liblzma agar python3 bisa build _bz2.so dan _lzma.so
# Tanpa ini, python3 configure detect bzlib.h dari system tapi cross-compile
# gagal karena header Android tidak ada → fatal error: 'bzlib.h' file not found
requirements = python3==3.12.10,kivy==2.3.0,libbz2,liblzma

# (str) Custom source folders for requirements
# Set custom source folders for requirements - this is useful when
# local development versions are needed
# requirements.source.kivy = ../../kivy

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# OSX / macOS / Cocoa Specifics
#
# author = © Copyright Name
# macos.identity = Name

#
# Android Specific
#
# (bool) Indicate if the application should be in fullscreen or not
fullscreen = 0

# (string) Presplash background color (for Android toolchain)
# Supported formats are: #RRGGBB #AARRGGBB or color names
#android.presplash_color = #FFFFFF
android.presplash_color = #07090b

# (list) Permissions
# Aplikasi ini hanya perlu akses internal storage (otomatis granted di Android 10+)
# CATATAN: Jangan biarkan kosong! buildozer akan tetap pass --permission '' ke p4a
# yang menghasilkan <uses-permission android:name="android.permission." /> INVALID
# dan menyebabkan force close di Android 12+.
# Berikan permission VALID minimal, atau comment baris ini sepenuhnya.
# VIBRATE + WRITE_EXTERNAL_STORAGE untuk crash log di /sdcard/Android/data/...
android.permissions = VIBRATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
# Android 13 (API 33) — LEBIH STABIL daripada API 34 untuk Kivy/SDL2 di Samsung Knox
# API 34 (Android 14) punya strict 16KB page alignment yang bisa crash di beberapa device
android.api = 33

# (int) Minimum API your APK will support.
# Android 7.0 (API 24) — mencakup >95% perangkat Android aktif
android.minapi = 24

# (int) Android SDK version to use
#android.sdk = 24

# (str) Android NDK version to use
# FIX: Pin ke NDK r25b (lebih stabil dari r28c untuk Kivy 2.3.0).
# NDK r28c enable FORTIFY level 3 yang sangat strict → detect use-after-free
# di SDL2 lama yang sebelumnya silent → SIGABRT.
# NDK r25b cukup stabil dan FORTIFY-nya tidak terlalu agresif.
# Catatan: kivy/__init__.py patch sudah include -Wno-error flags untuk NDK terbaru,
# tapi untuk safety kita tetap pin ke r25b yang sudah teruji luas.
android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app will support.
android.ndk_api = 24

# (bool) Use --private data storage (True) or --dir public storage (False)
# True = data tersimpan di /data/data/<pkg>/files  (PRIVATE — lebih aman)
# False = data tersimpan di /sdcard/<package>       (PUBLIC — bisa diakses file manager)
android.private_storage = True

# (str) Android NDK to use
#android.ndk_path =

# (str) Android SDK to use
#android.sdk_path =

# (str) ANT to use
#android.ant_path =

# (bool) If True, then skip trying to update the Android sdk
# This is useful if you want to avoid a slow update step.
#android.skip_update = False

# (bool) If True, then automatically accept SDK license
# agreements on CI and CI-like systems. This has no effect on
# developer machines.
# android.accept_sdk_license = False

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.kivy.android.PythonActivity

# (str) Android app theme, default is ok for Kivy-based app
# android.apptheme = "@android:style/Theme.NoTitleBar"

# (list) Pattern to whitelist for the whole project
#android.whitelist =

# (str) Path to a custom whitelist file
#android.whitelist_src =

# (str) Path to a custom blacklist file
#android.blacklist_src =

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process. Allows wildcards matching, for example:
# OUYA-ODK/libs/*.jar
#android.add_jars = foo.jar,bar.jar,path/to/jar/*

# (list) List of Java files to add to the android project (can be java or a
# directory containing the files)
#android.add_src =

# (list) Android AAR archives to add (currently works only with sdl2_gradle
# bootstrap)
#android.add_aars =

# (list) Put these files in the assets folder (don't include the prefix 'assets')
# Example: android.add_assets = assets/file.txt,assets/data.sqlite3
# PENTING: shop.json otomatis disertakan via source.include_exts = json
# jadi TIDAK perlu dideklarasikan lagi di sini.

# (list) Put these jar files in the libs folder (don't include the prefix 'libs')
#android.add_libs =

# (list) Gradle dependencies to add (currently works only with sdl2_gradle
# bootstrap)
#android.gradle_dependencies =

# (bool) Enable AndroidX support. Enable when 'android.gradle_dependencies'
# contains an AndroidX dependency.
#android.enable_androidx = True

# (list) add java compile options
# this can for example be necessary when using certain java libraries
#android.add_compile_options = "sourceCompatibility = 1.8", "targetCompatibility = 1.8"


# (list) Gradle repositories to add {can be necessary for some android.gradle_dependencies}
#android.add_gradle_repositories =

# (list) packaging options to add
# see https://google.github.io/android-gradle-dsl/current/com.android.build.gradle.internal.api.AndroidProjectOptions.html
#android.add_packaging_options = "exclude 'META-INF/common.kotlin_module'", "exclude 'META-INF/*.kotlin_module'"

# (list) Java classes to add as activities to the manifest.
#android.add_activities = com.example.ExampleActivity

# (str) OUYA Console category. Should be one of GAME or APP
#android.ouya.category = GAME

# (str) Filename of OUYA Console icon. It must be a 732x412 png image.
#android.ouya.icon.filename = %(source.dir)s/data/ouya_icon.png

# (str) XML file to include as an intent filters in <activity> tag
#android.manifest.intent_filters =

# (str) launchMode to set for the main activity
# CRITICAL FIX: singleTask mencegah multiple instance activity.
# Tanpa ini, user tap ikon beberapa kali → beberapa instance PythonActivity
# hidup bersamaan → SDL2 mutex di-destroy instance lama tapi masih diakses
# instance baru → FORTIFY: pthread_mutex_lock on destroyed mutex → SIGABRT.
# Log ADB menunjukkan 4 instance dibuat dalam 21 detik (PID 28514→28729→28780→28817).
android.manifest.launch_mode = singleTask

# (list) Android additional meta data to add into the manifest
#android.add_meta_data = logo@drawable/logo=true

# (list) Android library to use, currently only "SDL2" is supported
# bootstrap: sdl2 — default, mendukung semua fitur Kivy
p4a.bootstrap = sdl2
android.bootstrap = sdl2

# (str) meta-data androis:versionCode
android.numeric_version = 1

# (bool) enables Android auto-backup feature (Android >= 6.0)
# allows to backup the app's data (json custom shop file akan ikut ter-backup)
android.allow_backup = True

# (str) XML file for custom backup rules (Android >= 7.0)
#android.backup_rules =

# (str) XML file for custom full backup content (Android >= 7.0)
#android.full_backup_content =

#
# Python for Android (p4a) Specifics
#
# (str) python-for-android fork to use, defaults to upstream (kivy)
#p4a.fork = kivy

# (str) python-for-android branch to use, defaults to master
#p4a.branch = master

# (str) python-for-android git clone directory (if empty, it will be
# automatically cloned from github)
# FIX: Gunakan p4a yang sudah di-patch (python3 3.12.10, hostpython3 3.12.10,
# kivy CFLAGS relax, build.py skip pip install -U, PythonActivity.java fix).
# Tanpa ini, buildozer akan git fetch + reset --hard origin/master yang
# menghapus semua patches.
p4a.source_dir = /home/z/my-project/build/p4a_patched

# (str) The directory in which python-for-android should look for your own
# build recipes (if any)
#p4a.local_recipes =

# (str) Filename to the hook for p4a
#p4a.hook =

# (str) Bootstrap to use for android builds
# p4a.bootstrap = sdl2

# (int) port number to specify an explicit --port= p4a argument (eg for bootstrap
# flask)
#p4a.port =

# Control passing the --use-setup-py vs --ignore-setup-py to p4a
# This controls whether or not you want to use the setup.py
# In the future, this will be required to be True.
# p4a.setup_py = False


#
# iOS Specifics
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios
# Alternately, specify the URL and branch of a git checkout:
#ios.kivy_ios_url = https://github.com/kivy/kivy-ios
#ios.kivy_ios_branch = master

# Another platform dependency: ios-deploy
#ios.ios_deploy_dir = ../ios_deploy
#ios.ios_deploy_url = https://github.com/phonegap/ios-deploy

# (str) Name of the certificate to use for signing the debug version
# Get a list of available identities: buildozer ios list_identities
#ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"

# (str) Name of the certificate to use for signing the release version
#ios.codesign.release = %(ios.codesign.debug)s


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0

# (bool) Automatically accept SDK license agreements
android.accept_sdk_license = True

# (str) Path to build artifact storage, ie. .apk, .ipa files
# Default: bin/
# bin_dir = ./bin

# (str) List of source files to include in the source release
# source.include_exts = py,png,jpg,kv,atlas,json,ttf

# (str) Path to a custom template for the buildozer.spec file
# template = buildozer.spec.template
