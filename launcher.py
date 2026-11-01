import os
import re
import sys
import json
import time
import random
import subprocess
import shutil
import warnings
from pathlib import Path
from typing import Optional, Dict, Any

warnings.filterwarnings("ignore", category=DeprecationWarning)

if os.name == 'nt':
    os.system("")
    import asyncio
    import ctypes
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        ctypes.windll.kernel32.AllocConsole()
    except:
        pass
    sys.stdout = sys.__stdout__
    sys.stdin = sys.__stdin__
    sys.stderr = sys.__stderr__

REQUIRED_PACKAGES = {
    "minecraft_launcher_lib": "minecraft-launcher-lib",
    "requests": "requests",
    "questionary": "questionary"
}

def checkAndInstallPackages():
    missing = []
    for module, package in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(" \033[97mMissing libraries detected:\033[0m")
        for pkg in missing:
            print(f"  - {pkg}")
        print()
        response = input(" \033[97mWould you like to auto-install these libraries? (y/n): \033[0m").strip().lower()
        if response == 'y':
            for pkg in missing:
                print(f" \033[97mInstalling {pkg}..\033[0m")
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            print(" \033[91mLibraries installed successfully!\033[0m\n")
        else:
            print(" \033[91mCannot continue without required libraries.\033[0m")
            sys.exit(1)

checkAndInstallPackages()

import minecraft_launcher_lib
import requests
import questionary
from questionary import Choice, Style, Separator

white = "\033[97m"
red = "\033[91m"
bold = "\033[1m"
reset = "\033[0m"

launcherStyle = Style([
    ("qmark", "fg:#ff5555 bold"),
    ("question", "fg:#ffffff"),
    ("answer", "fg:#ff5555"),
    ("pointer", "fg:#ff5555 bold"),
    ("highlighted", "fg:#ff5555"),
    ("selected", "fg:#ff5555"),
    ("separator", ""),
    ("instruction", ""),
    ("text", "fg:#ffffff"),
    ("disabled", "fg:#606060"),
])

ADJECTIVES = ["Angry","Brave","Clever","Dark","Epic","Fast","Giant","Happy","Iron","Jungle","King","Lone","Mad","Noble","Old","Pro","Quick","Red","Silent","True","Ultimate","Wild","Young","Crazy","Diamond","Elder","Fire","Golden","Hidden","Icy","Lightning","Magic","Night","Ocean","Phantom","Royal","Shadow","Thunder","Urban","Void","Wicked","Ancient","Blazing","Cosmic","Deadly","Electric","Frozen","Glowing","Heroic","Immortal","Jade","Killer","Legendary","Mystic","Neon","Omega","Powerful","Quest","Raging","Savage","Toxic","Ultra","Vicious","Wise","Pixel","Zombie","Alpha","Beta","Chaos","Demon","Evil","Furious","Ghost","Heavy","Insane","Knight","Laser","Mighty","Neo","Prime","Quantum","Rogue","Super","Tech","Uber","Virus","Warp","Xeno","Yellow","Zeta","Atomic","Bright","Chrome","Disco","Emerald","Flaming","Galactic","Hyper"]
NOUNS = ["Steve","Creeper","Zombie","Skeleton","Enderman","Warrior","Builder","Miner","Hunter","Crafter","Dragon","Ninja","Wizard","Knight","Archer","Slayer","Master","Legend","Hero","Champion","Titan","Ghost","Demon","Angel","Phoenix","Wolf","Bear","Tiger","Eagle","Shark","Viper","Cobra","Falcon","Raven","Panther","Lion","Fox","Hawk","Owl","Spider","Scorpion","Reaper","Samurai","Spartan","Viking","Pirate","Assassin","Sniper","Soldier","Pilot","Raider","Ranger","Scout","Bandit","Outlaw","Rebel","Rogue","Thief","Spy","Agent","Player","Gamer","Killer","Fighter","Striker","Blaster","Bomber","Trooper","Guard","Defender","Crusader","Paladin","Warden","Sentinel","Keeper","Watcher","Seeker","Finder","Runner","Jumper","Rider","Driver","Flyer","Swimmer","Climber","Digger","Breaker","Maker","Creator","Destroyer","Commander","Captain","General","Admiral","Chief","Boss","King","Queen","Prince","Duke"]

def generateRandomUsername():
    return f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(0,999):03d}"

class MinecraftLauncher:
    def __init__(self):
        self.baseDir=Path.home()/".launcher"
        self.minecraftDir=self.baseDir/".minecraft"
        self.configFile=self.baseDir/"config.json"
        self.modsDir=self.baseDir/"mods"
        self.resourcepacksDir=self.baseDir/"resourcepacks"
        self.shaderpacksDir=self.baseDir/"shaderpacks"
        self.loaderSupport={}
        self.cachedVersions=None
        self.setupDirectories()
        self.config=self.loadConfig()

    def setupDirectories(self):
        self.baseDir.mkdir(exist_ok=True)
        self.minecraftDir.mkdir(exist_ok=True)
        for storeDir in(self.modsDir,self.resourcepacksDir,self.shaderpacksDir):
            storeDir.mkdir(exist_ok=True)
            (storeDir/"universal").mkdir(exist_ok=True)
        versionsDir=self.minecraftDir/"versions"
        installedLoaders={}
        if versionsDir.exists():
            for d in versionsDir.iterdir():
                if not d.is_dir()or not(d/f"{d.name}.json").exists():
                    continue
                if"-forge-"in d.name:
                    mc=d.name.split("-forge-")[0]
                    installedLoaders.setdefault(mc,set()).add("forge")
                    continue
                match=re.fullmatch(r"neoforge-(\d+\.\d+).*",d.name)
                if match:
                    g=match.group(1)
                    mc="1.20.1"if g.startswith("47.")else"1."+g.removesuffix(".0")
                    installedLoaders.setdefault(mc,set()).add("neoforge")
                    continue
                if d.name.startswith("fabric-loader-"):
                    mc=d.name.rsplit("-",1)[1]
                    installedLoaders.setdefault(mc,set()).add("fabric")
        for mc,loaders in installedLoaders.items():
            for loader in loaders:
                (self.modsDir/mc/loader).mkdir(parents=True,exist_ok=True)
        for d in list(self.modsDir.iterdir()):
            if not d.is_dir()or d.name=="universal":
                continue
            if"-forge-"in d.name:
                mc=d.name.split("-forge-")[0]
                target=self.modsDir/mc/"forge"
                target.mkdir(parents=True,exist_ok=True)
                for jar in d.glob("*.jar"):
                    if not(target/jar.name).exists():
                        shutil.move(str(jar),str(target/jar.name))
                try:
                    d.rmdir()
                except OSError:
                    pass
                continue
            subDirs=[s for s in d.iterdir()if s.is_dir()]
            if len(subDirs)==1:
                for jar in d.glob("*.jar"):
                    if not(subDirs[0]/jar.name).exists():
                        shutil.move(str(jar),str(subDirs[0]/jar.name))

    def loadConfig(self):
        default={"username":generateRandomUsername(),"selectedVersion":None,"loader":"vanilla","installedVersions":[]}
        if self.configFile.exists():
            try:
                with open(self.configFile,'r')as f:
                    cfg={**default,**json.load(f)}
                if"selected_version"in cfg:
                    cfg["selectedVersion"]=cfg.pop("selected_version")
                if"installed_versions"in cfg:
                    cfg["installedVersions"]=cfg.pop("installed_versions")
                return cfg
            except:
                pass
        self.saveConfigWithData(default)
        return default

    def saveConfig(self):
        with open(self.configFile,'w')as f:
            json.dump(self.config,f,indent=2)

    def saveConfigWithData(self,data):
        with open(self.configFile,'w')as f:
            json.dump(data,f,indent=2)

    def _findJava(self):
        javaHome=os.environ.get("JAVA_HOME")
        if javaHome:
            exe=Path(javaHome)/"bin"/("java.exe"if os.name=='nt'else"java")
            if exe.exists():
                return str(exe)
        javaInPath=shutil.which("java")
        if javaInPath:
            return javaInPath
        runtimeDir=self.minecraftDir/"runtime"
        if runtimeDir.exists():
            exeName="java.exe"if os.name=='nt'else"java"
            for p in sorted(runtimeDir.rglob(exeName)):
                if p.exists()and p.parent.name=="bin":
                    return str(p)
        return None

    def _installJava(self,mcVersion):
        try:
            parts=mcVersion.split('.')
            majorVersion=int(parts[1])
            if len(parts)>2:
                minorVersion=int(parts[2])
            else:
                minorVersion=0
        except(IndexError,ValueError):
            majorVersion=21
            minorVersion=0
        if majorVersion<17:
            javaVersion=8
        elif majorVersion==17 or majorVersion==18 or majorVersion==19:
            javaVersion=17
        elif majorVersion==20:
            if minorVersion<=4:
                javaVersion=17
            else:
                javaVersion=21
        else:
            javaVersion=21
        self._clear()
        self._header()
        print(f" {white}Java not found. Installing Java {javaVersion}..{reset}")
        state={"done":0,"progress":0,"max":0,"total":0,"pct":-1,"lastRender":0.0}
        def render():
            now=time.time()
            if now-state["lastRender"]<0.05:
                return
            state["lastRender"]=now
            total=state["total"]
            if total>0:
                pct=int(min((state["done"]+min(state["progress"],state["max"]))/total,1.0)*100)
            else:
                pct=0
            if pct<state["pct"]:
                pct=state["pct"]
            state["pct"]=pct
            sys.stdout.write("\x1b[2K\r"+f" {white}Installing Java {javaVersion}.. {pct}%{reset}")
            sys.stdout.flush()
        def setStatus(status):
            render()
        def setMax(maximum):
            state["done"]+=state["max"]
            state["total"]+=maximum
            state["max"]=maximum
            state["progress"]=0
            render()
        def setProgress(progress):
            state["progress"]=progress
            render()
        callback={"setStatus":setStatus,"setMax":setMax,"setProgress":setProgress}
        try:
            minecraft_launcher_lib.runtime.install_jvm_runtime(str(javaVersion),str(self.minecraftDir),callback=callback)
            sys.stdout.write("\x1b[2K\r"+f" {white}Installing Java {javaVersion}.. 100%{reset}\n")
            sys.stdout.flush()
            javaPath=self._findJava()
            if javaPath:
                return javaPath
        except Exception as e:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._showMessage(f"Failed to install Java: {e}",red)
        return None

    def _formatVersionName(self,versionId):
        if"-forge-"in versionId:
            mc=versionId.split("-forge-")[0]
            return f"{mc} Forge"
        match=re.fullmatch(r"neoforge-(\d+\.\d+).*",versionId)
        if match:
            g=match.group(1)
            mc="1.20.1"if g.startswith("47.")else"1."+g.removesuffix(".0")
            return f"{mc} Neoforge"
        if versionId.startswith("fabric-loader-"):
            mc=versionId.rsplit("-",1)[1]
            return f"{mc} Fabric"
        return versionId

    def _makeCallback(self,version):
        displayName=self._formatVersionName(version)
        state={"done":0,"progress":0,"max":0,"total":0,"pct":-1,"lastRender":0.0}
        def render():
            now=time.time()
            if now-state["lastRender"]<0.05:
                return
            state["lastRender"]=now
            total=state["total"]
            if total>0:
                pct=int(min((state["done"]+min(state["progress"],state["max"]))/total,1.0)*100)
            else:
                pct=0
            if pct<state["pct"]:
                pct=state["pct"]
            state["pct"]=pct
            sys.stdout.write("\x1b[2K\r"+f" {white}Downloading {displayName}.. {pct}%{reset}")
            sys.stdout.flush()
        def setStatus(status):
            render()
        def setMax(maximum):
            state["done"]+=state["max"]
            state["total"]+=maximum
            state["max"]=maximum
            state["progress"]=0
            render()
        def setProgress(progress):
            state["progress"]=progress
            render()
        def finish():
            state["lastRender"]=0.0
            state["pct"]=100
            sys.stdout.write("\x1b[2K\r"+f" {white}Downloading {displayName}.. 100%{reset}")
            sys.stdout.flush()
        return{"setStatus":setStatus,"setMax":setMax,"setProgress":setProgress,"finish":finish}

    def _finishProgress(self):
        sys.stdout.write("\n")
        sys.stdout.flush()

    def getVersions(self):
        if self.cachedVersions is None:
            versions=minecraft_launcher_lib.utils.get_version_list()
            self.cachedVersions=[v["id"]for v in versions if v["type"]=="release"]
        return self.cachedVersions

    def selectVersion(self):
        self._clear()
        self._header()
        print(f" {white}Loading versions..{reset}")
        allVersions=self.getVersions()
        current=self.config.get("selectedVersion")
        self._clear()
        self._header()
        selected=questionary.autocomplete("Version",choices=allVersions,default=current if current in allVersions else"",style=launcherStyle,qmark="").ask()
        if selected and selected in allVersions:
            self.config["selectedVersion"]=selected
            loader=self.config.get("loader","vanilla")
            if not self.loaderSupports(loader,selected):
                self.config["loader"]="vanilla"
            self.saveConfig()

    def loaderSupports(self,loader,mcVersion):
        if loader=="vanilla":
            return True
        key=(loader,mcVersion)
        if key not in self.loaderSupport:
            try:
                modLoader=minecraft_launcher_lib.mod_loader.get_mod_loader(loader)
                self.loaderSupport[key]=modLoader.is_minecraft_version_supported(mcVersion)
            except Exception:
                self.loaderSupport[key]=False
        return self.loaderSupport[key]

    def selectLoader(self):
        version=self.config.get("selectedVersion")
        loaders=["vanilla"]
        if version:
            loaders+=[l for l in("forge","neoforge","fabric")if self.loaderSupports(l,version)]
        current=self.config.get("loader","vanilla")
        selected=questionary.select("Loader",choices=loaders,default=current if current in loaders else"vanilla",style=launcherStyle,qmark="",instruction="").ask()
        if selected:
            self.config["loader"]=selected
            self.saveConfig()

    def setUsername(self):
        username=questionary.text("Username",default=self.config.get("username","Player"),style=launcherStyle,qmark="",instruction="").ask()
        if username and username.strip():
            self.config["username"]=username.strip()
            self.saveConfig()

    def _folders(self,storeDir):
        return sorted(d.name for d in storeDir.iterdir()if d.is_dir())

    def _searchModrinth(self,query,facets=""):
        try:
            params={"query":query,"limit":20}
            if facets:params["facets"]=facets
            r=requests.get("https://api.modrinth.com/v2/search",params=params,headers={"User-Agent":"MinecraftLauncher/1.0"},timeout=15)
            r.raise_for_status()
            return r.json().get("hits",[])
        except:return[]

    def _getModrinthVersions(self,projectId,mcVersion,loader):
        try:
            params={"game_versions":json.dumps([mcVersion])}
            if loader:params["loaders"]=json.dumps([loader])
            r=requests.get(f"https://api.modrinth.com/v2/project/{projectId}/version",params=params,headers={"User-Agent":"MinecraftLauncher/1.0"},timeout=15)
            r.raise_for_status()
            return r.json()
        except:return[]

    def _downloadModrinthFile(self,url,targetPath):
        try:
            r=requests.get(url,stream=True,headers={"User-Agent":"MinecraftLauncher/1.0"},timeout=60)
            r.raise_for_status()
            with open(targetPath,'wb')as f:
                for chunk in r.iter_content(chunk_size=8192):f.write(chunk)
            return True
        except:return False

    def _findOnlineModrinth(self,itemType,suffix,targetDir):
        self._clear();self._header()
        query=questionary.text(f"Search {itemType}",style=launcherStyle,qmark="",instruction="").ask()
        if not query or not query.strip():return
        facetMap={"Mod":'[["project_type:mod"]]',"Resource Pack":'[["project_type:resourcepack"]]',"Shader Pack":'[["project_type:shader"]]'}
        facets=facetMap.get(itemType,"")
        self._showMessage("Searching..",white,wait=False)
        results=self._searchModrinth(query.strip(),facets)
        if not results:self._showMessage("No results found",red);return
        self._clear();self._header()
        choices=[Choice(title=[("fg:#ffffff",hit.get("title","Unknown"))],value=hit)for hit in results]
        choices.append(Separator());choices.append(Choice("Back",value="__back__"))
        selected=questionary.select("Select",choices=choices,style=launcherStyle,qmark="",instruction="").ask()
        if not selected or selected=="__back__":return
        projectId=selected.get("project_id")
        if not projectId:return
        mcVersion=self.config.get("selectedVersion");loader=self.config.get("loader","vanilla")
        if not mcVersion:self._showMessage("No version selected",red);return
        self._showMessage("Loading versions..",white,wait=False)
        modrinthLoader=None
        if itemType=="Mod"and loader!="vanilla":modrinthLoader=loader
        elif itemType=="Resource Pack":modrinthLoader="minecraft"
        versions=self._getModrinthVersions(projectId,mcVersion,modrinthLoader)
        if not versions:self._showMessage("No compatible versions found",red);return
        version=versions[0];files=version.get("files",[])
        if not files:self._showMessage("No files available",red);return
        primaryFile=next((f for f in files if f.get("primary")),files[0])
        downloadUrl=primaryFile.get("url");fileName=primaryFile.get("filename")
        if not downloadUrl or not fileName:self._showMessage("Invalid file data",red);return
        self._showMessage(f"Downloading {fileName}..",white,wait=False)
        if self._downloadModrinthFile(downloadUrl,targetDir/fileName):self._showMessage(f"+ {fileName}",red)
        else:self._showMessage("Download failed",red)

    def _pickFile(self,title,filetypes):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root=tk.Tk()
            root.withdraw()
            root.attributes("-topmost",True)
            path=filedialog.askopenfilename(title=title,filetypes=filetypes)
            root.destroy()
            if path:return Path(path)
        except:pass
        return None

    def fileMenu(self,storeDir,title,item,suffix,filetypes):
        mcVersion=self.config.get("selectedVersion")
        if mcVersion:(storeDir/mcVersion).mkdir(parents=True,exist_ok=True)
        folders=self._folders(storeDir)
        if not folders:self._showMessage("No folders yet",white);return
        choices=[Choice(title=[("fg:#ffffff",name)],value=name)for name in folders]
        choices.append(Separator());choices.append(Choice("Back",value="__back__"))
        folder=questionary.select(title,choices=choices,style=launcherStyle,qmark="",instruction="").ask()
        if not folder or folder=="__back__":return
        target=storeDir/folder
        while True:
            self._clear();self._header()
            files=sorted(p.name for p in target.glob(f"*{suffix}"))
            print(f" {bold}{white}Advanced Menu {title}{reset}\n")
            if files:
                for f in files:print(f" {white}{f}{reset}")
                print()
            opts=[Choice(title=[("fg:#ff5555",f"+ Add {item}")],value="__add__"),Choice(title=[("fg:#ff5555",f"- Remove {item}")],value="__remove__"),Separator(),Choice("Back",value="__back__")]
            sel=questionary.select("",choices=opts,style=launcherStyle,qmark="",instruction="").ask()
            if sel=="__add__":
                self._clear();self._header()
                importChoices=[Choice("Import from file",value="file"),Choice("Find online",value="online"),Separator(),Choice("Back",value="__back__")]
                importType=questionary.select(f"Add {item}",choices=importChoices,style=launcherStyle,qmark="",instruction="").ask()
                if importType=="file":
                    picked=self._pickFile(f"Select {item}",filetypes)
                    if picked and picked.suffix.lower()==suffix and picked.exists():
                        shutil.copy2(picked,target/picked.name)
                        self._showMessage(f"+ {picked.name}",red)
                elif importType=="online":
                    self._findOnlineModrinth(item,suffix,target)
            elif sel=="__remove__":
                if not files:continue
                toDelete=questionary.select("Remove",choices=files+[Separator(),"Back"],style=launcherStyle,qmark="",instruction="").ask()
                if toDelete and toDelete!="Back":
                    (target/toDelete).unlink(missing_ok=True)
                    self._showMessage(f"- {toDelete}",red)
            elif sel=="__back__"or sel is None:return

    def modsMenu(self):
        mcVersion=self.config.get("selectedVersion")
        if not mcVersion:self._showMessage("No version selected",red);return
        versionDir=self.modsDir/mcVersion
        if not versionDir.exists():self._showMessage(f"No mods folder for {mcVersion}",white);return
        loaders=[d.name for d in versionDir.iterdir()if d.is_dir()]
        if not loaders:self._showMessage(f"No mod loaders installed for {mcVersion}",white);return
        targetDir=None
        if len(loaders)==1:targetDir=versionDir/loaders[0]
        else:
            self._clear();self._header()
            choices=[Choice(title=[("fg:#ffffff",loader)],value=loader)for loader in sorted(loaders)]
            choices.append(Separator());choices.append(Choice("Back",value="__back__"))
            selectedLoader=questionary.select("Mod Loader",choices=choices,style=launcherStyle,qmark="",instruction="").ask()
            if not selectedLoader or selectedLoader=="__back__":return
            targetDir=versionDir/selectedLoader
        while True:
            self._clear();self._header()
            files=sorted(p.name for p in targetDir.glob("*.jar"))
            print(f" {bold}{white}Advanced Menu Mods{reset}\n")
            if files:
                for f in files:print(f" {white}{f}{reset}")
                print()
            opts=[Choice(title=[("fg:#ff5555","+ Add Mod")],value="__add__"),Choice(title=[("fg:#ff5555","- Remove Mod")],value="__remove__"),Separator(),Choice("Back",value="__back__")]
            sel=questionary.select("",choices=opts,style=launcherStyle,qmark="",instruction="").ask()
            if sel=="__add__":
                self._clear();self._header()
                importChoices=[Choice("Import from file",value="file"),Choice("Find online",value="online"),Separator(),Choice("Back",value="__back__")]
                importType=questionary.select("Add Mod",choices=importChoices,style=launcherStyle,qmark="",instruction="").ask()
                if importType=="file":
                    picked=self._pickFile("Select Mod",[("Jar files","*.jar"),("All files","*.*")])
                    if picked and picked.suffix.lower()==".jar"and picked.exists():
                        shutil.copy2(picked,targetDir/picked.name)
                        self._showMessage(f"+ {picked.name}",red)
                elif importType=="online":
                    self._findOnlineModrinth("Mod",".jar",targetDir)
            elif sel=="__remove__":
                if not files:continue
                toDelete=questionary.select("Remove",choices=files+[Separator(),"Back"],style=launcherStyle,qmark="",instruction="").ask()
                if toDelete and toDelete!="Back":
                    (targetDir/toDelete).unlink(missing_ok=True)
                    self._showMessage(f"- {toDelete}",red)
            elif sel=="__back__"or sel is None:return

    def resourcepacksMenu(self):
        self.fileMenu(self.resourcepacksDir,"Resource Packs","Resource Pack",".zip",[("Zip files","*.zip"),("All files","*.*")])

    def shaderpacksMenu(self):
        self.fileMenu(self.shaderpacksDir,"Shader Packs","Shader Pack",".zip",[("Zip files","*.zip"),("All files","*.*")])

    def openScreenshots(self):
        shotsDir=self.minecraftDir/"screenshots"
        shotsDir.mkdir(exist_ok=True)
        try:
            if os.name=='nt':os.startfile(shotsDir)
            elif sys.platform=='darwin':subprocess.Popen(["open",str(shotsDir)])
            else:subprocess.Popen(["xdg-open",str(shotsDir)])
        except Exception as e:
            self._showMessage(f"Error: {e}",red)

    def _organizeDir(self,storeDir,gameSubdir,mcVersion,pattern):
        (storeDir/"universal").mkdir(exist_ok=True)
        (storeDir/mcVersion).mkdir(exist_ok=True)
        gameDir=self.minecraftDir/gameSubdir
        gameDir.mkdir(parents=True,exist_ok=True)
        for existing in gameDir.glob(pattern):existing.unlink(missing_ok=True)
        for name in("universal",mcVersion):
            for f in(storeDir/name).glob(pattern):shutil.copy2(f,gameDir/f.name)

    def organizeMods(self,mcVersion,loader):
        gameDir=self.minecraftDir/"mods"
        gameDir.mkdir(parents=True,exist_ok=True)
        for existing in gameDir.glob("*.jar"):existing.unlink(missing_ok=True)
        universalDir=self.modsDir/"universal"
        if universalDir.exists():
            for f in universalDir.glob("*.jar"):shutil.copy2(f,gameDir/f.name)
        versionLoaderDir=self.modsDir/mcVersion/loader
        if versionLoaderDir.exists():
            for f in versionLoaderDir.glob("*.jar"):shutil.copy2(f,gameDir/f.name)

    def resolveInstalledVersion(self,version,loader):
        versionsDir=self.minecraftDir/"versions"
        if not versionsDir.exists():return None
        if loader=="forge":
            for d in versionsDir.iterdir():
                if not(d.is_dir()and d.name.startswith(f"{version}-forge")):continue
                if not(d/f"{d.name}.json").exists():continue
                if self.forgeIsComplete(version,d.name):return d.name
                return None
            return None
        if loader=="neoforge":
            shortVersion=version.removeprefix("1.")
            for d in versionsDir.iterdir():
                if not d.is_dir()or not(d/f"{d.name}.json").exists():continue
                match=re.fullmatch(r"neoforge-(\d+\.\d+).*",d.name)
                if match and match.group(1).removesuffix(".0")==shortVersion.removesuffix(".0"):return d.name
            return None
        if loader=="fabric":
            for d in versionsDir.iterdir():
                if not d.is_dir()or not(d/f"{d.name}.json").exists():continue
                if d.name.startswith("fabric-loader-")and d.name.endswith(f"-{version}"):return d.name
            return None
        if(versionsDir/version/f"{version}.json").exists():return version
        return None

    def forgeIsComplete(self,mcVersion,installedId):
        try:minor=int(mcVersion.split(".")[1])
        except(IndexError,ValueError):minor=0
        isNewForge=minor>=13
        forgeLibs=self.minecraftDir/"libraries"/"net"/"minecraftforge"/"forge"
        if not forgeLibs.exists():return False
        for d in forgeLibs.iterdir():
            if not(d.is_dir()and d.name.startswith(f"{mcVersion}-")):continue
            if not isNewForge:return any(d.glob("*.jar"))
            if not any(d.glob("*-client.jar")):return False
            clientDir=self.minecraftDir/"libraries"/"net"/"minecraft"/"client"
            if not clientDir.exists():return False
            for cd in clientDir.iterdir():
                if cd.is_dir()and cd.name.startswith(f"{mcVersion}-")and any(cd.glob("*-srg.jar"))and any(cd.glob("*-extra.jar")):return True
            return False
        return False

    def installVersion(self,version,loader):
        javaPath=self._findJava()
        if not javaPath:
            javaPath=self._installJava(version)
            if not javaPath:
                raise RuntimeError("Failed to find or install Java")
        callback=self._makeCallback(version)
        if loader!="vanilla":
            modLoader=minecraft_launcher_lib.mod_loader.get_mod_loader(loader)
            if not modLoader.is_minecraft_version_supported(version):raise RuntimeError(f"{loader.capitalize()} is not available for {version}")
            loaderVersion=modLoader.get_latest_loader_version(version)
            installedId=self._loaderInstallWithRetry(modLoader,version,loaderVersion,callback,javaPath)
            callback["finish"]()
            self._finishProgress()
            (self.modsDir/version/loader).mkdir(parents=True,exist_ok=True)
            return installedId
        self._installWithRetry(version,callback)
        callback["finish"]()
        self._finishProgress()
        return version

    def _loaderInstallWithRetry(self,modLoader,version,loaderVersion,callback,javaPath,attempts=3):
        lastErr=None
        for attempt in range(1,attempts+1):
            try:return modLoader.install(version,str(self.minecraftDir),loader_version=loaderVersion,callback=callback,java=javaPath)
            except(requests.exceptions.ConnectionError,requests.exceptions.Timeout,ConnectionError)as e:
                lastErr=e
                if attempt<attempts:time.sleep(attempt*3)
        raise lastErr

    def _installWithRetry(self,version,callback,attempts=3):
        lastErr=None
        for attempt in range(1,attempts+1):
            try:
                minecraft_launcher_lib.install.install_minecraft_version(version,str(self.minecraftDir),callback=callback)
                return
            except(requests.exceptions.ConnectionError,requests.exceptions.Timeout,ConnectionError)as e:
                lastErr=e
                if attempt<attempts:time.sleep(attempt*3)
        raise lastErr

    def launchGame(self):
        self._clear()
        version=self.config.get("selectedVersion");loader=self.config.get("loader","vanilla");username=self.config.get("username","Player")
        if not version:self._showMessage("No version selected",red);return
        try:
            javaPath=self._findJava()
            if not javaPath:
                javaPath=self._installJava(version)
                if not javaPath:
                    self._showMessage("Failed to find or install Java",red)
                    return
            installed=self.config.get("installedVersions",[])
            versionId=self.resolveInstalledVersion(version,loader)
            if not versionId:
                versionId=self.installVersion(version,loader)
                if versionId and versionId not in installed:
                    installed.append(versionId)
                    self.config["installedVersions"]=installed
                    self.saveConfig()
            if loader!="vanilla":self.organizeMods(version,loader)
            self._organizeDir(self.resourcepacksDir,"resourcepacks",version,"*.zip")
            self._organizeDir(self.shaderpacksDir,"shaderpacks",version,"*.zip")
            options={"username":username,"uuid":"","token":"","gameDirectory":str(self.minecraftDir),"jvmArguments":["-Xmx2G","-Xms1G"],"executablePath":javaPath}
            command=minecraft_launcher_lib.command.get_minecraft_command(versionId,str(self.minecraftDir),options)
            displayName=self._formatVersionName(versionId)
            self._showMessage(f"Launching {displayName}",white,wait=False)
            subprocess.run(command,cwd=str(self.minecraftDir),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except KeyboardInterrupt:return
        except Exception as e:
            self._finishProgress()
            self._showMessage(f"Error: {e}",red)

    def _clear(self):
        os.system('cls'if os.name=='nt'else'clear')

    def _header(self):
        statusVersion=self.config.get("selectedVersion","none")
        statusLoader=self.config.get("loader","vanilla").capitalize()
        statusUser=self.config.get("username","Player")
        print(f"\n {bold}{white}Flint Launcher{reset}")
        print(f" {red}{statusUser}{white}, {statusVersion} {white}{statusLoader}{reset}\n")

    def _showMessage(self,message,color=white,wait=True):
        self._clear()
        self._header()
        print(f" {color}{message}{reset}")
        if wait:input()

    def advancedMenu(self):
        while True:
            self._clear();self._header()
            selected=questionary.select("Advanced Menu",choices=["Username","Mods","Resource Packs","Shader Packs","Screenshots",Separator(),"Back"],style=launcherStyle,qmark="",instruction="").ask()
            if selected=="Username":self.setUsername()
            elif selected=="Mods":self.modsMenu()
            elif selected=="Resource Packs":self.resourcepacksMenu()
            elif selected=="Shader Packs":self.shaderpacksMenu()
            elif selected=="Screenshots":self.openScreenshots()
            else:return

    def mainMenu(self):
        while True:
            self._clear();self._header()
            selected=questionary.select("Menu",choices=["Launch","Version","Loader",Separator(),"Advanced"],style=launcherStyle,qmark="",instruction="").ask()
            if selected=="Launch":self.launchGame()
            elif selected=="Version":self.selectVersion()
            elif selected=="Loader":self.selectLoader()
            elif selected=="Advanced":self.advancedMenu()
            else:sys.exit(0)

    def run(self):
        try:self.mainMenu()
        except KeyboardInterrupt:sys.exit(0)

if __name__=="__main__":
    MinecraftLauncher().run()
