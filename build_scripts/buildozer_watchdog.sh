#!/bin/bash
# Watchdog build script with proper libtool + aclocal support
# CFLAGS relax hanya di-set di level kivy recipe (bukan global) agar hostpython3 tetap compile
cd /home/z/my-project/gachafarm/gachafarm_kivy

# Environment setup
export JAVA_HOME=/home/z/jdk/jdk-17.0.13+11
export ANDROID_HOME=/home/z/.buildozer/android/platform/android-sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export ANDROID_NDK_HOME=/home/z/.buildozer/android/platform/android-ndk-r28c
export MAKEFLAGS="-j2"
export BUILDOZER_WARN_ON_ROOT=0
export PYTHONUNBUFFERED=1

# Add user-local paths FIRST so wrappers are picked up
export PATH=/home/z/.local/bin:$JAVA_HOME/bin:$PATH
export ACLOCAL_PATH=/home/z/.local/share/aclocal:/usr/share/aclocal
export LIBTOOLIZE=/home/z/.local/bin/libtoolize

# NOTE: TIDAK set CFLAGS/CXXFLAGS global - itu akan menyebabkan hostpython3 configure gagal
# Kivy-specific CFLAGS sudah di-set di recipe kivy/__init__.py (get_recipe_env)

LOGFILE=/home/z/my-project/scripts/buildozer_build.log
echo "=== Build started at $(date) ===" > "$LOGFILE"
echo "JAVA_HOME: $JAVA_HOME" >> "$LOGFILE"
echo "ACLOCAL_PATH: $ACLOCAL_PATH" >> "$LOGFILE"
echo "PATH: $PATH" >> "$LOGFILE"
echo "which aclocal: $(which aclocal)" >> "$LOGFILE"
echo "which libtoolize: $(which libtoolize)" >> "$LOGFILE"
echo "===================================" >> "$LOGFILE"

# Start buildozer
/home/z/.venv/bin/buildozer android debug >> "$LOGFILE" 2>&1 &
BUILDOZER_PID=$!
echo "Buildozer PID: $BUILDOZER_PID" >> "$LOGFILE"

# Watchdog
while kill -0 $BUILDOZER_PID 2>/dev/null; do
    date > /home/z/my-project/scripts/buildozer_alive
    sleep 5
done

wait $BUILDOZER_PID
EXIT_CODE=$?
echo "=== Buildozer exit code: $EXIT_CODE ===" >> "$LOGFILE"
echo "=== Build finished at $(date) ===" >> "$LOGFILE"

# Copy APK if exists
APK_FILE=$(ls -t /home/z/my-project/gachafarm/gachafarm_kivy/bin/*.apk 2>/dev/null | head -1)
if [ -n "$APK_FILE" ]; then
    cp "$APK_FILE" /home/z/my-project/download/
    echo "=== APK copied to /home/z/my-project/download/ ===" >> "$LOGFILE"
    ls -lh /home/z/my-project/download/*.apk >> "$LOGFILE"
fi

date > /home/z/my-project/scripts/buildozer_done
