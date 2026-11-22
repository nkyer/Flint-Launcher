# Flint Launcher 1.1.1

A lightweight, terminal-based Minecraft launcher for Windows written in Python.

## Features

- Minecraft versions: Any release version of Minecraft with autocomplete search
- Loaders: Forge, NeoForge, Fabric and Quilt
- Automatic Java installation: downloads the required Java runtime when it is not available
- Authentication: Offline username or Ely.by
- Modrinth integration: search and download mods, resource packs and shader packs
- Organized storage: separate directories for mods, resource packs and shaders, with support for universal files
- Launcher and game data are stored in `~/.launcher`

## Installation

### From Releases

1. Open the [Releases page](https://github.com/nkyer/Flint-Launcher/releases/latest).
2. Download the file:

   | Platform | File |
   |----------|------|
   | Windows  | `FlintLauncher.exe` |

3. Run it:

   ```bash
   FlintLauncher.exe
   ```

### From Source

Requirements: Windows, Python 3.10+ and `pip`.

```bash
git clone https://github.com/nkyer/Flint-Launcher.git
cd Flint-Launcher
pip install -r requirements.txt
python flauncher-1.1.1.py
```

## Build

Requirements: Windows, Python 3.10+ and the dependencies from `requirements.txt`.

### Nuitka (recommended)

```bash
python -m nuitka --onefile --assume-yes-for-downloads --include-package-data=minecraft_launcher_lib --plugin-disable=multiprocessing "--nofollow-import-to=tkinter,_tkinter,turtle,unittest,pydoc,pydoc_data,doctest,test,setuptools,pip,distutils,lib2to3,idlelib,asyncio,multiprocessing,concurrent.futures.process,xmlrpc,xml,decimal,_pydecimal,_decimal,statistics,fractions,_pydatetime,_pyio,tomllib,html,tarfile,argparse,gettext,getopt,configparser,pickletools,tracemalloc,cgi,cgitb,chunk,cmd,code,codeop,colorsys,difflib,filecmp,fileinput,ftplib,imaplib,poplib,imghdr,sndhdr,mailcap,modulefinder,pipes,pstats,pyclbr,rlcompleter,symtable,timeit,trace,webbrowser,xdrlib,uu,sched,socketserver,graphlib,py_compile,urllib3.contrib.pyopenssl,urllib3.contrib.socks,charset_normalizer,urllib3.http2.connection,sqlite3,curses,ensurepip" --noinclude-unittest-mode=nofollow --noinclude-setuptools-mode=nofollow --noinclude-pytest-mode=nofollow --python-flag=no_docstrings --python-flag=-OO --lto=yes "--onefile-tempdir-spec={CACHE_DIR}/FlintLauncher/1.0.0" --windows-console-mode=force --report=build/report.xml --output-dir=build --output-filename=FlintLauncher.exe flauncher-1.1.1.py
```

### PyInstaller

```powershell
python -m PyInstaller flauncher-1.1.1.py --onefile --console --noconfirm --clean --name FlintLauncher --collect-data minecraft_launcher_lib --optimize 2 --noupx --log-level WARN $("tkinter,_tkinter,turtle,unittest,pydoc,pydoc_data,doctest,test,setuptools,pip,distutils,lib2to3,idlelib,asyncio,multiprocessing,concurrent.futures.process,xmlrpc,xml,decimal,_pydecimal,_decimal,statistics,fractions,_pydatetime,_pyio,tomllib,html,tarfile,argparse,gettext,getopt,configparser,pickletools,tracemalloc,cgi,cgitb,chunk,cmd,code,codeop,colorsys,difflib,filecmp,fileinput,ftplib,imaplib,poplib,imghdr,sndhdr,mailcap,modulefinder,pipes,pstats,pyclbr,rlcompleter,symtable,timeit,trace,webbrowser,xdrlib,uu,sched,socketserver,graphlib,py_compile,urllib3.contrib.pyopenssl,urllib3.contrib.socks,charset_normalizer,urllib3.http2.connection,sqlite3,curses,ensurepip".Split(",") | ForEach-Object { "--exclude-module",$_ })
```

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).
