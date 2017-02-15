# Defining the package namespace
%global ns_name ea-apache24
%global upstream_name modsecurity
%global module_name mod_security2

# Ugly hack. Harcoded values to avoid relocation.
%global _httpd_mmn          %(cat %{_includedir}/apache2/.mmn 2>/dev/null || echo missing-ea-apache2-devel)
%global _httpd_confdir      %{_sysconfdir}/apache2/conf.d
%global _httpd_moddir       %{_libdir}/apache2/modules
%global _httpd_modconfdir   %{_sysconfdir}/apache2/conf.modules.d
%global _httpd_logdir       %{_var}/log/apache2

%if 0%{?fedora} >= 18 || 0%{?rhel} >= 6
%global _httpd_apxs         %{_bindir}/apxs
%else
%global _httpd_apxs         %{_sbindir}/apxs
%endif

Summary: Security module for the Apache HTTP Server
Name: %{ns_name}-%{module_name}
Version: 2.9.0
# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4560 for more details
%define release_prefix 15
Release: %{release_prefix}%{?dist}.cpanel
License: ASL 2.0
URL: http://www.modsecurity.org/
Vendor: cPanel, Inc.
Group: System Environment/Daemons
Source: https://www.modsecurity.org/tarball/%{version}/%{upstream_name}-%{version}.tar.gz
Source1: modsec2.conf
Source2: loadmod.conf
Source3: modsec2.user.conf
Source4: modsec2.cpanel.conf

# Don't allow CentOS version of mod_security to be installed to avoid confusion
Conflicts: mod_security
BuildRequires: ea-apache24-devel libxml2-devel pcre-devel curl-devel lua-devel
BuildRequires: ea-apr-devel ea-apr-util-devel
BuildRequires: lua-devel >= 5.1, libxml2-devel
Requires: lua%{?_isa} >= 5.1, libxml2%{?_isa}
Requires: ea-apache24-config, ea-apache24%{?_isa}, ea-apache24-mmn = %{_httpd_mmn}
Requires: ea-apache24-mod_unique_id%{?_isa}
Requires: ea-modsec-sdbm-util%{?_isa}
Requires: ea-apr-util%{?_isa}
Patch0: 2.8.0-concurrent-logging.cpanel.patch
Patch1: 2.9.0-rule-processing-failed-expand.cpanel.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build-%(%{__id_u} -n)

%description
ModSecurity is an open source intrusion detection and prevention engine
for web applications. It operates embedded into the web server, acting
as a powerful umbrella - shielding web applications from attacks.

%prep
%setup -q -n %{upstream_name}-%{version}
%patch0 -p1 -b .concurrent
%patch1 -p1 -b .expandmsg

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
%configure --enable-pcre-match-limit=1000000 \
           --enable-pcre-match-limit-recursion=1000000 \
           --with-apr=%{ea_apr_dir} --with-apu=%{ea_apu_dir} \
           --with-apxs=%{_httpd_apxs}
# TODO: If we ever need to link off of our versions of software in /opt/cpanel,
# then we'll want to remove these 2 lines since hard-coding rpath is an intricate
# part of using cpanel SCL libraries.
%{__sed} -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
%{__sed} -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

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
%{__mkdir_p} %{buildroot}/%{_httpd_dir}/logs/modsec_audit

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
%doc CHANGES LICENSE README.TXT NOTICE
%attr(0755,root,root) %{_httpd_moddir}/mod_security2.so
%{_httpd_modconfdir}/*.conf
# Don't make modsec2.conf a config file, we need to ensure we own this and can fix as needed
%attr(0600,root,root) %{_httpd_confdir}/modsec2.conf
# These 2 files are config because they are modified directly/indirectly by users and admin
%attr(0600,root,root) %config(noreplace) %{_httpd_confdir}/modsec/modsec2.cpanel.conf
%attr(0600,root,root) %config(noreplace) %{_httpd_confdir}/modsec/modsec2.user.conf
# Prevent users from listing the directory
%attr(1733,root,root) %dir %{_httpd_dir}/logs/modsec_audit

%changelog
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

* Mon Jun 28 2016 Edwin Buck <e.buck@cpanel.net> - 2.9.0-10
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

* Wed May 3 2011 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.13-1
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

* Sat Jan 27 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.5-2
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
