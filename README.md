# sphinx

Container images with [Sphinx](https://www.sphinx-doc.org/), the documentation generator that turns reStructuredText sources into HTML, LaTeX, ePub, man pages and other formats. `latest` also includes Graphviz, which the `graphviz` and `inheritance_diagram` extensions use to draw diagrams. Sphinx is installed from PyPI into a virtual environment on Ubuntu or Alpine, for `linux/amd64` and `linux/arm64`, and the images are rebuilt when Sphinx publishes a release and when the base image changes.

This is an unofficial build, not affiliated with or endorsed by the Sphinx project. Report problems with the image in this repository and problems with Sphinx itself [upstream](https://github.com/sphinx-doc/sphinx/issues).

## Quick start

Build the HTML pages of the project whose `conf.py` is in the current directory:

```sh
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" ghcr.io/randomcontainers/sphinx
```

The entrypoint is `sphinx-build`, and its default arguments, `-M html . _build`, write the pages to `_build/html`. `make html` runs the same command in a project that `sphinx-quickstart` created without a separate source directory. The image has no `make`, so for other targets and directories pass the `sphinx-build` arguments yourself. A project in `docs/`, with warnings turned into errors:

```sh
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" \
  ghcr.io/randomcontainers/sphinx -W -b html docs docs/_build/html
```

Start a new project in `docs/`. `sphinx-quickstart` asks questions, so keep `-it`:

```sh
docker run --rm -it --user "$(id -u):$(id -g)" -v "$PWD:/work" \
  --entrypoint sphinx-quickstart ghcr.io/randomcontainers/sphinx docs
```

The other programs also run with `--entrypoint`. `sphinx-apidoc` writes a page for each module of a Python package, `sphinx-autogen` writes the stub pages that `autosummary` directives list, and `rst2html` converts a single reStructuredText file without a Sphinx project:

```sh
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" \
  --entrypoint sphinx-apidoc ghcr.io/randomcontainers/sphinx -o docs/api src/mypackage
docker run --rm -i --entrypoint rst2html ghcr.io/randomcontainers/sphinx < notes.rst > notes.html
```

## Themes and extensions

The images have Sphinx's built-in themes and alabaster, the default theme. Most built-in extensions need nothing else; these do:

- `sphinx.ext.graphviz` and `sphinx.ext.inheritance_diagram` run `dot` from Graphviz, which only the default image has.
- `sphinx.ext.imgmath` needs LaTeX and dvipng or dvisvgm, and the `latexpdf` target of `-M` needs LaTeX, latexmk and `make`. Neither image has them. `-b latex` still writes the `.tex` files. HTML pages render math with MathJax by default, which the reader's browser loads from a CDN.
- `sphinx.ext.imgconverter` needs ImageMagick.
- `sphinx.ext.intersphinx` and the `linkcheck` builder need network access.
- `sphinx.ext.autodoc` imports the code it documents. It finds pure-Python code in the mounted directory once `conf.py` adds its location to `sys.path`. Its dependencies, and a package with compiled extensions, must be installed in Sphinx's virtual environment.

Third-party themes and extensions, such as Furo, sphinx-rtd-theme or MyST-Parser, and the packages that autodoc needs go into Sphinx's virtual environment, in an image of your own:

```dockerfile
FROM ghcr.io/randomcontainers/sphinx:latest@sha256:...
USER root
RUN /usr/local/lib/sphinx/bin/pip freeze > /tmp/installed.txt \
 && /usr/local/lib/sphinx/bin/pip install --no-cache-dir --only-binary=:all: \
      -c /tmp/installed.txt furo myst-parser \
 && rm /tmp/installed.txt
USER 1000:1000
```

`pip freeze` lists the packages already in the image, and `-c` holds them at those versions. If a theme or extension needs a different version of Sphinx, docutils or another of their dependencies, pip stops with an error and changes nothing, so Sphinx stays at the version the tag names. The images have no compiler, so every package must also be available as a wheel for the platform. With `--only-binary=:all:`, pip never tries to build one and fails instead. Most themes and extensions are pure Python and have a single wheel for every platform.

## What is in the image

| | slim | default |
|---|---|---|
| Sphinx, docutils and their Python dependencies, installed from `requirements.lock` | yes | yes |
| Graphviz, for the `graphviz` and `inheritance_diagram` extensions | no | yes |

Graphviz is the [randomcontainers/graphviz](https://github.com/randomcontainers/graphviz) build.

`sphinx-build`, `sphinx-quickstart`, `sphinx-apidoc`, `sphinx-autogen` and docutils' `rst2html` are in `/usr/local/bin`, linked from a virtual environment in `/usr/local/lib/sphinx` that uses the distro's `python3`. The other docutils programs, such as `rst2man` and `rst2latex`, and pip stay in the virtual environment's `bin` directory.

## Default or slim

The default image (`latest`) has Sphinx and Graphviz and is recommended for general use. Many projects enable the `graphviz` or `inheritance_diagram` extension, and without `dot` Sphinx warns and prints the DOT source where each diagram should be. Use `slim`, which has Sphinx and Python only, when your documentation draws no diagrams, or as the base when you build your own image.

The default image is also published as `ghcr.io/randomcontainers/sphinx-graphviz`, built in the [sphinx-graphviz](https://github.com/randomcontainers/sphinx-graphviz) repository with the same contents and a different digest.

## Tags

`<version>` is a Sphinx release such as `9.1.0`. `<minor>` and `<major>` are its shorter forms, `9.1` and `9`, and follow the newest release in that series.

| Default (with Graphviz) | Slim | Base |
|---|---|---|
| `latest`, `<version>`, `<minor>`, `<major>` | `slim`, `<version>-slim`, `<minor>-slim`, `<major>-slim` | Ubuntu |
| `ubuntu`, `<version>-ubuntu`, `<minor>-ubuntu`, `<major>-ubuntu` | `slim-ubuntu`, `<version>-slim-ubuntu`, `<minor>-slim-ubuntu`, `<major>-slim-ubuntu` | Ubuntu |
| `<version>-ubuntu26.04` | `<version>-slim-ubuntu26.04` | Ubuntu 26.04 |
| `alpine`, `<version>-alpine`, `<minor>-alpine`, `<major>-alpine` | `slim-alpine`, `<version>-slim-alpine`, `<minor>-slim-alpine`, `<major>-slim-alpine` | Alpine |
| `<version>-alpine3.24` | `<version>-slim-alpine3.24` | Alpine 3.24 |

The images are currently built on Ubuntu 26.04 and Alpine 3.24. Tags without a distro version move to the next distro release when the project does; tags ending in `ubuntu26.04` or `alpine3.24` stay on that release and are no longer rebuilt once the project moves to the next one. Every tag of the current Sphinx version, including the exact version, is rebuilt in place (see [Updates](#updates)), so pin a digest when you need the same bytes every time.

## Platforms

`linux/amd64` and `linux/arm64`, for both Ubuntu and Alpine. Both are built natively on GitHub-hosted runners, without emulation. The same `requirements.lock` is installed on all four combinations of distro and architecture. Most of it is pure Python; MarkupSafe and charset-normalizer come as glibc (`manylinux`) wheels on Ubuntu and musl (`musllinux`) wheels on Alpine.

## Files and permissions

The working directory is `/work`. The image runs as UID 1000, and any other UID works too: `HOME` is then `/`, and caches go to `/cache`, which anyone can write to. Sphinx writes its output and its doctree cache (`.doctrees` inside the output directory, or `doctrees` in the build directory with `-M`) into the mounted directory, so run it as your own user:

| Runtime | Flag |
|---|---|
| Docker on Linux (rootful), GitHub Actions | `--user "$(id -u):$(id -g)"` |
| Rootless Podman | `--userns=keep-id` |
| Rootless Docker | `--user 0:0` (root in the container is your user on the host) |
| Docker Desktop on macOS or Windows | none, file ownership is mapped for you |

## Extending the slim image

Use a `slim` tag as the base for your own image. `slim`, `slim-ubuntu` and `slim-alpine` follow new Sphinx releases and are rebuilt when its locked Python dependencies or the distro change. The default tags work the same way when your image also needs Graphviz. Sphinx runs from a virtual environment in `/usr/local/lib/sphinx`; the `python3` on `PATH` is the distro's interpreter and cannot import Sphinx, so install Python packages with `/usr/local/lib/sphinx/bin/pip` as shown in [Themes and extensions](#themes-and-extensions). The distro packages Sphinx needs are listed in `/usr/local/share/randomcontainers/sphinx/runtime-deps`. Switch to root to install more, for example `git` for extensions that read the commit history, then back:

```dockerfile
FROM ghcr.io/randomcontainers/sphinx:slim-ubuntu@sha256:...
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*
USER 1000:1000
```

On Alpine, use `apk add --no-cache git`. The entrypoint is `["tini", "--", "sphinx-build"]`; set your own `ENTRYPOINT` if your image runs a script. To pick up new Sphinx releases and base image fixes, let Dependabot or Renovate update the digest in your `FROM` line.

## Verifying

Each image has a build provenance attestation from this repository's GitHub Actions run, signed by the shared build workflow in `randomcontainers/ci`:

```sh
gh attestation verify oci://ghcr.io/randomcontainers/sphinx:latest \
  --repo randomcontainers/sphinx --signer-repo randomcontainers/ci
```

Images from `ghcr.io/randomcontainers/sphinx-graphviz` are built in that repository, so verify them with `--repo randomcontainers/sphinx-graphviz` and the same `--signer-repo`.

Each platform image also carries an SPDX SBOM that lists the distro and Python packages in it with their versions:

```sh
docker buildx imagetools inspect ghcr.io/randomcontainers/sphinx:latest --format '{{ json .SBOM }}'
```

Sphinx and its Python dependencies are installed from [`requirements.lock`](requirements.lock), which pins every package to a version and its SHA-256 hashes, and pip refuses anything else. The URL and hash of each installed wheel are in `/usr/local/share/randomcontainers/sphinx/source`, and the installed versions in `buildinfo` next to it.

## Updates

The project checks [Sphinx on PyPI](https://pypi.org/project/Sphinx/) every 15 minutes. A release is picked up once it is 24 hours old and PyPI holds a provenance attestation showing it was published from the [sphinx-doc/sphinx](https://github.com/sphinx-doc/sphinx) repository. The new version and a regenerated `requirements.lock` are then committed together and the images are rebuilt. Only the newest release is built; tags of older versions stay as they were last built. Dependency versions in the lock must have been on PyPI for at least 7 days. The lock is also regenerated weekly at the same Sphinx version, so new releases of dependencies such as docutils and Pygments reach the current tags between Sphinx releases. When a new lock would change the version of one of the sphinxcontrib packages whose license files are kept in `licenses/`, the update, including a new Sphinx release, waits until those files are refreshed by hand (see [Building](#building)).

The images of the current version are also rebuilt when the Ubuntu or Alpine base image changes, the default ones when a new Graphviz image is published, and all of them at least every 7 days, so distro security fixes reach the current tags.

## Building

```sh
docker build -f Dockerfile.ubuntu --target slim --build-arg VERSION=<version> -t sphinx:local .
```

Use `Dockerfile.alpine` for the Alpine image. `<version>` must be the version pinned in `requirements.lock`; the build stops otherwise. The default image is generated from the `combos` section of `package.yml` by [randomcontainers/ci](https://github.com/randomcontainers/ci) and layers this image onto the Graphviz image.

The command that produced `requirements.lock` is on its second line; it resolves for Python 3.14, the version on both bases. To regenerate the lock at the version in `package.yml`, run `rc lock requirements.lock` in this directory. `rc` is the command-line tool of randomcontainers/ci, and it needs uv on `PATH`. If a new lock changes the version of sphinxcontrib-applehelp, sphinxcontrib-devhelp, sphinxcontrib-htmlhelp, sphinxcontrib-qthelp or sphinxcontrib-serializinghtml, run `python3 scripts/bundled-licenses.py` to refresh `licenses/`. The build fails until those files match the installed packages.

## Licenses

Sphinx is released under the [BSD 2-Clause license](https://github.com/sphinx-doc/sphinx/blob/master/LICENSE.rst). It is pure Python, so the installed files are its source, and the wheel it was installed from is named in `/usr/local/share/randomcontainers/sphinx/source`. The slim image adds its Python dependencies, which are mostly under BSD and MIT licenses, plus certifi (MPL-2.0), requests (Apache-2.0) and docutils, which is mostly in the public domain, with some files under BSD licenses. babel contains the Unicode CLDR locale data, under the Unicode License v3, whose text is in `/usr/local/share/randomcontainers/sphinx/licenses/babel/locale-data/LICENSE.unicode`. pip (MIT) includes packages under the Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MIT, MPL-2.0 and PSF-2.0 licenses. The complete SPDX expression is in the image's `org.opencontainers.image.licenses` label, and each package's license files are in `/usr/local/share/randomcontainers/sphinx/licenses/`.

The wheels of sphinxcontrib-applehelp, sphinxcontrib-devhelp, sphinxcontrib-htmlhelp, sphinxcontrib-qthelp and sphinxcontrib-serializinghtml (BSD-2-Clause) contain no license file: their build tool picks up `LICENSE*` and `COPYING*` files, and theirs is named `LICENCE.rst`. This repository keeps that file from each package's source release in [`licenses/`](licenses/), and the image has it in `/usr/local/share/randomcontainers/sphinx/licenses/<package>/`. The docutils wheel includes the text of the GPL-3.0, which in docutils covers only an Emacs mode that is not part of the wheel, so the label leaves it out.

`latest` also contains Graphviz, which is mainly licensed under the Eclipse Public License 2.0 (EPL-2.0). Its license files and corresponding source are described in the [graphviz repository](https://github.com/randomcontainers/graphviz#licenses).

The files in this repository are available under the MIT license, see [LICENSE](LICENSE), except the license texts in `licenses/`, which keep their own terms.

## Requesting a tool

To suggest another tool, use the [Request a tool](https://github.com/randomcontainers/.github/issues/new?template=tool-request.yml) form.
