# Installation-media APT source repair

Ubuntu installations made from an ISO can leave a dedicated
`/etc/apt/sources.list.d/cdrom.sources` entry pointing to installation media.
Once that media is absent, APT may request a CD-ROM, report a missing Release
file, or fail its cache update. This can block package installation even when
network repositories are configured correctly. No exact VM error log has been
saved in this repository, so these are typical symptoms, not quoted test output.

The common role imports `tasks/apt_sources.yml` **before its first APT task**.
It checks whether the dedicated file exists and comments every uncommented
non-empty line. All stanzas in that installer-only file are disabled, including
multiple media stanzas; comments retain their original contents for inspection.
Missing files are tolerated. A second application matches no active lines and
reports no change. A source change forces the following package-index refresh.

This policy assumes `cdrom.sources` is the dedicated installation-media file.
Do not put custom network repositories there. `ubuntu.sources`, Docker sources,
legacy `/etc/apt/sources.list`, and other `.sources` files are not edited. It does
not disable signature verification, mark sources trusted, or ignore APT errors.
A cdrom entry stored elsewhere needs separate inspection rather than a blanket
rewrite of every source file.

APT accepts comments to disable deb822 entries, as documented in the
[Ubuntu sources.list manual](https://manpages.ubuntu.com/manpages/noble/man5/sources.list.5.html).

## Executed regression test

`ansible/tests/apt-sources.yml` invokes the real task file against a freshly
allocated temporary directory, without sudo, APT commands or VM access. It tests:

- An absent installation-media file is not created.
- Multiple installer stanzas become comments while retaining their contents.
- The second repair reports no changes.
- A separate HTTP network source remains byte-for-byte unchanged.

Run from `ansible/` with the project venv active:

```bash
ansible-playbook -i tests/inventory/ci.ini tests/apt-sources.yml
```

The fixture removes only its own temporary directory. This proves local file
transformation/idempotency, not a successful APT update on the real VMs.
The role change has not been deployed during publication review. Applying it
requires permission for the next VM configuration run. Do not rerun setup merely
to finalize documentation.
