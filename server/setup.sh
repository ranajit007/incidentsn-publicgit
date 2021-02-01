#!/bin/bash
CURRENT_DIR=`pwd`
#go to path
cd /app/server/flaskr/
echo " ---> CUSTOM INSTALL..."
#download firefox driver
echo "      1. Getting Gecko Driver..."
wget --no-verbose --quiet https://github.com/mozilla/geckodriver/releases/download/v0.27.0/geckodriver-v0.27.0-linux64.tar.gz > /dev/null
tar -xvzf geckodriver-v0.27.0-linux64.tar.gz > /dev/null
chmod +x geckodriver > /dev/null
rm geckodriver-v0.27.0-linux64.tar.gz > /dev/null
#Install Xvfb / WM X11 / Libs
echo "      2. Installing X Enviroment..."
apt-get update -qqy  > /dev/null
apt-get -qqy install mongo-tools xvfb pulseaudio x11vnc fluxbox libgtk-3-0 libdbus-glib-1-2  unzip libxi6 libgconf-2-4 > /dev/null
#Install Webbrowser
echo "      3. Installing Firefox Web browser..."
apt-get -qqy --no-install-recommends install libfontconfig libfreetype6 xfonts-cyrillic xfonts-scalable fonts-liberation fonts-ipafont-gothic fonts-wqy-zenhei fonts-tlwg-loma-otf libavcodec-extra > /dev/null
rm -rf /var/lib/apt/lists/* /var/cache/apt/* > /dev/null
wget --no-verbose --quiet -O /tmp/firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US" > /dev/null
rm -rf /opt/firefox > /dev/null
tar -C /opt -xjf /tmp/firefox.tar.bz2 > /dev/null
rm /tmp/firefox.tar.bz2 > /dev/null
mv /opt/firefox /opt/firefox-latest > /dev/null
ln -fs /opt/firefox-latest/firefox /usr/bin/firefox > /dev/null
mkdir /usr/local/test 
export DISPLAY=:0.0
export MOZ_HEADLESS=1
#return to original dir
cd $CURRENT_DIR