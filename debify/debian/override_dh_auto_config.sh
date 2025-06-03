#!/bin/bash

source debian/vars.sh

set -x

# pulled from apr-util
mkdir -p config
cp $ea_apr_config config/apr-1-config
cp $ea_apr_config config/apr-config
cp /usr/share/pkgconfig/ea-apr16-1.pc config/apr-1.pc
cp /usr/share/pkgconfig/ea-apr16-util-1.pc config/apr-util-1.pc
cp /usr/share/pkgconfig/ea-apr16-1.pc config
cp /usr/share/pkgconfig/ea-apr16-util-1.pc config

export PKG_CONFIG_PATH="$PKG_CONFIG_PATH:`pwd`/config"
touch configure
# install modsec config (cPanel & WHM expects this name.. don't change it)
sed -e "s|@HTTPD_LOGDIR@|$_httpd_logdir|" \
    -e "s|@HTTPD_CONFDIR@|$_httpd_confdir|" \
    $SOURCE1 > $SOURCE1.new
sed -e "s|@HTTPD_LOGDIR@|$_httpd_logdir|" \
    -e "s|@HTTPD_CONFDIR@|$_httpd_confdir|" \
    $SOURCE3 > $SOURCE3.new
sed -e "s|@HTTPD_LOGDIR@|$_httpd_logdir|" \
    -e "s|@HTTPD_CONFDIR@|$_httpd_confdir|" \
    $SOURCE4 > $SOURCE4.new

echo "CONFIGURE :$ea_apr_dir: :$ea_apu_dir:"
ls -ld /usr/bin/apxs

./configure  \
    --with-pcre=/usr/bin/pcre-config \
    --with-apr=$ea_apr_dir \
    --with-apu=$ea_apu_dir \
    --with-apxs=$_httpd_apxs \
    --with-curl=/usr/bin/curl-config \
    --with-libxma=/usrl
make

make test
