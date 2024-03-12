#!/bin/bash

source debian/vars.sh

set -x

cp mlogc/INSTALL .

# install module
install -d $DEB_INSTALL_ROOT$_httpd_moddir
install apache2/.libs/$module_name.so $DEB_INSTALL_ROOT$_httpd_moddir/$module_name.so
# install loadmodule configuration
mkdir -p $DEB_INSTALL_ROOT$_httpd_modconfdir
install $SOURCE2 $DEB_INSTALL_ROOT$_httpd_modconfdir/800-$module_name.conf
# install modsecurity configuration
mkdir -p $DEB_INSTALL_ROOT$_httpd_confdir
mkdir -p $DEB_INSTALL_ROOT$_httpd_confdir/modsec
install $SOURCE1.new $DEB_INSTALL_ROOT$_httpd_confdir/modsec2.conf
install $SOURCE3.new $DEB_INSTALL_ROOT$_httpd_confdir/modsec/modsec2.user.conf
install $SOURCE4.new $DEB_INSTALL_ROOT$_httpd_confdir/modsec/modsec2.cpanel.conf
mkdir -p $DEB_INSTALL_ROOT/etc/apache2/logs/modsec_audit
# mlogc
install -d $DEB_INSTALL_ROOT$_localstatedir/log/mlogc
install -d $DEB_INSTALL_ROOT$_localstatedir/log/mlogc/data
install -d $DEB_INSTALL_ROOT$_bindir
install -m0755 mlogc/mlogc $DEB_INSTALL_ROOT$_bindir/mlogc
install -m0755 mlogc/mlogc-batch-load.pl $DEB_INSTALL_ROOT$_bindir/mlogc-batch-load
install -m0644 mlogc/mlogc-default.conf $DEB_INSTALL_ROOT$_sysconfdir/mlogc.conf
mkdir -p $DEB_INSTALL_ROOT/etc/cpanel/ea4
echo -n $version > $DEB_INSTALL_ROOT/etc/cpanel/ea4/modsecurity.version

echo "FILELIST"
find . -type f -print | sort

