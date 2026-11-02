import os,re,sys,json,time,random,subprocess,shutil,warnings
from pathlib import Path
warnings.filterwarnings("ignore",category=DeprecationWarning)

if os.name=='nt':
    os.system("")
    import asyncio,ctypes
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:ctypes.windll.kernel32.AllocConsole()
    except:pass
    sys.stdout,sys.stdin,sys.stderr=sys.__stdout__,sys.__stdin__,sys.__stderr__

white,red,bold,reset="\033[97m","\033[91m","\033[1m","\033[0m"
requiredPackages={"minecraft_launcher_lib":"minecraft-launcher-lib","requests":"requests","questionary":"questionary"}

def checkAndInstallPackages():
    import importlib.util
    missing=[pkg for mod,pkg in requiredPackages.items()if not importlib.util.find_spec(mod)]
    if missing:
        print(f"{white}Missing libraries:{reset}");[print(f"  - {p}")for p in missing];print()
        if input(f"{white}Auto-install? (y/n): {reset}").strip().lower()=='y':
            [print(f"{white}Installing {p}..{reset}")or subprocess.check_call([sys.executable,"-m","pip","install",p])for p in missing]
            print(f"{red}Installed successfully!{reset}\n")
        else:print(f"{red}Cannot continue without required libraries.{reset}");sys.exit(1)

checkAndInstallPackages()

import minecraft_launcher_lib,requests,questionary
from questionary import Choice,Style,Separator

accent,plain="fg:#ff5555","fg:#ffffff"
launcherStyle=Style([("qmark",accent+" bold"),("question",plain),("answer",accent),("pointer",accent+" bold"),("highlighted",accent),("selected",accent),("separator",""),("instruction",""),("text",plain),("disabled","fg:#606060")])
askOpts=dict(style=launcherStyle,qmark="",instruction="")
headers={"User-Agent":"MinecraftLauncher/1.0"}

translations={k:(en,ru)for k,en,ru in(l.split("|")for l in"""
menu|Menu|Меню
launch|Launch|Запуск
version|Version|Версия
loader|Loader|Загрузчик
settings|Settings|Настройки
advanced|Advanced|Дополнительно
back|Back|Назад
username|Username|Имя игрока
mods|Mods|Моды
resourcePacks|Resource Packs|Ресурспаки
shaderPacks|Shader Packs|Шейдерпаки
screenshots|Screenshots|Скриншоты
language|Language|Язык
ramUsage|RAM Usage|Использование ОЗУ
advancedMenu|Advanced Menu|Доп. меню
loadingVersions|Loading versions..|Загрузка версий..
noVersionSelected|No version selected|Версия не выбрана
noModsFolder|No mods folder for|Нет папки модов для
noLoadersInstalled|No mod loaders installed for|Загрузчики не установлены для
modLoader|Mod Loader|Загрузчик модов
searchMod|Search Mod|Поиск мода
searchResourcePack|Search Resource Pack|Поиск ресурспака
searchShaderPack|Search Shader Pack|Поиск шейдерпака
searching|Searching..|Поиск..
noResults|No results found|Ничего не найдено
select|Select|Выбрать
noCompatibleVersions|No compatible versions found|Совместимых версий не найдено
noFilesAvailable|No files available|Файлы недоступны
invalidFileData|Invalid file data|Неверные данные файла
downloading|Downloading|Загрузка
downloadFailed|Download failed|Загрузка не удалась
addMod|Add Mod|Добавить мод
addResourcePack|Add Resource Pack|Добавить ресурспак
addShaderPack|Add Shader Pack|Добавить шейдерпак
removeMod|Remove Mod|Удалить мод
removeResourcePack|Remove Resource Pack|Удалить ресурспак
removeShaderPack|Remove Shader Pack|Удалить шейдерпак
importFromFile|Import from file|Импорт из файла
findOnline|Find online|Найти онлайн
selectMod|Select Mod|Выбрать мод
selectResourcePack|Select Resource Pack|Выбрать ресурспак
selectShaderPack|Select Shader Pack|Выбрать шейдерпак
remove|Remove|Удалить
javaNotFound|Java not found. Installing Java|Java не найдена. Установка Java
installingJava|Installing Java|Установка Java
launching|Launching|Запуск
error|Error|Ошибка
""".strip().splitlines())}

ITEMS={"Mod":("mods","mod",".jar"),"ResourcePack":("resourcePacks","resourcepack",".zip"),"ShaderPack":("shaderPacks","shader",".zip")}
SETTINGS={"language":("language",["English","Русский"]),"ramUsage":("ramAllocation",["1G","2G","4G","8G","16G"])}

adjectives="Angry Brave Clever Dark Epic Fast Giant Happy Iron King Lone Mad Noble Old Pro Quick Red Silent True Wild Young Crazy Elder Fire Golden Hidden Icy Magic Night Ocean Royal Shadow Thunder Void Ancient Cosmic Deadly Frozen Heroic Jade Legendary Mystic Neon Omega Raging Savage Toxic Ultra Wise Alpha Chaos".split()
nouns="Steve Creeper Zombie Skeleton Enderman Warrior Builder Miner Hunter Dragon Ninja Wizard Knight Archer Master Legend Hero Titan Ghost Demon Phoenix Wolf Bear Tiger Eagle Viper Falcon Raven Lion Fox Hawk Spider Reaper Samurai Viking Pirate Sniper Soldier Raider Ranger Scout Bandit Rogue Thief Agent Player Gamer Fighter Striker".split()
generateRandomUsername=lambda:f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(0,9999):04d}"

def loaderOf(name):
    if"-forge-"in name:return name.split("-forge-")[0],"forge"
    if m:=re.fullmatch(r"neoforge-(\d+\.\d+).*",name):return("1.20.1"if m[1].startswith("47.")else"1."+m[1].removesuffix(".0")),"neoforge"
    if name.startswith("fabric-loader-"):return name.rsplit("-",1)[1],"fabric"

def moveJars(src,dst):
    for jar in src.glob("*.jar"):
        if not(dst/jar.name).exists():shutil.move(str(jar),str(dst/jar.name))

def modrinth(path,**params):
    try:r=requests.get("https://api.modrinth.com/v2/"+path,params=params,headers=headers,timeout=15);r.raise_for_status();return r.json()
    except:return None

def download(url,target):
    try:
        with requests.get(url,stream=True,headers=headers,timeout=60)as r:
            r.raise_for_status()
            with open(target,'wb')as f:
                for chunk in r.iter_content(chunk_size=8192):f.write(chunk)
        return True
    except:return False

class MinecraftLauncher:
    def __init__(self):
        base=Path.home()/".launcher"
        self.baseDir,self.minecraftDir,self.configFile=base,base/".minecraft",base/"config.json"
        self.modsDir,self.resourcepacksDir,self.shaderpacksDir=base/"mods",base/"resourcepacks",base/"shaderpacks"
        self.loaderSupport,self.cachedVersions={},None
        self.setupDirectories();self.config=self.loadConfig()

    def t(self,key):return translations[key][self.config["language"]=="Русский"]if key in translations else key

    def setupDirectories(self):
        self.baseDir.mkdir(exist_ok=True);self.minecraftDir.mkdir(exist_ok=True)
        for d in(self.modsDir,self.resourcepacksDir,self.shaderpacksDir):d.mkdir(exist_ok=True);(d/"universal").mkdir(exist_ok=True)
        if(versionsDir:=self.minecraftDir/"versions").exists():
            for d in versionsDir.iterdir():
                if d.is_dir()and(d/f"{d.name}.json").exists()and(info:=loaderOf(d.name)):(self.modsDir/info[0]/info[1]).mkdir(parents=True,exist_ok=True)
        for d in list(self.modsDir.iterdir()):
            if not d.is_dir()or d.name=="universal":continue
            if"-forge-"in d.name:
                target=self.modsDir/d.name.split("-forge-")[0]/"forge";target.mkdir(parents=True,exist_ok=True);moveJars(d,target)
                try:d.rmdir()
                except OSError:pass
            elif len(subDirs:=[s for s in d.iterdir()if s.is_dir()])==1:moveJars(d,subDirs[0])

    def loadConfig(self):
        default={"username":generateRandomUsername(),"selectedVersion":None,"loader":"vanilla","installedVersions":[],"language":"English","ramAllocation":"2G"}
        try:
            cfg={**default,**json.loads(self.configFile.read_text())}
            for new,old in(("selectedVersion","selected_version"),("installedVersions","installed_versions")):
                if old in cfg:cfg[new]=cfg.pop(old)
            return cfg
        except:self.configFile.write_text(json.dumps(default,indent=2));return default

    def saveConfig(self):self.configFile.write_text(json.dumps(self.config,indent=2))

    def _findJava(self):
        exeName="java.exe"if os.name=='nt'else"java"
        if javaHome:=os.environ.get("JAVA_HOME"):
            if(exe:=Path(javaHome)/"bin"/exeName).exists():return str(exe)
        if javaInPath:=shutil.which("java"):return javaInPath
        if(runtimeDir:=self.minecraftDir/"runtime").exists():
            for p in sorted(runtimeDir.rglob(exeName)):
                if p.exists()and p.parent.name=="bin":return str(p)

    def _installJava(self,mcVersion):
        try:parts=mcVersion.split('.');major,minor=int(parts[1]),int(parts[2])if len(parts)>2 else 0
        except:major,minor=21,0
        javaVersion=8 if major<17 else 17 if major<=19 or(major==20 and minor<=4)else 21
        self._showMessage(f"{self.t('javaNotFound')} {javaVersion}..",white,wait=False)
        callback=self._makeCallback(f"{self.t('installingJava')} {javaVersion}")
        try:
            minecraft_launcher_lib.runtime.install_jvm_runtime(str(javaVersion),str(self.minecraftDir),callback=callback)
            callback["finish"]();print()
            if javaPath:=self._findJava():return javaPath
        except Exception as e:print();self._showMessage(f"{self.t('error')}: {e}",red)

    def _makeCallback(self,label):
        done=current=top=total=pct=last=0
        def draw(final=False):
            nonlocal pct
            pct=100 if final else max(pct,int(min((done+min(current,top))/total,1.0)*100)if total else 0)
            sys.stdout.write(f"\x1b[2K\r {white}{label}.. {pct}%{reset}");sys.stdout.flush()
        def render(*_):
            nonlocal last
            if(now:=time.time())-last>=0.05:last=now;draw()
        def setMax(maximum):
            nonlocal done,total,top,current
            done+=top;total+=maximum;top,current=maximum,0;render()
        def setProgress(progress):
            nonlocal current
            current=progress;render()
        return{"setStatus":render,"setMax":setMax,"setProgress":setProgress,"finish":lambda:draw(True)}

    def _retry(self,func,attempts=3):
        for attempt in range(1,attempts+1):
            try:return func()
            except(requests.ConnectionError,requests.Timeout,ConnectionError):
                if attempt==attempts:raise
                time.sleep(attempt*3)

    def _formatVersionName(self,versionId):
        info=loaderOf(versionId);return f"{info[0]} {info[1].capitalize()}"if info else versionId

    def getVersions(self):
        if self.cachedVersions is None:self.cachedVersions=[v["id"]for v in minecraft_launcher_lib.utils.get_version_list()if v["type"]=="release"]
        return self.cachedVersions

    def ask(self,title,choices,back=False,**kw):
        if back:choices=[*choices,Separator(),Choice(self.t("back"),value=False)]
        return questionary.select(title,choices=choices,**askOpts,**kw).ask()

    def menu(self,title,items,back=False):
        return self.ask(self.t(title),[Separator()if i is None else Choice(self.t(i[0]),value=i[1])for i in items],back)

    def selectVersion(self):
        self._showMessage(self.t("loadingVersions"),white,wait=False)
        allVersions,current=self.getVersions(),self.config["selectedVersion"]
        self._screen()
        if(selected:=questionary.autocomplete(self.t("version"),choices=allVersions,default=current if current in allVersions else"",style=launcherStyle,qmark="").ask())and selected in allVersions:
            self.config["selectedVersion"]=selected
            if not self.loaderSupports(self.config["loader"],selected):self.config["loader"]="vanilla"
            self.saveConfig()

    def loaderSupports(self,loader,mcVersion):
        if loader=="vanilla":return True
        if(key:=(loader,mcVersion))not in self.loaderSupport:
            try:self.loaderSupport[key]=minecraft_launcher_lib.mod_loader.get_mod_loader(loader).is_minecraft_version_supported(mcVersion)
            except:self.loaderSupport[key]=False
        return self.loaderSupport[key]

    def selectLoader(self):
        version,current=self.config["selectedVersion"],self.config["loader"]
        loaders=["vanilla"]+([l for l in("forge","neoforge","fabric")if self.loaderSupports(l,version)]if version else[])
        if selected:=self.ask(self.t("loader"),loaders,default=current if current in loaders else"vanilla"):
            self.config["loader"]=selected;self.saveConfig()

    def setUsername(self):
        if(username:=questionary.text(self.t("username"),default=self.config["username"],**askOpts).ask())and username.strip():
            self.config["username"]=username.strip();self.saveConfig()

    def settingsMenu(self):
        while True:
            self._screen()
            if not(key:=self.menu("settings",[(k,k)for k in SETTINGS],True)):return
            cfgKey,options=SETTINGS[key]
            if value:=self.ask(self.t(key),options,default=self.config[cfgKey]):self.config[cfgKey]=value;self.saveConfig()

    def _findOnline(self,item,target):
        _,projectType,_=ITEMS[item]
        self._screen()
        query=questionary.text(self.t(f"search{item}"),**askOpts).ask()
        if not query or not query.strip():return
        self._showMessage(self.t("searching"),white,wait=False)
        hits=(modrinth("search",query=query.strip(),limit=20,facets=f'[["project_type:{projectType}"]]')or{}).get("hits",[])
        if not hits:self._showMessage(self.t("noResults"),red);return
        self._screen()
        selected=self.ask(self.t("select"),[Choice(hit.get("title","Unknown"),value=hit)for hit in hits],True)
        if not selected or not(projectId:=selected.get("project_id")):return
        mcVersion,loader=self.config["selectedVersion"],self.config["loader"]
        if not mcVersion:self._showMessage(self.t("noVersionSelected"),red);return
        self._showMessage(self.t("loadingVersions"),white,wait=False)
        modrinthLoader="minecraft"if item=="ResourcePack"else loader if item=="Mod"and loader!="vanilla"else None
        versions=modrinth(f"project/{projectId}/version",game_versions=json.dumps([mcVersion]),loaders=json.dumps([modrinthLoader])if modrinthLoader else None)
        if not versions:self._showMessage(self.t("noCompatibleVersions"),red);return
        if not(files:=versions[0].get("files",[])):self._showMessage(self.t("noFilesAvailable"),red);return
        primary=next((f for f in files if f.get("primary")),files[0])
        url,fileName=primary.get("url"),primary.get("filename")
        if not url or not fileName:self._showMessage(self.t("invalidFileData"),red);return
        self._showMessage(f"{self.t('downloading')} {fileName}..",white,wait=False)
        self._showMessage(f"+ {fileName}"if download(url,target/fileName)else self.t("downloadFailed"),red)

    def _pickFile(self,title,filetypes):
        try:
            import tkinter as tk;from tkinter import filedialog
            root=tk.Tk();root.withdraw();root.attributes("-topmost",True)
            path=filedialog.askopenfilename(title=title,filetypes=filetypes);root.destroy()
            return Path(path)if path else None
        except:return None

    def _filesMenu(self,item,target):
        title,_,suffix=ITEMS[item]
        while True:
            self._screen()
            files=sorted(p.name for p in target.glob(f"*{suffix}"))
            print(f" {bold}{white}{self.t('advancedMenu')} {self.t(title)}{reset}\n")
            if files:print("\n".join(f" {white}{f}{reset}"for f in files)+"\n")
            sel=self.ask("",[Choice([(accent,self.t(f"add{item}"))],value="add"),Choice([(accent,self.t(f"remove{item}"))],value="remove"),Separator(),Choice(self.t("back"),value=False)])
            if sel=="add":
                self._screen()
                source=self.ask(self.t(f"add{item}"),[Choice(self.t("importFromFile"),value="file"),Choice(self.t("findOnline"),value="online")],True)
                if source=="file":
                    picked=self._pickFile(self.t(f"select{item}"),[(f"{suffix[1:].capitalize()} files",f"*{suffix}"),("All files","*.*")])
                    if picked and picked.suffix.lower()==suffix and picked.exists():
                        shutil.copy2(picked,target/picked.name);self._showMessage(f"+ {picked.name}",red)
                elif source=="online":self._findOnline(item,target)
            elif sel=="remove":
                if files and(toDelete:=self.ask(self.t("remove"),files,True)):
                    (target/toDelete).unlink(missing_ok=True);self._showMessage(f"- {toDelete}",red)
            else:return

    def packsMenu(self,item,storeDir):
        if mcVersion:=self.config["selectedVersion"]:(storeDir/mcVersion).mkdir(parents=True,exist_ok=True)
        if folder:=self.ask(self.t(ITEMS[item][0]),sorted(d.name for d in storeDir.iterdir()if d.is_dir()),True):self._filesMenu(item,storeDir/folder)

    def modsMenu(self):
        if not(mcVersion:=self.config["selectedVersion"]):self._showMessage(self.t("noVersionSelected"),red);return
        if not(versionDir:=self.modsDir/mcVersion).exists():self._showMessage(f"{self.t('noModsFolder')} {mcVersion}",white);return
        if not(loaders:=sorted(d.name for d in versionDir.iterdir()if d.is_dir())):self._showMessage(f"{self.t('noLoadersInstalled')} {mcVersion}",white);return
        if len(loaders)>1:
            self._screen()
            if not(loader:=self.ask(self.t("modLoader"),loaders,True)):return
        else:loader=loaders[0]
        self._filesMenu("Mod",versionDir/loader)

    def openScreenshots(self):
        (shotsDir:=self.minecraftDir/"screenshots").mkdir(exist_ok=True)
        try:
            if os.name=='nt':os.startfile(shotsDir)
            else:subprocess.Popen(["open"if sys.platform=='darwin'else"xdg-open",str(shotsDir)])
        except Exception as e:self._showMessage(f"{self.t('error')}: {e}",red)

    def _syncToGame(self,sources,gameSubdir,pattern):
        (gameDir:=self.minecraftDir/gameSubdir).mkdir(parents=True,exist_ok=True)
        for f in gameDir.glob(pattern):f.unlink(missing_ok=True)
        for source in sources:
            for f in source.glob(pattern):shutil.copy2(f,gameDir/f.name)

    def resolveInstalledVersion(self,version,loader):
        if loader=="vanilla":return version if(self.minecraftDir/"versions"/version/f"{version}.json").exists()else None
        for d in(self.minecraftDir/"versions").glob("*"):
            if(d/f"{d.name}.json").exists()and loaderOf(d.name)==(version,loader):
                return d.name if loader!="forge"or self.forgeIsComplete(version)else None

    def forgeIsComplete(self,mcVersion):
        try:minor=int(mcVersion.split(".")[1])
        except:minor=0
        if not(forgeLibs:=self.minecraftDir/"libraries"/"net"/"minecraftforge"/"forge").exists():return False
        for d in forgeLibs.iterdir():
            if not(d.is_dir()and d.name.startswith(f"{mcVersion}-")):continue
            if minor<13:return any(d.glob("*.jar"))
            if not any(d.glob("*-client.jar"))or not(clientDir:=self.minecraftDir/"libraries"/"net"/"minecraft"/"client").exists():return False
            return any(cd.is_dir()and cd.name.startswith(f"{mcVersion}-")and any(cd.glob("*-srg.jar"))and any(cd.glob("*-extra.jar"))for cd in clientDir.iterdir())
        return False

    def installVersion(self,version,loader,javaPath):
        callback,gameDir=self._makeCallback(f"{self.t('downloading')} {version}"),str(self.minecraftDir)
        if loader=="vanilla":
            self._retry(lambda:minecraft_launcher_lib.install.install_minecraft_version(version,gameDir,callback=callback));installedId=version
        else:
            if not(modLoader:=minecraft_launcher_lib.mod_loader.get_mod_loader(loader)).is_minecraft_version_supported(version):raise RuntimeError(f"{loader.capitalize()} is not available for {version}")
            installedId=self._retry(lambda:modLoader.install(version,gameDir,loader_version=modLoader.get_latest_loader_version(version),callback=callback,java=javaPath))
            (self.modsDir/version/loader).mkdir(parents=True,exist_ok=True)
        callback["finish"]();print()
        return installedId

    def launchGame(self):
        self._clear()
        version,loader,installed=self.config["selectedVersion"],self.config["loader"],self.config["installedVersions"]
        if not version:self._showMessage(self.t("noVersionSelected"),red);return
        try:
            if not(javaPath:=self._findJava()or self._installJava(version)):self._showMessage(f"{self.t('error')}: Java",red);return
            if not(versionId:=self.resolveInstalledVersion(version,loader)):
                versionId=self.installVersion(version,loader,javaPath)
                if versionId and versionId not in installed:installed.append(versionId);self.saveConfig()
            if loader!="vanilla":self._syncToGame([self.modsDir/"universal",self.modsDir/version/loader],"mods","*.jar")
            for storeDir,gameSubdir in((self.resourcepacksDir,"resourcepacks"),(self.shaderpacksDir,"shaderpacks")):
                (storeDir/version).mkdir(exist_ok=True);self._syncToGame([storeDir/"universal",storeDir/version],gameSubdir,"*.zip")
            ram=self.config["ramAllocation"]
            options={"username":self.config["username"],"uuid":"","token":"","gameDirectory":str(self.minecraftDir),"jvmArguments":[f"-Xmx{ram}",f"-Xms{ram}"],"executablePath":javaPath}
            command=minecraft_launcher_lib.command.get_minecraft_command(versionId,str(self.minecraftDir),options)
            self._showMessage(f"{self.t('launching')} {self._formatVersionName(versionId)}",white,wait=False)
            subprocess.run(command,cwd=str(self.minecraftDir),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except KeyboardInterrupt:return
        except Exception as e:print();self._showMessage(f"{self.t('error')}: {e}",red)

    def _clear(self):os.system('cls'if os.name=='nt'else'clear')
    def _header(self):c=self.config;print(f"\n {bold}{white}Flint Launcher{reset}\n {red}{c['username']}{white}, {c['selectedVersion']} {white}{c['loader'].capitalize()}{reset}\n")
    def _screen(self):self._clear();self._header()
    def _showMessage(self,message,color=white,wait=True):self._screen();print(f" {color}{message}{reset}");wait and input()

    def advancedMenu(self):
        items=[("username",self.setUsername),("mods",self.modsMenu),("resourcePacks",lambda:self.packsMenu("ResourcePack",self.resourcepacksDir)),("shaderPacks",lambda:self.packsMenu("ShaderPack",self.shaderpacksDir)),None,("screenshots",self.openScreenshots)]
        while True:
            self._screen()
            if not(action:=self.menu("advancedMenu",items,True)):return
            action()

    def mainMenu(self):
        items=[("launch",self.launchGame),("version",self.selectVersion),("loader",self.selectLoader),None,("settings",self.settingsMenu),("advanced",self.advancedMenu)]
        while True:
            self._screen()
            (self.menu("menu",items)or sys.exit)()

    def run(self):
        try:self.mainMenu()
        except KeyboardInterrupt:sys.exit(0)

if __name__=="__main__":
    MinecraftLauncher().run()
