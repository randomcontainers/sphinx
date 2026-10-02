"""Collect the license files that five sphinxcontrib wheels leave out.

Usage: bundled-licenses.py

The wheels of sphinxcontrib-applehelp, -devhelp, -htmlhelp, -qthelp and
-serializinghtml are built with flit_core, which copies only files named
COPYING* and LICENSE* into a wheel. Their license file is LICENCE.rst, so
the wheels have none. For each of them this reads the version pinned in
requirements.lock, checks that the locked wheel still has no license file,
downloads the source release, checks it against its SHA-256 on PyPI and
writes its LICENCE.rst to licenses/<name>-<version>/. Run it whenever one of
these pins in requirements.lock changes.
"""

import hashlib
import io
import json
import pathlib
import re
import shutil
import sys
import tarfile
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent

PACKAGES = (
    "sphinxcontrib-applehelp",
    "sphinxcontrib-devhelp",
    "sphinxcontrib-htmlhelp",
    "sphinxcontrib-qthelp",
    "sphinxcontrib-serializinghtml",
)
LICENSE_FILE = "LICENCE.rst"

# The file names scripts/metadata.py takes as license files.
LICENSE_NAMES = ("LICENSE", "LICENCE", "COPYING", "NOTICE", "AUTHORS")


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def fetch_checked(item):
    data = fetch(item["url"])
    if hashlib.sha256(data).hexdigest() != item["digests"]["sha256"]:
        sys.exit(f"{item['url']} does not match its SHA-256 on PyPI")
    return data


def locked(lock, name):
    match = re.search(rf"^{re.escape(name)}==([^\s;]+)((?:\s*\\\n\s*--hash=sha256:[0-9a-f]{{64}})+)", lock, re.M)
    if not match:
        sys.exit(f"requirements.lock does not pin {name}")
    return match.group(1), set(re.findall(r"sha256:([0-9a-f]{64})", match.group(2)))


def has_license_file(wheel):
    for path in wheel.namelist():
        parts = path.split("/")
        if len(parts) < 2 or not parts[0].endswith(".dist-info"):
            continue
        if parts[1] == "licenses" or parts[-1].upper().startswith(LICENSE_NAMES):
            return True
    return False


def license_text(name, version, hashes):
    release = json.loads(fetch(f"https://pypi.org/pypi/{name}/{version}/json"))
    wheels = [f for f in release["urls"] if f["packagetype"] == "bdist_wheel" and f["digests"]["sha256"] in hashes]
    if not wheels:
        sys.exit(f"no wheel of {name} {version} on PyPI has a hash listed in requirements.lock")
    for item in wheels:
        with zipfile.ZipFile(io.BytesIO(fetch_checked(item))) as wheel:
            if has_license_file(wheel):
                print(f"{item['filename']} has a license file, so {name} {version} needs no copy")
                return None

    sdists = [f for f in release["urls"] if f["packagetype"] == "sdist"]
    if len(sdists) != 1 or not sdists[0]["filename"].endswith(".tar.gz"):
        sys.exit(f"{name} {version} has no single .tar.gz source release on PyPI")
    sdist = sdists[0]
    top = sdist["filename"].removesuffix(".tar.gz")
    with tarfile.open(fileobj=io.BytesIO(fetch_checked(sdist))) as tar:
        try:
            text = tar.extractfile(f"{top}/{LICENSE_FILE}").read()
        except KeyError:
            sys.exit(f"{sdist['url']} has no {top}/{LICENSE_FILE}")
    if not text.strip():
        sys.exit(f"{top}/{LICENSE_FILE} in {sdist['url']} is empty")
    return text


def main():
    lock = (ROOT / "requirements.lock").read_text()
    texts = {}
    for name in PACKAGES:
        version, hashes = locked(lock, name)
        texts[(name, version)] = license_text(name, version, hashes)

    base = ROOT / "licenses"
    for name, version in texts:
        for old in base.glob(f"{name}-*"):
            shutil.rmtree(old)
    for (name, version), text in texts.items():
        if text is None:
            continue
        out = base / f"{name}-{version}"
        out.mkdir(parents=True)
        (out / LICENSE_FILE).write_bytes(text)
        print(f"wrote {(out / LICENSE_FILE).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
