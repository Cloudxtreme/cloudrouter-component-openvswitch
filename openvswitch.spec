%global _hardened_build 1

Summary: Open vSwitch daemon/database/utilities
Name: openvswitch
Version: 2.4.0
Release: 2%{?dist}
License: ASL 2.0 and LGPLv2+ and SISSL
URL: http://openvswitch.org
Source0: http://openvswitch.org/releases/%{name}-%{version}.tar.gz

ExcludeArch: ppc

AutoReqProv: no

BuildRequires: autoconf automake libtool
BuildRequires: systemd-units openssl openssl-devel
BuildRequires: python python-twisted-core python-zope-interface PyQt4
BuildRequires: desktop-file-utils
BuildRequires: groff graphviz
BuildRequires: procps-ng

Requires: iproute
Requires: module-init-tools
Requires: openssl
Requires: python
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
Obsoletes: openvswitch-controller <= 0:2.1.0-1

%bcond_without check

%description
Open vSwitch provides standard network bridging functions and
support for the OpenFlow protocol for remote per-flow control of
traffic.

%package -n python-openvswitch
Summary: Open vSwitch python bindings
License: ASL 2.0
BuildArch: noarch
Requires: python

%description -n python-openvswitch
Python bindings for the Open vSwitch database

%package test
Summary: Open vSwitch testing utilities
License: ASL 2.0
BuildArch: noarch
Requires: python-openvswitch = %{version}-%{release}
Requires: python python-twisted-core python-twisted-web

%description test
Utilities that are useful to diagnose performance and connectivity
issues in Open vSwitch setup.

%package devel
Summary: Open vSwitch OpenFlow development package (library, headers)
License: ASL 2.0
Provides: openvswitch-static = %{version}-%{release}

%description devel
This provides static library, libopenswitch.a and the openvswitch header
files needed to build an external application.

%prep
%setup -q -n %{name}-%{version}

%build
%configure --enable-ssl --with-pkidir=%{_sharedstatedir}/openvswitch/pki
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

install -d -m 0755 $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch

install -p -D -m 0644 \
        rhel/usr_share_openvswitch_scripts_systemd_sysconfig.template \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/openvswitch
install -p -D -m 0644 \
        rhel/usr_lib_systemd_system_openvswitch.service \
        $RPM_BUILD_ROOT%{_unitdir}/openvswitch.service
install -p -D -m 0644 \
        rhel/usr_lib_systemd_system_openvswitch-nonetwork.service \
        $RPM_BUILD_ROOT%{_unitdir}/openvswitch-nonetwork.service

install -m 0755 rhel/etc_init.d_openvswitch \
        $RPM_BUILD_ROOT%{_datadir}/openvswitch/scripts/openvswitch.init

install -p -D -m 0644 rhel/etc_logrotate.d_openvswitch \
        $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/openvswitch

install -m 0644 vswitchd/vswitch.ovsschema \
        $RPM_BUILD_ROOT/%{_datadir}/openvswitch/vswitch.ovsschema

install -d -m 0755 $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifdown-ovs \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifup-ovs \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs

install -d -m 0755 $RPM_BUILD_ROOT%{python_sitelib}
mv $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/* \
   $RPM_BUILD_ROOT%{python_sitelib}
rmdir $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/

install -d -m 0755 $RPM_BUILD_ROOT/%{_sharedstatedir}/openvswitch

touch $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch/conf.db
touch $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch/system-id.conf

%check
%if %{with check}
    if make check TESTSUITEFLAGS='%{_smp_mflags}' ||
       make check TESTSUITEFLAGS='--recheck'; then :;
    else
        cat tests/testsuite.log
        exit 1
    fi
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%preun
%if 0%{?systemd_preun:1}
    %systemd_preun %{name}.service
%else
    if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
        /bin/systemctl --no-reload disable %{name}.service >/dev/null 2>&1 || :
        /bin/systemctl stop %{name}.service >/dev/null 2>&1 || :
    fi
%endif

%post
%if 0%{?systemd_post:1}
    %systemd_post %{name}.service
%else
    # Package install, not upgrade
    if [ $1 -eq 1 ]; then
        /bin/systemctl daemon-reload >dev/null || :
    fi
%endif


%postun
%if 0%{?systemd_postun_with_restart:1}
    %systemd_postun_with_restart %{name}.service
%else
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
    if [ "$1" -ge "1" ] ; then
    # Package upgrade, not uninstall
        /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
    fi
%endif

%files -n python-openvswitch
%{python_sitelib}/ovs
%doc COPYING

%files test
%{_bindir}/ovs-test
%{_bindir}/ovs-vlan-test
%{_bindir}/ovs-l3ping
%{_mandir}/man8/ovs-test.8*
%{_mandir}/man8/ovs-vlan-test.8*
%{_mandir}/man8/ovs-l3ping.8*
%{python_sitelib}/ovstest

%files devel
%{_libdir}/*.a
%{_libdir}/*.la
%{_libdir}/pkgconfig/*.pc
%{_includedir}/openvswitch/*
%{_includedir}/openflow/*

%files
%defattr(-,root,root)
%{_sysconfdir}/bash_completion.d/ovs-appctl-bashcomp.bash
%{_sysconfdir}/bash_completion.d/ovs-vsctl-bashcomp.bash
%dir %{_sysconfdir}/openvswitch
%config %ghost %{_sysconfdir}/openvswitch/conf.db
%config %ghost %{_sysconfdir}/openvswitch/system-id.conf
%config(noreplace) %{_sysconfdir}/sysconfig/openvswitch
%config(noreplace) %{_sysconfdir}/logrotate.d/openvswitch
%{_unitdir}/openvswitch.service
%{_unitdir}/openvswitch-nonetwork.service
%{_datadir}/openvswitch/scripts/openvswitch.init
%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs
%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
%{_datadir}/openvswitch/bugtool-plugins/
%{_datadir}/openvswitch/scripts/ovs-bugtool-*
%{_datadir}/openvswitch/scripts/ovs-check-dead-ifs
%{_datadir}/openvswitch/scripts/ovs-lib
%{_datadir}/openvswitch/scripts/ovs-vtep
%{_datadir}/openvswitch/scripts/ovs-ctl
%config %{_datadir}/openvswitch/vswitch.ovsschema
%config %{_datadir}/openvswitch/vtep.ovsschema
%{_bindir}/ovs-appctl
%{_bindir}/ovs-docker
%{_bindir}/ovs-dpctl
%{_bindir}/ovs-dpctl-top
%{_bindir}/ovs-ofctl
%{_bindir}/ovs-vsctl
%{_bindir}/ovsdb-client
%{_bindir}/ovsdb-tool
%{_bindir}/ovs-testcontroller
%{_bindir}/ovs-pki
%{_bindir}/vtep-ctl
%{_sbindir}/ovs-bugtool
%{_sbindir}/ovs-vswitchd
%{_sbindir}/ovsdb-server
%{_mandir}/man1/ovs-benchmark.1*
%{_mandir}/man1/ovs-pcap.1*
%{_mandir}/man1/ovs-tcpundump.1*
%{_mandir}/man1/ovsdb-client.1*
%{_mandir}/man1/ovsdb-server.1*
%{_mandir}/man1/ovsdb-tool.1*
%{_mandir}/man5/ovs-vswitchd.conf.db.5*
%{_mandir}/man5/vtep.5*
%{_mandir}/man8/vtep-ctl.8*
%{_mandir}/man8/ovs-appctl.8*
%{_mandir}/man8/ovs-bugtool.8*
%{_mandir}/man8/ovs-ctl.8*
%{_mandir}/man8/ovs-dpctl.8*
%{_mandir}/man8/ovs-dpctl-top.8*
%{_mandir}/man8/ovs-ofctl.8*
%{_mandir}/man8/ovs-pki.8*
%{_mandir}/man8/ovs-vsctl.8*
%{_mandir}/man8/ovs-vswitchd.8*
%{_mandir}/man8/ovs-parse-backtrace.8*
%{_mandir}/man8/ovs-testcontroller.8*
%doc COPYING DESIGN.md INSTALL.SSL.md NOTICE README.md WHY-OVS.md
%doc FAQ.md NEWS INSTALL.DPDK.md rhel/README.RHEL
/var/lib/openvswitch
/var/log/openvswitch
%ghost %attr(755,root,root) %{_localstatedir}/run/openvswitch
%exclude %{_bindir}/ovs-benchmark
%exclude %{_bindir}/ovs-parse-backtrace
%exclude %{_bindir}/ovs-pcap
%exclude %{_bindir}/ovs-tcpundump
%exclude %{_sbindir}/ovs-vlan-bug-workaround
%exclude %{_mandir}/man1/ovs-benchmark.1.gz
%exclude %{_mandir}/man1/ovs-pcap.1.gz
%exclude %{_mandir}/man1/ovs-tcpundump.1.gz
%exclude %{_mandir}/man8/ovs-vlan-bug-workaround.8.gz
%exclude %{_datadir}/openvswitch/scripts/ovs-save

%changelog
* Tue Jan 12 2016 John Siegrist <john@complects.com> - 2.4.0-2
- Disabled AutoReqProv.

* Wed Sep 09 2015 John Siegrist <john@complects.com> - 2.4.0-1
- Updated version to 2.4.0.

* Thu Aug 06 2015 John Siegrist <john@complects.com> - 2.3.2-1
- Initial fork from Fedora project and import into CloudRouter.
