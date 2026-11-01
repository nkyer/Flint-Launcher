# Flint Launcher

A lightweight, terminal-based Minecraft launcher written in Python.

- Minecraft versions: browse and install available release versions
- Loaders: Vanilla, Fabric, Forge, NeoForge
- Modrinth integration: search and download mods, resource packs and shader packs
- - Organized storage: separate directories for mods, resource packs and shaders, with support for universal files
- Automatic Java installation: downloads the required Java runtime when it is not available
- Automatic dependency installation: detects and offers to install missing Python packages
- Persistent configuration: remembers selected versions, loaders and launcher settings

Launcher data is stored in `~/.launcher`.

## Installation

### Automatic

1. Download `launcher.py` from this repository.
2. Run it using Python:

```bash
python launcher.py
```

On first launch, Flint Launcher checks for missing dependencies and offers to install them automatically.

### Manual

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the launcher:

```bash
python launcher.py
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
