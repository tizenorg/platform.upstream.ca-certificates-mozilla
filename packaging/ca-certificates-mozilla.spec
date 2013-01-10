#
# spec file for package ca-certificates-mozilla
#
# Copyright (c) 2013 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.



%bcond_with trustedcerts

BuildRequires:  openssl

Name:           ca-certificates-mozilla
%define sslusrdir %{_datadir}/ca-certificates
Version:        1.85
Release:        0
Summary:        CA certificates for OpenSSL
License:        MPL-2.0
Group:          Productivity/Networking/Security
Url:            http://www.mozilla.org
# IMPORTANT: procedure to update certificates:
# - Check the CVS log of the cert file:
#   http://bonsai.mozilla.org/cvslog.cgi?file=mozilla/security/nss/lib/ckfw/builtins/certdata.txt&rev=HEAD
#   Alternatively hg:
#   http://hg.mozilla.org/releases/mozilla-release/file/tip/security/nss/lib/ckfw/builtins/certdata.txt
# - download the new certdata.txt
#   wget -O certdata.txt "http://mxr.mozilla.org/mozilla/source//security/nss/lib/ckfw/builtins/certdata.txt?raw=1"
# - run compareoldnew to show fingerprints of new and changed certificates
# - check the bugs referenced in cvs log and compare the checksum
#   to output of compareoldnew
# - Watch out that blacklisted or untrusted certificates are not
#   accidentally included!
Source:         certdata.txt
Source1:        extractcerts.pl
Source2:        %{name}.COPYING
Source3:        compareoldnew
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch
# for update-ca-certificates
Requires(post):    ca-certificates
Requires(postun):  ca-certificates
#
Provides:       openssl-certs = 0.9.9
Obsoletes:      openssl-certs < 0.9.9

%description
This package contains some CA root certificates for OpenSSL extracted
from MozillaFirefox



%prep
%setup -qcT
/bin/cp %{SOURCE0} .
install -m 644 %{S:1} COPYING

%build
perl %{SOURCE1} --trustbits < certdata.txt

%install
mkdir -p %{buildroot}/%{sslusrdir}/mozilla
set +x
for i in *.pem; do
	args=()
	trust=`sed -n '/^# openssl-trust=/{s/^.*=//;p;q;}' "$i"`
	alias=`sed -n '/^# alias=/{s/^.*=//;p;q;}' "$i"`
%if %{with trustedcerts}
	args+=('-trustout')
	for t in $trust; do
		args+=("-addtrust" "$t")
	done
	[ -z "$alias" ] || args+=('-setalias' "$alias")
%else
	case "$trust" in
		*serverAuth*) ;;
		*) echo "skipping $i, not trusted for serverAuth"; continue ;;
	esac
%endif
	echo "$i"
	{
		grep '^#' "$i"
		openssl x509 -in "$i" "${args[@]}"
	} > "%{buildroot}/%{sslusrdir}/mozilla/$i"
done
set -x

%post
update-ca-certificates || true

%postun
update-ca-certificates || true

%files
%defattr(-, root, root)
%doc COPYING
%{sslusrdir}/mozilla

%changelog
