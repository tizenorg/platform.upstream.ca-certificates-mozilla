#
# spec file for package ca-certificates-mozilla
#
# Copyright (c) 2015 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#

Name:           ca-certificates-mozilla
# Version number is NSS_BUILTINS_LIBRARY_VERSION in this file:
# http://hg.mozilla.org/projects/nss/file/default/lib/ckfw/builtins/nssckbi.h
Version:        2.6
Release:        0
Summary:        CA certificates for OpenSSL
License:        MPL-2.0
Group:          Security/Certificate Management
Url:            http://www.mozilla.org
# IMPORTANT: procedure to update certificates:
# - Check the log of the cert file:
#   http://hg.mozilla.org/projects/nss/log/default/lib/ckfw/builtins/certdata.txt
# - download the new certdata.txt
#   wget -O certdata.txt "http://hg.mozilla.org/projects/nss/file/default/lib/ckfw/builtins/certdata.txt"
# - run compareoldnew to show fingerprints of new and changed certificates
# - check the bugs referenced in hg log and compare the checksum
#   to output of compareoldnew
# - Watch out that blacklisted or untrusted certificates are not
#   accidentally included!
#Source:         http://hg.mozilla.org/projects/nss/raw-file/default/lib/ckfw/builtins/certdata.txt
#Source1:        http://hg.mozilla.org/projects/nss/raw-file/default/lib/ckfw/builtins/nssckbi.h
Source:         certdata.txt
Source1:        nssckbi.h
# from Fedora. Note: currently contains extra fix to remove quotes. Pending upstream approval.
Source10:       certdata2pem.py
Source11:       %{name}.COPYING
Source12:       compareoldnew
Source13:       %{name}.manifest
BuildArch:      noarch
BuildRequires:  p11-kit-devel
BuildRequires:  openssl
BuildRequires:  ca-certificates
BuildRequires:  python
BuildRequires:  pkgconfig(libtzplatform-config)
# for update-ca-certificates
Requires(post):    ca-certificates
Requires(postun):  ca-certificates

%description
This package contains some CA root certificates for OpenSSL extracted
from MozillaFirefox


%prep
%setup -qcT

/bin/cp %{SOURCE0} %{SOURCE13} .

install -m 644 %{SOURCE11} COPYING
ver=`sed -ne '/NSS_BUILTINS_LIBRARY_VERSION /s/.*"\(.*\)"/\1/p' < "%{SOURCE1}"`
if [ "%{version}" != "$ver" ]; then
	echo "*** Version number mismatch: spec file should be version $ver"
	false
fi

%define trustdir_static %{TZ_SYS_SHARE}/ca-certificates/certs

%build
python %{SOURCE10}

%install
mkdir -p %{buildroot}/%{trustdir_static}/anchors
set +x
for i in *.crt; do
	args=()
	trust=`sed -n '/^# openssl-trust=/{s/^.*=//;p;q;}' "$i"`
	distrust=`sed -n '/^# openssl-distrust=/{s/^.*=//;p;q;}' "$i"`
	alias=`sed -n '/^# alias=/{s/^.*=//;p;q;}' "$i"`
	args+=('-trustout')
	for t in $trust; do
		args+=("-addtrust" "$t")
	done
	for t in $distrust; do
		args+=("-addreject" "$t")
	done
	[ -z "$alias" ] || args+=('-setalias' "$alias")

	echo "$i ${args[*]}"
	fname="%{buildroot}/%{trustdir_static}$d/${i%%:*}.pem"
	if [ -e "$fname" ]; then
		fname="${fname%.pem}"
		j=1
		while [ -e "$fname.$j.pem" ]; do
			j=$((j+1))
		done
		fname="$fname.$j.pem"
	fi
	{
		grep '^#' "$i"
		openssl x509 -in "$i" "${args[@]}"
	} > "$fname"
done
for i in *.p11-kit ; do
	install -m 644 "$i" "%{buildroot}/%{trustdir_static}"
done

for i in %{buildroot}/%{trustdir_static}/*.pem; do
	subject_hash=`openssl x509 -in "$i" -noout -subject_hash`
	suffix=0
	new_fname="%{buildroot}/%{trustdir_static}/$subject_hash"
	while [ -e "$new_fname.$suffix" ]; do
		suffix=$((suffix+1))
	done
	new_fname="$new_fname.$suffix"
	mv "$i" "$new_fname"
done
set -x

%post
update-ca-certificates || true

%postun
update-ca-certificates || true

%files
%manifest %{name}.manifest
%license COPYING
%{trustdir_static}

%changelog
