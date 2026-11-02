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

requiredPackages={"minecraft_launcher_lib":"minecraft-launcher-lib","requests":"requests","questionary":"questionary"}

def checkAndInstallPackages():
    import importlib.util
    missing=[pkg for mod,pkg in requiredPackages.items()if not importlib.util.find_spec(mod)]
    if missing:
        print("\033[97mMissing libraries:\033[0m");[print(f"  - {p}")for p in missing];print()
        if input("\033[97mAuto-install? (y/n): \033[0m").strip().lower()=='y':
            [print(f"\033[97mInstalling {p}..\033[0m")or subprocess.check_call([sys.executable,"-m","pip","install",p])for p in missing]
            print("\033[91mInstalled successfully!\033[0m\n")
        else:print("\033[91mCannot continue without required libraries.\033[0m");sys.exit(1)

checkAndInstallPackages()

import minecraft_launcher_lib,requests,questionary
from questionary import Choice,Style,Separator

white,red,bold,reset="\033[97m","\033[91m","\033[1m","\033[0m"
launcherStyle=Style([("qmark","fg:#ff5555 bold"),("question","fg:#ffffff"),("answer","fg:#ff5555"),("pointer","fg:#ff5555 bold"),("highlighted","fg:#ff5555"),("selected","fg:#ff5555"),("separator",""),("instruction",""),("text","fg:#ffffff"),("disabled","fg:#606060")])
translations={"English":{"menu":"Menu","launch":"Launch","version":"Version","loader":"Loader","settings":"Settings","advanced":"Advanced","back":"Back","username":"Username","mods":"Mods","resourcePacks":"Resource Packs","shaderPacks":"Shader Packs","screenshots":"Screenshots","language":"Language","ramUsage":"RAM Usage","advancedMenu":"Advanced Menu","loadingVersions":"Loading versions..","noVersionSelected":"No version selected","noModsFolder":"No mods folder for","noLoadersInstalled":"No mod loaders installed for","modLoader":"Mod Loader","searchMod":"Search Mod","searchResourcePack":"Search Resource Pack","searchShaderPack":"Search Shader Pack","searching":"Searching..","noResults":"No results found","select":"Select","loadingVersionsMsg":"Loading versions..","noCompatibleVersions":"No compatible versions found","noFilesAvailable":"No files available","invalidFileData":"Invalid file data","downloading":"Downloading","downloadFailed":"Download failed","addMod":"Add Mod","addResourcePack":"Add Resource Pack","addShaderPack":"Add Shader Pack","removeMod":"Remove Mod","removeResourcePack":"Remove Resource Pack","removeShaderPack":"Remove Shader Pack","importFromFile":"Import from file","findOnline":"Find online","selectMod":"Select Mod","selectResourcePack":"Select Resource Pack","selectShaderPack":"Select Shader Pack","remove":"Remove","javaNotFound":"Java not found. Installing Java","installingJava":"Installing Java","launching":"Launching","error":"Error"},"Русский":{"menu":"Меню","launch":"Запуск","version":"Версия","loader":"Загрузчик","settings":"Настройки","advanced":"Дополнительно","back":"Назад","username":"Имя игрока","mods":"Моды","resourcePacks":"Ресурспаки","shaderPacks":"Шейдерпаки","screenshots":"Скриншоты","language":"Язык","ramUsage":"Использование ОЗУ","advancedMenu":"Доп. меню","loadingVersions":"Загрузка версий..","noVersionSelected":"Версия не выбрана","noModsFolder":"Нет папки модов для","noLoadersInstalled":"Загрузчики не установлены для","modLoader":"Загрузчик модов","searchMod":"Поиск мода","searchResourcePack":"Поиск ресурспака","searchShaderPack":"Поиск шейдерпака","searching":"Поиск..","noResults":"Ничего не найдено","select":"Выбрать","loadingVersionsMsg":"Загрузка версий..","noCompatibleVersions":"Совместимых версий не найдено","noFilesAvailable":"Файлы недоступны","invalidFileData":"Неверные данные файла","downloading":"Загрузка","downloadFailed":"Загрузка не удалась","addMod":"Добавить мод","addResourcePack":"Добавить ресурспак","addShaderPack":"Добавить шейдерпак","removeMod":"Удалить мод","removeResourcePack":"Удалить ресурспак","removeShaderPack":"Удалить шейдерпак","importFromFile":"Импорт из файла","findOnline":"Найти онлайн","selectMod":"Выбрать мод","selectResourcePack":"Выбрать ресурспак","selectShaderPack":"Выбрать шейдерпак","remove":"Удалить","javaNotFound":"Java не найдена. Установка Java","installingJava":"Установка Java","launching":"Запуск","error":"Ошибка"}}
adjectives=["Angry","Brave","Clever","Dark","Epic","Fast","Giant","Happy","Iron","King","Lone","Mad","Noble","Old","Pro","Quick","Red","Silent","True","Wild","Young","Crazy","Elder","Fire","Golden","Hidden","Icy","Magic","Night","Ocean","Royal","Shadow","Thunder","Void","Ancient","Cosmic","Deadly","Frozen","Heroic","Jade","Legendary","Mystic","Neon","Omega","Raging","Savage","Toxic","Ultra","Wise","Alpha","Chaos"]
nouns=["Steve","Creeper","Zombie","Skeleton","Enderman","Warrior","Builder","Miner","Hunter","Dragon","Ninja","Wizard","Knight","Archer","Master","Legend","Hero","Titan","Ghost","Demon","Phoenix","Wolf","Bear","Tiger","Eagle","Viper","Falcon","Raven","Lion","Fox","Hawk","Spider","Reaper","Samurai","Viking","Pirate","Sniper","Soldier","Raider","Ranger","Scout","Bandit","Rogue","Thief","Agent","Player","Gamer","Fighter","Striker"]
generateRandomUsername=lambda:f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(0,9999):04d}"

class MinecraftLauncher:
    def __init__(self):
        base=Path.home()/".launcher"
        self.baseDir,self.minecraftDir,self.configFile=base,base/".minecraft",base/"config.json"
        self.modsDir,self.resourcepacksDir,self.shaderpacksDir=base/"mods",base/"resourcepacks",base/"shaderpacks"
        self.loaderSupport,self.cachedVersions={},None
        self.setupDirectories();self.config=self.loadConfig()

    def t(self,key):return translations.get(self.config.get("language","English"),translations["English"]).get(key,key)

    def setupDirectories(self):
        self.baseDir.mkdir(exist_ok=True);self.minecraftDir.mkdir(exist_ok=True)
        [storeDir.mkdir(exist_ok=True)or(storeDir/"universal").mkdir(exist_ok=True)for storeDir in(self.modsDir,self.resourcepacksDir,self.shaderpacksDir)]
        versionsDir,installedLoaders=self.minecraftDir/"versions",{}
        if versionsDir.exists():
            for d in versionsDir.iterdir():
                if not d.is_dir()or not(d/f"{d.name}.json").exists():continue
                if"-forge-"in d.name:installedLoaders.setdefault(d.name.split("-forge-")[0],set()).add("forge");continue
                if m:=re.fullmatch(r"neoforge-(\d+\.\d+).*",d.name):installedLoaders.setdefault("1.20.1"if(g:=m.group(1)).startswith("47.")else"1."+g.removesuffix(".0"),set()).add("neoforge");continue
                if d.name.startswith("fabric-loader-"):installedLoaders.setdefault(d.name.rsplit("-",1)[1],set()).add("fabric")
        [[( self.modsDir/mc/loader).mkdir(parents=True,exist_ok=True)for loader in loaders]for mc,loaders in installedLoaders.items()]
        for d in list(self.modsDir.iterdir()):
            if not d.is_dir()or d.name=="universal":continue
            if"-forge-"in d.name:
                target=(self.modsDir/(mc:=d.name.split("-forge-")[0])/"forge");target.mkdir(parents=True,exist_ok=True)
                [(target/jar.name).exists()or shutil.move(str(jar),str(target/jar.name))for jar in d.glob("*.jar")]
                try:d.rmdir()
                except:pass
                continue
            if(subDirs:=[s for s in d.iterdir()if s.is_dir()])and len(subDirs)==1:
                [(subDirs[0]/jar.name).exists()or shutil.move(str(jar),str(subDirs[0]/jar.name))for jar in d.glob("*.jar")]

    def loadConfig(self):
        default={"username":generateRandomUsername(),"selectedVersion":None,"loader":"vanilla","installedVersions":[],"language":"English","ramAllocation":"2G"}
        if self.configFile.exists():
            try:
                cfg={**default,**json.load(open(self.configFile))}
                cfg.update({"selectedVersion":cfg.pop("selected_version")}if"selected_version"in cfg else{})
                cfg.update({"installedVersions":cfg.pop("installed_versions")}if"installed_versions"in cfg else{})
                return cfg
            except:pass
        json.dump(default,open(self.configFile,'w'),indent=2)
        return default

    def saveConfig(self):json.dump(self.config,open(self.configFile,'w'),indent=2)

    def _findJava(self):
        if javaHome:=os.environ.get("JAVA_HOME"):
            if(exe:=Path(javaHome)/"bin"/("java.exe"if os.name=='nt'else"java")).exists():return str(exe)
        if javaInPath:=shutil.which("java"):return javaInPath
        if(runtimeDir:=self.minecraftDir/"runtime").exists():
            for p in sorted(runtimeDir.rglob("java.exe"if os.name=='nt'else"java")):
                if p.exists()and p.parent.name=="bin":return str(p)

    def _installJava(self,mcVersion):
        try:parts=mcVersion.split('.');major,minor=int(parts[1]),int(parts[2])if len(parts)>2 else 0
        except:major,minor=21,0
        javaVersion=8 if major<17 else(17 if major<=19 or(major==20 and minor<=4)else 21)
        self._clear();self._header();print(f" {white}{self.t('javaNotFound')} {javaVersion}..{reset}")
        state={"done":0,"progress":0,"max":0,"total":0,"pct":-1,"lastRender":0.0}
        def render():
            if(now:=time.time())-state["lastRender"]<0.05:return
            state["lastRender"]=now;total,pct=state["total"],max(state["pct"],int(min((state["done"]+min(state["progress"],state["max"]))/total,1.0)*100)if total>0 else 0);state["pct"]=pct
            sys.stdout.write(f"\x1b[2K\r {white}{self.t('installingJava')} {javaVersion}.. {pct}%{reset}");sys.stdout.flush()
        def setStatus(status):render()
        def setMax(maximum):state["done"]+=state["max"];state["total"]+=maximum;state["max"],state["progress"]=maximum,0;render()
        def setProgress(progress):state["progress"]=progress;render()
        try:
            minecraft_launcher_lib.runtime.install_jvm_runtime(str(javaVersion),str(self.minecraftDir),callback={"setStatus":setStatus,"setMax":setMax,"setProgress":setProgress})
            sys.stdout.write(f"\x1b[2K\r {white}{self.t('installingJava')} {javaVersion}.. 100%{reset}\n");sys.stdout.flush()
            if javaPath:=self._findJava():return javaPath
        except Exception as e:sys.stdout.write("\n");sys.stdout.flush();self._showMessage(f"{self.t('error')}: {e}",red)

    def _formatVersionName(self,versionId):
        if"-forge-"in versionId:return f"{versionId.split('-forge-')[0]} Forge"
        if m:=re.fullmatch(r"neoforge-(\d+\.\d+).*",versionId):return f"{'1.20.1'if(g:=m.group(1)).startswith('47.')else'1.'+g.removesuffix('.0')} Neoforge"
        if versionId.startswith("fabric-loader-"):return f"{versionId.rsplit('-',1)[1]} Fabric"
        return versionId

    def _makeCallback(self,version):
        displayName,state=self._formatVersionName(version),{"done":0,"progress":0,"max":0,"total":0,"pct":-1,"lastRender":0.0}
        def render():
            if(now:=time.time())-state["lastRender"]<0.05:return
            state["lastRender"]=now;total,pct=state["total"],max(state["pct"],int(min((state["done"]+min(state["progress"],state["max"]))/total,1.0)*100)if total>0 else 0);state["pct"]=pct
            sys.stdout.write(f"\x1b[2K\r {white}{self.t('downloading')} {displayName}.. {pct}%{reset}");sys.stdout.flush()
        def setMax(maximum):state["done"]+=state["max"];state["total"]+=maximum;state["max"],state["progress"]=maximum,0;render()
        def setProgress(progress):state["progress"]=progress;render()
        def finish():state["lastRender"],state["pct"]=0.0,100;sys.stdout.write(f"\x1b[2K\r {white}{self.t('downloading')} {displayName}.. 100%{reset}");sys.stdout.flush()
        return{"setStatus":render,"setMax":setMax,"setProgress":setProgress,"finish":finish}

    def _finishProgress(self):sys.stdout.write("\n");sys.stdout.flush()

    def getVersions(self):
        if self.cachedVersions is None:self.cachedVersions=[v["id"]for v in minecraft_launcher_lib.utils.get_version_list()if v["type"]=="release"]
        return self.cachedVersions

    def selectVersion(self):
        self._clear();self._header();print(f" {white}{self.t('loadingVersions')}{reset}")
        allVersions,current=self.getVersions(),self.config.get("selectedVersion")
        self._clear();self._header()
        if(selected:=questionary.autocomplete(self.t("version"),choices=allVersions,default=current if current in allVersions else"",style=launcherStyle,qmark="").ask())and selected in allVersions:
            self.config["selectedVersion"]=selected
            if not self.loaderSupports(self.config.get("loader","vanilla"),selected):self.config["loader"]="vanilla"
            self.saveConfig()

    def loaderSupports(self,loader,mcVersion):
        if loader=="vanilla":return True
        if(key:=(loader,mcVersion))not in self.loaderSupport:
            try:self.loaderSupport[key]=minecraft_launcher_lib.mod_loader.get_mod_loader(loader).is_minecraft_version_supported(mcVersion)
            except:self.loaderSupport[key]=False
        return self.loaderSupport[key]

    def selectLoader(self):
        current=self.config.get("loader","vanilla")
        loaders=["vanilla"]+([l for l in("forge","neoforge","fabric")if self.loaderSupports(l,version)]if(version:=self.config.get("selectedVersion"))else[])
        if selected:=questionary.select(self.t("loader"),choices=loaders,default=current if current in loaders else"vanilla",style=launcherStyle,qmark="",instruction="").ask():
            self.config["loader"]=selected;self.saveConfig()

    def setUsername(self):
        if(username:=questionary.text(self.t("username"),default=self.config.get("username","Player"),style=launcherStyle,qmark="",instruction="").ask())and username.strip():
            self.config["username"]=username.strip();self.saveConfig()

    def settingsMenu(self):
        while True:
            self._clear();self._header()
            selected=questionary.select(self.t("settings"),choices=[self.t("language"),self.t("ramUsage"),Separator(),self.t("back")],style=launcherStyle,qmark="",instruction="").ask()
            if selected==self.t("language"):
                lang=questionary.select(self.t("language"),choices=["English","Русский"],default=self.config.get("language","English"),style=launcherStyle,qmark="",instruction="").ask()
                lang and(self.config.update({"language":lang})or self.saveConfig())
            elif selected==self.t("ramUsage"):
                ram=questionary.select(self.t("ramUsage"),choices=["1G","2G","4G","8G","16G"],default=self.config.get("ramAllocation","2G"),style=launcherStyle,qmark="",instruction="").ask()
                ram and(self.config.update({"ramAllocation":ram})or self.saveConfig())
            else:return

    def _folders(self,storeDir):return sorted(d.name for d in storeDir.iterdir()if d.is_dir())

    def _searchModrinth(self,query,facets=""):
        try:
            params={"query":query,"limit":20};facets and params.update({"facets":facets})
            r=requests.get("https://api.modrinth.com/v2/search",params=params,headers={"User-Agent":"MinecraftLauncher/1.0"},timeout=15);r.raise_for_status()
            return r.json().get("hits",[])
        except:return[]

    def _getModrinthVersions(self,projectId,mcVersion,loader):
        try:
            params={"game_versions":json.dumps([mcVersion])};loader and params.update({"loaders":json.dumps([loader])})
            r=requests.get(f"https://api.modrinth.com/v2/project/{projectId}/version",params=params,headers={"User-Agent":"MinecraftLauncher/1.0"},timeout=15);r.raise_for_status()
            return r.json()
        except:return[]

    def _downloadModrinthFile(self,url,targetPath):
        try:
            r=requests.get(url,stream=True,headers={"User-Agent":"MinecraftLauncher/1.0"},timeout=60);r.raise_for_status()
            with open(targetPath,'wb')as f:[f.write(chunk)for chunk in r.iter_content(chunk_size=8192)]
            return True
        except:return False

    def _findOnlineModrinth(self,itemType,suffix,targetDir):
        self._clear();self._header()
        typeKey={"Mod":"searchMod","Resource Pack":"searchResourcePack","Shader Pack":"searchShaderPack"}.get(itemType,"searchMod")
        query=questionary.text(self.t(typeKey),style=launcherStyle,qmark="",instruction="").ask()
        if not query or not query.strip():return
        facetMap={"Mod":'[["project_type:mod"]]',"Resource Pack":'[["project_type:resourcepack"]]',"Shader Pack":'[["project_type:shader"]]'}
        facets=facetMap.get(itemType,"")
        self._showMessage(self.t("searching"),white,wait=False)
        results=self._searchModrinth(query.strip(),facets)
        if not results:self._showMessage(self.t("noResults"),red);return
        self._clear();self._header()
        choices=[Choice(title=[("fg:#ffffff",hit.get("title","Unknown"))],value=hit)for hit in results]
        choices.append(Separator());choices.append(Choice(self.t("back"),value="__back__"))
        selected=questionary.select(self.t("select"),choices=choices,style=launcherStyle,qmark="",instruction="").ask()
        if not selected or selected=="__back__":return
        projectId=selected.get("project_id")
        if not projectId:return
        mcVersion=self.config.get("selectedVersion");loader=self.config.get("loader","vanilla")
        if not mcVersion:self._showMessage(self.t("noVersionSelected"),red);return
        self._showMessage(self.t("loadingVersionsMsg"),white,wait=False)
        modrinthLoader=None
        if itemType=="Mod"and loader!="vanilla":modrinthLoader=loader
        elif itemType=="Resource Pack":modrinthLoader="minecraft"
        versions=self._getModrinthVersions(projectId,mcVersion,modrinthLoader)
        if not versions:self._showMessage(self.t("noCompatibleVersions"),red);return
        version=versions[0];files=version.get("files",[])
        if not files:self._showMessage(self.t("noFilesAvailable"),red);return
        primaryFile=next((f for f in files if f.get("primary")),files[0])
        downloadUrl=primaryFile.get("url");fileName=primaryFile.get("filename")
        if not downloadUrl or not fileName:self._showMessage(self.t("invalidFileData"),red);return
        self._showMessage(f"{self.t('downloading')} {fileName}..",white,wait=False)
        if self._downloadModrinthFile(downloadUrl,targetDir/fileName):self._showMessage(f"+ {fileName}",red)
        else:self._showMessage(self.t("downloadFailed"),red)

    def _pickFile(self,title,filetypes):
        try:
            import tkinter as tk;from tkinter import filedialog
            root=tk.Tk();root.withdraw();root.attributes("-topmost",True)
            path=filedialog.askopenfilename(title=title,filetypes=filetypes);root.destroy()
            return Path(path)if path else None
        except:return None

    def fileMenu(self,storeDir,title,item,suffix,filetypes):
        mcVersion=self.config.get("selectedVersion")
        if mcVersion:(storeDir/mcVersion).mkdir(parents=True,exist_ok=True)
        folders=self._folders(storeDir)
        if not folders:self._showMessage("No folders yet",white);return
        choices=[Choice(title=[("fg:#ffffff",name)],value=name)for name in folders]
        choices.append(Separator());choices.append(Choice(self.t("back"),value="__back__"))
        folder=questionary.select(title,choices=choices,style=launcherStyle,qmark="",instruction="").ask()
        if not folder or folder=="__back__":return
        target=storeDir/folder
        while True:
            self._clear();self._header()
            files=sorted(p.name for p in target.glob(f"*{suffix}"))
            print(f" {bold}{white}{self.t('advancedMenu')} {title}{reset}\n")
            if files:
                for f in files:print(f" {white}{f}{reset}")
                print()
            addKey={"Mod":"addMod","Resource Pack":"addResourcePack","Shader Pack":"addShaderPack"}.get(item,f"+ Add {item}")
            removeKey={"Mod":"removeMod","Resource Pack":"removeResourcePack","Shader Pack":"removeShaderPack"}.get(item,f"- Remove {item}")
            opts=[Choice(title=[("fg:#ff5555",self.t(addKey)if addKey in translations["English"]else addKey)],value="__add__"),Choice(title=[("fg:#ff5555",self.t(removeKey)if removeKey in translations["English"]else removeKey)],value="__remove__"),Separator(),Choice(self.t("back"),value="__back__")]
            sel=questionary.select("",choices=opts,style=launcherStyle,qmark="",instruction="").ask()
            if sel=="__add__":
                self._clear();self._header()
                importChoices=[Choice(self.t("importFromFile"),value="file"),Choice(self.t("findOnline"),value="online"),Separator(),Choice(self.t("back"),value="__back__")]
                importType=questionary.select(self.t(addKey)if addKey in translations["English"]else f"Add {item}",choices=importChoices,style=launcherStyle,qmark="",instruction="").ask()
                if importType=="file":
                    selectKey={"Mod":"selectMod","Resource Pack":"selectResourcePack","Shader Pack":"selectShaderPack"}.get(item,f"Select {item}")
                    picked=self._pickFile(self.t(selectKey)if selectKey in translations["English"]else selectKey,filetypes)
                    if picked and picked.suffix.lower()==suffix and picked.exists():
                        shutil.copy2(picked,target/picked.name)
                        self._showMessage(f"+ {picked.name}",red)
                elif importType=="online":
                    self._findOnlineModrinth(item,suffix,target)
            elif sel=="__remove__":
                if not files:continue
                toDelete=questionary.select(self.t("remove"),choices=files+[Separator(),self.t("back")],style=launcherStyle,qmark="",instruction="").ask()
                if toDelete and toDelete!=self.t("back"):
                    (target/toDelete).unlink(missing_ok=True)
                    self._showMessage(f"- {toDelete}",red)
            elif sel=="__back__"or sel is None:return

    def modsMenu(self):
        mcVersion=self.config.get("selectedVersion")
        if not mcVersion:self._showMessage(self.t("noVersionSelected"),red);return
        versionDir=self.modsDir/mcVersion
        if not versionDir.exists():self._showMessage(f"{self.t('noModsFolder')} {mcVersion}",white);return
        loaders=[d.name for d in versionDir.iterdir()if d.is_dir()]
        if not loaders:self._showMessage(f"{self.t('noLoadersInstalled')} {mcVersion}",white);return
        targetDir=None
        if len(loaders)==1:targetDir=versionDir/loaders[0]
        else:
            self._clear();self._header()
            choices=[Choice(title=[("fg:#ffffff",loader)],value=loader)for loader in sorted(loaders)]
            choices.append(Separator());choices.append(Choice(self.t("back"),value="__back__"))
            selectedLoader=questionary.select(self.t("modLoader"),choices=choices,style=launcherStyle,qmark="",instruction="").ask()
            if not selectedLoader or selectedLoader=="__back__":return
            targetDir=versionDir/selectedLoader
        while True:
            self._clear();self._header()
            files=sorted(p.name for p in targetDir.glob("*.jar"))
            print(f" {bold}{white}{self.t('advancedMenu')} {self.t('mods')}{reset}\n")
            if files:
                for f in files:print(f" {white}{f}{reset}")
                print()
            opts=[Choice(title=[("fg:#ff5555",self.t("addMod"))],value="__add__"),Choice(title=[("fg:#ff5555",self.t("removeMod"))],value="__remove__"),Separator(),Choice(self.t("back"),value="__back__")]
            sel=questionary.select("",choices=opts,style=launcherStyle,qmark="",instruction="").ask()
            if sel=="__add__":
                self._clear();self._header()
                importChoices=[Choice(self.t("importFromFile"),value="file"),Choice(self.t("findOnline"),value="online"),Separator(),Choice(self.t("back"),value="__back__")]
                importType=questionary.select(self.t("addMod"),choices=importChoices,style=launcherStyle,qmark="",instruction="").ask()
                if importType=="file":
                    picked=self._pickFile(self.t("selectMod"),[("Jar files","*.jar"),("All files","*.*")])
                    if picked and picked.suffix.lower()==".jar"and picked.exists():
                        shutil.copy2(picked,targetDir/picked.name)
                        self._showMessage(f"+ {picked.name}",red)
                elif importType=="online":
                    self._findOnlineModrinth("Mod",".jar",targetDir)
            elif sel=="__remove__":
                if not files:continue
                toDelete=questionary.select(self.t("remove"),choices=files+[Separator(),self.t("back")],style=launcherStyle,qmark="",instruction="").ask()
                if toDelete and toDelete!=self.t("back"):
                    (targetDir/toDelete).unlink(missing_ok=True)
                    self._showMessage(f"- {toDelete}",red)
            elif sel=="__back__"or sel is None:return

    def resourcepacksMenu(self):
        self.fileMenu(self.resourcepacksDir,"Resource Packs","Resource Pack",".zip",[("Zip files","*.zip"),("All files","*.*")])

    def shaderpacksMenu(self):
        self.fileMenu(self.shaderpacksDir,"Shader Packs","Shader Pack",".zip",[("Zip files","*.zip"),("All files","*.*")])

    def openScreenshots(self):
        (shotsDir:=self.minecraftDir/"screenshots").mkdir(exist_ok=True)
        try:(os.startfile if os.name=='nt'else(lambda p:subprocess.Popen(["open"if sys.platform=='darwin'else"xdg-open",str(p)])))(shotsDir)
        except Exception as e:self._showMessage(f"{self.t('error')}: {e}",red)

    def _organizeDir(self,storeDir,gameSubdir,mcVersion,pattern):
        (storeDir/"universal").mkdir(exist_ok=True);(storeDir/mcVersion).mkdir(exist_ok=True);(gameDir:=self.minecraftDir/gameSubdir).mkdir(parents=True,exist_ok=True)
        [existing.unlink(missing_ok=True)for existing in gameDir.glob(pattern)]
        [[shutil.copy2(f,gameDir/f.name)for f in(storeDir/name).glob(pattern)]for name in("universal",mcVersion)]

    def organizeMods(self,mcVersion,loader):
        (gameDir:=self.minecraftDir/"mods").mkdir(parents=True,exist_ok=True);[existing.unlink(missing_ok=True)for existing in gameDir.glob("*.jar")]
        (universalDir:=self.modsDir/"universal").exists()and[shutil.copy2(f,gameDir/f.name)for f in universalDir.glob("*.jar")]
        (versionLoaderDir:=self.modsDir/mcVersion/loader).exists()and[shutil.copy2(f,gameDir/f.name)for f in versionLoaderDir.glob("*.jar")]

    def resolveInstalledVersion(self,version,loader):
        if not(versionsDir:=self.minecraftDir/"versions").exists():return None
        if loader=="forge":
            for d in versionsDir.iterdir():
                if d.is_dir()and d.name.startswith(f"{version}-forge")and(d/f"{d.name}.json").exists():return d.name if self.forgeIsComplete(version,d.name)else None
            return None
        if loader=="neoforge":
            shortVersion=version.removeprefix("1.")
            return next((d.name for d in versionsDir.iterdir()if d.is_dir()and(d/f"{d.name}.json").exists()and(m:=re.fullmatch(r"neoforge-(\d+\.\d+).*",d.name))and m.group(1).removesuffix(".0")==shortVersion.removesuffix(".0")),None)
        if loader=="fabric":return next((d.name for d in versionsDir.iterdir()if d.is_dir()and(d/f"{d.name}.json").exists()and d.name.startswith("fabric-loader-")and d.name.endswith(f"-{version}")),None)
        return version if(versionsDir/version/f"{version}.json").exists()else None

    def forgeIsComplete(self,mcVersion,installedId):
        try:minor=int(mcVersion.split(".")[1])
        except:minor=0
        if not(forgeLibs:=self.minecraftDir/"libraries"/"net"/"minecraftforge"/"forge").exists():return False
        for d in forgeLibs.iterdir():
            if not(d.is_dir()and d.name.startswith(f"{mcVersion}-")):continue
            if minor<13:return any(d.glob("*.jar"))
            if not any(d.glob("*-client.jar"))or not(clientDir:=self.minecraftDir/"libraries"/"net"/"minecraft"/"client").exists():return False
            return any(cd.is_dir()and cd.name.startswith(f"{mcVersion}-")and any(cd.glob("*-srg.jar"))and any(cd.glob("*-extra.jar"))for cd in clientDir.iterdir())
        return False

    def installVersion(self,version,loader):
        if not(javaPath:=self._findJava()or self._installJava(version)):raise RuntimeError("Failed to find or install Java")
        callback=self._makeCallback(version)
        if loader!="vanilla":
            if not(modLoader:=minecraft_launcher_lib.mod_loader.get_mod_loader(loader)).is_minecraft_version_supported(version):raise RuntimeError(f"{loader.capitalize()} is not available for {version}")
            installedId=self._loaderInstallWithRetry(modLoader,version,modLoader.get_latest_loader_version(version),callback,javaPath)
            callback["finish"]();self._finishProgress();(self.modsDir/version/loader).mkdir(parents=True,exist_ok=True)
            return installedId
        self._installWithRetry(version,callback);callback["finish"]();self._finishProgress()
        return version

    def _loaderInstallWithRetry(self,modLoader,version,loaderVersion,callback,javaPath,attempts=3):
        lastErr=None
        for attempt in range(1,attempts+1):
            try:return modLoader.install(version,str(self.minecraftDir),loader_version=loaderVersion,callback=callback,java=javaPath)
            except(requests.exceptions.ConnectionError,requests.exceptions.Timeout,ConnectionError)as e:lastErr=e;attempt<attempts and time.sleep(attempt*3)
        raise lastErr

    def _installWithRetry(self,version,callback,attempts=3):
        lastErr=None
        for attempt in range(1,attempts+1):
            try:minecraft_launcher_lib.install.install_minecraft_version(version,str(self.minecraftDir),callback=callback);return
            except(requests.exceptions.ConnectionError,requests.exceptions.Timeout,ConnectionError)as e:lastErr=e;attempt<attempts and time.sleep(attempt*3)
        raise lastErr

    def launchGame(self):
        self._clear()
        version=self.config.get("selectedVersion");loader=self.config.get("loader","vanilla");username=self.config.get("username","Player")
        if not version:self._showMessage(self.t("noVersionSelected"),red);return
        try:
            javaPath=self._findJava()
            if not javaPath:
                javaPath=self._installJava(version)
                if not javaPath:
                    self._showMessage(f"{self.t('error')}: Java",red)
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
            ramAlloc=self.config.get("ramAllocation","2G")
            options={"username":username,"uuid":"","token":"","gameDirectory":str(self.minecraftDir),"jvmArguments":[f"-Xmx{ramAlloc}",f"-Xms{ramAlloc}"],"executablePath":javaPath}
            command=minecraft_launcher_lib.command.get_minecraft_command(versionId,str(self.minecraftDir),options)
            displayName=self._formatVersionName(versionId)
            self._showMessage(f"{self.t('launching')} {displayName}",white,wait=False)
            subprocess.run(command,cwd=str(self.minecraftDir),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except KeyboardInterrupt:return
        except Exception as e:
            self._finishProgress()
            self._showMessage(f"{self.t('error')}: {e}",red)

    def _clear(self):os.system('cls'if os.name=='nt'else'clear')
    def _header(self):print(f"\n {bold}{white}Flint Launcher{reset}\n {red}{self.config.get('username','Player')}{white}, {self.config.get('selectedVersion','none')} {white}{self.config.get('loader','vanilla').capitalize()}{reset}\n")
    def _showMessage(self,message,color=white,wait=True):self._clear();self._header();print(f" {color}{message}{reset}");wait and input()

    def advancedMenu(self):
        while True:
            self._clear();self._header()
            choices=[self.t("username"),self.t("mods"),self.t("resourcePacks"),self.t("shaderPacks"),Separator(),self.t("screenshots"),Separator(),self.t("back")]
            {self.t("username"):self.setUsername,self.t("mods"):self.modsMenu,self.t("resourcePacks"):self.resourcepacksMenu,self.t("shaderPacks"):self.shaderpacksMenu,self.t("screenshots"):self.openScreenshots}.get(selected:=questionary.select(self.t("advancedMenu"),choices=choices,style=launcherStyle,qmark="",instruction="").ask(),lambda:None)()
            if not selected or selected==self.t("back"):return

    def mainMenu(self):
        while True:
            self._clear();self._header()
            choices=[self.t("launch"),self.t("version"),self.t("loader"),Separator(),self.t("settings"),self.t("advanced")]
            {self.t("launch"):self.launchGame,self.t("version"):self.selectVersion,self.t("loader"):self.selectLoader,self.t("settings"):self.settingsMenu,self.t("advanced"):self.advancedMenu}.get(selected:=questionary.select(self.t("menu"),choices=choices,style=launcherStyle,qmark="",instruction="").ask(),sys.exit)()

    def run(self):
        try:self.mainMenu()
        except KeyboardInterrupt:sys.exit(0)

if __name__=="__main__":
    MinecraftLauncher().run()

