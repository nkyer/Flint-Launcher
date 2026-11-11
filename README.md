# Flint Launcher

A lightweight, terminal-based Minecraft launcher written in Python.

- Minecraft versions: browse and install available release versions
- Loaders: Vanilla, Forge, NeoForge, Fabric, Quilt
- Account: ely.by authentication or offline username
- Modrinth integration: search and download mods, resource packs and shader packs
- Organized storage: separate directories for mods, resource packs and shaders, with support for universal files
- Automatic Java installation: downloads the required Java runtime when it is not available
- Automatic dependency installation: detects and offers to install missing Python packages

Launcher data is stored in `~/.launcher` (can be changed)

## Installation

### Automatic

On first launch, Flint Launcher checks for missing dependencies and offers to install them automatically.

### Manual

Install the required dependencies from requirements.

```bash
pip install -r requirements.txt
```

## Build

### Nuitka (recommended) 
```bash
python -m nuitka --onefile --assume-yes-for-downloads --include-package-data=minecraft_launcher_lib --plugin-disable=multiprocessing "--nofollow-import-to=tkinter,_tkinter,turtle,unittest,pydoc,pydoc_data,doctest,test,setuptools,pip,distutils,lib2to3,idlelib,asyncio,multiprocessing,concurrent.futures.process,xmlrpc,xml,decimal,_pydecimal,_decimal,statistics,fractions,_pydatetime,_pyio,tomllib,html,tarfile,argparse,gettext,getopt,configparser,pickletools,tracemalloc,cgi,cgitb,chunk,cmd,code,codeop,colorsys,difflib,filecmp,fileinput,ftplib,imaplib,poplib,imghdr,sndhdr,mailcap,modulefinder,pipes,pstats,pyclbr,rlcompleter,symtable,timeit,trace,webbrowser,xdrlib,uu,sched,socketserver,graphlib,py_compile,urllib3.contrib.pyopenssl,urllib3.contrib.socks,charset_normalizer,urllib3.http2.connection,sqlite3,curses,ensurepip" --noinclude-unittest-mode=nofollow --noinclude-setuptools-mode=nofollow --noinclude-pytest-mode=nofollow --python-flag=no_docstrings --python-flag=-OO --lto=yes "--onefile-tempdir-spec={CACHE_DIR}/FlintLauncher/1.0.0" --windows-console-mode=force --report=build/report.xml --output-dir=build --output-filename=FlintLauncher.exe launcher.py
```

### PyInstaller

```powershell
python -m PyInstaller launcher.py --onefile --console --noconfirm --clean --name FlintLauncher --collect-data minecraft_launcher_lib --optimize 2 --noupx --log-level WARN $("tkinter,_tkinter,turtle,unittest,pydoc,pydoc_data,doctest,test,setuptools,pip,distutils,lib2to3,idlelib,asyncio,multiprocessing,concurrent.futures.process,xmlrpc,xml,decimal,_pydecimal,_decimal,statistics,fractions,_pydatetime,_pyio,tomllib,html,tarfile,argparse,gettext,getopt,configparser,pickletools,tracemalloc,cgi,cgitb,chunk,cmd,code,codeop,colorsys,difflib,filecmp,fileinput,ftplib,imaplib,poplib,imghdr,sndhdr,mailcap,modulefinder,pipes,pstats,pyclbr,rlcompleter,symtable,timeit,trace,webbrowser,xdrlib,uu,sched,socketserver,graphlib,py_compile,urllib3.contrib.pyopenssl,urllib3.contrib.socks,charset_normalizer,urllib3.http2.connection,sqlite3,curses,ensurepip".Split(",") | ForEach-Object { "--exclude-module",$_ })
```

## Storage

The launcher maintains its own directory structure:

```text
~/.launcher/
├── config.json
├── .minecraft/
├── mods/
│   ├── universal/
│   └── <minecraft-version>/
│       ├── forge/
│       ├── neoforge/
│       └── fabric/
├── resourcepacks/
│   ├── universal/
│   └── <minecraft-version>/
└── shaderpacks/
    ├── universal/
    └── <minecraft-version>/
```

Files placed in `universal` directories are available across Minecraft versions.
