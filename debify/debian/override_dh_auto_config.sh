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

# Ubuntu 26.04+ libtool 2.5.x treats any bare "-R" flag as "-rpath" and
# requires an absolute path after it.  ea-apr16's apu-1-config --ldflags
# outputs a bare "-R" (no path argument) which configure.ac (find_apu.m4)
# concatenates with --libs output, producing "-R -lpthread -lldap_r ...".
# libtool then fails with "argument to -rpath is not absolute: -lpthread".
#
# find_apu.m4 constructs the absolute path "${APU_DIR}/bin/apu-1-config" from
# the --with-apu= argument, bypassing PATH entirely.  The wrapper must live at
# ${fake_apu_dir}/bin/apu-1-config and --with-apu must point to ${fake_apu_dir}.
_apu_dir=$ea_apu_dir
# On Ubuntu 26.04+ libpcre3-dev (which provides pcre-config) is dropped.
# find_pcre2.m4 skips pcre2 detection entirely when --with-pcre is set to any
# non-"no" value, even if pcre-config doesn't exist.  So pass --with-pcre=no on
# U26+ to let CHECK_PCRE2() run and set PCRE2_LDADD=-lpcre2-8.
_pcre_flag="--with-pcre=/usr/bin/pcre-config"
UBUNTU_VERSION=$(. /etc/os-release 2>/dev/null && echo "${VERSION_ID:-0}" | tr -d '.')
if [[ "${UBUNTU_VERSION:-0}" -ge 2604 ]]; then
    _pcre_flag="--with-pcre=no"
    # libaprutil-1.so references crypt() which moved to libxcrypt on Ubuntu 26.04.
    # libxcrypt-dev (unversioned libcrypt.so symlink) is not in the OBS mirror.
    # Find the actual versioned .so from the installed libcrypt1 runtime package
    # and embed its full path into Makefile.in/Makefile.am so the linker uses it
    # directly without needing a -dev symlink or a hardcoded soname version.
    _libcrypt_so=$(find /usr/lib /lib -name 'libcrypt.so.*' ! -name '*.hmac' 2>/dev/null | sort | tail -1)
    if [[ -n "${_libcrypt_so}" ]]; then
        find . -name 'Makefile.in' | xargs -r sed -i "/^LIBS[[:space:]]*=/s|$| ${_libcrypt_so}|"
        # tests/Makefile.in is generated from Makefile.am by automake; patch both.
        # Last entry of msc_test_LDADD is @SSDEEP_CFLAGS@ (no trailing \).
        perl -i -pe "s|^(\\s+\@SSDEEP_CFLAGS\@)\\s*\$|\$1 \\\\\n    ${_libcrypt_so}|" tests/Makefile.am
        if [[ -f tests/Makefile.in ]]; then
            perl -i -pe "s|^(\\s+\@SSDEEP_CFLAGS\@)\\s*\$|\$1 \\\\\n    ${_libcrypt_so}|" tests/Makefile.in
        fi
    fi
    _wrapper_dir=$(mktemp -d)
    mkdir -p "${_wrapper_dir}/bin"
    cat > "${_wrapper_dir}/bin/apu-1-config" << 'WRAPPER'
#!/bin/bash
# Proxy to real apu-1-config, stripping bare -R flags not followed by an
# absolute path (they cause libtool 2.5.x to fail with "not absolute: -lpthread").
# NOTE: sed 's/ -R //' would miss -R at start of string (no leading space);
# use perl with a lookahead so -R /absolute/path is preserved.
output=$(/opt/cpanel/ea-apr16/bin/apu-1-config "$@")
printf '%s\n' "$output" | perl -pe 's/(^|[ =])-R(?= [^\/]|\s*$)/$1/g; s/  +/ /g; s/^\s+|\s+$//g'
WRAPPER
    chmod +x "${_wrapper_dir}/bin/apu-1-config"
    _apu_dir="${_wrapper_dir}"
fi

./configure  \
    ${_pcre_flag} \
    --with-apr=$ea_apr_dir \
    --with-apu=${_apu_dir} \
    --with-apxs=$_httpd_apxs \
    --with-curl=/usr/bin/curl-config \
    --with-libxma=/usrl \
    || exit 1

make

make test
