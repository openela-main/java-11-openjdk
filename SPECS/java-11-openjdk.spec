# To rebuild this RPM, you must first rebuild the portable
# RPM using the java-11-openjdk-portable.specfile, install
# it and then adjust portablerelease and portablesuffix
# to match the new portable.

# RPM conditionals so as to be able to dynamically produce
# slowdebug/release builds. See:
# http://rpm.org/user_doc/conditional_builds.html
#
# Examples:
#
# Produce release, fastdebug *and* slowdebug builds on x86_64 (default):
# $ rpmbuild -ba java-11-openjdk.spec
#
# Produce only release builds (no slowdebug builds) on x86_64:
# $ rpmbuild -ba java-11-openjdk.spec --without slowdebug --without fastdebug
#
# Only produce a release build on x86_64:
# $ fedpkg mockbuild --without slowdebug --without fastdebug

# Enable fastdebug builds by default on relevant arches.
%bcond_without fastdebug
# Enable slowdebug builds by default on relevant arches.
%bcond_without slowdebug
# Enable release builds by default on relevant arches.
%bcond_without release
# Enable static library builds by default.
%bcond_without staticlibs
# Build a fresh libjvm.so for use in a copy of the bootstrap JDK
%bcond_without fresh_libjvm
# Build with system libraries
%bcond_with system_libs

# Workaround for stripping of debug symbols from static libraries
%if %{with staticlibs}
%define __brp_strip_static_archive %{nil}
%global include_staticlibs 1
%else
%global include_staticlibs 0
%endif

# Define whether to use the bootstrap JDK directly or with a fresh libjvm.so
%if %{with fresh_libjvm}
%global build_hotspot_first 1
%else
%global build_hotspot_first 0
%endif

%if %{with system_libs}
%global system_libs 1
%global link_type system
%global freetype_lib %{nil}
%else
%global system_libs 0
%global link_type bundled
%global freetype_lib |libfreetype[.]so.*
%endif

# The -g flag says to use strip -g instead of full strip on DSOs or EXEs.
# This fixes detailed NMT and other tools which need minimal debug info.
# See: https://bugzilla.redhat.com/show_bug.cgi?id=1520879
%global _find_debuginfo_opts -g

# Architecture on which we run Java only tests
%global jdk_test_arch x86_64

# note: parametrized macros are order-sensitive (unlike not-parametrized) even with normal macros
# also necessary when passing it as parameter to other macros. If not macro, then it is considered a switch
# see the difference between global and define:
# See https://github.com/rpm-software-management/rpm/issues/127 to comments at  "pmatilai commented on Aug 18, 2017"
# (initiated in https://bugzilla.redhat.com/show_bug.cgi?id=1482192)
%global debug_suffix_unquoted -slowdebug
%global fastdebug_suffix_unquoted -fastdebug
# quoted one for shell operations
%global debug_suffix "%{debug_suffix_unquoted}"
%global fastdebug_suffix "%{fastdebug_suffix_unquoted}"
%global normal_suffix ""

%global debug_warning This package is unoptimised with full debugging. Install only as needed and remove ASAP.
%global fastdebug_warning This package is optimised with full debugging. Install only as needed and remove ASAP.
%global debug_on unoptimised with full debugging on
%global fastdebug_on optimised with full debugging on
%global for_fastdebug for packages with debugging on and optimisation
%global for_debug for packages with debugging on and no optimisation

%if %{with release}
%global include_normal_build 1
%else
%global include_normal_build 0
%endif

%if %{include_normal_build}
%global normal_build %{normal_suffix}
%else
%global normal_build %{nil}
%endif

# We have hardcoded list of files, which  is appearing in alternatives, and in files
# in alternatives those are slaves and master, very often triplicated by man pages
# in files all masters and slaves are ghosted
# the ghosts are here to allow installation via query like `dnf install /usr/bin/java`
# you can list those files, with appropriate sections: cat *.spec | grep -e --install -e --slave -e post_ -e alternatives
# TODO - fix those hardcoded lists via single list
# Those files must *NOT* be ghosted for *slowdebug* packages
# FIXME - if you are moving jshell or jlink or similar, always modify all three sections
# you can check via headless and devels:
#    rpm -ql --noghost java-11-openjdk-headless-11.0.1.13-8.fc29.x86_64.rpm  | grep bin
# == rpm -ql           java-11-openjdk-headless-slowdebug-11.0.1.13-8.fc29.x86_64.rpm  | grep bin
# != rpm -ql           java-11-openjdk-headless-11.0.1.13-8.fc29.x86_64.rpm  | grep bin
# similarly for other %%{_jvmdir}/{jre,java} and %%{_javadocdir}/{java,java-zip}
%define is_release_build() %( if [ "%{?1}" == "%{debug_suffix_unquoted}" -o "%{?1}" == "%{fastdebug_suffix_unquoted}" ]; then echo "0" ; else echo "1"; fi )

# Indicates whether this is the default JDK on this version of RHEL
%global is_system_jdk 1

%global aarch64         aarch64 arm64 armv8
# we need to distinguish between big and little endian PPC64
%global ppc64le         ppc64le
%global ppc64be         ppc64 ppc64p7
# Set of architectures which support multiple ABIs
%global multilib_arches %{power64} sparc64 x86_64
# Set of architectures for which we build slowdebug builds
%global debug_arches    %{ix86} x86_64 sparcv9 sparc64 %{aarch64} %{power64} s390x
# Set of architectures for which we build fastdebug builds
%global fastdebug_arches x86_64 ppc64le aarch64
# Set of architectures with a Just-In-Time (JIT) compiler
%global jit_arches      %{arm} %{aarch64} %{ix86} %{power64} s390x sparcv9 sparc64 x86_64
# Set of architectures which use the Zero assembler port (!jit_arches)
%global zero_arches ppc s390
# Set of architectures which run a full bootstrap cycle
%global bootstrap_arches %{jit_arches}
# Set of architectures which support SystemTap tapsets
%global systemtap_arches %{jit_arches}
# Set of architectures with a Ahead-Of-Time (AOT) compiler
%global aot_arches      x86_64 %{aarch64}
# Set of architectures which support the serviceability agent
%global sa_arches       %{ix86} x86_64 sparcv9 sparc64 %{aarch64} %{power64} %{arm}
# Set of architectures which support class data sharing
# As of JDK-8005165 in OpenJDK 10, class sharing is not arch-specific
# However, it does segfault on the Zero assembler port, so currently JIT only
%global share_arches    %{jit_arches}
# Set of architectures for which we build the Shenandoah garbage collector
%global shenandoah_arches x86_64 %{aarch64}
# Set of architectures for which we build the Z garbage collector
%global zgc_arches x86_64
# Set of architectures for which alt-java has SSB mitigation
%global ssbd_arches x86_64
# Set of architectures where we verify backtraces with gdb
%global gdb_arches %{jit_arches} %{zero_arches}
# Set of architectures for which we have a portable build
%global portable_build_arches %{aarch64} %{ix86} %{power64} s390x x86_64

# By default, we build a slowdebug build during main build on JIT architectures
%if %{with slowdebug}
%ifarch %{debug_arches}
%global include_debug_build 1
%else
%global include_debug_build 0
%endif
%else
%global include_debug_build 0
%endif

# On certain architectures, we compile the Shenandoah GC
%ifarch %{shenandoah_arches}
%global use_shenandoah_hotspot 1
%global shenandoah_feature shenandoahgc
%else
%global use_shenandoah_hotspot 0
%global shenandoah_feature -shenandoahgc
%endif

# On certain architectures, we compile the ZGC
%ifarch %{zgc_arches}
%global use_zgc_hotspot 1
%global zgc_feature zgc
%else
%global use_zgc_hotspot 0
%global zgc_feature -zgc
%endif

# By default, we build a fastdebug build during main build only on fastdebug architectures
%if %{with fastdebug}
%ifarch %{fastdebug_arches}
%global include_fastdebug_build 1
%else
%global include_fastdebug_build 0
%endif
%else
%global include_fastdebug_build 0
%endif

%if %{include_debug_build}
%global slowdebug_build %{debug_suffix}
%else
%global slowdebug_build %{nil}
%endif

%if %{include_fastdebug_build}
%global fastdebug_build %{fastdebug_suffix}
%else
%global fastdebug_build %{nil}
%endif

# If you disable all builds, then the build fails
# Build and test slowdebug first as it provides the best diagnostics
%global build_loop %{slowdebug_build} %{fastdebug_build} %{normal_build}

%if 0%{?flatpak}
%global bootstrap_build false
%else
%ifarch %{bootstrap_arches}
%global bootstrap_build true
%else
%global bootstrap_build false
%endif
%endif

%if %{include_staticlibs}
# Extra target for producing the static-libraries. Separate from
# other targets since this target is configured to use in-tree
# AWT dependencies: lcms, libjpeg, libpng, libharfbuzz, giflib
# and possibly others
%global static_libs_target static-libs-image
%else
%global static_libs_target %{nil}
%endif

# RPM JDK builds keep the debug symbols internal, to be later stripped by RPM
%global debug_symbols internal

# unlike portables,the rpms have to use static_libs_target very dynamically
%global bootstrap_targets images
%global release_targets images docs-zip
# No docs nor bootcycle for debug builds
%global debug_targets images
# Target to use to just build HotSpot
%global hotspot_target hotspot

# JDK to use for bootstrapping
%global bootjdk /usr/lib/jvm/java-%{buildjdkver}-openjdk

# debugedit tool for rewriting ELF file paths
%global debugedit %{_rpmconfigdir}/debugedit

# Disable LTO as this causes build failures at the moment.
# See RHBZ#1861401
%define _lto_cflags %{nil}

# Filter out flags from the optflags macro that cause problems with the OpenJDK build
# We filter out -O flags so that the optimization of HotSpot is not lowered from O3 to O2
# We filter out -Wall which will otherwise cause HotSpot to produce hundreds of thousands of warnings (100+mb logs)
# We replace it with -Wformat (required by -Werror=format-security) and -Wno-cpp to avoid FORTIFY_SOURCE warnings
# We filter out -fexceptions as the HotSpot build explicitly does -fno-exceptions and it's otherwise the default for C++
%global ourflags %(echo %optflags | sed -e 's|-Wall|-Wformat -Wno-cpp|' | sed -r -e 's|-O[0-9]*||')
%global ourcppflags %(echo %ourflags | sed -e 's|-fexceptions||')
%global ourldflags %{__global_ldflags}

# With disabled nss is NSS deactivated, so NSS_LIBDIR can contain the wrong path
# the initialization must be here. Later the pkg-config have buggy behavior
# looks like openjdk RPM specific bug
# Always set this so the nss.cfg file is not broken
%global NSS_LIBDIR %(pkg-config --variable=libdir nss)

# In some cases, the arch used by the JDK does
# not match _arch.
# Also, in some cases, the machine name used by SystemTap
# does not match that given by _target_cpu
%ifarch x86_64
%global archinstall amd64
%global stapinstall x86_64
%endif
%ifarch ppc
%global archinstall ppc
%global stapinstall powerpc
%endif
%ifarch %{ppc64be}
%global archinstall ppc64
%global stapinstall powerpc
%endif
%ifarch %{ppc64le}
%global archinstall ppc64le
%global stapinstall powerpc
%endif
%ifarch %{ix86}
%global archinstall i686
%global stapinstall i386
%endif
%ifarch ia64
%global archinstall ia64
%global stapinstall ia64
%endif
%ifarch s390
%global archinstall s390
%global stapinstall s390
%endif
%ifarch s390x
%global archinstall s390x
%global stapinstall s390
%endif
%ifarch %{arm}
%global archinstall arm
%global stapinstall arm
%endif
%ifarch %{aarch64}
%global archinstall aarch64
%global stapinstall arm64
%endif
# 32 bit sparc, optimized for v9
%ifarch sparcv9
%global archinstall sparc
%global stapinstall %{_target_cpu}
%endif
# 64 bit sparc
%ifarch sparc64
%global archinstall sparcv9
%global stapinstall %{_target_cpu}
%endif
# Need to support noarch for srpm build
%ifarch noarch
%global archinstall %{nil}
%global stapinstall %{nil}
%endif

%ifarch %{systemtap_arches}
%global with_systemtap 1
%else
%global with_systemtap 0
%endif

# New Version-String scheme-style defines
%global featurever 11
%global interimver 0
%global updatever 25
%global patchver 0
# buildjdkver is usually same as %%{featurever},
# but in time of bootstrap of next jdk, it is featurever-1,
# and this it is better to change it here, on single place
%global buildjdkver %{featurever}
# Add LTS designator for RHEL builds
%if 0%{?rhel}
  %global lts_designator "LTS"
  %global lts_designator_zip -%{lts_designator}
%else
  %global lts_designator ""
  %global lts_designator_zip ""
%endif

# Define vendor information used by OpenJDK
%global oj_vendor Red Hat, Inc.
%global oj_vendor_url https://www.redhat.com/
# Define what url should JVM offer in case of a crash report
# order may be important, epel may have rhel declared
%if 0%{?epel}
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora%20EPEL&component=%{name}&version=epel%{epel}
%else
%if 0%{?fedora}
# Does not work for rawhide, keeps the version field empty
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&component=%{name}&version=%{fedora}
%else
%if 0%{?rhel}
%global oj_vendor_bug_url https://access.redhat.com/support/cases/
%else
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi
%endif
%endif
%endif
%global oj_vendor_version (Red_Hat-%{version}-%{portablerelease})

# Define IcedTea version used for SystemTap tapsets and desktop file
%global icedteaver      6.0.0pre00-c848b93a8598
# Define current Git revision for the FIPS support patches
%global fipsver f93a863b56
# Define JDK versions
%global javaver         %{featurever}
%global newjavaver %{featurever}.%{interimver}.%{updatever}.%{patchver}
# Strip up to 6 trailing zeros in newjavaver, as the JDK does, to get the correct version used in filenames
%global filever %(svn=%{newjavaver}; for i in 1 2 3 4 5 6 ; do svn=${svn%%.0} ; done; echo ${svn})
# The tag used to create the OpenJDK tarball
%global vcstag jdk-%{filever}+%{buildver}%{?tagsuffix:-%{tagsuffix}}

# Standard JPackage naming and versioning defines
%global origin          openjdk
%global origin_nice     OpenJDK
%global top_level_dir_name   %{vcstag}
%global top_level_dir_name_backup %{top_level_dir_name}-backup
%global buildver        9
# rpmrelease numbering must start at 2 to be later than the 9.0 RPM
%global rpmrelease      2
# Settings used by the portable build
%global portablerelease 1
%global portablerhel 8
%global portablesuffix el%{portablerhel}
%global portablebuilddir /builddir/build/BUILD

#%%global tagsuffix     %%{nil}
# Priority must be 8 digits in total; up to openjdk 1.8, we were using 18..... so when we moved to 11, we had to add another digit
%if %is_system_jdk
# Using 10 digits may overflow the int used for priority, so we combine the patch and build versions
# It is very unlikely we will ever have a patch version > 4 or a build version > 20, so we combine as (patch * 20) + build.
# This means 11.0.9.0+11 would have had a priority of 11000911 as before
# A 11.0.9.1+1 would have had a priority of 11000921 (20 * 1 + 1), thus ensuring it is bigger than 11.0.9.0+11
%global combiver $( expr 20 '*' %{patchver} + %{buildver} )
%global priority %( printf '%02d%02d%02d%02d' %{featurever} %{interimver} %{updatever} %{combiver} )
%else
# for non-default, using 1, so slowdebugs can have 0
%global priority %( printf '%08d' 1 )
%endif

# Define milestone (EA for pre-releases, GA for releases)
# Release will be (where N is usually a number starting at 1):
# - 0.N%%{?extraver}%%{?dist} for EA releases,
# - N%%{?extraver}{?dist} for GA releases
%global is_ga           1
%if %{is_ga}
%global ea_designator ""
%global ea_designator_zip ""
%global extraver %{nil}
%global eaprefix %{nil}
%else
%global ea_designator ea
%global ea_designator_zip -%{ea_designator}
%global extraver .%{ea_designator}
%global eaprefix 0.
%endif

# parametrized macros are order-sensitive
%global compatiblename  java-%{featurever}-%{origin}
%global fullversion     %{compatiblename}-%{version}-%{release}
# images directories from upstream build
%global jdkimage                jdk
%global static_libs_image       static-libs
# output dir stub
%define installoutputdir() %{expand:install/jdk%{featurever}.install%{?1}}
# we can copy the javadoc to not arched dir, or make it not noarch
%define uniquejavadocdir()    %{expand:%{fullversion}.%{_arch}%{?1}}
# main id and dir of this jdk
%define uniquesuffix()        %{expand:%{fullversion}.%{_arch}%{?1}}

#################################################################
# fix for https://bugzilla.redhat.com/show_bug.cgi?id=1111349
#         https://bugzilla.redhat.com/show_bug.cgi?id=1590796#c14
#         https://bugzilla.redhat.com/show_bug.cgi?id=1655938
%global _privatelibs libsplashscreen[.]so.*|libawt_xawt[.]so.*|libjli[.]so.*|libattach[.]so.*|libawt[.]so.*|libextnet[.]so.*|libawt_headless[.]so.*|libdt_socket[.]so.*|libfontmanager[.]so.*|libinstrument[.]so.*|libj2gss[.]so.*|libj2pcsc[.]so.*|libj2pkcs11[.]so.*|libjaas[.]so.*|libjavajpeg[.]so.*|libjdwp[.]so.*|libjimage[.]so.*|libjsound[.]so.*|liblcms[.]so.*|libmanagement[.]so.*|libmanagement_agent[.]so.*|libmanagement_ext[.]so.*|libmlib_image[.]so.*|libnet[.]so.*|libnio[.]so.*|libprefs[.]so.*|librmi[.]so.*|libsaproc[.]so.*|libsctp[.]so.*|libsunec[.]so.*|libsystemconf[.]so.*|libunpack[.]so.*|libzip[.]so.*%{freetype_lib}
%global _publiclibs libjawt[.]so.*|libjava[.]so.*|libjvm[.]so.*|libverify[.]so.*|libjsig[.]so.*
%if %is_system_jdk
%global __provides_exclude ^(%{_privatelibs})$
%global __requires_exclude ^(%{_privatelibs})$
# Never generate lib-style provides/requires for any debug packages
%global __provides_exclude_from ^.*/%{uniquesuffix -- %{debug_suffix_unquoted}}/.*$
%global __requires_exclude_from ^.*/%{uniquesuffix -- %{debug_suffix_unquoted}}/.*$
%global __provides_exclude_from ^.*/%{uniquesuffix -- %{fastdebug_suffix_unquoted}}/.*$
%global __requires_exclude_from ^.*/%{uniquesuffix -- %{fastdebug_suffix_unquoted}}/.*$
%else
# Don't generate provides/requires for JDK provided shared libraries at all.
%global __provides_exclude ^(%{_privatelibs}|%{_publiclibs})$
%global __requires_exclude ^(%{_privatelibs}|%{_publiclibs})$
%endif

%global etcjavasubdir     %{_sysconfdir}/java/java-%{javaver}-%{origin}
%define etcjavadir()      %{expand:%{etcjavasubdir}/%{uniquesuffix -- %{?1}}}
# Standard JPackage directories and symbolic links.
%define sdkdir()        %{expand:%{uniquesuffix -- %{?1}}}
%define jrelnk()        %{expand:jre-%{javaver}-%{origin}-%{version}-%{release}.%{_arch}%{?1}}

%define sdkbindir()     %{expand:%{_jvmdir}/%{sdkdir -- %{?1}}/bin}
%define jrebindir()     %{expand:%{_jvmdir}/%{sdkdir -- %{?1}}/bin}

%global alt_java_name     alt-java

%global rpm_state_dir %{_localstatedir}/lib/rpm-state/

# For flatpack builds hard-code /usr/sbin/alternatives,
# otherwise use %%{_sbindir} relative path.
%if 0%{?flatpak}
%global alternatives_requires /usr/sbin/alternatives
%else
%global alternatives_requires %{_sbindir}/alternatives
%endif

%global family %{name}.%{_arch}
%global family_noarch  %{name}

%if %{with_systemtap}
# Where to install systemtap tapset (links)
# We would like these to be in a package specific sub-dir,
# but currently systemtap doesn't support that, so we have to
# use the root tapset dir for now. To distinguish between 64
# and 32 bit architectures we place the tapsets under the arch
# specific dir (note that systemtap will only pickup the tapset
# for the primary arch for now). Systemtap uses the machine name
# aka target_cpu as architecture specific directory name.
%global tapsetroot /usr/share/systemtap
%global tapsetdirttapset %{tapsetroot}/tapset/
%global tapsetdir %{tapsetdirttapset}/%{stapinstall}
%endif

# not-duplicated scriptlets for normal/debug packages
%global update_desktop_icons /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%define save_alternatives() %{expand:
  # warning! alternatives are localised!
  # LANG=cs_CZ.UTF-8  alternatives --display java | head
  # LANG=en_US.UTF-8  alternatives --display java | head
  function nonLocalisedAlternativesDisplayOfMaster() {
    LANG=en_US.UTF-8 alternatives --display "$MASTER"
  }
  function headOfAbove() {
    nonLocalisedAlternativesDisplayOfMaster | head -n $1
  }
  MASTER="%{?1}"
  LOCAL_LINK="%{?2}"
  FAMILY="%{?3}"
  rm -f %{_localstatedir}/lib/rpm-state/"$MASTER"_$FAMILY > /dev/null
  if nonLocalisedAlternativesDisplayOfMaster > /dev/null ; then
      if headOfAbove 1 | grep -q manual ; then
        if headOfAbove 2 | tail -n 1 | grep -q %{compatiblename} ; then
           headOfAbove 2  > %{_localstatedir}/lib/rpm-state/"$MASTER"_"$FAMILY"
        fi
      fi
  fi
}

%define save_and_remove_alternatives() %{expand:
  if [ "x$debug"  == "xtrue" ] ; then
    set -x
  fi
  upgrade1_uninstal0=%{?3}
  if [ "0$upgrade1_uninstal0" -gt 0 ] ; then # removal of this condition will cause persistence between uninstall
    %{save_alternatives %{?1} %{?2} %{?4}}
  fi
  alternatives --remove  "%{?1}" "%{?2}"
}

%define set_if_needed_alternatives() %{expand:
  MASTER="%{?1}"
  FAMILY="%{?2}"
  ALTERNATIVES_FILE="%{_localstatedir}/lib/rpm-state/$MASTER"_"$FAMILY"
  if [ -e  "$ALTERNATIVES_FILE" ] ; then
    rm "$ALTERNATIVES_FILE"
    alternatives --set $MASTER $FAMILY
  fi
}


%define post_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
exit 0
}

%define alternatives_java_install() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
key=java
alternatives \\
  --install %{_bindir}/java $key %{jrebindir -- %{?1}}/java $PRIORITY  --family %{family} \\
  --slave %{_jvmdir}/jre jre %{_jvmdir}/%{sdkdir -- %{?1}} \\
  --slave %{_bindir}/%{alt_java_name} %{alt_java_name} %{jrebindir -- %{?1}}/%{alt_java_name} \\
  --slave %{_bindir}/jcmd jcmd %{sdkbindir -- %{?1}}/jcmd \\
  --slave %{_bindir}/jjs jjs %{jrebindir -- %{?1}}/jjs \\
  --slave %{_bindir}/keytool keytool %{jrebindir -- %{?1}}/keytool \\
  --slave %{_bindir}/pack200 pack200 %{jrebindir -- %{?1}}/pack200 \\
  --slave %{_bindir}/rmid rmid %{jrebindir -- %{?1}}/rmid \\
  --slave %{_bindir}/rmiregistry rmiregistry %{jrebindir -- %{?1}}/rmiregistry \\
  --slave %{_bindir}/unpack200 unpack200 %{jrebindir -- %{?1}}/unpack200 \\
  --slave %{_mandir}/man1/java.1$ext java.1$ext \\
  %{_mandir}/man1/java-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/%{alt_java_name}.1$ext %{alt_java_name}.1$ext \\
  %{_mandir}/man1/%{alt_java_name}-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jcmd.1$ext jcmd.1$ext \\
  %{_mandir}/man1/jcmd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jjs.1$ext jjs.1$ext \\
  %{_mandir}/man1/jjs-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/keytool.1$ext keytool.1$ext \\
  %{_mandir}/man1/keytool-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/pack200.1$ext pack200.1$ext \\
  %{_mandir}/man1/pack200-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmid.1$ext rmid.1$ext \\
  %{_mandir}/man1/rmid-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmiregistry.1$ext rmiregistry.1$ext \\
  %{_mandir}/man1/rmiregistry-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/unpack200.1$ext unpack200.1$ext \\
  %{_mandir}/man1/unpack200-%{uniquesuffix -- %{?1}}.1$ext

%{set_if_needed_alternatives $key %{family}}

for X in %{origin} %{javaver} ; do
  key=jre_"$X"
  alternatives --install %{_jvmdir}/jre-"$X" $key %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY --family %{family}
  %{set_if_needed_alternatives $key %{family}}
done

key=jre_%{javaver}_%{origin}
alternatives --install %{_jvmdir}/jre-%{javaver}-%{origin} $key %{_jvmdir}/%{jrelnk -- %{?1}} $PRIORITY  --family %{family}
%{set_if_needed_alternatives $key %{family}}
}

%define post_headless() %{expand:
%ifarch %{share_arches}
%{jrebindir -- %{?1}}/java -Xshare:dump >/dev/null 2>/dev/null
%endif

update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

# see pretrans where this file is declared
# also see that pretrans is only for non-debug
if [ ! "%{?1}" == %{debug_suffix} ]; then
  if [ -f %{_libexecdir}/copy_jdk_configs_fixFiles.sh ] ; then
    sh  %{_libexecdir}/copy_jdk_configs_fixFiles.sh %{rpm_state_dir}/%{name}.%{_arch}  %{_jvmdir}/%{sdkdir -- %{?1}}
  fi
fi

exit 0
}

%define postun_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}


%define postun_headless() %{expand:
  if [ "x$debug"  == "xtrue" ] ; then
    set -x
  fi
  post_state=$1 # from postun, https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
  %{save_and_remove_alternatives  java  %{jrebindir -- %{?1}}/java $post_state %{family}}
  %{save_and_remove_alternatives  jre_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}} $post_state %{family}}
  %{save_and_remove_alternatives  jre_%{javaver} %{_jvmdir}/%{sdkdir -- %{?1}} $post_state %{family}}
  %{save_and_remove_alternatives  jre_%{javaver}_%{origin} %{_jvmdir}/%{jrelnk -- %{?1}} $post_state %{family}}
}

%define posttrans_script() %{expand:
%{update_desktop_icons}
}


%define alternatives_javac_install() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
key=javac
alternatives \\
  --install %{_bindir}/javac $key %{sdkbindir -- %{?1}}/javac $PRIORITY  --family %{family} \\
  --slave %{_jvmdir}/java java_sdk %{_jvmdir}/%{sdkdir -- %{?1}} \\
%ifarch %{aot_arches}
  --slave %{_bindir}/jaotc jaotc %{sdkbindir -- %{?1}}/jaotc \\
%endif
  --slave %{_bindir}/jlink jlink %{sdkbindir -- %{?1}}/jlink \\
  --slave %{_bindir}/jmod jmod %{sdkbindir -- %{?1}}/jmod \\
%ifarch %{sa_arches}
%ifnarch %{zero_arches}
  --slave %{_bindir}/jhsdb jhsdb %{sdkbindir -- %{?1}}/jhsdb \\
%endif
%endif
  --slave %{_bindir}/jar jar %{sdkbindir -- %{?1}}/jar \\
  --slave %{_bindir}/jarsigner jarsigner %{sdkbindir -- %{?1}}/jarsigner \\
  --slave %{_bindir}/javadoc javadoc %{sdkbindir -- %{?1}}/javadoc \\
  --slave %{_bindir}/javap javap %{sdkbindir -- %{?1}}/javap \\
  --slave %{_bindir}/jconsole jconsole %{sdkbindir -- %{?1}}/jconsole \\
  --slave %{_bindir}/jdb jdb %{sdkbindir -- %{?1}}/jdb \\
  --slave %{_bindir}/jdeps jdeps %{sdkbindir -- %{?1}}/jdeps \\
  --slave %{_bindir}/jdeprscan jdeprscan %{sdkbindir -- %{?1}}/jdeprscan \\
  --slave %{_bindir}/jfr jfr %{sdkbindir -- %{?1}}/jfr \\
  --slave %{_bindir}/jimage jimage %{sdkbindir -- %{?1}}/jimage \\
  --slave %{_bindir}/jinfo jinfo %{sdkbindir -- %{?1}}/jinfo \\
  --slave %{_bindir}/jmap jmap %{sdkbindir -- %{?1}}/jmap \\
  --slave %{_bindir}/jps jps %{sdkbindir -- %{?1}}/jps \\
  --slave %{_bindir}/jrunscript jrunscript %{sdkbindir -- %{?1}}/jrunscript \\
  --slave %{_bindir}/jshell jshell %{sdkbindir -- %{?1}}/jshell \\
  --slave %{_bindir}/jstack jstack %{sdkbindir -- %{?1}}/jstack \\
  --slave %{_bindir}/jstat jstat %{sdkbindir -- %{?1}}/jstat \\
  --slave %{_bindir}/jstatd jstatd %{sdkbindir -- %{?1}}/jstatd \\
  --slave %{_bindir}/rmic rmic %{sdkbindir -- %{?1}}/rmic \\
  --slave %{_bindir}/serialver serialver %{sdkbindir -- %{?1}}/serialver \\
  --slave %{_mandir}/man1/jar.1$ext jar.1$ext \\
  %{_mandir}/man1/jar-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jarsigner.1$ext jarsigner.1$ext \\
  %{_mandir}/man1/jarsigner-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javac.1$ext javac.1$ext \\
  %{_mandir}/man1/javac-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javadoc.1$ext javadoc.1$ext \\
  %{_mandir}/man1/javadoc-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javap.1$ext javap.1$ext \\
  %{_mandir}/man1/javap-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jconsole.1$ext jconsole.1$ext \\
  %{_mandir}/man1/jconsole-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jdb.1$ext jdb.1$ext \\
  %{_mandir}/man1/jdb-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jdeps.1$ext jdeps.1$ext \\
  %{_mandir}/man1/jdeps-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jinfo.1$ext jinfo.1$ext \\
  %{_mandir}/man1/jinfo-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jmap.1$ext jmap.1$ext \\
  %{_mandir}/man1/jmap-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jps.1$ext jps.1$ext \\
  %{_mandir}/man1/jps-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jrunscript.1$ext jrunscript.1$ext \\
  %{_mandir}/man1/jrunscript-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstack.1$ext jstack.1$ext \\
  %{_mandir}/man1/jstack-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstat.1$ext jstat.1$ext \\
  %{_mandir}/man1/jstat-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstatd.1$ext jstatd.1$ext \\
  %{_mandir}/man1/jstatd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmic.1$ext rmic.1$ext \\
  %{_mandir}/man1/rmic-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/serialver.1$ext serialver.1$ext \\
  %{_mandir}/man1/serialver-%{uniquesuffix -- %{?1}}.1$ext

%{set_if_needed_alternatives  $key %{family}}

for X in %{origin} %{javaver} ; do
  key=java_sdk_"$X"
  alternatives --install %{_jvmdir}/java-"$X" $key %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY  --family %{family}
  %{set_if_needed_alternatives  $key %{family}}
done

key=java_sdk_%{javaver}_%{origin}
alternatives --install %{_jvmdir}/java-%{javaver}-%{origin} $key %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY  --family %{family}
%{set_if_needed_alternatives  $key %{family}}
}

%define post_devel() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

exit 0
}

%define postun_devel() %{expand:
  if [ "x$debug"  == "xtrue" ] ; then
    set -x
  fi
  post_state=$1 # from postun, https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
  %{save_and_remove_alternatives  javac %{sdkbindir -- %{?1}}/javac $post_state %{family}}
  %{save_and_remove_alternatives  java_sdk_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}} $post_state %{family}}
  %{save_and_remove_alternatives  java_sdk_%{javaver} %{_jvmdir}/%{sdkdir -- %{?1}} $post_state %{family}}
  %{save_and_remove_alternatives  java_sdk_%{javaver}_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}} $post_state %{family}}

update-desktop-database %{_datadir}/applications &> /dev/null || :

if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}

%define posttrans_devel() %{expand:
%{alternatives_javac_install --  %{?1}}
%{update_desktop_icons}
}

%define alternatives_javadoc_install() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

key=javadocdir
alternatives --install %{_javadocdir}/java $key %{_javadocdir}/%{uniquejavadocdir -- %{?1}}/api $PRIORITY  --family %{family_noarch}
%{set_if_needed_alternatives  $key %{family_noarch}}
exit 0
}

%define postun_javadoc() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
  post_state=$1 # from postun, https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
  %{save_and_remove_alternatives  javadocdir  %{_javadocdir}/%{uniquejavadocdir -- %{?1}}/api $post_state %{family_noarch}}
exit 0
}

%define alternatives_javadoczip_install() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi
key=javadoczip
alternatives --install %{_javadocdir}/java-zip $key %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip $PRIORITY  --family %{family_noarch}
%{set_if_needed_alternatives  $key %{family_noarch}}
exit 0
}

%define postun_javadoc_zip() %{expand:
  if [ "x$debug"  == "xtrue" ] ; then
    set -x
  fi
  post_state=$1 # from postun, https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
  %{save_and_remove_alternatives  javadoczip  %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip $post_state %{family_noarch}}
exit 0
}

%define files_jre() %{expand:
%{_datadir}/icons/hicolor/*x*/apps/java-%{javaver}-%{origin}.png
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libsplashscreen.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libawt_xawt.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjawt.so
}


%define files_jre_headless() %{expand:
%license %{_jvmdir}/%{sdkdir -- %{?1}}/legal
%doc %{_defaultdocdir}/%{uniquejavadocdir -- %{?1}}/NEWS
%doc %{_defaultdocdir}/%{uniquejavadocdir -- %{?1}}/README.md
%doc %{_defaultdocdir}/%{uniquejavadocdir -- %{?1}}/java-%{featurever}-openjdk-portable.specfile
%dir %{_sysconfdir}/.java/.systemPrefs
%dir %{_sysconfdir}/.java
%dir %{_jvmdir}/%{sdkdir -- %{?1}}
%{_jvmdir}/%{sdkdir -- %{?1}}/release
%{_jvmdir}/%{jrelnk -- %{?1}}
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/bin
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/java
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/%{alt_java_name}
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jcmd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jjs
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/keytool
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/pack200
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmid
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmiregistry
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/unpack200
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib
%ifarch %{jit_arches}
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/classlist
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jexec
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jspawnhelper
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jrt-fs.jar
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/modules
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/psfont.properties.ja
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/psfontj2d.properties
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/tzdb.dat
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib/jli
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jli/libjli.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jvm.cfg
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libattach.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libawt.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libextnet.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjsig.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libawt_headless.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libdt_socket.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libfontmanager.so
%if ! %{system_libs}
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libfreetype.so
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libinstrument.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libj2gss.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libj2pcsc.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libj2pkcs11.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjaas.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjava.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjavajpeg.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjdwp.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjimage.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libjsound.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/liblcms.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libmanagement.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libmanagement_agent.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libmanagement_ext.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libmlib_image.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libnet.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libnio.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libprefs.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/librmi.so
# Some architectures don't have the serviceability agent
%ifarch %{sa_arches}
%ifnarch %{zero_arches}
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libsaproc.so
%endif
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libsctp.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libsunec.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libsystemconf.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libunpack.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libverify.so
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/libzip.so
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib/jfr
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jfr/default.jfc
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jfr/profile.jfc
%{_mandir}/man1/java-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/%{alt_java_name}-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jcmd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jjs-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/keytool-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/pack200-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmid-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmiregistry-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/unpack200-%{uniquesuffix -- %{?1}}.1*
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/server/
%ifarch %{share_arches}
%attr(444, root, root) %ghost %{_jvmdir}/%{sdkdir -- %{?1}}/lib/server/classes.jsa
%endif
%dir %{etcjavasubdir}
%dir %{etcjavadir -- %{?1}}
%dir %{etcjavadir -- %{?1}}/lib
%dir %{etcjavadir -- %{?1}}/lib/security
%{etcjavadir -- %{?1}}/lib/security/cacerts
%dir %{etcjavadir -- %{?1}}/conf
%dir %{etcjavadir -- %{?1}}/conf/management
%dir %{etcjavadir -- %{?1}}/conf/security
%dir %{etcjavadir -- %{?1}}/conf/security/policy
%dir %{etcjavadir -- %{?1}}/conf/security/policy/limited
%dir %{etcjavadir -- %{?1}}/conf/security/policy/unlimited
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/default.policy
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/blocked.certs
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/public_suffix_list.dat
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/limited/exempt_local.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/limited/default_local.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/limited/default_US_export.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/unlimited/default_local.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/policy/unlimited/default_US_export.policy
 %{etcjavadir -- %{?1}}/conf/security/policy/README.txt
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/java.policy
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/java.security
%config(noreplace) %{etcjavadir -- %{?1}}/conf/logging.properties
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/nss.cfg
%config(noreplace) %{etcjavadir -- %{?1}}/conf/security/nss.fips.cfg
%config(noreplace) %{etcjavadir -- %{?1}}/conf/management/jmxremote.access
# This is a configuration template and thus not config-noreplace
%config %{etcjavadir -- %{?1}}/conf/management/jmxremote.password.template
%config(noreplace) %{etcjavadir -- %{?1}}/conf/management/management.properties
%config(noreplace) %{etcjavadir -- %{?1}}/conf/net.properties
%config(noreplace) %{etcjavadir -- %{?1}}/conf/sound.properties
%{_jvmdir}/%{sdkdir -- %{?1}}/conf
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/security
%if %is_system_jdk
%if %{is_release_build -- %{?1}}
# RHEL-11313; alternatives not owned by packages
%ghost %{_bindir}/java
%ghost %{_jvmdir}/jre
%ghost %{_bindir}/%{alt_java_name}
%ghost %{_bindir}/jcmd
%ghost %{_bindir}/jjs
%ghost %{_bindir}/keytool
%ghost %{_bindir}/pack200
%ghost %{_bindir}/rmid
%ghost %{_bindir}/rmiregistry
%ghost %{_bindir}/unpack200
%ghost %{_jvmdir}/jre-%{origin}
%ghost %{_jvmdir}/jre-%{javaver}
%ghost %{_jvmdir}/jre-%{javaver}-%{origin}
%endif
%endif
# https://bugzilla.redhat.com/show_bug.cgi?id=1820172
# https://docs.fedoraproject.org/en-US/packaging-guidelines/Directory_Replacement/
%ghost %{_jvmdir}/%{sdkdir -- %{?1}}/conf.rpmmoved
%ghost %{_jvmdir}/%{sdkdir -- %{?1}}/lib/security.rpmmoved
}

%define files_devel() %{expand:
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/bin
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jar
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jarsigner
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javac
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javadoc
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javap
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jconsole
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdb
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdeps
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdeprscan
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jfr
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jimage
# Some architectures don't have the serviceability agent
%ifarch %{sa_arches}
%ifnarch %{zero_arches}
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jhsdb
%endif
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jinfo
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jlink
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jmap
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jmod
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jps
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jrunscript
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jshell
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstack
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstat
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstatd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmic
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/serialver
%ifarch %{aot_arches}
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jaotc
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/include
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/ct.sym
%if %{with_systemtap}
%{_jvmdir}/%{sdkdir -- %{?1}}/tapset
%endif
%{_datadir}/applications/*jconsole%{?1}.desktop
%{_mandir}/man1/jar-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jarsigner-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javac-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javadoc-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javap-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jconsole-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jdb-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jdeps-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jinfo-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jmap-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jps-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jrunscript-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstack-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstat-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstatd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmic-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/serialver-%{uniquesuffix -- %{?1}}.1*
%if %{with_systemtap}
%dir %{tapsetroot}
%dir %{tapsetdirttapset}
%dir %{tapsetdir}
%{tapsetdir}/*%{_arch}%{?1}.stp
%endif
%if %is_system_jdk
%if %{is_release_build -- %{?1}}
# RHEL-11313; alternatives not owned by packages
%ghost %{_bindir}/javac
%ghost %{_jvmdir}/java
%ghost %{_bindir}/jaotc
%ghost %{_bindir}/jlink
%ghost %{_bindir}/jmod
%ghost %{_bindir}/jhsdb
%ghost %{_bindir}/jar
%ghost %{_bindir}/jarsigner
%ghost %{_bindir}/javadoc
%ghost %{_bindir}/javap
%ghost %{_bindir}/jconsole
%ghost %{_bindir}/jdb
%ghost %{_bindir}/jdeps
%ghost %{_bindir}/jdeprscan
%ghost %{_bindir}/jfr
%ghost %{_bindir}/jimage
%ghost %{_bindir}/jinfo
%ghost %{_bindir}/jmap
%ghost %{_bindir}/jps
%ghost %{_bindir}/jrunscript
%ghost %{_bindir}/jshell
%ghost %{_bindir}/jstack
%ghost %{_bindir}/jstat
%ghost %{_bindir}/jstatd
%ghost %{_bindir}/rmic
%ghost %{_bindir}/serialver
%ghost %{_jvmdir}/java-%{origin}
%ghost %{_jvmdir}/java-%{javaver}
%ghost %{_jvmdir}/java-%{javaver}-%{origin}
%endif
%endif
}

%define files_jmods() %{expand:
%{_jvmdir}/%{sdkdir -- %{?1}}/jmods
}

%define files_demo() %{expand:
%license %{_jvmdir}/%{sdkdir -- %{?1}}/legal
%{_jvmdir}/%{sdkdir -- %{?1}}/demo
%{_jvmdir}/%{sdkdir -- %{?1}}/sample
}

%define files_src() %{expand:
%license %{_jvmdir}/%{sdkdir -- %{?1}}/legal
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/src.zip
}

%define files_static_libs() %{expand:
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib/static
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib/static/linux-%{archinstall}
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib/static/linux-%{archinstall}/glibc
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/static/linux-%{archinstall}/glibc/lib*.a
}

%define files_javadoc() %{expand:
%doc %{_javadocdir}/%{uniquejavadocdir -- %{?1}}
%license %{_jvmdir}/%{sdkdir -- %{?1}}/legal
%if %is_system_jdk
%if %{is_release_build -- %{?1}}
%ghost %{_javadocdir}/java
%endif
%endif
}

%define files_javadoc_zip() %{expand:
%doc %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip
%license %{_jvmdir}/%{sdkdir -- %{?1}}/legal
%if %is_system_jdk
%if %{is_release_build -- %{?1}}
%ghost %{_javadocdir}/java-zip
%endif
%endif
}

# not-duplicated requires/provides/obsoletes for normal/debug packages
%define java_rpo() %{expand:
Requires: fontconfig%{?_isa}
Requires: xorg-x11-fonts-Type1
# Require libXcomposite explicitly since it's only dynamically loaded
# at runtime. Fixes screenshot issues. See JDK-8150954.
Requires: libXcomposite%{?_isa}
# Requires rest of java
Requires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
# for java-X-openjdk package's desktop binding
%if 0%{?rhel} >= 8
Recommends: gtk3%{?_isa}
%endif

Provides: java-%{javaver}-%{origin}%{?1} = %{epoch}:%{version}-%{release}

# Standard JPackage base provides
Provides: jre-%{javaver}%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{javaver}-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java%{?1} = %{epoch}:%{version}-%{release}
Provides: jre%{?1} = %{epoch}:%{version}-%{release}
%endif
}

%define java_headless_rpo() %{expand:
# Require /etc/pki/java/cacerts
Requires: ca-certificates
# Require javapackages-filesystem for ownership of /usr/lib/jvm/ and macros
Requires: javapackages-filesystem
# 2024a required as of JDK-8325150
# Use 2023d until 2024a is in the buildroot
Requires: tzdata-java >= 2024a
# for support of kernel stream control
# libsctp.so.1 is being `dlopen`ed on demand
Requires: lksctp-tools%{?_isa}
%if ! 0%{?flatpak}
# tool to copy jdk's configs - should be Recommends only, but then only dnf/yum enforce it,
# not rpm transaction and so no configs are persisted when pure rpm -u is run. It may be
# considered as regression
Requires: copy-jdk-configs >= 3.3
OrderWithRequires: copy-jdk-configs
%endif
# for printing support
Requires: cups-libs
# for system security properties
Requires: crypto-policies
# for FIPS PKCS11 provider
Requires: nss
# Post requires alternatives to install tool alternatives
Requires(post):   %{alternatives_requires}
# Postun requires alternatives to uninstall tool alternatives
Requires(postun): %{alternatives_requires}
# for optional support of kernel stream control, card reader and printing bindings
%if 0%{?rhel} >= 8
Suggests: lksctp-tools%{?_isa}, pcsc-lite-devel%{?_isa}
%endif

# Standard JPackage base provides
Provides: jre-%{javaver}-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{javaver}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-headless%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: java-headless%{?1} = %{epoch}:%{version}-%{release}
%endif
}

%define java_devel_rpo() %{expand:
# Requires base package
Requires:         %{name}%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
# Post requires alternatives to install tool alternatives
Requires(post):   %{alternatives_requires}
# Postun requires alternatives to uninstall tool alternatives
Requires(postun): %{alternatives_requires}

# Standard JPackage devel provides
Provides: java-sdk-%{javaver}-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-sdk-%{javaver}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-devel%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-devel%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-devel-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-sdk-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-devel%{?1} = %{epoch}:%{version}-%{release}
Provides: java-sdk%{?1} = %{epoch}:%{version}-%{release}
%endif
}

%define java_static_libs_rpo() %{expand:
Requires:         %{name}-devel%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
}

%define java_jmods_rpo() %{expand:
# Requires devel package
# as jmods are bytecode, they should be OK without any _isa
Requires:         %{name}-devel%{?1} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1} = %{epoch}:%{version}-%{release}

Provides: java-%{javaver}-jmods%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-jmods%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-jmods%{?1} = %{epoch}:%{version}-%{release}
%endif
}

%define java_demo_rpo() %{expand:
Requires: %{name}%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}

Provides: java-%{javaver}-demo%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-demo%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-demo%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{origin}-demo%{?1} = %{epoch}:%{version}-%{release}
%endif
}

%define java_javadoc_rpo() %{expand:
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
# Post requires alternatives to install javadoc alternative
Requires(post):   %{alternatives_requires}
# Postun requires alternatives to uninstall javadoc alternative
Requires(postun): %{alternatives_requires}

# Standard JPackage javadoc provides
Provides: java-%{javaver}-javadoc%{?1}%{?2} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-javadoc%{?1}%{?2} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-javadoc%{?1}%{?2} = %{epoch}:%{version}-%{release}
%endif
}

%define java_src_rpo() %{expand:
Requires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}

# Standard JPackage sources provides
Provides: java-%{javaver}-src%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-src%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-src%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{origin}-src%{?1} = %{epoch}:%{version}-%{release}
%endif
}

# Prevent brp-java-repack-jars from being run
%global __jar_repack 0

Name:    java-%{javaver}-%{origin}
Version: %{newjavaver}.%{buildver}
Release: %{?eaprefix}%{rpmrelease}%{?extraver}%{?dist}
# Equivalent for the portable build
%global prelease %{?eaprefix}%{portablerelease}%{?extraver}
# java-1.5.0-ibm from jpackage.org set Epoch to 1 for unknown reasons
# and this change was brought into RHEL-4. java-1.5.0-ibm packages
# also included the epoch in their virtual provides. This created a
# situation where in-the-wild java-1.5.0-ibm packages provided "java =
# 1:1.5.0". In RPM terms, "1.6.0 < 1:1.5.0" since 1.6.0 is
# interpreted as 0:1.6.0. So the "java >= 1.6.0" requirement would be
# satisfied by the 1:1.5.0 packages. Thus we need to set the epoch in
# JDK package >= 1.6.0 to 1, and packages referring to JDK virtual
# provides >= 1.6.0 must specify the epoch, "java >= 1:1.6.0".

Epoch:   1
Summary: %{origin_nice} %{featurever} Runtime Environment
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

# HotSpot code is licensed under GPLv2
# JDK library code is licensed under GPLv2 with the Classpath exception
# The Apache license is used in code taken from Apache projects (primarily xalan & xerces)
# DOM levels 2 & 3 and the XML digital signature schemas are licensed under the W3C Software License
# The JSR166 concurrency code is in the public domain
# The BSD and MIT licenses are used for a number of third-party libraries (see ADDITIONAL_LICENSE_INFO)
# The OpenJDK source tree includes:
# - JPEG library (IJG), zlib & libpng (zlib), giflib (MIT), harfbuzz (ISC),
# - freetype (FTL), jline (BSD) and LCMS (MIT)
# - jquery (MIT), jdk.crypto.cryptoki PKCS 11 wrapper (RSA)
# - public_suffix_list.dat from publicsuffix.org (MPLv2.0)
# The test code includes copies of NSS under the Mozilla Public License v2.0
# The PCSClite headers are under a BSD with advertising license
# The elliptic curve cryptography (ECC) source code is licensed under the LGPLv2.1 or any later version
License:  ASL 1.1 and ASL 2.0 and BSD and BSD with advertising and GPL+ and GPLv2 and GPLv2 with exceptions and IJG and LGPLv2+ and MIT and MPLv2.0 and Public Domain and W3C and zlib and ISC and FTL and RSA
URL:      http://openjdk.java.net/


# to regenerate source0 (jdk) run update_package.sh
# update_package.sh contains hard-coded repos, revisions, tags, and projects to regenerate the source archives
Source0: openjdk-jdk%{featurever}u-%{vcstag}.tar.xz

# Use 'icedtea_sync.sh' to update the following
# They are based on code contained in the IcedTea project (6.x).
# Systemtap tapsets. Zipped up to keep it small.
Source8: tapsets-icedtea-%{icedteaver}.tar.xz

# Desktop files. Adapted from IcedTea
Source9: jconsole.desktop.in

# nss configuration file
Source11: nss.cfg.in

# Removed libraries that we link instead
Source12: remove-intree-libraries.sh

# Ensure we aren't using the limited crypto policy
Source13: TestCryptoLevel.java

# Ensure ECDSA is working
Source14: TestECDSA.java

# Verify system crypto (policy) can be disabled via a property
Source15: TestSecurityProperties.java

# Ensure vendor settings are correct
Source16: CheckVendor.java

# nss fips configuration file
Source17: nss.fips.cfg.in

# Ensure translations are available for new timezones
Source18: TestTranslations.java

# Include portable spec and instructions on how to rebuild
Source19: README.md
Source20: java-%{featurever}-openjdk-portable.specfile

# Setup variables to reference correct sources
%global releasezip %{_jvmdir}/%{name}-%{version}-%{prelease}.portable.unstripped.jdk.%{_arch}.tar.xz
%global staticlibzip %{_jvmdir}/%{name}-%{version}-%{prelease}.portable.static-libs.%{_arch}.tar.xz
%global docszip %{_jvmdir}/%{name}-%{version}-%{prelease}.portable.docs.%{_arch}.tar.xz
%global misczip %{_jvmdir}/%{name}-%{version}-%{prelease}.portable.misc.%{_arch}.tar.xz
%global slowdebugzip %{_jvmdir}/%{name}-%{version}-%{prelease}.portable.slowdebug.jdk.%{_arch}.tar.xz
%global slowdebugstaticlibzip %{_jvmdir}/%{name}-%{version}-%{prelease}.portable.slowdebug.static-libs.%{_arch}.tar.xz
%global fastdebugzip %{_jvmdir}/%{name}-%{version}-%{prelease}.portable.fastdebug.jdk.%{_arch}.tar.xz
%global fastdebugstaticlibzip %{_jvmdir}/%{name}-%{version}-%{prelease}.portable.fastdebug.static-libs.%{_arch}.tar.xz

############################################
#
# RPM/distribution specific patches
#
############################################

# Ignore AWTError when assistive technologies are loaded
Patch1:    rh1648242-accessible_toolkit_crash_do_not_break_jvm.patch
# NSS via SunPKCS11 Provider (disabled due to memory leak).
Patch1000: rh1648249-add_commented_out_nss_cfg_provider_to_java_security.patch
# RH1750419: enable build of speculative store bypass hardened alt-java (CVE-2018-3639)
Patch600: rh1750419-redhat_alt_java.patch
# RH1582504: Use RSA as default for keytool, as DSA is disabled in all crypto policies except LEGACY
Patch1003: rh1842572-rsa_default_for_keytool.patch

# Crypto policy and FIPS support patches
# Patch is generated from the fips tree at https://github.com/rh-openjdk/jdk11u/tree/fips
# as follows: git diff %%{vcstag} src make test > fips-11u-$(git show -s --format=%h HEAD).patch
# Diff is limited to src and make subdirectories to exclude .github changes
# Fixes currently included:
# PR3694, RH1340845: Add security.useSystemPropertiesFile option to java.security to use system crypto policy
# PR3695: Allow use of system crypto policy to be disabled by the user
# RH1655466: Support RHEL FIPS mode using SunPKCS11 provider
# RH1818909: No ciphersuites availale for SSLSocket in FIPS mode
# RH1860986: Disable TLSv1.3 with the NSS-FIPS provider until PKCS#11 v3.0 support is available
# RH1915071: Always initialise JavaSecuritySystemConfiguratorAccess
# RH1929465: Improve system FIPS detection
# RH1996182: Login to the NSS software token in FIPS mode
# RH1991003: Allow plain key import unless com.redhat.fips.plainKeySupport is set to false
# RH2021263: Make sure java.security.Security is initialised when retrieving JavaSecuritySystemConfiguratorAccess instance
# RH2021263: Return in C code after having generated Java exception
# RH2052819: Improve Security initialisation, now FIPS support no longer relies on crypto policy support
# RH2051605: Detect NSS at Runtime for FIPS detection
# RH2052819: Fix FIPS reliance on crypto policies
# RH2036462: sun.security.pkcs11.wrapper.PKCS11.getInstance breakage
# RH2090378: Revert to disabling system security properties and FIPS mode support together
Patch1001: fips-11u-%{fipsver}.patch

#############################################
#
# Shenandoah specific patches
#
#############################################

# Currently empty

#############################################
#
# Upstreamable patches
#
# This section includes patches which need to
# be reviewed & pushed to the current development
# tree of OpenJDK.
#############################################
Patch3:    rh649512-remove_uses_of_far_in_jpeg_libjpeg_turbo_1_4_compat_for_jdk10_and_up.patch

#############################################
#
# Backportable patches
#
# This section includes patches which are
# present in the current development tree, but
# need to be reviewed & pushed to the appropriate
# updates tree of OpenJDK.
#############################################
Patch2002: jdk8242332-rh2108712-sha3-sunpkcs11.patch

#############################################
#
# Patches appearing in 11.0.23
#
# This section includes patches which are present
# in the listed OpenJDK 8u release and should be
# able to be removed once that release is out
# and used by this RPM.
#############################################

BuildRequires: autoconf
BuildRequires: automake
BuildRequires: alsa-lib-devel
BuildRequires: binutils
BuildRequires: cups-devel
BuildRequires: desktop-file-utils
# elfutils only are OK for build without AOT
BuildRequires: elfutils-devel
BuildRequires: fontconfig-devel
BuildRequires: gcc-c++
BuildRequires: gdb
BuildRequires: libxslt
BuildRequires: libX11-devel
BuildRequires: libXi-devel
BuildRequires: libXinerama-devel
BuildRequires: libXrandr-devel
BuildRequires: libXrender-devel
BuildRequires: libXt-devel
BuildRequires: libXtst-devel
# Requirement for setting up nss.cfg and nss.fips.cfg
BuildRequires: nss-devel
# Requirement for system security property test
BuildRequires: crypto-policies
BuildRequires: pkgconfig
BuildRequires: xorg-x11-proto-devel
BuildRequires: zip
BuildRequires: unzip
BuildRequires: javapackages-filesystem
%if %{include_normal_build}
BuildRequires: java-%{featurever}-openjdk-portable-unstripped = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
BuildRequires: java-%{featurever}-openjdk-portable-static-libs = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
%endif
%if %{include_fastdebug_build}
BuildRequires: java-%{featurever}-openjdk-portable-devel-fastdebug = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
BuildRequires: java-%{featurever}-openjdk-portable-static-libs-fastdebug = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
%endif
%if %{include_debug_build}
BuildRequires: java-%{featurever}-openjdk-portable-devel-slowdebug = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
BuildRequires: java-%{featurever}-openjdk-portable-static-libs-slowdebug = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
%endif
BuildRequires: java-%{featurever}-openjdk-portable-docs = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
BuildRequires: java-%{featurever}-openjdk-portable-misc = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
# Zero-assembler build requirement
%ifarch %{zero_arches}
BuildRequires: libffi-devel
%endif
# 2024a required as of JDK-8325150
# Use 2023d until 2024a is in the buildroot
BuildRequires: tzdata-java >= 2024a
# Earlier versions have a bug in tree vectorization on PPC
BuildRequires: gcc >= 4.8.3-8

%if %{with_systemtap}
BuildRequires: systemtap-sdt-devel
%endif
BuildRequires: make

%if %{system_libs}
BuildRequires: freetype-devel
BuildRequires: giflib-devel
BuildRequires: harfbuzz-devel
BuildRequires: lcms2-devel
BuildRequires: libjpeg-devel
BuildRequires: libpng-devel
BuildRequires: zlib-devel
%else
# Version in src/java.desktop/share/native/libfreetype/include/freetype/freetype.h
Provides: bundled(freetype) = 2.13.2
# Version in src/java.desktop/share/native/libsplashscreen/giflib/gif_lib.h
Provides: bundled(giflib) = 5.2.2
# Version in src/java.desktop/share/native/libharfbuzz/hb-version.h
Provides: bundled(harfbuzz) = 8.2.2
# Version in src/java.desktop/share/native/liblcms/lcms2.h
Provides: bundled(lcms2) = 2.16.0
# Version in src/java.desktop/share/native/libjavajpeg/jpeglib.h
Provides: bundled(libjpeg) = 6b
# Version in src/java.desktop/share/native/libsplashscreen/libpng/png.h
Provides: bundled(libpng) = 1.6.43
# Version in src/java.base/share/native/libzip/zlib/zlib.h
Provides: bundled(zlib) = 1.3.1
%endif

# this is always built, also during debug-only build
# when it is built in debug-only this package is just placeholder
%{java_rpo %{nil}}

%description
The %{origin_nice} %{featurever} runtime environment.

%if %{include_debug_build}
%package slowdebug
Summary: %{origin_nice} %{featurever} Runtime Environment %{debug_on}
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_rpo -- %{debug_suffix_unquoted}}
%description slowdebug
The %{origin_nice} %{featurever} runtime environment.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package fastdebug
Summary: %{origin_nice} %{featurever} Runtime Environment %{fastdebug_on}
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_rpo -- %{fastdebug_suffix_unquoted}}
%description fastdebug
The %{origin_nice} %{featurever} runtime environment.
%{fastdebug_warning}
%endif

%if %{include_normal_build}
%package headless
Summary: %{origin_nice} %{featurever} Headless Runtime Environment
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_headless_rpo %{nil}}

%description headless
The %{origin_nice} %{featurever} runtime environment without audio and video support.
%endif

%if %{include_debug_build}
%package headless-slowdebug
Summary: %{origin_nice} %{featurever} Runtime Environment %{debug_on}
Group:   Development/Languages

%{java_headless_rpo -- %{debug_suffix_unquoted}}

%description headless-slowdebug
The %{origin_nice} %{featurever} runtime environment without audio and video support.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package headless-fastdebug
Summary: %{origin_nice} %{featurever} Runtime Environment %{fastdebug_on}
Group:   Development/Languages

%{java_headless_rpo -- %{fastdebug_suffix_unquoted}}

%description headless-fastdebug
The %{origin_nice} %{featurever} runtime environment without audio and video support.
%{fastdebug_warning}
%endif

%if %{include_normal_build}
%package devel
Summary: %{origin_nice} %{featurever} Development Environment
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_devel_rpo %{nil}}

%description devel
The %{origin_nice} %{featurever} development tools.
%endif

%if %{include_debug_build}
%package devel-slowdebug
Summary: %{origin_nice} %{featurever} Development Environment %{debug_on}
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_devel_rpo -- %{debug_suffix_unquoted}}

%description devel-slowdebug
The %{origin_nice} %{featurever} development tools.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package devel-fastdebug
Summary: %{origin_nice} %{featurever} Development Environment %{fastdebug_on}
Group:   Development/Tools

%{java_devel_rpo -- %{fastdebug_suffix_unquoted}}

%description devel-fastdebug
The %{origin_nice} %{featurever} development tools.
%{fastdebug_warning}
%endif

%if %{include_staticlibs}

%if %{include_normal_build}
%package static-libs
Summary: %{origin_nice} %{featurever} libraries for static linking

%{java_static_libs_rpo %{nil}}

%description static-libs
The %{origin_nice} %{featurever} libraries for static linking.
%endif

%if %{include_debug_build}
%package static-libs-slowdebug
Summary: %{origin_nice} %{featurever} libraries for static linking %{debug_on}

%{java_static_libs_rpo -- %{debug_suffix_unquoted}}

%description static-libs-slowdebug
The %{origin_nice} %{featurever} libraries for static linking.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package static-libs-fastdebug
Summary: %{origin_nice} %{featurever} libraries for static linking %{fastdebug_on}

%{java_static_libs_rpo -- %{fastdebug_suffix_unquoted}}

%description static-libs-fastdebug
The %{origin_nice} %{featurever} libraries for static linking.
%{fastdebug_warning}
%endif

# staticlibs
%endif

%if %{include_normal_build}
%package jmods
Summary: JMods for %{origin_nice} %{featurever}
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_jmods_rpo %{nil}}

%description jmods
The JMods for %{origin_nice} %{featurever}.
%endif

%if %{include_debug_build}
%package jmods-slowdebug
Summary: JMods for %{origin_nice} %{featurever} %{debug_on}
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_jmods_rpo -- %{debug_suffix_unquoted}}

%description jmods-slowdebug
The JMods for %{origin_nice} %{featurever}.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package jmods-fastdebug
Summary: JMods for %{origin_nice} %{featurever} %{fastdebug_on}
Group:   Development/Tools

%{java_jmods_rpo -- %{fastdebug_suffix_unquoted}}

%description jmods-fastdebug
The JMods for %{origin_nice} %{featurever}.
%{fastdebug_warning}
%endif

%if %{include_normal_build}
%package demo
Summary: %{origin_nice} %{featurever} Demos
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_demo_rpo %{nil}}

%description demo
The %{origin_nice} %{featurever} demos.
%endif

%if %{include_debug_build}
%package demo-slowdebug
Summary: %{origin_nice} %{featurever} Demos %{debug_on}
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_demo_rpo -- %{debug_suffix_unquoted}}

%description demo-slowdebug
The %{origin_nice} %{featurever} demos.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package demo-fastdebug
Summary: %{origin_nice} %{featurever} Demos %{fastdebug_on}
Group:   Development/Languages

%{java_demo_rpo -- %{fastdebug_suffix_unquoted}}

%description demo-fastdebug
The %{origin_nice} %{featurever} demos.
%{fastdebug_warning}
%endif

%if %{include_normal_build}
%package src
Summary: %{origin_nice} %{featurever} Source Bundle
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_src_rpo %{nil}}

%description src
The %{compatiblename}-src sub-package contains the complete %{origin_nice} %{featurever}
class library source code for use by IDE indexers and debuggers.
%endif

%if %{include_debug_build}
%package src-slowdebug
Summary: %{origin_nice} %{featurever} Source Bundle %{for_debug}
%if 0%{?rhel} <= 8
Group:   Development/Languages
%endif

%{java_src_rpo -- %{debug_suffix_unquoted}}

%description src-slowdebug
The %{compatiblename}-src-slowdebug sub-package contains the complete %{origin_nice} %{featurever}
 class library source code for use by IDE indexers and debuggers, %{for_debug}.
%endif

%if %{include_fastdebug_build}
%package src-fastdebug
Summary: %{origin_nice} %{featurever} Source Bundle %{for_fastdebug}
Group:   Development/Languages

%{java_src_rpo -- %{fastdebug_suffix_unquoted}}

%description src-fastdebug
The %{compatiblename}-src-fastdebug sub-package contains the complete %{origin_nice} %{featurever}
 class library source code for use by IDE indexers and debuggers, %{for_fastdebug}.
%endif

%if %{include_normal_build}
%package javadoc
Summary: %{origin_nice} %{featurever} API documentation
%if 0%{?rhel} <= 8
Group:   Documentation
%endif
Requires: javapackages-filesystem
Obsoletes: javadoc-slowdebug < 1:11.0.3.7-4

%{java_javadoc_rpo -- %{nil} %{nil}}

%description javadoc
The %{origin_nice} %{featurever} API documentation.

%package javadoc-zip
Summary: %{origin_nice} %{featurever} API documentation compressed in a single archive
%if 0%{?rhel} <= 8
Group:   Documentation
%endif
Requires: javapackages-filesystem
Obsoletes: javadoc-zip-slowdebug < 1:11.0.3.7-4

%{java_javadoc_rpo -- %{nil} -zip}
%{java_javadoc_rpo -- %{nil} %{nil}}

%description javadoc-zip
The %{origin_nice} %{featurever} API documentation compressed in a single archive.
%endif

%prep

echo "Preparing %{oj_vendor_version}"
echo "Vendor: %{oj_vendor}"
echo "Vendor URL: %{oj_vendor_url}"
echo "Vendor Bug URL: %{oj_vendor_bug_url}"

# Using the echo macro breaks rpmdev-bumpspec, as it parses the first line of stdout :-(
%if 0%{?stapinstall:1}
  echo "CPU: %{_target_cpu}, arch install directory: %{archinstall}, SystemTap install directory: %{stapinstall}"
%else
  %{error:Unrecognised architecture %{_target_cpu}}
%endif

if [ %{include_normal_build} -eq 0 -o  %{include_normal_build} -eq 1 ] ; then
  echo "include_normal_build is %{include_normal_build}"
else
  echo "include_normal_build is %{include_normal_build}, that is invalid. Use 1 for yes or 0 for no"
  exit 11
fi
if [ %{include_debug_build} -eq 0 -o  %{include_debug_build} -eq 1 ] ; then
  echo "include_debug_build is %{include_debug_build}"
else
  echo "include_debug_build is %{include_debug_build}, that is invalid. Use 1 for yes or 0 for no"
  exit 12
fi
if [ %{include_fastdebug_build} -eq 0 -o  %{include_fastdebug_build} -eq 1 ] ; then
  echo "include_fastdebug_build is %{include_fastdebug_build}"
else
  echo "include_fastdebug_build is %{include_fastdebug_build}, that is invalid. Use 1 for yes or 0 for no"
  exit 13
fi
if [ %{include_debug_build} -eq 0 -a  %{include_normal_build} -eq 0 -a  %{include_fastdebug_build} -eq 0 ] ; then
  echo "You have disabled all builds (normal,fastdebug,slowdebug). That is a no go."
  exit 14
fi
%setup -q -c -n %{uniquesuffix ""} -T -a 0
# https://bugzilla.redhat.com/show_bug.cgi?id=1189084
prioritylength=`expr length %{priority}`
if [ $prioritylength -ne 8 ] ; then
 echo "priority must be 8 digits in total, violated"
 exit 14
fi

# OpenJDK patches

%if %{system_libs}
# Remove libraries that are linked by both static and dynamic builds
sh %{SOURCE12} %{top_level_dir_name}
%endif

# Patch the JDK
pushd %{top_level_dir_name}
%patch1 -p1
%patch3 -p1
# Add crypto policy and FIPS support
%patch1001 -p1
# nss.cfg PKCS11 support; must come last as it also alters java.security
%patch1000 -p1
# PKCS11 SHA3 backport
%patch2002 -p1
# alt-java
%patch600 -p1
# RSA default
%patch1003 -p1
popd # openjdk


# Prepare desktop files
# The _X_ syntax indicates variables that are replaced by make upstream
# The @X@ syntax indicates variables that are replaced by configure upstream
for suffix in %{build_loop} ; do
for file in %{SOURCE9}; do
    FILE=`basename $file | sed -e s:\.in$::g`
    EXT="${FILE##*.}"
    NAME="${FILE%.*}"
    OUTPUT_FILE=$NAME$suffix.$EXT
    sed    -e  "s:_SDKBINDIR_:%{sdkbindir -- $suffix}:g" $file > $OUTPUT_FILE
    sed -i -e  "s:@target_cpu@:%{_arch}:g" $OUTPUT_FILE
    sed -i -e  "s:@OPENJDK_VER@:%{version}-%{release}.%{_arch}$suffix:g" $OUTPUT_FILE
    sed -i -e  "s:@JAVA_VER@:%{javaver}:g" $OUTPUT_FILE
    sed -i -e  "s:@JAVA_VENDOR@:%{origin}:g" $OUTPUT_FILE
done
done

# Setup nss.cfg
sed -e "s:@NSS_LIBDIR@:%{NSS_LIBDIR}:g" %{SOURCE11} > nss.cfg

# Setup nss.fips.cfg
sed -e "s:@NSS_LIBDIR@:%{NSS_LIBDIR}:g" %{SOURCE17} > nss.fips.cfg

%build

function customisejdk() {
    local imagepath=${1}


     if [ -d ${imagepath} ] ; then
        # Turn on system security properties
        sed -i -e "s:^security.useSystemPropertiesFile=.*:security.useSystemPropertiesFile=true:" \
            ${imagepath}/conf/security/java.security

        # Use system-wide tzdata
        rm ${imagepath}/lib/tzdb.dat
        ln -s %{_datadir}/javazi-1.8/tzdb.dat ${imagepath}/lib/tzdb.dat
     fi
}

mkdir -p $(dirname %{installoutputdir})

docdir=%{installoutputdir -- "-docs"}
tar -xJf %{docszip}
mv java-%{featurever}-openjdk*.docs.* ${docdir}

miscdir=%{installoutputdir -- "-misc"}
tar -xJf %{misczip}
mv java-%{featurever}-openjdk*.misc.* ${miscdir}

for suffix in %{build_loop} ; do

  if [ "x$suffix" = "x" ] ; then
      jdkzip=%{releasezip}
      staticlibzip=%{staticlibzip}
  elif [ "x$suffix" = "x%{fastdebug_suffix_unquoted}" ] ; then
      jdkzip=%{fastdebugzip}
      staticlibzip=%{fastdebugstaticlibzip}
  else # slowdebug
      jdkzip=%{slowdebugzip}
      staticlibzip=%{slowdebugstaticlibzip}
  fi

  installdir=%{installoutputdir -- ${suffix}}

  # TODO: should verify checksums when using packages from buildroot
  tar -xJf ${jdkzip}
  tar -xJf ${staticlibzip}
  mv java-%{featurever}-openjdk* ${installdir}

  # Fix build paths in ELF files so it looks like we built them
  portablenvr="%{name}-%{VERSION}-%{prelease}.%{portablesuffix}.%{_arch}"
  for file in $(find ${installdir} -type f) ; do
      if file ${file} | grep -q 'ELF'; then
          %{debugedit} -b %{portablebuilddir}/${portablenvr} -d $(pwd) -n ${file}
      fi
  done

  # Set tapset variables to match this build
%if %{with_systemtap}
  for file in ${miscdir}/tapset${suffix}/*.in; do
    OUTPUT_FILE=`echo $file | sed -e "s:\.stp\.in$:-%{version}-%{release}.%{_arch}.stp:g"`
    sed -e "s:@ABS_SERVER_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/lib/server/libjvm.so:g" $file > ${OUTPUT_FILE}
# TODO find out which architectures other than i686 have a client vm
%ifarch %{ix86}
    sed -i -e "s:@ABS_CLIENT_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/lib/client/libjvm.so:g" ${OUTPUT_FILE}
%else
    sed -i -e "/@ABS_CLIENT_LIBJVM_SO@/d" ${OUTPUT_FILE}
%endif
    sed -i -e "s:@ABS_JAVA_HOME_DIR@:%{_jvmdir}/%{sdkdir -- $suffix}:g" $OUTPUT_FILE
    sed -i -e "s:@prefix@:%{_jvmdir}/%{sdkdir -- $suffix}/:g" $OUTPUT_FILE
  done
%endif

  # Final setup on the main image
  customisejdk ${installdir}

  # Print release information
  cat ${installdir}/release

# build cycles
done # end of release / debug cycle loop

%check

# We test debug first as it will give better diagnostics on a crash
for suffix in %{build_loop} ; do

export JAVA_HOME=$(pwd)/%{installoutputdir -- ${suffix}}

# Check Shenandoah is enabled
%if %{use_shenandoah_hotspot}
$JAVA_HOME/bin/java -XX:+UseShenandoahGC -version
%endif

# Only test on one architecture (the fastest) for Java only tests
%ifarch %{jdk_test_arch}

    # Check unlimited policy has been used
    $JAVA_HOME/bin/javac -d . %{SOURCE13}
    $JAVA_HOME/bin/java --add-opens java.base/javax.crypto=ALL-UNNAMED TestCryptoLevel

    # Check ECC is working
    $JAVA_HOME/bin/javac -d . %{SOURCE14}
    $JAVA_HOME/bin/java $(echo $(basename %{SOURCE14})|sed "s|\.java||")

    # Check system crypto (policy) is active and can be disabled
    # Test takes a single argument - true or false - to state whether system
    # security properties are enabled or not.
    $JAVA_HOME/bin/javac -d . %{SOURCE15}
    export PROG=$(echo $(basename %{SOURCE15})|sed "s|\.java||")
    export SEC_DEBUG="-Djava.security.debug=properties"
    $JAVA_HOME/bin/java ${SEC_DEBUG} ${PROG} true
    $JAVA_HOME/bin/java ${SEC_DEBUG} -Djava.security.disableSystemPropertiesFile=true ${PROG} false

    # Check correct vendor values have been set
    $JAVA_HOME/bin/javac -d . %{SOURCE16}
    $JAVA_HOME/bin/java $(echo $(basename %{SOURCE16})|sed "s|\.java||") "%{oj_vendor}" "%{oj_vendor_url}" "%{oj_vendor_bug_url}" "%{oj_vendor_version}"

    # Check translations are available for new timezones
    $JAVA_HOME/bin/javac -d . %{SOURCE18}
    $JAVA_HOME/bin/java $(echo $(basename %{SOURCE18})|sed "s|\.java||") JRE
    $JAVA_HOME/bin/java -Djava.locale.providers=CLDR $(echo $(basename %{SOURCE18})|sed "s|\.java||") CLDR

    # Check src.zip has all sources. See RHBZ#1130490
    $JAVA_HOME/bin/jar -tf $JAVA_HOME/lib/src.zip | grep 'sun.misc.Unsafe'

    # Check class files include useful debugging information
    $JAVA_HOME/bin/javap -l java.lang.Object | grep "Compiled from"
    $JAVA_HOME/bin/javap -l java.lang.Object | grep LineNumberTable
    $JAVA_HOME/bin/javap -l java.lang.Object | grep LocalVariableTable

    # Check generated class files include useful debugging information
    $JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep "Compiled from"
    $JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LineNumberTable
    $JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LocalVariableTable

%else

    # Just run a basic java -version test on other architectures
    $JAVA_HOME/bin/java -version

%endif

# Check java launcher has no SSB mitigation
if ! nm $JAVA_HOME/bin/java | grep set_speculation ; then true ; else false; fi

# Check alt-java launcher has SSB mitigation on supported architectures
%ifarch %{ssbd_arches}
nm $JAVA_HOME/bin/%{alt_java_name} | grep set_speculation
%else
if ! nm $JAVA_HOME/bin/%{alt_java_name} | grep set_speculation ; then true ; else false; fi
%endif

%if %{include_staticlibs}
# Check debug symbols in static libraries (smoke test)
export STATIC_LIBS_HOME=${JAVA_HOME}/lib/static/linux-%{archinstall}/glibc
readelf --debug-dump $STATIC_LIBS_HOME/libfdlibm.a | grep w_remainder.c
readelf --debug-dump $STATIC_LIBS_HOME/libfdlibm.a | grep e_remainder.c
%endif

so_suffix="so"
# Check debug symbols are present and can identify code
find "$JAVA_HOME" -iname "*.$so_suffix" -print0 | while read -d $'\0' lib
do
  if [ -f "$lib" ] ; then
    echo "Testing $lib for debug symbols"
    # All these tests rely on RPM failing the build if the exit code of any set
    # of piped commands is non-zero.

    # Test for .debug_* sections in the shared object. This is the main test
    # Stripped objects will not contain these
    eu-readelf -S "$lib" | grep "] .debug_"
    test $(eu-readelf -S "$lib" | grep -E "\]\ .debug_(info|abbrev)" | wc --lines) == 2

    # Test FILE symbols. These will most likely be removed by anything that
    # manipulates symbol tables because it's generally useless. So a nice test
    # that nothing has messed with symbols
    old_IFS="$IFS"
    IFS=$'\n'
    for line in $(eu-readelf -s "$lib" | grep "00000000      0 FILE    LOCAL  DEFAULT")
    do
     # We expect to see .cpp files, except for architectures like aarch64 and
     # s390 where we expect .o and .oS files
      echo "$line" | grep -E "ABS ((.*/)?[-_a-zA-Z0-9]+\.(c|cc|cpp|cxx|o|oS))?$"
    done
    IFS="$old_IFS"

    # If this is the JVM, look for javaCalls.(cpp|o) in FILEs, for extra sanity checking
    if [ "`basename $lib`" = "libjvm.so" ]; then
      eu-readelf -s "$lib" | \
        grep -E "00000000      0 FILE    LOCAL  DEFAULT      ABS javaCalls.(cpp|o)$"
    fi

    # Test that there are no .gnu_debuglink sections pointing to another
    # debuginfo file. There shouldn't be any debuginfo files, so the link makes
    # no sense either
    eu-readelf -S "$lib" | grep 'gnu'
    if eu-readelf -S "$lib" | grep '] .gnu_debuglink' | grep PROGBITS; then
      echo "bad .gnu_debuglink section."
      eu-readelf -x .gnu_debuglink "$lib"
      false
    fi
  fi
done

# Make sure gdb can do a backtrace based on line numbers on libjvm.so
# javaCalls.cpp:58 should map to:
# http://hg.openjdk.java.net/jdk8u/jdk8u/hotspot/file/ff3b27e6bcc2/src/share/vm/runtime/javaCalls.cpp#l58
# Using line number 1 might cause build problems. See:
# https://bugzilla.redhat.com/show_bug.cgi?id=1539664
# https://bugzilla.redhat.com/show_bug.cgi?id=1538767
gdb -q "$JAVA_HOME/bin/java" <<EOF | tee gdb.out
handle SIGSEGV pass nostop noprint
handle SIGILL pass nostop noprint
set breakpoint pending on
break javaCalls.cpp:58
commands 1
backtrace
quit
end
run -version
EOF
%ifarch %{gdb_arches}
grep 'JavaCallWrapper::JavaCallWrapper' gdb.out
%endif

# build cycles check
done

%install
STRIP_KEEP_SYMTAB=libjvm*

for suffix in %{build_loop} ; do

jdk_image=$(pwd)/%{installoutputdir -- ${suffix}}
# Should match same definitions in build section
docdir=$(pwd)/%{installoutputdir -- "-docs"}
miscdir=$(pwd)/%{installoutputdir -- "-misc"}

# Install release notes and rebuild instructions
commondocdir=${RPM_BUILD_ROOT}%{_defaultdocdir}/%{uniquejavadocdir -- $suffix}
install -d -m 755 ${commondocdir}
mv ${jdk_image}/NEWS ${commondocdir}
cp -a %{SOURCE19} %{SOURCE20} ${commondocdir}

# Install the jdk
mkdir -p $RPM_BUILD_ROOT%{_jvmdir}
cp -a ${jdk_image} $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}

%if %{with_systemtap}
  # Install systemtap support files
  install -dm 755 $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset
  cp -a ${miscdir}/tapset$suffix/*.stp $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset/
  pushd  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset/
   tapsetFiles=`ls *.stp`
  popd
  install -d -m 755 $RPM_BUILD_ROOT%{tapsetdir}
  for name in $tapsetFiles ; do
    targetName=`echo $name | sed "s/.stp/$suffix.stp/"`
    ln -sf %{_jvmdir}/%{sdkdir -- $suffix}/tapset/$name $RPM_BUILD_ROOT%{tapsetdir}/$targetName
  done
%endif

  # Remove empty cacerts database
  rm -f $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/lib/security/cacerts
  # Install cacerts symlink needed by some apps which hard-code the path
  pushd $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/lib/security
      ln -sf /etc/pki/java/cacerts .
  popd

  # Install version-ed symlinks
  pushd $RPM_BUILD_ROOT%{_jvmdir}
    ln -sf %{sdkdir -- $suffix} %{jrelnk -- $suffix}
  popd

  # Install man pages
  pushd ${jdk_image}
  install -d -m 755 $RPM_BUILD_ROOT%{_mandir}/man1
  for manpage in man/man1/*
  do
    # Convert man pages to UTF8 encoding
    iconv -f ISO_8859-1 -t UTF8 $manpage -o $manpage.tmp
    mv -f $manpage.tmp $manpage
    install -m 644 -p $manpage $RPM_BUILD_ROOT%{_mandir}/man1/$(basename \
      $manpage .1)-%{uniquesuffix -- $suffix}.1
  done
  # Remove man pages from jdk image
  rm -rf $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/man
  popd

if ! echo $suffix | grep -q "debug" ; then
    # Install Javadoc documentation
    install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}
    cp -a ${docdir}/docs $RPM_BUILD_ROOT%{_javadocdir}/%{uniquejavadocdir -- $suffix}
    built_doc_archive=jdk-%{filever}%{ea_designator_zip}+%{buildver}%{lts_designator_zip}-docs.zip
    cp -a ${docdir}/${built_doc_archive} \
        $RPM_BUILD_ROOT%{_javadocdir}/%{uniquejavadocdir -- $suffix}.zip
fi

# Install icons and menu entries
for s in 16 24 32 48 ; do
  install -D -p -m 644 \
    ${miscdir}/java-icon${s}.png \
    $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/${s}x${s}/apps/java-%{javaver}-%{origin}.png
done

# Install desktop files
# TODO: provide desktop files via portable
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/{applications,pixmaps}
for e in jconsole$suffix ; do
    desktop-file-install --vendor=%{uniquesuffix -- $suffix} --mode=644 \
        --dir=$RPM_BUILD_ROOT%{_datadir}/applications $e.desktop
done

# Install /etc/.java/.systemPrefs/ directory
# See https://bugzilla.redhat.com/show_bug.cgi?id=741821
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/.java/.systemPrefs

# copy samples next to demos; samples are mostly js files
cp -r ${miscdir}/sample  $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/

# moving config files to /etc
mkdir -p $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}
mkdir -p $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}/lib
mv $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/conf/  $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}
mv $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/lib/security  $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}/lib
pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}
  ln -s %{etcjavadir -- $suffix}/conf  ./conf
popd
pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/lib
  ln -s %{etcjavadir -- $suffix}/lib/security  ./security
popd
# end moving files to /etc

# stabilize permissions
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/ -name "*.so" -exec chmod 755 {} \; ;
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/ -type d -exec chmod 755 {} \; ;
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/legal -type f -exec chmod 644 {} \; ;

# end, dual install
done

%if %{include_normal_build}
# intentionally only for non-debug
%pretrans headless -p <lua>
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1290388 for pretrans over pre
-- if copy-jdk-configs is in transaction, it installs in pretrans to temp
-- if copy_jdk_configs is in temp, then it means that copy-jdk-configs is in transaction  and so is
-- preferred over one in %%{_libexecdir}. If it is not in transaction, then depends
-- whether copy-jdk-configs is installed or not. If so, then configs are copied
-- (copy_jdk_configs from %%{_libexecdir} used) or not copied at all
local posix = require "posix"
local debug = false

SOURCE1 = "%{rpm_state_dir}/copy_jdk_configs.lua"
SOURCE2 = "%{_libexecdir}/copy_jdk_configs.lua"

local stat1 = posix.stat(SOURCE1, "type");
local stat2 = posix.stat(SOURCE2, "type");

  if (stat1 ~= nil) then
  if (debug) then
    print(SOURCE1 .." exists - copy-jdk-configs in transaction, using this one.")
  end;
  package.path = package.path .. ";" .. SOURCE1
else
  if (stat2 ~= nil) then
  if (debug) then
    print(SOURCE2 .." exists - copy-jdk-configs already installed and NOT in transaction. Using.")
  end;
  package.path = package.path .. ";" .. SOURCE2
  else
    if (debug) then
      print(SOURCE1 .." does NOT exists")
      print(SOURCE2 .." does NOT exists")
      print("No config files will be copied")
    end
  return
  end
end
-- run content of included file with fake args
arg = {"--currentjvm", "%{uniquesuffix %{nil}}", "--jvmdir", "%{_jvmdir %{nil}}", "--origname", "%{name}", "--origjavaver", "%{javaver}", "--arch", "%{_arch}", "--temp", "%{rpm_state_dir}/%{name}.%{_arch}"}
require "copy_jdk_configs.lua"

%post
%{post_script %{nil}}

%post headless
%{post_headless %{nil}}

%postun
%{postun_script %{nil}}

%postun headless
%{postun_headless %{nil}}

%posttrans
%{posttrans_script %{nil}}

%posttrans headless
%{alternatives_java_install %{nil}}

%post devel
%{post_devel %{nil}}

%postun devel
%{postun_devel %{nil}}

%posttrans  devel
%{posttrans_devel %{nil}}

%posttrans javadoc
%{alternatives_javadoc_install %{nil}}

%postun javadoc
%{postun_javadoc %{nil}}

%posttrans javadoc-zip
%{alternatives_javadoczip_install %{nil}}

%postun javadoc-zip
%{postun_javadoc_zip %{nil}}
%endif

%if %{include_debug_build}
%post slowdebug
%{post_script -- %{debug_suffix_unquoted}}

%post headless-slowdebug
%{post_headless -- %{debug_suffix_unquoted}}

%posttrans headless-slowdebug
%{alternatives_java_install -- %{debug_suffix_unquoted}}

%postun slowdebug
%{postun_script -- %{debug_suffix_unquoted}}

%postun headless-slowdebug
%{postun_headless -- %{debug_suffix_unquoted}}

%posttrans slowdebug
%{posttrans_script -- %{debug_suffix_unquoted}}

%post devel-slowdebug
%{post_devel -- %{debug_suffix_unquoted}}

%postun devel-slowdebug
%{postun_devel -- %{debug_suffix_unquoted}}

%posttrans  devel-slowdebug
%{posttrans_devel -- %{debug_suffix_unquoted}}
%endif

%if %{include_fastdebug_build}
%post fastdebug
%{post_script -- %{fastdebug_suffix_unquoted}}

%post headless-fastdebug
%{post_headless -- %{fastdebug_suffix_unquoted}}

%postun fastdebug
%{postun_script -- %{fastdebug_suffix_unquoted}}

%postun headless-fastdebug
%{postun_headless -- %{fastdebug_suffix_unquoted}}

%posttrans fastdebug
%{posttrans_script -- %{fastdebug_suffix_unquoted}}

%posttrans headless-fastdebug
%{alternatives_java_install -- %{fastdebug_suffix_unquoted}}

%post devel-fastdebug
%{post_devel -- %{fastdebug_suffix_unquoted}}

%postun devel-fastdebug
%{postun_devel -- %{fastdebug_suffix_unquoted}}

%posttrans  devel-fastdebug
%{posttrans_devel -- %{fastdebug_suffix_unquoted}}

%endif

%if %{include_normal_build}
%files
# main package builds always
%{files_jre %{nil}}
%else
%files
# placeholder
%endif


%if %{include_normal_build}
%files headless
# important note, see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue
# all config/noreplace files (and more) have to be declared in pretrans. See pretrans
%{files_jre_headless %{nil}}

%files devel
%{files_devel %{nil}}

%if %{include_staticlibs}
%files static-libs
%{files_static_libs %{nil}}
%endif

%files jmods
%{files_jmods %{nil}}

%files demo
%{files_demo %{nil}}

%files src
%{files_src %{nil}}

%files javadoc
%{files_javadoc %{nil}}

# This puts a huge documentation file in /usr/share
# It is now architecture-dependent, as eg. AOT and Graal are now x86_64 only
# same for debug variant
%files javadoc-zip
%{files_javadoc_zip %{nil}}
%endif

%if %{include_debug_build}
%files slowdebug
%{files_jre -- %{debug_suffix_unquoted}}

%files headless-slowdebug
%{files_jre_headless -- %{debug_suffix_unquoted}}

%files devel-slowdebug
%{files_devel -- %{debug_suffix_unquoted}}

%if %{include_staticlibs}
%files static-libs-slowdebug
%{files_static_libs -- %{debug_suffix_unquoted}}
%endif

%files jmods-slowdebug
%{files_jmods -- %{debug_suffix_unquoted}}

%files demo-slowdebug
%{files_demo -- %{debug_suffix_unquoted}}

%files src-slowdebug
%{files_src -- %{debug_suffix_unquoted}}
%endif

%if %{include_fastdebug_build}
%files fastdebug
%{files_jre -- %{fastdebug_suffix_unquoted}}

%files headless-fastdebug
%{files_jre_headless -- %{fastdebug_suffix_unquoted}}

%files devel-fastdebug
%{files_devel -- %{fastdebug_suffix_unquoted}}

%if %{include_staticlibs}
%files static-libs-fastdebug
%{files_static_libs -- %{fastdebug_suffix_unquoted}}
%endif

%files jmods-fastdebug
%{files_jmods -- %{fastdebug_suffix_unquoted}}

%files demo-fastdebug
%{files_demo -- %{fastdebug_suffix_unquoted}}

%files src-fastdebug
%{files_src -- %{fastdebug_suffix_unquoted}}

%endif

%changelog
* Thu Oct 10 2024 Antonio Vieiro <avieirov@redhat.com> - 1:11.0.25.0.9-2
- Update to jdk-11.0.25+9 (GA)
- Update release notes to 11.0.25+9
- Switch to GA mode for release
- Related: RHEL-58775
- ** This tarball is embargoed until 2024-10-15 @ 1pm PT. **

* Tue Oct 08 2024 Antonio Vieiro <avieirov@redhat.com> - 1:11.0.25.0.8-0.1.ea
- Update to jdk-11.0.25+8 (EA)
- Update release notes to 11.0.25+8
- Related: RHEL-58775

* Fri Oct 04 2024 Antonio Vieiro <avieirov@redhat.com> - 1:11.0.25.0.7-0.3.ea
- RHJDKBP-875 - Added gating.yaml and/or rpminspect.yaml
- RHJDKBP-874 - Removed %bcond_with artifacts
- Related: RHEL-58775

* Fri Sep 27 2024 Antonio Vieiro <avieirov@redhat.com> - 1:11.0.25.0.7-0.2.ea
- Update to jdk-11.0.25+7 (EA)
- Update release notes to 11.0.25+7
- Related: RHEL-58775

* Wed Sep 25 2024 Antonio Vieiro <avieirov@redhat.com> - 1:11.0.25.0.6-0.3.ea
- Limit Java only tests to one 'jdk_test_arch'
- Related: RHEL-58775
- Resolves: RHEL-59730

* Wed Sep 25 2024 Antonio Vieiro <avieirov@redhat.com> - 1:11.0.25.0.6-0.2.ea
- Update to jdk-11.0.25+6 (EA)
- Update release notes to 11.0.25+6
- Switch to EA mode
- Bump giflib version to 5.2.2 following JDK-8328999
- Bump libpng version to 1.6.43 following JDK-8329004
- Related: RHEL-58775

* Wed Jul 10 2024 Anton Bobrov <abobrov@redhat.com> - 1:11.0.24.0.8-1
- Update to jdk-11.0.24+8 (GA)
- Update release notes to 11.0.24+8
- Adjusted DTLS & RPATH NEWS entries to match OpenJDK 17 & 21 release notes
- Switch to GA mode for release
- Fix Provides to reflect up to date component versions
- Add zlib build required or bundled version (1.3.1), depending on system_libs setting
- Resolves: RHEL-45202
- ** This tarball is embargoed until 2024-07-16 @ 1pm PT. **

* Thu Apr 11 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.23.0.9-2
- Fix 11.0.22 release date in NEWS

* Wed Apr 10 2024 Anton Bobrov <abobrov@redhat.com> - 1:11.0.23.0.9-1
- Update to jdk-11.0.23+9 (GA)
- Update release notes to 11.0.23+9
- Switch to GA mode for release
- Require tzdata 2024a due to upstream inclusion of JDK-8322725
- Only require tzdata 2023d for now as 2024a is unavailable in buildroot
- ** This tarball is embargoed until 2024-04-16 @ 1pm PT. **
- Resolves: RHEL-30920

* Thu Mar 28 2024 Anton Bobrov <abobrov@redhat.com> - 1:11.0.23.0.1-0.1.ea
- Update to jdk-11.0.23+1 (EA)
- Update release notes to 11.0.23+1
- Switch to EA mode

* Wed Jan 10 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.22.0.7-1
- Update to jdk-11.0.22+7 (GA)
- Sync the copy of the portable specfile with the latest update
- Drop local copy of JDK-8312489 which is now included upstream
- ** This tarball is embargoed until 2024-01-16 @ 1pm PT. **
- Resolves: RHEL-20991

* Fri Oct 13 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.21.0.9-2
- Update to jdk-11.0.21+9 (GA)
- Sync the copy of the portable specfile with the latest update
- Re-generate FIPS patch against 11.0.21+1 following backport of JDK-8155246
- Re-generate SHA3 patch following backport of JDK-8242151
- Bump libpng version to 1.6.39 following JDK-8305815
- Bump HarfBuzz version to 7.2.0 following JDK-8307301
- Bump freetype version to 2.13.0 following JDK-8306881
- Update generate_tarball.sh to be closer to upstream vanilla script inc. no more ECC removal
- Update bug URL for RHEL to point to the Red Hat customer portal
- Change top_level_dir_name to use the VCS tag, matching new upstream release style tarball
- Apply all patches using -p1
- Drop local backport of JDK-8243210 which is upstream from 11.0.21+2
- Add missing JFR alternative ghost
- Move jcmd to the headless package
- ** This tarball is embargoed until 2023-10-17 @ 1pm PT. **
- Resolves: RHEL-12214
- Resolves: RHEL-13526
- Resolves: RHEL-13529
- Resolves: RHEL-13532
- Resolves: RHEL-13536
- Resolves: RHEL-13539

* Fri Sep 08 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.20.1.1-2
- Bump release number so we are newer than 9.0
- Related: rhbz#2236590

* Tue Sep 05 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.20.1.1-1
- Update to jdk-11.0.20.1+1 (GA)
- Add backport of JDK-8312489 already upstream in 11.0.22 (see OPENJDK-2095)
- Add backport of JDK-8243210 already upstream in 11.0.21 (see RH2229269)
- Update openjdk_news script to specify subdirectory last
- Add missing discover_trees script required by openjdk_news
- Resolves: rhbz#2236590

* Thu Jul 20 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.20.0.8-3
- Fix tzdata requirement copy-and-paste error that led to two BuildRequires and no Requires
- Resolves: rhbz#2224420

* Wed Jul 19 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.20.0.8-2
- Bump release number so we are newer than 9.0
- Related: rhbz#2221106

* Fri Jul 14 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.20.0.8-1
- Update to jdk-11.0.20.0+8 (GA)
- Update release notes to 11.0.20.0+8
- Drop local inclusion of JDK-8274864 & JDK-8305113 as they are included in 11.0.20+1
- Bump tzdata requirement to 2023c now it is available in the buildroot
- Bump bundled LCMS version to 2.15 as in jdk-11.0.20+1.
- Bump bundled HarfBuzz version to 7.0.1 as in jdk-11.0.20+7
- Use tapsets from the misc tarball
- Introduce 'prelease' for the portable release versioning, to handle EA builds
- Make sure root installation directory is created first
- Use in-place substitution for all but the first of the tapset changes
- Sync the copy of the portable specfile with the latest update
- Add note at top of spec file about rebuilding
- ** This tarball is embargoed until 2023-07-18 @ 1pm PT. **
- Resolves: rhbz#2217715
- Resolves: rhbz#2221106

* Wed Apr 26 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.19.0.7-4
- Include the java-11-openjdk-portable.spec file with instructions on how to rebuild.
- Related: rhbz#2150201

* Wed Apr 26 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.19.0.7-3
- Revert "Restore native build for x86 as there is no portable build"
- Reintroduce useful cleanups from x86 reversion
- Adjust oj_vendor_version & oj_vendor_bug_url to match the portable so test passes
- Related: rhbz#2150201

* Wed Apr 26 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.19.0.7-2
- Update to jdk-11.0.19.0+7
- Update release notes to 11.0.19.0+7
- Require tzdata 2023c due to local inclusion of JDK-8274864 & JDK-8305113
- Update generate_tarball.sh to add support for passing a boot JDK to the configure run
- Add POSIX-friendly error codes to generate_tarball.sh and fix whitespace
- Remove .jcheck and GitHub support when generating tarballs, as done in upstream release tarballs
- Rebase FIPS support against 11.0.19+6
- Rebase RH1750419 alt-java patch against 11.0.19+6
- Replace local copies of JDK portable binaries with build dependencies
- Use portable build on x86_32 now one is available
- ** This tarball is embargoed until 2023-04-18 @ 1pm PT. **
- Resolves: rhbz#2185182
- Resolves: rhbz#2150201

* Tue Feb 28 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.18.0.10-4
- On portable architectures, replace build section with extraction of existing builds from portables
- Rewrite ELF files so the source file path is correct and debugsources can be assembled
- Backport SHA-3 support for PKCS11 provider
- Sync patch set with portable build we are using by removing rh1648644-java_access_bridge_privileged_security.patch
- Resolves: rhbz#2150201

* Wed Jan 11 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.18.0.10-3
- Update to jdk-11.0.18+10 (GA)
- Update release notes to 11.0.18+10
- Switch to GA mode for release
- Resolves: rhbz#2160111

* Tue Jan 03 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.18.0.9-0.3.ea
- Update to jdk-11.0.18+9
- Update release notes to 11.0.18+9
- Drop local copy of JDK-8293834 now this is upstream
- Require tzdata 2022g due to inclusion of JDK-8296108, JDK-8296715 & JDK-8297804
- Update TestTranslations.java to test the new America/Ciudad_Juarez zone
- Resolves: rhbz#2150197

* Thu Dec 15 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.18.0.1-0.3.ea
- Update to jdk-11.0.18+1
- Update release notes to 11.0.18+1
- Switch to EA mode for 11.0.18 pre-release builds.
- Drop local copies of JDK-8294357 & JDK-8295173 now upstream contains tzdata 2022e
- Drop local copy of JDK-8275535 which is finally upstream
- Related: rhbz#2150197

* Wed Oct 26 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.17.0.8-2
- Update to jdk-11.0.17+8 (GA)
- Update release notes to 11.0.17+8
- Switch to GA mode for release
- Update in-tree tzdata to 2022e with JDK-8294357 & JDK-8295173
- Update CLDR data with Europe/Kyiv (JDK-8293834)
- Drop JDK-8292223 patch which we found to be unnecessary
- Update TestTranslations.java to use public API based on TimeZoneNamesTest upstream
- The stdc++lib, zlib & freetype options should always be set from the global, so they are not altered for staticlibs builds
- Remove freetype sources along with zlib sources
- Resolves: rhbz#2133695

* Wed Oct 05 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.17.0.7-0.1.ea
- Update to jdk-11.0.17+7
- Update release notes to 11.0.17+7
- Resolves: rhbz#2130619

* Tue Sep 06 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.17.0.1-0.2.ea
- Update to jdk-11.0.17+1
- Update release notes to 11.0.17+1
- Switch to EA mode for 11.0.17 pre-release builds.
- Bump HarfBuzz bundled version to 4.4.1 following JDK-8289853
- Bump FreeType bundled version to 2.12.1 following JDK-8290334
- Related: rhbz#2130619

* Tue Aug 30 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.16.1.1-3
- Switch to static builds, reducing system dependencies and making build more portable
- Resolves: rhbz#2121275

* Wed Aug 24 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.16.1.1-2
- Update to jdk-11.0.16.1+1
- Update release notes to 11.0.16.1+1
- Add patch to provide translations for Europe/Kyiv added in tzdata2022b
- Add test to ensure timezones can be translated
- Resolves: rhbz#2119528

* Fri Jul 22 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.16.0.8-2
- Update to jdk-11.0.16+8
- Update release notes to 11.0.16+8
- Switch to GA mode for release
- Resolves: rhbz#2106517

* Sat Jul 16 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.16.0.7-0.1.ea
- Update to jdk-11.0.16+7
- Update release notes to 11.0.16+7
- Switch to EA mode for 11.0.16 pre-release builds.
- Use same tarball naming style as java-17-openjdk and java-latest-openjdk
- Drop JDK-8257794 patch now upstreamed
- Print release file during build, which should now include a correct SOURCE value from .src-rev
- Update tarball script with IcedTea GitHub URL and .src-rev generation
- Use "git apply" with patches in the tarball script to allow binary diffs
- Include script to generate bug list for release notes
- Update tzdata requirement to 2022a to match JDK-8283350
- Make use of the vendor version string to store our version & release rather than an upstream release date
- Explicitly require crypto-policies during build and runtime for system security properties
- Resolves: rhbz#2083325

* Thu Jul 14 2022 Jiri Vanek <jvanek@redhat.com> - 1:11.0.16.0.7-0.1.ea
- Add additional patch during tarball generation to align tests with ECC changes
- Related: rhbz#2083325

* Fri Jul 08 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.15.0.10-4
- Rebase FIPS patches from fips branch and simplify by using a single patch from that repository
- * RH2036462: sun.security.pkcs11.wrapper.PKCS11.getInstance breakage
- * RH2090378: Revert to disabling system security properties and FIPS mode support together
- Rebase RH1648249 nss.cfg patch so it applies after the FIPS patch
- Enable system security properties in the RPM (now disabled by default in the FIPS repo)
- Improve security properties test to check both enabled and disabled behaviour
- Run security properties test with property debugging on
- Resolves: rhbz#2099839
- Resolves: rhbz#2100676

* Thu Jun 30 2022 Francisco Ferrari Bihurriet <fferrari@redhat.com> - 1:11.0.15.0.10-3
- RH2007331: SecretKey generate/import operations don't add the CKA_SIGN attribute in FIPS mode
- Resolves: rhbz#2102434

* Thu Jun 30 2022 Stephan Bergmann <sbergman@redhat.com> - 1:11.0.15.0.10-2
- Fix flatpak builds by exempting them from bootstrap
- Resolves: rhbz#2067189

* Sun Apr 24 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.15.0.10-1
- Update to jdk-11.0.15.0+10
- Update release notes to 11.0.15.0+10
- Switch to GA mode for release
- Resolves: rhbz#2073595

* Tue Apr 12 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.15.0.8-0.1.ea
- Update to jdk-11.0.15.0+8
- Update release notes to 11.0.15.0+8
- Rebase RH1996182 FIPS patch after JDK-8254410
- Resolves: rhbz#2050458

* Tue Apr 12 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.15.0.1-0.1.ea
- Update to jdk-11.0.15.0+1
- Update release notes to 11.0.15.0+1
- Switch to EA mode for 11.0.15 pre-release builds.
- Related: rhbz#2050458

* Mon Feb 28 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.14.1.1-6
- Detect NSS at runtime for FIPS detection
- Turn off build-time NSS linking and go back to an explicit Requires on NSS
- Resolves: rhbz#2052831

* Sun Feb 27 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.14.1.1-5
- Introduce tests/tests.yml, based on the one in RHEL 8
- Resolves: rhbz#2058489

* Fri Feb 25 2022 Jiri Vanek <jvanek@redhat.com> - 1:11.0.14.1.1-4
- Storing and restoring alterntives during update manually
- Fixing Bug 2001567 - update of JDK/JRE is removing its manually selected alterantives and select (as auto) system JDK/JRE
-- The move of alternatives creation to posttrans to fix:
-- Bug 1200302 - dnf reinstall breaks alternatives
-- Had caused the alternatives to be removed, and then created again,
-- instead of being added, and then removing the old, and thus persisting
-- the selection in family
-- Thus this fix, is storing the family of manually selected master, and if
-- stored, then it is restoring the family of the master
- Resolves: rhbz#2008205

* Fri Feb 25 2022 Jiri Vanek <jvanek@redhat.com> - 1:11.0.14.1.1-3
- Family extracted to globals
- Resolves: rhbz#2008205

* Wed Feb 23 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.14.1.1-2
- Add JDK-8275535 patch to fix LDAP authentication issue.
- Resolves: rhbz#2053523

* Fri Feb 18 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.14.1.1-1
- Update to jdk-11.0.14.1+1
- Update release notes to 11.0.14.1+1
- Require tzdata 2021e as of JDK-8275766.
- Resolves: rhbz#2052834

* Thu Feb 17 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.14.0.9-2
- Separate crypto policy initialisation from FIPS initialisation, now they are no longer interdependent
- Resolves: rhbz#2052820

* Wed Feb 16 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.14.0.9-1
- Update to jdk-11.0.14.0+9
- Update release notes to 11.0.14.0+9
- Switch to GA mode for final release.
- Resolves: rhbz#2039395

* Tue Feb 15 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.14.0.8-0.3.ea
- Fix FIPS issues in native code and with initialisation of java.security.Security
- Resolves: rhbz#2023530

* Fri Feb 11 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.14.0.8-0.2.ea
- Refactor build functions so we can build just HotSpot without any attempt at installation.
- Sync gdb test with java-1.8.0-openjdk.
- Improve architecture restrictions for the gdb test.
- Replace -mstackrealign with -mincoming-stack-boundary=2 -mpreferred-stack-boundary=4 on x86_32 for stack alignment
- Explicitly list JIT architectures rather than relying on those with slowdebug builds
- Disable the serviceability agent on Zero architectures even when the architecture itself is supported
- Add backport of JDK-8257794 to fix bogus assert on slowdebug x86-32 Zero builds
- Related: rhbz#2052834

* Fri Feb 11 2022 Jiri Vanek <jvanek@redhat.com> - 1:11.0.14.0.8-0.2.ea
- Give javadoc-zip its own Provides, next to the plain javadoc ones
- Related: rhbz#2052834

* Fri Feb 11 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.14.0.8-0.1.ea
- Update to jdk-11.0.14.0+8
- Update release notes to 11.0.14.0+8
- Switch to EA mode for 11.0.14 pre-release builds.
- Rename blacklisted.certs to blocked.certs following JDK-8253866
- Rebase RH1996182 login patch and drop redundant security policy extension after JDK-8269034
- Resolves: rhbz#2022825

* Thu Jan 13 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.13.0.8-5
- Turn off bootstrapping for slow debug builds, which are particularly slow on ppc64le.
- Related: rhbz#2022825

* Thu Dec 02 2021 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.13.0.8-4
- Use 'sql:' prefix in nss.fips.cfg as F35+ no longer ship the legacy
  secmod.db file as part of NSS
- Resolves: rhbz#2023535

* Wed Dec 01 2021 Jiri Vanek <jvanek@redhat.com> - 1:11.0.13.0.8-3
- Replaced hardcoded 11 by featurever where appropriate
- Fixed comment of `for slowdebug` to correct `any debug`
- Related: rhbz#2022825

* Tue Nov 09 2021 Jiri Vanek <jvanek@redhat.com> - 1:11.0.13.0.8-2
- alternatives creation moved to posttrans
- Thus fixing the old reisntall issue:
- https://bugzilla.redhat.com/show_bug.cgi?id=1200302
- https://bugzilla.redhat.com/show_bug.cgi?id=1976053
- Resolves: rhbz#2008205

* Wed Oct 13 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.13.0.8-1
- Update to jdk-11.0.13.0+8
- Update release notes to 11.0.13.0+8
- Update tarball generation script to use git following OpenJDK 11u's move to github
- Remove "-clean" suffix as no 11.0.13 builds are unclean.
- Drop JDK-8269668 patch which is now applied upstream.
- Resolves: rhbz#2013845

* Sun Oct 10 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.12.0.7-6
- Reduce disk footprint by removing build artifacts by default.
- Related: rhbz#1999940

* Sun Oct 10 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.12.0.7-5
- Restructure the build so a minimal initial build is then used for the final build (with docs)
- This reduces pressure on the system JDK and ensures the JDK being built can do a full build
- Related: rhbz#1999940

* Tue Oct 05 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.12.0.7-4
- Allow plain key import to be disabled with -Dcom.redhat.fips.plainKeySupport=false
- Resolves: rhbz#1994681

* Tue Oct 05 2021 Martin Balao <mbalao@redhat.com> - 1:11.0.12.0.7-4
- Add patch to allow plain key import.
- Resolves: rhbz#1994681

* Thu Sep 02 2021 Jiri Vanek <jvanek@redhat.com> - 1:11.0.12.0.7-3
- Minor cosmetic improvements to make spec more comparable between variants
- Related: rhbz#1999940

* Mon Aug 30 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.12.0.7-2
- Extend the default security policy to accomodate PKCS11 accessing jdk.internal.misc.
- Resolves: rhbz#1997360

* Fri Aug 27 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.12.0.7-1
- Add patch to login to the NSS software token when in FIPS mode.
- Resolves: rhbz#1997360

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 1:11.0.12.0.7-0.1
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Mon Aug 09 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.12.0.7-0
- Update to jdk-11.0.12.0+7
- Update release notes to 11.0.12.0+7
- Switch to GA mode for final release.
- Remove non-Free test from source tarball.
- Resolves: rhbz#1967815

* Wed Jul 28 2021 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.12.0.7-0
- Add patch in order to fix java.library.path issue on aarch64 (JDK-8269668)
- Resolves: rhbz#1967815

* Tue Jul 20 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.12.0.6-0.0.ea
- Update to jdk-11.0.12.0+6
- Update release notes to 11.0.12.0+6
- Correct bug ID JDK-8264846 to intended ID of JDK-8264848
- Switch to EA mode for 11.0.12 pre-release builds.
- Update ECC patch following JDK-8226374 (bug ID yet to be confirmed)
- Use the "reverse" build loop (debug first) as the main and only build loop to get more diagnostics.
- Remove restriction on disabling product build, as debug packages no longer have javadoc packages.
- Resolves: rhbz#1967815

* Tue Jul 20 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.11.0.9-2
- Minor code cleanups on FIPS detection patch and check for SECMOD_GetSystemFIPSEnabled in configure.
- Remove unneeded Requires on NSS as it will now be dynamically linked and detected by RPM.
- Resolves: rhbz#1971689

* Tue Jul 20 2021 Martin Balao <mbalao@redhat.com> - 1:11.0.11.0.9-2
- Detect FIPS using SECMOD_GetSystemFIPSEnabled in the new libsystemconf JDK library.
- Resolves: rhbz#1971689

* Tue Jul 06 2021 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.11.0.9-1
- Update RH1655466 FIPS patch with changes in OpenJDK 8 version.
- SunPKCS11 runtime provider name is a concatenation of "SunPKCS11-" and the name in the config file.
- Change nss.fips.cfg config name to "NSS-FIPS" to avoid confusion with nss.cfg.
- No need to substitute path to nss.fips.cfg as java.security file supports a java.home variable.
- Disable FIPS mode support unless com.redhat.fips is set to "true".
- Enable alignment with FIPS crypto policy by default (-Dcom.redhat.fips=false to disable).
- Add explicit runtime dependency on NSS for the PKCS11 provider in FIPS mode
- Move setup of JavaSecuritySystemConfiguratorAccess to Security class so it always occurs (RH1915071)
- Resolves: rhbz#1971689

* Tue Jul 06 2021 Martin Balao <mbalao@redhat.com> - 1:11.0.11.0.9-1
- Support the FIPS mode crypto policy (RH1655466)
- Use appropriate keystore types when in FIPS mode (RH1818909)
- Disable TLSv1.3 when the FIPS crypto policy and the NSS-FIPS provider are in use (RH1860986)
- Resolves: rhbz#1971689

* Mon Jul 05 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.11.0.9-0
- Update to jdk-11.0.11.0+9
- Update release notes to 11.0.11.0+9
- Remove upstreamed patch JDK-8259949
- Require tzdata 2020f to match upstream change JDK-8259048
- Require tzdata 2021a to match upstream change JDK-8260356
- Update tapsets from IcedTea 6.x repository with fix for JDK-8015774 changes (_heap->_heaps)
- Update icedtea_sync.sh with a VCS mode that retrieves sources from a Mercurial repository
- Perform static library build on a separate source tree with bundled image libraries
- Make static library build optional
- Resolves: rhbz#1967815

* Mon Jul 05 2021 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.11.0.9-0
- Remove -fcommon work-around as the OpenJDK 11 code has been fixed.
- Resolves: rhbz#1967815

* Mon Jul 05 2021 Stephan Bergmann <sbergman@redhat.com> - 1:11.0.11.0.9-0
- Hardcode /usr/sbin/alternatives for Flatpak builds
- Disable copy-jdk-configs for Flatpak builds
- Resolves: rhbz#1967815

* Mon Jul 05 2021 Jayashree Huttanagoudar <jhuttana@redhat.com> - 1:11.0.11.0.9-0
- Fix issue where CheckVendor.java test erroneously passes when it should fail.
- Add proper quoting so '&' is not treated as a special character by the shell.
- Resolves: rhbz#1967815

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 1:11.0.10.0.9-0.1
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Mon Feb  1 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.9-0
- Update to jdk-11.0.10.0+9
- Update release notes to 11.0.10.0+9
- Switch to GA mode for final release.

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1:11.0.10.0.8-0.5.ea.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Jan 25 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.8-0.5.ea
- Fix location and comment differences from RHEL.

* Mon Jan 25 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.8-0.5.ea
- Following JDK-8005165, class data sharing can be enabled on all JIT architectures

* Sun Jan 24 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.8-0.4.ea
- Include a test in the RPM to check the build has the correct vendor information.

* Sun Jan 24 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.8-0.4.ea
- Update build documentation to reflect this is java-11-openjdk, not java-1.8.0-openjdk
- Remove redundant closure and immediate reopening of include_normal_build block.

* Sun Jan 24 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.8-0.3.ea
- Use RSA as default for keytool, as DSA is disabled in all crypto policies except LEGACY
- Adjust RH1842572 patch due to context change from JDK-8213400

* Sat Jan 23 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.8-0.2.ea
- Need to support noarch for creating source RPMs for non-scratch builds.

* Mon Jan 18 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.8-0.2.ea
- Introduce stapinstall variable to set SystemTap arch directory correctly (e.g. arm64 on aarch64)

* Mon Jan 18 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.8-0.1.ea
- Use -march=i686 for x86 builds if -fcf-protection is detected (needs CMOV)

* Thu Jan 14 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.8-0.0.ea
- Update to jdk-11.0.10.0+8
- Update release notes to 11.0.10.0+8.
- Update tarball generation script to use PR3818 which handles JDK-8171279 changes
- Drop JDK-8250861 as applied upstream.

* Tue Dec 22 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.10.0.1-0.0.ea
- Update to jdk-11.0.10.0+1
- Update release notes to 11.0.10.0+1
- Use JEP-322 Time-Based Versioning so we can handle a future 11.0.9.1-like release correctly.
- Still use 11.0.x rather than 11.0.x.0 for file naming, as the trailing zero is omitted from tags.
- Revert configure and built_doc_archive hacks to build 11.0.9.1 from 11.0.9.0 sources, and synced with RHEL version.
- Cleanup debug package descriptions and version number placement.
- Switch to EA mode for 11.0.10 pre-release builds.
- Drop JDK-8222286 & JDK-8254177 as applied upstream
- Use system harfbuzz now this is supported.

* Tue Dec 22 2020 Jiri Vanek <jvanek@redhat.com> - 1:11.0.9.11-9
- fixed missing condition for fastdebug packages being counted as debug ones

* Sat Dec 19 2020 Jiri Vanek <jvanek@redhat.com> - 1:11.0.9.11-8
- removed lib-style provides for fastdebug_suffix_unquoted

* Thu Dec 17 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.11-6
- introduced nm based check to verify alt-java on x86_64 is patched, and no other alt-java or java is patched
- patch600 rh1750419-redhat_alt_java.patch amended to die, if it is used wrongly
- introduced ssbd_arches with currently only valid arch of x86_64 to separate real alt-java architectures

* Tue Dec 01 2020 Jiri Vanek <jvanek@redhat.com> - 1:11.0.9.11-5
- removed patch6, rh1566890-CVE_2018_3639-speculative_store_bypass.patch, surpassed by new patch
- added patch600, rh1750419-redhat_alt_java.patch, suprassing removed patch
- no longer copying of java->alt-java as it is created by  patch600

* Mon Nov 23 2020 Jiri Vanek <jvanek@redhat.com> - 1:11.0.9.11-4
- Create a copy of java as alt-java with alternatives and man pages
- java-11-openjdk doesn't have a JRE tree, so don't try and copy alt-java there...

* Fri Nov 06 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.11-3
- Update release notes for 11.0.9.1 release.

* Wed Nov 04 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.9.11-2
- Update to jdk-11.0.9.1+1
- RPM version stays at 11.0.9.11-2 so as to not break upgrade path.
- Adds a single patch for JDK-8250861.

* Thu Oct 29 2020 Jiri Vanek <jvanek@redhat.com> - 1:11.0.9.11-1
- Move all license files to NVR-specific JVM directory.
- This bad placement was killing parallel installability and thus having a bad impact on leapp, if used.

* Mon Oct 19 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.9.11-0
- Fix directory ownership of static-libs package

* Thu Oct 15 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.11-0
- Update to jdk-11.0.9+11
- Update release notes for 11.0.9 release.
- Add backport of JDK-8254177 to update to tzdata 2020b
- Require tzdata 2020b due to resource changes in JDK-8254177

* Mon Oct 05 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.10-0.0.ea
- Update to jdk-11.0.9+10 (EA)

* Mon Oct 05 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.9-0.0.ea
- Update to jdk-11.0.9+9 (EA)

* Thu Oct 01 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.8-0.0.ea
- Update to jdk-11.0.9+8 (EA)

* Mon Sep 28 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.7-0.0.ea
- Update to jdk-11.0.9+7 (EA)

* Tue Sep 15 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.9.6-0.1.ea
- Update static-libs packaging to new layout

* Tue Sep 15 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.6-0.0.ea
- Update to jdk-11.0.9+6 (EA)
- Update tarball generation script to use PR3802, handling JDK-8233228 & JDK-8177334
- Resolves: rhbz#1869017

* Tue Sep 08 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.5-0.0.ea
- Update to jdk-11.0.9+5 (EA)

* Thu Sep 03 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.4-0.0.ea
- Update to jdk-11.0.9+4 (EA)

* Wed Aug 19 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.3-0.0.ea
- Update to jdk-11.0.9+3 (EA)

* Tue Aug 11 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.2-0.0.ea
- Update to jdk-11.0.9+2 (EA)
- With Shenandoah now upstream in OpenJDK 11, we can use jdk-updates/jdk11 directly

* Tue Aug 11 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.1-0.2.ea
- Cleanup architecture and JVM feature handling in preparation for using upstreamed Shenandoah.

* Sun Aug 09 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.9.1-0.1.ea
- Update to shenandoah-jdk-11.0.9+1 (EA)
- Switch to EA mode for 11.0.9 pre-release builds.
- Drop JDK-8247874 backport now applied upstream.
- JDK-8245832 increases the set of static libraries, so try and include them all with a wildcard.

* Tue Jul 28 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.8.10-1
- Disable LTO as this breaks the build. See RHBZ#1861401.

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:11.0.8.10-0.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Sat Jul 11 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.10-0
- Update to shenandoah-jdk-11.0.8+10 (GA)
- Switch to GA mode for final release.
- Update release notes with last minute fix (JDK-8248505).

* Fri Jul 10 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.9-0.0.ea
- Update to shenandoah-jdk-11.0.8+9 (EA)
- Update release notes for 11.0.8 release.

* Thu Jul 09 2020 Jiri Vanek <jvanek@redhat.com> - 1:11.0.8.8-0.2.ea
- bumped to become system jdk, is_system_jdk moved from 0 to 1

* Thu Jul 09 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.8-0.1.ea
- Re-introduce java-openjdk-src & java-openjdk-demo for system_jdk builds.
- Fix accidental renaming of java-openjdk-devel to java-devel-openjdk.

* Tue Jun 30 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.8-0.0.ea
- Update to shenandoah-jdk-11.0.8+8 (EA)

* Tue Jun 23 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.7-0.0.ea
- Update to shenandoah-jdk-11.0.8+7 (EA)

* Tue Jun 23 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.6-0.0.ea
- Update to shenandoah-jdk-11.0.8+6 (EA)

* Tue Jun 23 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.5-0.3.ea
- Add release notes.
- Amend release notes, removing issue actually fixed in 11.0.6.

* Tue Jun 23 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.5-0.2.ea
- Sync JDK-8247874 patch with upstream status in 11.0.9.
- Add missing ChangeLog entry from last series of commits.

* Mon Jun 22 2020 Jayashree Huttanagoudar <jhuttana@redhat.com> - 1:1.0.8.5-0.2.ea
- Added a patch jdk8247874-fix_ampersand_in_vm_bug_url.patch

* Thu Jun 18 2020 Jayashree Huttanagoudar <jhuttana@redhat.com> - 1:1.0.8.5-0.2.ea
- Moved vendor_version_string to better place

* Thu Jun 18 2020 Jiri Vanek <jvanek@redhat.com> - 1:11.0.8.5-0.2.ea
- set vendor property and vendor urls
- made urls to be preconfigured by os

* Tue Jun 09 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.8.5-0.1.ea
- Disable stripping of debug symbols for static libraries part of
  the -static-libs sub-package.

* Sun Jun 07 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.5-0.0.ea
- Update to shenandoah-jdk-11.0.8+5 (EA)

* Mon May 25 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.4-0.0.ea
- Update to shenandoah-jdk-11.0.8+4 (EA)
- Require tzdata 2020a due to resource changes in JDK-8243541

* Fri May 22 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.8.3-0.1.ea
- Build static-libs-image and add resulting files via -static-libs
  sub-package.

* Tue May 19 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.3-0.0.ea
- Update to shenandoah-jdk-11.0.8+3 (EA)
- Drop JDK-8233880 backport now applied upstream.

* Mon May 18 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.2-0.0.ea
- Update to shenandoah-jdk-11.0.8+2 (EA)

* Mon May 18 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.8.1-0.0.ea
- Update to shenandoah-jdk-11.0.8+1 (EA)
- Switch to EA mode for 11.0.8 pre-release builds.
- Drop JDK-8237396 & JDK-8228407 backports now applied upstream.

* Sun May 17 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.10-2
- Backport JDK-8233880 to fix version detection of GCC 10.
- Remove explicit compiler flags which should be handled by the upstream build
  (-std=gnu++98, -fno-delete-null-pointer-checks, -fno-lifetime-dse)

* Fri Apr 24 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.10-1
- Make use of --with-extra-asflags introduced in jdk-11.0.6+1.

* Wed Apr 22 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.10-0
- Update to shenandoah-jdk-11.0.7+10 (GA)
- Switch to GA mode for final release.
- Remove JDK-8237879 backport as this was integrated upstream in jdk-11.0.7+10.

* Tue Apr 21 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.9-0.0.ea
- Update to shenandoah-jdk-11.0.7+9 (EA)
- Remove JDK-8241296 backport as this was integrated upstream in jdk-11.0.7+9.

* Tue Apr 21 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.8-0.0.ea
- Update to shenandoah-jdk-11.0.7+8 (EA)

* Mon Apr 20 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.7-0.0.ea
- Update to shenandoah-jdk-11.0.7+7 (EA)

* Mon Apr 20 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.6-0.0.ea
- Update to shenandoah-jdk-11.0.7+6 (EA)

* Sun Apr 19 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.5-0.0.ea
- Update to shenandoah-jdk-11.0.7+5 (EA)

* Sun Apr 19 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.4-0.0.ea
- Update to shenandoah-jdk-11.0.7+4 (EA)

* Thu Apr 16 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.3-0.0.ea
- Add JDK-8228407 backport to resolve crashes during verification.

* Thu Apr 16 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.3-0.0.ea
- Update to shenandoah-jdk-11.0.7+3 (EA)

* Mon Apr 06 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.2-0.5.ea
- Sync SystemTap & desktop files with upstream IcedTea release 3.15.0 using new script

* Sat Mar 28 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.2-0.4.ea
- Add JDK-8237396 backport to resolve Shenandoah TCK breakage in traversal mode.

* Tue Mar 24 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.7.2-0.3.ea
- Revert GCC 10 workaround for s390x.
- Resolves RHBZ#1799087.

* Fri Mar 20 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.2-0.2.ea
- Backport JDK-8241296 to fix segfaults when active_handles is NULL (RH1813550)

* Fri Mar 13 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.7.2-0.1.ea
- Add patch for make 4.3 (JDK-8237879)

* Wed Mar 04 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.7.2-0.0.ea
- Update to shenandoah-jdk-11.0.7+2 (EA)
- Drop JDK-8224851 backport now included upstream.

* Thu Feb 27 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.7.1-0.0.ea
- Update to shenandoah-jdk-11.0.7+1 (EA)
- Switch to EA mode for 11.0.7 pre-release builds.
- Drop JDK-8236039 backport now applied upstream.

* Thu Feb 27 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.6.10-0
- Add workaround for building with GCC 10 on s390x. See RHBZ#1799087

* Wed Jan 29 2020 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.6.10-0
- Account for building with GCC 10: JDK-8224851, -fcommon switch.

* Wed Jan 29 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.6.10-0
- Update to shenandoah-jdk-11.0.6+10 (GA)
- Add JDK-8236039 backport to resolve OpenShift blocker.
- Add JDK-8224851 backport to resolve AArch64 compiler issues.

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:11.0.6.9-0.1.ea
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Jan 09 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.6.9-0.0.ea
- Update to shenandoah-jdk-11.0.6+9 (EA)

* Mon Dec 30 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.6.2-0.0.ea
- Update to shenandoah-jdk-11.0.6+2 (EA)

* Thu Dec 19 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.6.1-0.0.ea
- Update to shenandoah-jdk-11.0.6+1 (EA)
- Switch to EA mode for 11.0.6 pre-release builds.
- Add support for jfr binary.

* Wed Oct 09 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.5.10-0
- Update to shenandoah-jdk-11.0.5+10 (GA)
- Switch to GA mode for final release.

* Mon Oct 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.5.9-0.0.ea
- Update to shenandoah-jdk-11.0.5+9 (EA)

* Tue Aug 27 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.5.2-0.2.ea
- Update generate_source_tarball.sh script to use the PR3751 patch and retain the secp256k1 curve.
- Regenerate source tarball using the updated script and add the -'4curve' suffix.
- PR3751 includes the changes in the PR1834/RH1022017 patch which is removed.

* Sat Aug 24 2019 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.5.2-0.1.ea
- Update to shenandoah-jdk-11.0.5+2 (EA)

* Mon Aug 12 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.5.1-0.1.ea
- Update to shenandoah-jdk-11.0.5+1 (EA)
- Switch to EA mode for 11.0.5 pre-release builds.

* Thu Aug 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.4.11-4
- Switch to in-tree SunEC code, dropping NSS runtime dependencies and patches to link against it.

* Fri Jul 26 2019 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.4.11-3
- Drop unnecessary build requirement on gtk3-devel, as OpenJDK searches for Gtk+ at runtime.
- Add missing build requirement for libXrender-devel, previously masked by Gtk3+ dependency
- Add missing build requirement for libXrandr-devel, previously masked by Gtk3+ dependency
- fontconfig build requirement should be fontconfig-devel, previously masked by Gtk3+ dependency

* Fri Jul 26 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.4.11-2
- Rebuild with itself as boot JDK.

* Fri Jul 26 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.4.11-1
- Remove -fno-tree-ch workaround for i686 as the root cause has been
  fixed with 11.0.4+9.
- Resolves RHBZ#1683095

* Tue Jul 09 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.4.11-0
- Update to shenandoah-jdk-11.0.4+11 (GA)
- Switch to GA mode for final release.

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.4.10-0.2.ea
- Obsolete javadoc-slowdebug and javadoc-slowdebug-zip packages via javadoc and javadoc-zip respectively.

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.4.10-0.1.ea
- Update to shenandoah-jdk-11.0.4+10 (EA)

* Sun Jun 30 2019 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.4.2-0.1.ea
- Update to shenandoah-jdk-11.0.4+2 (EA)

* Fri Jun 21 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.4.2-0.1.ea
- Package jspawnhelper (see JDK-8220360).

* Fri Jun 21 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.3.7-6
- Include 'ea' designator in Release when appropriate.

* Wed May 22 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.3.7-6
- Handle milestone as variables so we can alter it easily and set the docs zip filename appropriately.

* Tue May 14 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.3.7-5
- Bump release for rebuild.

* Fri May 10 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.3.7-4
- Add -fno-tree-ch in order to work around GCC 9 issue on
  i686.
- Resolves: RHBZ#1683095

* Thu Apr 25 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.3.7-3
- Don't produce javadoc/javadoc-zip sub packages for the
  debug variant build.
- Don't perform a bootcycle build for the debug variant build.

* Wed Apr 24 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.3.7-2
- Don't generate lib-style requires for -slowdebug subpackages.
- Resolves: RHBZ#1702379

* Tue Apr 23 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.3.7-1
- Fix requires/provides for the non-system JDK case. JDK 11
  isn't a system JDK at this point.
- Resolves: RHBZ#1702324

* Sun Apr 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.3.7-0
- Update to shenandoah-jdk-11.0.3+7 (April 2019 GA)

* Sat Apr 06 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.3.6-0
- Update to shenandoah-jdk-11.0.3+6 (April 2019 EA)
- Drop JDK-8210416/RH1632174 applied upstream.
- Drop JDK-8210425/RH1632174 applied upstream.
- Drop JDK-8210647/RH1632174 applied upstream.
- Drop JDK-8210761/RH1632174 applied upstream.
- Drop JDK-8210703/RH1632174 applied upstream.
- Add cast to resolve s390 ambiguity in call to log2_intptr

* Thu Mar 21 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.2.7-9
- Add patch for RH1566890

* Wed Mar 20 2019 Peter Robinson <pbrobinson@fedoraproject.org> 1:11.0.2.7-8
- Drop chkconfig dep, 1.7 shipped in f24

* Mon Mar 11 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.2.7-7
- Add -Wa,--generate-missing-build-notes=yes C flags. So as to
  fix annocheck warnings for assembler source files.

* Tue Feb 26 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.2.7-6
- Don't package lib/client and lib/client/classes.jsa
  which don't exist.
- Resolves: RHBZ#1643469

* Tue Feb 19 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.2.7-5
- Add explicit requirement for libXcomposite which is used when performing
  screenshots from Java.
- Add explicit BR unzip required for building OpenJDK.

* Thu Feb 14 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.2.7-4
- Add a test verifying system crypto policies can be disabled

* Tue Feb 12 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.2.7-3
- Don't build the test images needlessly.

* Thu Feb 07 2019 Andrew John Hughes <gnu.andrew@redhat.com> - 1:11.0.2.7-2
- Add PR3695 to allow the system crypto policy to be turned off.
- Correct original system crypto policy patch to refer to OpenJDK 11 bug (PR3694)

* Fri Feb 01 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1:11.0.2.7-1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Tue Jan 15 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.2.7-0
- Update to shenandoah-jdk-11.0.2+7 (January 2019 CPU)
- Drop JDK-8211105/RH1628612/RH1630996 applied upstream.
- Drop JDK-8209639/RH1640127 applied upstream.
- Re-generate JDK-8210416/RH1632174 following JDK-8209786

* Fri Jan 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:11.0.1.13-11
- Update to shenandoah-jdk-11.0.1+13-20190101
- Update tarball generation script in preparation for PR3681/RH1656677 SunEC changes.
- Use remove-intree-libraries.sh to remove the remaining SunEC code for now.
- Fix PR1983 SunEC patch so that ecc_impl.h is patched rather than added
- Add missing RH1022017 patch to reduce curves reported by SSL to those we support.
- Remove RH1648995; fixed upstream.

* Wed Dec 5 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.1.13-9
- for non debug supackages, ghosted all masters and slaves (rhbz1649776)
- for tech-preview packages, if-outed versionless provides. Aligned versions to be %%{epoch}:%%{version}-%%{release} instead of chaotic
- Removed all slowdebug provides (rhbz1655938); for tech-preview packages also removed all internal provides

* Wed Nov 28 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.1.13-8
- Added %%global _find_debuginfo_opts -g
- Resolves: RHBZ#1520879 (Detailed NMT issue)

* Mon Nov 12 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.1.13-6
- fixed tck failures of arraycopy and process exec with shenandoah on
- added patch585 rh1648995-shenandoah_array_copy_broken_by_not_always_copy_forward_for_disjoint_arrays.patch

* Wed Nov 07 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.1.13-5
- headless' suggests of cups, replaced by Requires of cups-libs

* Thu Nov 01 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.1.13-3
- added Patch584 jdk8209639-rh1640127-02-coalesce_attempted_spill_non_spillable.patch

* Mon Oct 29 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.1.13-3
- Use upstream's version of Aarch64 intrinsics disable patch:
  - Removed:
    RHBZ-1628612-JDK-8210461-workaround-disable-aarch64-intrinsic.patch
    RHBZ-1630996-JDK-8210858-workaround-disable-aarch64-intrinsic-log.patch
  - Superceded by:
    jdk8211105-aarch64-disable_cos_sin_and_log_intrinsics.patch

* Thu Oct 18 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.1.13-2
- Use LTS designator in version output for RHEL.

* Thu Oct 18 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.1.13-1
- Update to October 2018 CPU release, 11.0.1+13.

* Wed Oct 17 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.0.28-2
- Use --with-vendor-version-string=18.9 so as to show original
  GA date for the JDK.

* Fri Sep 28 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.0.28-1
- Identify as GA version and no longer as early access (EA).
- JDK 11 has been released for GA on 2018-09-25.

* Fri Sep 28 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.28-9
- Rework changes from 1:11.0.ea.22-6. RHBZ#1632174 supercedes
  RHBZ-1624122.
- Add patch, jdk8210416-rh1632174-compile_fdlibm_with_o2_ffp_contract_off_on_gcc_clang_arches.patch, so as to
  optimize compilation of fdlibm library.
- Add patch, jdk8210425-rh1632174-sharedRuntimeTrig_sharedRuntimeTrans_compiled_without_optimization.patch, so
  as to optimize compilation of sharedRuntime{Trig,Trans}.cpp
- Add patch, jdk8210647-rh1632174-libsaproc_is_being_compiled_without_optimization.patch, so as to
  optimize compilation of libsaproc (extra c flags won't override
  optimization).
- Add patch, jdk8210761-rh1632174-libjsig_is_being_compiled_without_optimization.patch, so as to
  optimize compilation of libjsig.
- Add patch, jdk8210703-rh1632174-vmStructs_cpp_no_longer_compiled_with_o0, so as to
  optimize compilation of vmStructs.cpp (part of libjvm.so).
- Reinstate filtering of opt flags coming from redhat-rpm-config.

* Thu Sep 27 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.ea.28-8
- removed version less provides
- javadocdir moved to arched dir as it is no longer noarch

* Thu Sep 20 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.28-6
- Add patch, RHBZ-1630996-JDK-8210858-workaround-disable-aarch64-intrinsic-log.patch,
  so as to disable log math intrinsic on aarch64. Work-around for
  JDK-8210858

* Thu Sep 13 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.28-5
- Add patch, RHBZ-1628612-JDK-8210461-workaround-disable-aarch64-intrinsic.patch,
  so as to disable dsin/dcos math intrinsics on aarch64. Work-around for
  JDK-8210461.

* Wed Sep 12 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.22-6
- Add patch, JDK-8210416-RHBZ-1624122-fdlibm-opt-fix.patch, so as to
  optimize compilation of fdlibm library.
- Add patch, JDK-8210425-RHBZ-1624122-sharedRuntimeTrig-opt-fix.patch, so
  as to optimize compilation of sharedRuntime{Trig,Trans}.cpp
- Add patch, JDK-8210647-RHBZ-1624122-libsaproc-opt-fix.patch, so as to
  optimize compilation of libsaproc (extra c flags won't override
  optimization).
- Add patch, JDK-8210703-RHBZ-1624122-vmStructs-opt-fix.patch, so as to
  optimize compilation of vmStructs.cpp (part of libjvm.so).
- No longer filter -O flags from C flags coming from
  redhat-rpm-config.

* Mon Sep 10 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.ea.28-4
- link to jhsdb followed its file to ifarch jit_arches ifnarch s390x

* Fri Sep 7 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.28-3
- Enable ZGC on x86_64.

* Tue Sep 4 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.ea.28-2
- jfr/*jfc files listed for all arches
- lib/classlist do not exists s390, ifarch-ed via jit_arches out

* Fri Aug 31 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.28-1
- Update to latest upstream build jdk11+28, the first release
  candidate.

* Wed Aug 29 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.22-8
- Adjust system NSS patch, pr1983-rh1565658-support_using_the_system_installation_of_nss_with_the_sunec_provider_jdk11.patch, so
  as to filter -Wl,--as-needed from linker flags. Fixes FTBFS issue.

* Thu Aug 23 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.ea.22-6
- dissabled accessibility, fixed provides for main package's debug variant

* Mon Jul 30 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.ea.22-5
- now buildrequires javapackages-filesystem as the  issue with macros should be fixed

* Wed Jul 18 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.ea.22-2
- changed to build by itself instead of by jdk10

* Tue Jul 17 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.ea.22-1
- added Recommends gtk3 for main package
- changed BuildRequires from gtk2-devel to gtk3-devel (it can be more likely dropped)
- added Suggests lksctp-tools, pcsc-lite-devel, cups for headless package
- see RHBZ1598152
- added trick to catch hs_err files (sgehwolf)
- updated to shenandaoh-jdk-11+22

* Sat Jul 07 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.ea.20-1
- removed patch6 JDK-8205616-systemLcmsAndJpgFixFor-rev_f0aeede1b855.patch
- improved a bit generate_source_tarball.sh to serve also for systemtap
- thus deleted generate_tapsets.sh
- simplified and cleared update_package.sh
- moved to single source jdk - from shenandoah/jdk11
- bumped to latest jdk11+20
- adapted PR2126 to jdk11+20
- adapted handling of systemtap sources to new style
- (no (misleading) version inside (full version is in name), thus different sed on tapsets and different directory)
- shortened summaries and descriptions to around 80 chars
- Hunspell spell checked
- license fixed to correct jdk11 (sgehwolf)
- more correct handling of internal libraries (sgehwolf)
- added lib/security/public_suffix_list.dat as +20 have added it (JDK-8201815)
- added test for shenandaoh GC presence where expected
- Removed workaround for broken aarch64 slowdebug build
- Removed all defattrs
- Removed no longer necessary cleanup of diz and  debuginfo files

* Fri Jun 22 2018 Jiri Vanek <jvanek@redhat.com> - 1:11.0.ea.19-1
- updated sources to jdk-11+19
- added patch6 systemLcmsAndJpgFixFor-f0aeede1b855.patch to fix regression of system libraries after f0aeede1b855 commit
- adapted pr1983-rh1565658-support_using_the_system_installation_of_nss_with_the_sunec_provider_jdk11.patch to accommodate changes after f0aeede1b855 commit

* Thu Jun 14 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.16-5
- Revert rename: java-11-openjdk => java-openjdk.

* Wed Jun 13 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.16-4
- Add aarch64 to aot_arches.

* Wed Jun 13 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.16-3
- Rename to package java-11-openjdk.

* Wed Jun 13 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.16-2
- Disable Aarch64 slowdebug build (see JDK-8204331).
- s390x doesn't have the SA even though it's a JIT arch.

* Wed Jun 13 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:11.0.ea.16-1
- Initial version of JDK 11 ea based on tag jdk-11+16.
- Removed patches no longer needed or upstream:
  sorted-diff.patch (see JDK-8198844)
  JDK-8201788-bootcycle-images-jobs.patch
  JDK-8201509-s390-atomic_store.patch
  JDK-8202262-libjsig.so-extra-link-flags.patch (never was an issue on 11)
  JDK-8193802-npe-jar-getVersionMap.patch
- Updated and renamed patches:
  java-openjdk-s390-size_t.patch => JDK-8203030-s390-size_t.patch
- Updated patches for JDK 11:
  pr1983-rh1565658-support_using_the_system_installation_of_nss_with_the_sunec_provider_jdk11.patch

* Tue Jun 12 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:10.0.1.10-9
- Use proper private_libs expression for filtering requires/provides.

* Fri Jun 08 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:10.0.1.10-8
- Bump release and rebuild for fixed gdb. See RHBZ#1589118.

* Mon Jun 04 2018 Jiri Vanek <jvanek@redhat.com> - 1:10.0.1.10-7
- quoted sed expressions, changed possibly confusing # by @
- added vendor(origin) into icons
- removed last trace of relative symlinks
- added BuildRequires of javapackages-tools to fix build failure after Requires change to javapackages-filesystem

* Thu May 17 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:10.0.1.10-5
- Move to javapackages-filesystem for directory ownership.
  Resolves RHBZ#1500288

* Mon Apr 30 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:10.0.1.10-4
- Add JDK-8193802-npe-jar-getVersionMap.patch so as to fix
  RHBZ#1557375.

* Mon Apr 23 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:10.0.1.10-3
- Inject build flags properly. See RHBZ#1571359
- Added patch JDK-8202262-libjsig.so-extra-link-flags.patch
  since libjsig.so doesn't get linker flags injected properly.

* Fri Apr 20 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:10.0.1.10-2
- Removed unneeded patches:
  PStack-808293.patch
  multiple-pkcs11-library-init.patch
  ppc_stack_overflow_fix.patch
- Added patches for s390 Zero builds:
  JDK-8201495-s390-java-opts.patch
  JDK-8201509-s390-atomic_store.patch
- Renamed patches for clarity:
  aarch64BuildFailure.patch => JDK-8200556-aarch64-slowdebug-crash.patch
  systemCryptoPolicyPR3183.patch => pr3183-rh1340845-support_fedora_rhel_system_crypto_policy.patch
  bootcycle_jobs.patch => JDK-8201788-bootcycle-images-jobs.patch
  system-nss-ec-rh1565658.patch => pr1983-rh1565658-support_using_the_system_installation_of_nss_with_the_sunec_provider_jdk11.patch

* Fri Apr 20 2018 Jiri Vanek <jvanek@redhat.com> - 1:10.0.1.10-1
- updated to security update 1
- jexec unlinked from path
- used java-openjdk as boot jdk
- aligned provides/requires
- renamed zip javadoc

* Tue Apr 10 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:10.0.0.46-12
- Enable basic EC ciphers test in %%check.

* Tue Apr 10 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:10.0.0.46-11
- Port Martin Balao's JDK 9 patch for system NSS support to JDK 10.
- Resolves RHBZ#1565658

* Mon Apr 09 2018 Jiri Vanek <jvanek@redhat.com> - 1:10.0.0.46-10
- jexec linked to path

* Fri Apr 06 2018 Jiri Vanek <jvanek@redhat.com> - 1:10.0.0.46-9
- subpackage(s) replaced by sub-package(s) and other cosmetic changes

* Tue Apr 03 2018 Jiri Vanek <jvanek@redhat.com> - 1:10.0.0.46-8
- removed accessibility sub-packages
- kept applied patch and properties files
- debug sub-packages renamed to slowdebug

* Fri Feb 23 2018 Jiri Vanek <jvanek@redhat.com> - 1:10.0.0.46-1
- initial load
