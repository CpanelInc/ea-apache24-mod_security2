# Defining the package namespace
%global ns_name ea-apache24
%global upstream_name ModSecurity
%global module_name mod_security2

# Ugly hack. Harcoded values to avoid relocation.
%global _httpd_mmn          %(cat %{_includedir}/apache2/.mmn 2>/dev/null || echo missing-ea-apache2-devel)
%global _httpd_confdir      %{_sysconfdir}/apache2/conf.d
%global _httpd_moddir       %{_libdir}/apache2/modules
%global _httpd_modconfdir   %{_sysconfdir}/apache2/conf.modules.d
%global _httpd_logdir       %{_var}/log/apache2

# Change to use higher optimization level
# By adding -O3 to the end, it will overide any other "-O" settings
%global optflags %{optflags} -O3

%if 0%{?fedora} >= 18 || 0%{?rhel} >= 6
%global _httpd_apxs         %{_bindir}/apxs
%else
%global _httpd_apxs         %{_sbindir}/apxs
%endif

%if 0%{?rhel} >= 8
# On CentOS8, ea-libcurl needs libssh2 which is only available in EPEL, so for
# now we are using system libcurl
%define libcurl_ver 7.61.0
%else
%define ea_libcurl_ver 7.68.0-2
%endif

%if 0%{?rhel} >= 10
# In the newer rpm_builds like AL10, it is doing a much more strict set of checks that are incompatible
# with EA4, so disable the checks.

%global __brp_check_rpaths %{nil}
%endif

Summary: Security module for the Apache HTTP Server
Name: %{ns_name}-%{module_name}
Version: 2.9.12
# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4560 for more details
%define release_prefix 1
Release: %{release_prefix}%{?dist}.cpanel
License: ASL 2.0
URL: http://www.modsecurity.org/
Vendor: cPanel, Inc.
Group: System Environment/Daemons
Source: v%{version}.tar.gz
Source1: modsec2.conf
Source2: loadmod.conf
Source3: modsec2.user.conf
Source4: modsec2.cpanel.conf

# Don't allow CentOS version of mod_security to be installed to avoid confusion
# Do not conflict against C6 since we do not build ea-modsec3+ against it -- see EA-9584 for more details on why
%if 0%{?rhel} >= 7
Conflicts: mod_security
%endif
Provides: mod_security

# WHM only factors in real package names so:
Conflicts: ea-modsec30 ea-modsec31

BuildRequires: pcre2-devel
BuildRequires: autotools-latest-autoconf libtool

BuildRequires: ea-apache24-devel ea-libxml2-devel lua-devel
BuildRequires: ea-apr-devel ea-apr-util-devel
BuildRequires: lua-devel >= 5.1, ea-libxml2-devel
%if 0%{?rhel} < 10
%if 0%{?rhel} >= 7
BuildRequires: yajl yajl-devel
Requires: yajl
%endif
%endif
Requires: lua%{?_isa} >= 5.1, ea-libxml2%{?_isa}
Requires: ea-apache24-config, ea-apache24%{?_isa}, ea-apache24-mmn = %{_httpd_mmn}
Requires: ea-apache24-mod_unique_id%{?_isa}
Requires: ea-modsec-sdbm-util%{?_isa}
Requires: ea-apr-util%{?_isa}

%if 0%{?rhel} == 7
Requires: pcre2
%endif

%if 0%{?rhel} >= 8
%if 0%{?rhel} < 10
BuildRequires: ea-brotli
%else
BuildRequires: brotli
%endif
BuildRequires: libcurl >= %{libcurl_ver}
BuildRequires: libcurl-devel >= %{libcurl_ver}
%if 0%{?rhel} < 10
Requires: ea-brotli
%else
Requires: brotli
%endif
Requires: libcurl >= %{libcurl_ver}
%else
BuildRequires: ea-libcurl >= %{ea_libcurl_ver}
BuildRequires: ea-libcurl-devel >= %{ea_libcurl_ver}
BuildRequires: libssh2 libssh2-devel
BuildRequires: krb5-devel
Requires: ea-libcurl >= %{ea_libcurl_ver}
%endif

Patch0: 0001-PCRE-config-RPATH-adjustment.patch
Patch1: 0002-Fix-httpd.conf.in-template-so-that-tests-run-regress.patch
Patch2: 0003-Replace-pcre2_set_depth_limit.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build-%(%{__id_u} -n)

%description
ModSecurity is an open source intrusion detection and prevention engine
for web applications. It operates embedded into the web server, acting
as a powerful umbrella - shielding web applications from attacks.

%package -n     ea-apache24-mod_security2-mlogc
Summary:        ModSecurity Audit Log Collector
Group:          System Environment/Daemons
Requires:       ea-apache24-mod_security2
Conflicts:      mlogc

%description -n ea-apache24-mod_security2-mlogc
This package contains the ModSecurity Audit Log Collector.


%prep
%setup -q -n %{upstream_name}-%{version}
%patch0 -p1 -b .pcrerpath
%patch1 -p1 -b .runregressiontests
%if 0%{?rhel} <= 7
%patch2 -p1 -b .replace_depth_limit
%endif

# install modsec config (cPanel & WHM expects this name.. don't change it)
%{__sed} -e "s|@HTTPD_LOGDIR@|%{_httpd_logdir}|" \
    -e "s|@HTTPD_CONFDIR@|%{_httpd_confdir}|" \
    %{SOURCE1} > %{SOURCE1}.new
%{__sed} -e "s|@HTTPD_LOGDIR@|%{_httpd_logdir}|" \
    -e "s|@HTTPD_CONFDIR@|%{_httpd_confdir}|" \
    %{SOURCE3} > %{SOURCE3}.new
%{__sed} -e "s|@HTTPD_LOGDIR@|%{_httpd_logdir}|" \
    -e "s|@HTTPD_CONFDIR@|%{_httpd_confdir}|" \
    %{SOURCE4} > %{SOURCE4}.new

%build
# Force dependency resolution to pick /usr/bin/perl instead of /bin/perl
# This helps downstream users of our RPMS (see: EA-7468) and (EA-9583)
export PATH="/usr/bin:$PATH"


%if 0%{?rhel} >= 10
export PKG_CONFIG_PATH="/usr/lib64/pkgconfig:$PKG_CONFIG_PATH"
export LDFLAGS="-Wl,-rpath,/opt/cpanel/ea-openssl11/%{_lib} -Wl,-rpath,/opt/cpanel/ea-libxml2/%{_lib} -L/opt/cpanel/ea-libxml2/%{_lib} -lxml2 -lz -llzma -lm -ldl -Wl,-z,relro,-z,now"
%else
export LDFLAGS="-Wl,-rpath=/opt/cpanel/ea-brotli/lib -Wl,-rpath,/opt/cpanel/ea-openssl11/%{_lib} -Wl,-rpath,/opt/cpanel/ea-libxml2/%{_lib} -L/opt/cpanel/ea-libxml2/%{_lib} -lxml2 -lz -llzma -lm -ldl -Wl,-z,relro,-z,now"
%endif

./autogen.sh
find . -type f -exec touch -r ./configure \{\} \;

# Define base configure options
%global configure_opts --with-apr=%{ea_apr_dir} --with-apu=%{ea_apu_dir} --with-apxs=%{_httpd_apxs} --with-libxml=/opt/cpanel/ea-libxml2 --with-pcre2=/usr/bin/pcre2-config

# For c6 and c7 they need -std=gnu99 for pcre2 (2.9.9 only supports pcre2 it seems)
%if 0%{?rhel} < 8
export CFLAGS="-std=gnu99"
%endif

# Dynamically adjust curl path based on OS version
%if 0%{?rhel} >= 8
%global curl_config /usr/bin/curl-config
%else
%global curl_config /opt/cpanel/libcurl
%endif

# Now just one simple configure command:
./configure %{configure_opts} --with-curl=%{curl_config}

%{__make} %{_smp_mflags}

%install
%{__rm} -rf %{buildroot}

# install module
%{__install} -d %{buildroot}%{_httpd_moddir}
%{__install} apache2/.libs/%{module_name}.so %{buildroot}%{_httpd_moddir}/%{module_name}.so
# install loadmodule configuration
%{__mkdir_p} %{buildroot}%{_httpd_modconfdir}
%{__install} %{SOURCE2} %{buildroot}%{_httpd_modconfdir}/800-%{module_name}.conf
# install modsecurity configuration
%{__mkdir_p} %{buildroot}%{_httpd_confdir}
%{__mkdir_p} %{buildroot}%{_httpd_confdir}/modsec
%{__install} %{SOURCE1}.new %{buildroot}%{_httpd_confdir}/modsec2.conf
%{__install} %{SOURCE3}.new %{buildroot}%{_httpd_confdir}/modsec/modsec2.user.conf
%{__install} %{SOURCE4}.new %{buildroot}%{_httpd_confdir}/modsec/modsec2.cpanel.conf
%{__mkdir_p} %{buildroot}/etc/apache2/logs/modsec_audit

# mlogc
install -d %{buildroot}%{_localstatedir}/log/mlogc
install -d %{buildroot}%{_localstatedir}/log/mlogc/data
install -d %{buildroot}%{_bindir}
install -m0755 mlogc/mlogc %{buildroot}%{_bindir}/mlogc
install -m0755 mlogc/mlogc-batch-load.pl %{buildroot}%{_bindir}/mlogc-batch-load
install -m0644 mlogc/mlogc-default.conf %{buildroot}%{_sysconfdir}/mlogc.conf

mkdir -p $RPM_BUILD_ROOT/etc/cpanel/ea4
echo -n %{version} > $RPM_BUILD_ROOT/etc/cpanel/ea4/modsecurity.version

%clean
%{__rm} -rf %{buildroot}

# These don't use univeral hooks.  Removing the mod_security2 package would remove the code needed
# to bounce tailwatchd.  The alternative is to place a univeral-hook into the ea-apache24-config-runtime
# package; thus introducing more "action at a distance" code.
%post
# Upgrade the ea4 old config locations to the EA4 new config locations
# No need to concern ourselves with EA3 here, because it writes to the new EA4 location
[[ -e %{_httpd_confdir}/modsec2.user.conf ]] && %{__mv} %{_httpd_confdir}/modsec2.user.conf %{_httpd_confdir}/modsec/modsec2.user.conf || /bin/true
[[ -e %{_httpd_confdir}/modsec2.user.conf.PREVIOUS ]] && %{__mv} %{_httpd_confdir}/modsec2.user.conf.PREVIOUS %{_httpd_confdir}/modsec/modsec2.user.conf.PREVIOUS || /bin/true
[[ -e %{_httpd_confdir}/modsec2.cpanel.conf ]] && %{__mv} %{_httpd_confdir}/modsec2.cpanel.conf %{_httpd_confdir}/modsec/modsec2.cpanel.conf || /bin/true
[[ -e %{_httpd_confdir}/modsec2.cpanel.conf.PREVIOUS ]] && %{__mv} %{_httpd_confdir}/modsec2.cpanel.conf.PREVIOUS %{_httpd_confdir}/modsec/modsec2.cpanel.conf.PREVIOUS || /bin/true

# Tell tailwatchd to start monitoring modsec_audit.log
[[ -x /usr/local/cpanel/scripts/restartsrv_tailwatchd ]] && /usr/local/cpanel/scripts/restartsrv_tailwatchd &>/dev/null || /bin/true

%postun
# Tell tailwatchd to stop monitoring modsec_audit.log
[[ -x /usr/local/cpanel/scripts/restartsrv_tailwatchd ]] && /usr/local/cpanel/scripts/restartsrv_tailwatchd &>/dev/null || /bin/true

%files
# - EA4 RPM only deploys 2 configuration files.
# - One config loads the module
# - The other config passes basic configuration settings.
# - No configuration "enables" modsec.. that's cPanel & WHM's job
%defattr (0644,root,root,0755)
%doc CHANGES LICENSE README.md NOTICE
%attr(0755,root,root) %{_httpd_moddir}/mod_security2.so
%{_httpd_modconfdir}/*.conf
# Don't make modsec2.conf a config file, we need to ensure we own this and can fix as needed
%attr(0600,root,root) %{_httpd_confdir}/modsec2.conf
# These 2 files are config because they are modified directly/indirectly by users and admin
%attr(0600,root,root) %config(noreplace) %{_httpd_confdir}/modsec/modsec2.cpanel.conf
%attr(0600,root,root) %config(noreplace) %{_httpd_confdir}/modsec/modsec2.user.conf
# Prevent users from listing the directory
%attr(1733,root,root) %dir /etc/apache2/logs/modsec_audit
/etc/cpanel/ea4/modsecurity.version

%files -n ea-apache24-mod_security2-mlogc
%defattr (-,root,root)
%doc mlogc/INSTALL
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mlogc.conf
%attr(0755,root,root) %dir %{_localstatedir}/log/mlogc
%attr(0770,root,root) %dir %{_localstatedir}/log/mlogc/data
%attr(0755,root,root) %{_bindir}/mlogc
%attr(0755,root,root) %{_bindir}/mlogc-batch-load

%changelog
* Wed Aug 06 2025 Dan Muey <daniel.muey@webpros.com> - 2.9.12-1
- EA-13061: Update ea-apache24-mod_security2 from v2.9.11 to v2.9.12
- fix: Improper error handling CVE 2025-54571

* Tue Jul 01 2025 Cory McIntire <cory.mcintire@webpros.com> - 2.9.11-1
- EA-12994: Update ea-apache24-mod_security2 from v2.9.10 to v2.9.11
- prevent segmentation fault if the XML node is empty: CVE-2025-52891

* Mon Jun 02 2025 Dan Muey <daniel.muey@webpros.com> - 2.9.10-1
- ZC-12886: Update ea-apache24-mod_security2 from v2.9.9 to v2.9.10
- DoS vulnerability: CVE-2025-48866

* Thu May 22 2025 Dan Muey <daniel.muey@webpros.com> - 2.9.9-1
- EA-12885: Update ea-apache24-mod_security2 from v2.9.8 to v2.9.9
- Possible DoS vulnerability: CVE-2025-47947

* Wed Feb 05 2025 Cory McIntire <cory.mcintire@webpros.com> - 2.9.8-1
- EA-12853: Update ea-apache24-mod_security2 from v2.9.7 to v2.9.8
- Remove 2 patches that were added upstream.
	- 0003-Import-some-memory-leak-fixes-for-Mod-Security-2.9.x.patch
	- 0004-Allow-Lua-5.4.patch
- Add new patch for re.c to allow it to build on Ubuntu
- Add new patch for tests on Ubuntu 20

* Tue Mar 12 2024 Julian Brown <julian.brown@cpanel.net> - 2.9.7-2
- ZC-11691: Correct build problems on Ubuntu

* Thu Jan 05 2023 Cory McIntire <cory@cpanel.net> - 2.9.7-1
- EA-11134: Update mod_security2 from v2.9.6 to v2.9.7
- Security impacting issues
    Fix: FILES_TMP_CONTENT may sometimes lack complete content
    [Issue #2857 - gieltje, @airween, @dune73, @martinhsv]

* Thu Dec 08 2022 Travis Holloway <t.holloway@cpanel.net> - 2.9.6-2
- EA-11091: Fix linking issues on C6/C7

* Wed Nov 23 2022 Travis Holloway <t.holloway@cpanel.net> - 2.9.6-1
- EA-11068: Update mod_security2 from v2.9.3 to v2.9.6

* Wed Sep 21 2022 Dan Muey <dan@cpanel.net> - 2.9.3-19
- ZC-10009: Add lua 5.4 support

* Fri Jan 21 2022 Tim Mullin <tim@cpanel.net> - 2.9.3-18
- EA-10239: Increase compiler optimization level to help mitigate performance loss from large rulesets

* Tue Jan 11 2022 Julian Brown <julian.brown@cpanel.net> - 2.9.3-17
- ZC-9641: Rebuilt to include libcurl4 and libgnutls

* Mon Jan 03 2022 Travis Holloway <t.holloway@cpanel.net> - 2.9.3-16
- EA-10203: Add patch to fix memory leaks

* Fri Nov 12 2021 Travis Holloway <t.holloway@cpanel.net> - 2.9.3-15
- EA-10229: Add patch to allow run-regression-tests.pl to function with EA4

* Wed Aug 18 2021 Daniel Muey <dan@cpanel.net> - 2.9.3-14
- ZC-9217: fix the RPM path for modsec_audit

* Fri Jul 09 2021 Julian Brown <julian.brown@webpros.com> - 2.9.3-13
- ZC-8704: Build for Ubuntu, and minor changes for CentOS

* Wed Feb 10 2021 Travis Holloway <t.holloway@cpanel.net> - 2.9.3-12
- EA-9584: Update Conflicts for C6

* Tue Feb 09 2021 Cory McIntire <cory@cpanel.net> - 2.9.3-11
- EA-9427: change the PATH to use /usr/bin/ so perl doesn't conflict

* Thu Nov 19 2020 Daniel Muey <dan@cpanel.net> - 2.9.3-10
- ZC-7925: Install /etc/cpanel/ea4/modsecurity.version

* Mon Oct 26 2020 Tim Mullin <tim@cpanel.net> - 2.9.3-9
- EA-9177: Set SecRequestBodyLimitAction to ProcessPartial in the conf file

* Fri Oct 23 2020 Tim Mullin <tim@cpanel.net> - 2.9.3-8
- EA-9379: Build modsecurity with ea-brotli rather than brotli

* Tue Sep 01 2020 Daniel Muey <dan@cpanel.net> - 2.9.3-7
- ZC-7376: Add explicit package name conflicts for non-yum resolution

* Tue May 26 2020 Julian Brown <julian.brown@cpanel.net> - 2.9.3-6
- ZC-6871: Fix for C8

* Thu Mar 26 2020 Tim Mullin <tim@cpanel.net> - 2.9.3-5
- EA-8928: Updated the required version for ea-libcurl

* Thu Dec 19 2019 Tim Mullin <tim@cpanel.net> - 2.9.3-4
- EA-8753: Compile mod_security2 with yajl-devel for JSON

* Mon Oct 14 2019 Daniel Muey <dan@cpanel.net> - 2.9.3-3
- ZC-5192: Add find-latest-version script for `et update` support

* Wed Jun 05 2019 Cory McIntire <cory@cpanel.net> - 2.9.3-2
- EA-8507: Apply upstream patch to fix curl call segfaults

* Thu May 30 2019 Tim Mullin <tim@cpanel.net> - 2.9.3-1
- EA-8506: Re-update from upstream to 2.9.3

* Wed Mar 20 2019 Cory McIntire <cory@cpanel.net> - 2.9.2-11
- EA-8292: Add patch Store temporaries in the request pool for regexes compiled per-request.

* Mon Dec 17 2018 Cory McIntire <cory@cpanel.net> - 2.9.2-10
- EA-8080: Fix typos in modsec2.conf comments

* Mon Apr 16 2018 Rishwanth Yeddula <rish@cpanel.net> - 2.9.2-9
- EA-7382: Update dependency on ea-libcurl to require the latest version with versioned symbols.

* Fri Mar 30 2018 Cory McIntire <cory@cpanel.net> - 2.9.2-8
- ZC-3552: Add versioning for ea-libcurl requirements

* Wed Feb 28 2018 Daniel Muey <dan@cpanel.net> - 2.9.2-7
- EA-7263: Do not generate SecHashKey when SecHashEngine isn’t on

* Thu Jan 11 2018 <dan@cpanel.net> - 2.9.2-6
- EA-7098: fix rpath to allow to build against ea-libxml2 libs

* Wed Dec 27 2017 <cory@cpanel.net> - 2.9.2-5
- EA-7044: Adjust mod_security to use ea-libxml2

* Tue Dec 12 2017 Cory McIntire <cory@cpanel.net> - 2.9.2-4
- EA-6863: Applied patch for DoS protection logic fix
- Cleaned up patchset

* Thu Nov 30 2017 Cory McIntire <cory@cpanel.net> - 2.9.2-3
- EA-6984: Change file perms from apache group to root group

* Fri Nov 17 2017 Cory McIntire <cory@cpanel.net> - 2.9.2-2
- EA-6376: Fix faulty RPATH
- EA-6376: update timestamps on files to allow patches to succeed.

* Mon Jul 24 2017 Jacob Perkins <jacob.perkins@cpanel.net> - 2.9.2-1
- EA-6312: Update ModSec to 2.9.2
- Removed RuleProcessingFailedExpand patch as it was fixed upstream

* Fri May 05 2017 Jacob Perkins <jacob.perkins@cpanel.net> - 2.9.0-17
- EA-5950: Added mlogc package

* Mon Mar 06 2017 Dan Muey <dan@cpanel.net> - 2.9.0-16
- ZC-2469: Use ea-libcurl* instead of system curl

* Wed Feb 15 2017 Dan Muey <dan@cpanel.net> - 2.9.0-15
- EA-5805: Patch "Rule processing failed" message to include the id of the rule in question

* Tue Feb 07 2017 Jacob Perkins <jacob.perkins@cpanel.net> - 2.9.0-14
- Enabled debuginfo packages

* Fri Dec 16 2016 Jacob Perkins <jacob.perkins@cpanel.net> - 2.9.0-13
- EA-5493: Added vendor field

* Fri Dec 02 2016 S. Kurt Newman <kurt.newman@cpanel.net> - 2.9.0-12
- Enforce apr-util dependency (EA-5720)
- Ensure dependent libraries are the same arch type (EA-5720)

* Wed Aug 17 2016 S. Kurt Newman <kurt.newman@cpanel.net> - 2.9.0-11
- Fix permissions on modsec_audit directory (EA-5068)

* Mon Jun 27 2016 Edwin Buck <e.buck@cpanel.net> - 2.9.0-10
- EA-4687: Relocate modsec2.cpanel.conf and modsec2.user.conf

* Mon Jun 20 2016 Dan Muey <dan@cpanel.net> - 2.9.0-9
- EA-4383: Update Release value to OBS-proof versioning

* Mon May 30 2016 S. Kurt Newman <kurt.newman@cpanel.net> - 2.9.0-6
- Added explicit lua and xml2 Requires statements (EA-4433)
- Remove mpm_itk and mod_ruid2 conflicts (EA-4433)
- Added more comments to explain portions of spec file (EA-4433)
- Arrest control of modsec2.conf so we can ensure proper Apache logging type (EA-4433)
- Arrest control of conf.modules.d/800-mod_security2.conf (EA-4433)
- RPM now creates logs/modsec_audit dir for concurrent logging (EA-4433)
- Added comments to configuration files to help guide administrator (EA-4433)
- Use module name, not file name in configuration file (EA-4654)

* Tue Nov 03 2015 Julian Brown <julian.brown@cpanel.net>  - 2.9.0-5
- Undo previous change.

* Tue Nov 03 2015 Julian Brown <julian.brown@cpanel.net>  - 2.9.0-4
- Hard code a conflict in place to make EA4 UI able to detect issues with MPM.

* Thu Sep 10 2015 S. Kurt Newman <kurt.newman@cpanel.net>  - 2.9.0-3
- Restart tailwatchd to re-read monitoring need of modsec_audit.log (CPANEL-1098)

* Fri Jul 31 2015 Trinity Quirk <trinity.quirk@cpanel.net> - 2.9.0-2
- Added references to the moved apr and apu

* Mon Jul 27 2015 Trinity Quirk <trinity.quirk@cpanel.net> - 2.9.0-1
- Added conflicts with mod_ruid2 and mod_mpm_itk

* Fri Jul 24 2015 Trinity Quirk <trinity.quirk@cpanel.net> - 2.9.0-0
- Updated to 2.9.0

* Thu May 28 2015 Darren Mobley <darren@cpanel.net> - 2.8.0-2
- Changed name from ea-apache2 to ea-apache24

* Mon May 11 2015 Darren Mobley <darren@cpanel.net> - 2.8.0-1
- Changed name of ea-httpd rpm dependancy to ea-apache2-config
- Fixed previous changelog entry claiming version was updated to 2.9.0

* Thu Mar 19 2015 S. Kurt Newman <kurt.newman@cpanel.net> - 2.8.0-0
- Upgraded to 2.8.0

* Thu Apr  3 2014 Daniel Kopecek <dkopecek@redhat.com> - 2.7.3-5
- Fix Chunked string case sensitive issue (CVE-2013-5705)
  Resolves: rhbz#1082907

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 2.7.3-4
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 2.7.3-3
- Mass rebuild 2013-12-27

* Tue May 28 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.3-2
- Fix NULL pointer dereference (DoS, crash) (CVE-2013-2765) (RHBZ #967615)
- Fix a possible memory leak.

* Sat Mar 30 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.3-1
- Update to 2.7.3

* Fri Jan 25 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.2-1
- Update to 2.7.2
- Update source url in the spec.

* Thu Nov 22 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.1-5
- Use conditional for loading mod_unique_id (rhbz #879264)
- Fix syntax errors on httpd 2.4.x by using IncludeOptional (rhbz #879264, comment #2)

* Mon Nov 19 2012 Peter Vrabec <pvrabec@redhat.com> 2.7.1-4
- mlogc subpackage is not provided on RHEL7

* Thu Nov 15 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.1-3
- Add some missing directives RHBZ #569360
- Fix multipart/invalid part ruleset bypass issue (CVE-2012-4528)
  (RHBZ #867424, #867773, #867774)

* Thu Nov 15 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.1-2
- Fix mod_security.conf

* Thu Nov 15 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.1-1
- Update to 2.7.1
- Remove libxml2 build patch (upstreamed)
- Update spec since upstream moved to github

* Thu Oct 18 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.0-2
- Add a patch to fix failed build against libxml2 >= 2.9.0

* Wed Oct 17 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.0-1
- Update to 2.7.0

* Fri Sep 28 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.6.8-1
- Update to 2.6.8

* Wed Sep 12 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.6.7-2
- Re-add mlogc sub-package for epel (#856525)

* Sat Aug 25 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.6.7-1
- Update to 2.6.7

* Sat Aug 25 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.6.7-1
- Update to 2.6.7

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Fri Jun 22 2012 Peter Vrabec <pvrabec@redhat.com> - 2.6.6-2
- mlogc subpackage is not provided on RHEL

* Thu Jun 21 2012 Peter Vrabec <pvrabec@redhat.com> - 2.6.6-1
- upgrade

* Mon May  7 2012 Joe Orton <jorton@redhat.com> - 2.6.5-3
- packaging fixes

* Fri Apr 27 2012 Peter Vrabec <pvrabec@redhat.com> 2.6.5-2
- fix license tag

* Thu Apr 05 2012 Peter Vrabec <pvrabec@redhat.com> 2.6.5-1
- upgrade & move rules into new package mod_security_crs

* Fri Feb 10 2012 Petr Pisar <ppisar@redhat.com> - 2.5.13-3
- Rebuild against PCRE 8.30
- Do not install non-existing files

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.13-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue May 03 2011 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.13-1
- Newer upstream version

* Wed Jun 30 2010 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.12-3
- Fix log dirs and files ordering per bz#569360

* Thu Apr 29 2010 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.12-2
- Fix SecDatadir and minimal config per bz #569360

* Sat Feb 13 2010 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.12-1
- Update to latest upstream release
- SECURITY: Fix potential rules bypass and denial of service (bz#563576)

* Fri Nov 6 2009 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.10-2
- Fix rules and Apache configuration (bz#533124)

* Thu Oct 8 2009 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.10-1
- Upgrade to 2.5.10 (with Core Rules v2)

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Mar 12 2009 Michael Fleming <mfleming+rpm@thatfleminggent.com> 2.5.9-1
- Update to upstream release 2.5.9
- Fixes potential DoS' in multipart request and PDF XSS handling

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Dec 29 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.5.7-1
- Update to upstream 2.5.7
- Reinstate mlogc

* Sat Aug 2 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.5.6-1
- Update to upstream 2.5.6
- Remove references to mlogc, it no longer ships in the main tarball.
- Link correctly vs. libxml2 and lua (bz# 445839)
- Remove bogus LoadFile directives as they're no longer needed.

* Sun Apr 13 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.7-1
- Update to upstream 2.1.7

* Sat Feb 23 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.6-1
- Update to upstream 2.1.6 (Extra features including SecUploadFileMode)

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 2.1.5-3
- Autorebuild for GCC 4.3

* Sun Jan 27 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.5-2
- Update to 2.1.5 (bz#425986)
- "blocking" -> "optional_rules" per tarball ;-)


* Thu Sep  13 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.3-1
- Update to 2.1.3
- Update License tag per guidelines.

* Mon Sep  3 2007 Joe Orton <jorton@redhat.com> 2.1.1-3
- rebuild for fixed 32-bit APR (#254241)

* Wed Aug 29 2007 Fedora Release Engineering <rel-eng at fedoraproject dot org> - 2.1.1-2
- Rebuild for selinux ppc32 issue.

* Tue Jun 19 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.1-1
- New upstream release
- Drop ASCIIZ rule (fixed upstream)
- Re-enable protocol violation/anomalies rules now that REQUEST_FILENAME
  is fixed upstream.

* Sun Apr 1 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.0-3
- Automagically configure correct library path for libxml2 library.
- Add LoadModule for mod_unique_id as the logging wants this at runtime

* Mon Mar 26 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.0-2
- Fix DSO permissions (bz#233733)

* Tue Mar 13 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.0-1
- New major release - 2.1.0
- Fix CVE-2007-1359 with a local rule courtesy of Ivan Ristic
- Addition of core ruleset
- (Build)Requires libxml2 and pcre added.

* Sun Sep 3 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.4-2
- Rebuild
- Fix minor longstanding braino in included sample configuration (bz #203972)

* Mon May 15 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.4-1
- New upstream release

* Tue Apr 11 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.3-1
- New upstream release
- Trivial spec tweaks

* Wed Mar 1 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.2-3
- Bump for FC5

* Fri Feb 10 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.2-2
- Bump for newer gcc/glibc

* Wed Jan 18 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.2-1
- New upstream release

* Fri Dec 16 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.1-2
- Bump for new httpd

* Thu Dec 1 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.1-1
- New release 1.9.1

* Wed Nov 9 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9-1
- New stable upstream release 1.9

* Sat Jul 9 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.8.7-4
- Add Requires: httpd-mmn to get the appropriate "module magic" version
  (thanks Ville Skytta)
- Disabled an overly-agressive rule or two..

* Sat Jul 9 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.8.7-3
- Correct Buildroot
- Some sensible and safe rules for common apps in mod_security.conf

* Thu May 19 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.8.7-2
- Don't strip the module (so we can get a useful debuginfo package)

* Thu May 19 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.8.7-1
- Initial spin for Extras
