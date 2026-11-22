# Flint Launcher 1.0.1

A lightweight, terminal-based Minecraft launcher for Windows written in Python.

## Features

- Minecraft versions: Any release version of Minecraft with autocomplete search
- Loaders: Forge, NeoForge and Fabric
- Automatic Java installation: downloads the required Java runtime when it is not available
- Authentication: Offline username
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
python flauncher-1.0.1.py
```

## Build

Requirements: Windows, Python 3.10+ and the dependencies from `requirements.txt`.

### Nuitka (recommended)

```bash
python -m nuitka --onefile --assume-yes-for-downloads --enable-plugin=tk-inter --include-package-data=minecraft_launcher_lib --output-filename=FlintLauncher.exe flauncher-1.0.1.py
```

### PyInstaller

```bash
python -m PyInstaller --onefile --name FlintLauncher --collect-all minecraft_launcher_lib --hidden-import tkinter flauncher-1.0.1.py
```

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).
