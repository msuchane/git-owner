Name: git-owner
Summary: Estimate who the approximate owner of a file is in a Git repository.
Version: 0.1.1
Release: 1%{?dist}
License: ASL 2.0
URL: https://github.com/msuchane/git-owner
Group: Applications/Text
Source0: https://github.com/msuchane/%{name}/archive/refs/tags/v%{version}.tar.gz

Requires: python3
Requires: git

%description
Estimate who the approximate owner of a file is in a Git repository. Take into account the Git blame and Git log information.

%prep
# Unpack the sources.
%setup -q

%install
# Clean up previous artifacts.
rm -rf %{buildroot}
# Prepare the target directories.
install -d %{buildroot}%{_bindir}
# install -d %{buildroot}%{_mandir}/man1
# Install the executable into the chroot environment.
install -m 0755 git_owner/__init__.py %{buildroot}%{_bindir}/%{name}
# Compress the man page
# gzip -c target/release/build/%{name}-*/out/%{name}.1 > %{name}.1.gz
# Install the man page into the chroot environment.
# install -m 0644 %{name}.1.gz %{buildroot}%{_mandir}/man1/%{name}.1.gz

%files
# Pick documentation and license files from the source directory.
%doc README.md
# %doc CHANGELOG.md
%license LICENSE
# %{_mandir}/man1/%{name}.1.gz
# Pick the executable from the virtual, chroot system.
%{_bindir}/%{name}
