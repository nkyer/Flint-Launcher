import os,re,sys,json,time,random,hashlib,subprocess,shutil,stat,uuid,warnings
from pathlib import Path
warnings.filterwarnings("ignore",category=DeprecationWarning)

if os.name=='nt':
    import ctypes
    try:ctypes.windll.kernel32.AllocConsole()
    except:pass
    sys.stdout,sys.stdin,sys.stderr=sys.__stdout__,sys.__stdin__,sys.__stderr__
    try:k=ctypes.windll.kernel32;h=k.GetStdHandle(-11);m=ctypes.c_uint();k.GetConsoleMode(h,ctypes.byref(m));k.SetConsoleMode(h,m.value|4)
    except:pass

white,red,bold,reset="\033[97m","\033[91m","\033[1m","\033[0m"

requiredPackages={"minecraft_launcher_lib":"minecraft-launcher-lib","requests":"requests"}

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

import minecraft_launcher_lib,requests

class Choice:
    def __init__(self,title,value=None,color=white):self.title,self.value,self.color=title,value,color
class Separator:pass

def readKey():
    if os.name=='nt':
        import msvcrt
        k=msvcrt.getwch()
        if k in("\x00","\xe0"):return{"H":"up","P":"down","K":"left","M":"right","G":"home","O":"end","S":"delete"}.get(msvcrt.getwch(),"")
        return{"\r":"enter","\x1b":"esc","\x08":"backspace","\x7f":"backspace","\t":"tab","\x03":"ctrl-c"}.get(k,k)
    import termios,tty,select
    fd=sys.stdin.fileno();old=termios.tcgetattr(fd)
    try:
        tty.setraw(fd);b=os.read(fd,1)
        if b==b"\x1b":
            if not select.select([fd],[],[],0.05)[0]:return"esc"
            seq=os.read(fd,8).decode(errors="ignore")
            return{"[A":"up","[B":"down","[C":"right","[D":"left","[H":"home","[F":"end","OH":"home","OF":"end","[1~":"home","[4~":"end","[3~":"delete"}.get(seq,"")
        if b[0]>=0xC0:b+=os.read(fd,1 if b[0]<0xE0 else 2 if b[0]<0xF0 else 3)
        k=b.decode(errors="ignore")
        return{"\r":"enter","\n":"enter","\x7f":"backspace","\x08":"backspace","\t":"tab","\x03":"ctrl-c"}.get(k,k)
    finally:termios.tcsetattr(fd,termios.TCSADRAIN,old)

def out(text):sys.stdout.write(text);sys.stdout.flush()
def fit(text,pad=6):return text[:max(10,shutil.get_terminal_size((80,24)).columns-pad)]

class Live:
                                            
    rows=0
    def draw(self,lines,cur=None):
        o=(f"\x1b[{self.rows}A"if self.rows else"")+"\r\x1b[J"+"\n".join(lines)
        if cur:
            up=len(lines)-1-cur[0];o+=(f"\x1b[{up}A"if up else"")+"\r"+(f"\x1b[{cur[1]}C"if cur[1]else"");self.rows=cur[0]
        else:self.rows=len(lines)-1
        out(o)
    def clear(self):out((f"\x1b[{self.rows}A"if self.rows else"")+"\r\x1b[J");self.rows=0

def select(title,choices,default=None):
    items=[c if isinstance(c,(Choice,Separator))else Choice(str(c),c)for c in choices]
    sel=[i for i,c in enumerate(items)if isinstance(c,Choice)]
    if not sel:return None
    pos=next((i for i in sel if default is not None and items[i].value==default),sel[0])
    canBack=any(isinstance(c,Choice)and c.value is False for c in items)
    live,top=Live(),0
    out("\x1b[?25l")
    try:
        while True:
            h=max(5,shutil.get_terminal_size((80,24)).lines-9)
            top=max(0,min(max(top,pos-h+1),pos,len(items)-h))
            lines=[f" {white}{title}{reset}"]if title else[]
            for i in range(top,min(top+h,len(items))):
                c=items[i]
                lines.append(""if isinstance(c,Separator)else f" {bold}{red}» {fit(c.title)}{reset}"if i==pos else f"   {c.color}{fit(c.title)}{reset}")
            live.draw(lines)
            key=readKey();at=sel.index(pos)
            if key=="up":pos=sel[(at-1)%len(sel)]
            elif key=="down":pos=sel[(at+1)%len(sel)]
            elif key=="home":pos=sel[0]
            elif key=="end":pos=sel[-1]
            elif key=="enter":live.clear();return items[pos].value
            elif key=="ctrl-c":live.clear();return None
            elif key=="esc"and canBack:live.clear();return False
    finally:out("\x1b[?25h")

def prompt(title,default="",validate=None,password=False,choices=None):
    buf,pos,live,idx,moved,err=list(default),len(default),Live(),0,False,""
    try:
        while True:
            text="".join(buf);low=text.lower()
            matches=[c for c in choices if low in c.lower()][:5]if choices else[]
            idx=min(idx,max(len(matches)-1,0))
            lines=[f" {white}{title}{reset}",f" {bold}{red}» {fit('*'*len(buf)if password else text)}{reset}"]
            lines+=[f"   {red if i==idx else white}{m}{reset}"for i,m in enumerate(matches)]
            if err:lines.append(f" {red}{err}{reset}")
            live.draw(lines,(1,3+pos))
            key=readKey()
            if key in("ctrl-c","esc"):live.clear();return None
            elif key=="enter":
                if choices:
                    if matches and(moved or text not in choices):text=matches[idx]
                    if text not in choices:continue
                if validate and(r:=validate(text))is not True:err=r;continue
                live.clear();return text
            elif key=="backspace"and pos:pos-=1;del buf[pos];err="";idx=0;moved=False
            elif key=="delete"and pos<len(buf):del buf[pos];err="";idx=0;moved=False
            elif key=="left":pos=max(0,pos-1)
            elif key=="right":pos=min(len(buf),pos+1)
            elif key=="home":pos=0
            elif key=="end":pos=len(buf)
            elif key=="up"and matches:idx=(idx-1)%len(matches);moved=True
            elif key=="down"and matches:idx=(idx+1)%len(matches);moved=True
            elif key=="tab"and matches:buf=list(matches[idx]);pos=len(buf);moved=False
            elif len(key)==1 and key.isprintable():buf.insert(pos,key);pos+=1;err="";idx=0;moved=False
    finally:out("\x1b[?25h")

headers={"User-Agent":"MinecraftLauncher/1.0"}

translations={k:tuple(v)for k,*v in(l.split("|")for l in"""
menu|Menu|Меню|Menü|Меню
launch|Launch|Запуск|Starten|Запуск
version|Version|Версия|Version|Версія
loader|Loader|Загрузчик|Loader|Завантажувач
settings|Settings|Настройки|Einstellungen|Налаштування
advanced|Advanced|Дополнительно|Erweitert|Додатково
back|Back|Назад|Zurück|Назад
username|Username|Имя игрока|Spielername|Ім'я гравця
mods|Mods|Моды|Mods|Моди
resourcePacks|Resource Packs|Ресурспаки|Ressourcenpakete|Ресурспаки
shaderPacks|Shader Packs|Шейдерпаки|Shaderpakete|Шейдерпаки
screenshots|Screenshots|Скриншоты|Screenshots|Скріншоти
language|Language|Язык|Sprache|Мова
ramUsage|RAM Usage|Использование ОЗУ|RAM-Nutzung|Використання ОЗП
advancedMenu|Advanced Menu|Доп. меню|Erweitertes Menü|Дод. меню
loadingVersions|Loading versions..|Загрузка версий..|Versionen werden geladen..|Завантаження версій..
noVersionSelected|No version selected|Версия не выбрана|Keine Version ausgewählt|Версію не вибрано
noModsFolder|No mods folder for|Нет папки модов для|Kein Mods-Ordner für|Немає теки модів для
noLoadersInstalled|No mod loaders installed for|Загрузчики не установлены для|Keine Mod-Loader installiert für|Завантажувачі не встановлено для
modLoader|Mod Loader|Загрузчик модов|Mod-Loader|Завантажувач модів
searchMod|Search Mod|Поиск мода|Mod suchen|Пошук мода
searchResourcePack|Search Resource Pack|Поиск ресурспака|Ressourcenpaket suchen|Пошук ресурспака
searchShaderPack|Search Shader Pack|Поиск шейдерпака|Shaderpaket suchen|Пошук шейдерпака
searching|Searching..|Поиск..|Suche läuft..|Пошук..
noResults|No results found|Ничего не найдено|Keine Ergebnisse gefunden|Нічого не знайдено
select|Select|Выбрать|Auswählen|Вибрати
noCompatibleVersions|No compatible versions found|Совместимых версий не найдено|Keine kompatiblen Versionen gefunden|Сумісних версій не знайдено
noFilesAvailable|No files available|Файлы недоступны|Keine Dateien verfügbar|Файли недоступні
invalidFileData|Invalid file data|Неверные данные файла|Ungültige Dateidaten|Некоректні дані файлу
downloading|Downloading|Загрузка|Herunterladen|Завантаження
downloadFailed|Download failed|Загрузка не удалась|Download fehlgeschlagen|Завантаження не вдалося
addMod|Add Mod|Добавить мод|Mod hinzufügen|Додати мод
addResourcePack|Add Resource Pack|Добавить ресурспак|Ressourcenpaket hinzufügen|Додати ресурспак
addShaderPack|Add Shader Pack|Добавить шейдерпак|Shaderpaket hinzufügen|Додати шейдерпак
removeMod|Remove Mod|Удалить мод|Mod entfernen|Видалити мод
removeResourcePack|Remove Resource Pack|Удалить ресурспак|Ressourcenpaket entfernen|Видалити ресурспак
removeShaderPack|Remove Shader Pack|Удалить шейдерпак|Shaderpaket entfernen|Видалити шейдерпак
importFromFile|Import from file|Импорт из файла|Aus Datei importieren|Імпорт з файлу
findOnline|Find online|Найти онлайн|Online suchen|Знайти онлайн
selectMod|Select Mod|Выбрать мод|Mod auswählen|Вибрати мод
selectResourcePack|Select Resource Pack|Выбрать ресурспак|Ressourcenpaket auswählen|Вибрати ресурспак
selectShaderPack|Select Shader Pack|Выбрать шейдерпак|Shaderpaket auswählen|Вибрати шейдерпак
remove|Remove|Удалить|Entfernen|Видалити
javaNotFound|Java not found. Installing Java|Java не найдена. Установка Java|Java nicht gefunden. Java wird installiert|Java не знайдено. Встановлення Java
installingJava|Installing Java|Установка Java|Java wird installiert|Встановлення Java
launching|Launching|Запуск|Starte|Запуск
error|Error|Ошибка|Fehler|Помилка
custom|Custom|Своё|Benutzerdefiniert|Власне
ramPrompt|RAM in GB (1-128)|ОЗУ в ГБ (1-128)|RAM in GB (1-128)|ОЗП у ГБ (1-128)
ramInvalid|Enter a whole number from 1 to 128|Введите целое число от 1 до 128|Ganze Zahl von 1 bis 128 eingeben|Введіть ціле число від 1 до 128
on|On|Вкл|An|Увімк
off|Off|Выкл|Aus|Вимк
showSnapshots|Snapshots & Betas|Снапшоты и беты|Snapshots & Betas|Снапшоти та бета-версії
hideLauncher|Hide launcher in game|Прятать лаунчер в игре|Launcher im Spiel ausblenden|Ховати лаунчер у грі
gameLogs|Game logs|Логи игры|Spiel-Logs|Логи гри
launcherFolder|Launcher folder|Папка лаунчера|Launcher-Ordner|Тека лаунчера
reset|Reset|Сброс|Zurücksetzen|Скидання
moveFolder|Move folder|Переместить папку|Ordner verschieben|Перемістити теку
useExistingFolder|Use existing folder|Указать существующую папку|Vorhandenen Ordner verwenden|Вказати наявну теку
selectFolder|Select folder|Выберите папку|Ordner auswählen|Виберіть теку
folderExists|Folder already exists|Папка уже существует|Ordner existiert bereits|Тека вже існує
folderInside|Cannot move a folder into itself|Нельзя переместить папку внутрь самой себя|Ordner kann nicht in sich selbst verschoben werden|Не можна перемістити теку саму в себе
movingFolder|Moving folder|Перемещение папки|Ordner wird verschoben|Переміщення теки
folderMoved|Folder moved|Папка перемещена|Ordner verschoben|Теку переміщено
notLauncherFolder|Launcher folder not found there|Папка лаунчера там не найдена|Dort wurde kein Launcher-Ordner gefunden|Теку лаунчера там не знайдено
resetConfirm|Confirm|Подтвердить|Bestätigen|Підтвердити
resetWarning|The following will be deleted|Будет удалено|Folgendes wird gelöscht|Буде видалено
resetHint|Enter - confirm ({}/5), Esc - cancel|Enter - подтвердить ({}/5), Esc - отмена|Enter - bestätigen ({}/5), Esc - abbrechen|Enter - підтвердити ({}/5), Esc - скасувати
resetMemory|Version and loader|Версия и загрузчик|Version und Loader|Версія та завантажувач
versions|Versions|Версии|Versionen|Версії
resetDone|Done|Готово|Fertig|Готово
account|Account|Аккаунт|Konto|Акаунт
loginEly|Log in with Ely.by|Войти через Ely.by|Mit Ely.by anmelden|Увійти через Ely.by
logoutEly|Log out of Ely.by|Выйти из Ely.by|Von Ely.by abmelden|Вийти з Ely.by
elyLogin|Ely.by username or E-mail|Ник или E-mail Ely.by|Ely.by-Name oder E-Mail|Нік або E-mail Ely.by
password|Password|Пароль|Passwort|Пароль
twoFactorCode|Two-factor code|Код двухфакторной защиты|Zwei-Faktor-Code|Код двофакторного захисту
elySessionExpired|Ely.by session expired, log in again|Сессия Ely.by истекла, войдите заново|Ely.by-Sitzung abgelaufen, bitte erneut anmelden|Сесія Ely.by закінчилась, увійдіть знову
authlibFailed|Failed to download authlib-injector|Не удалось скачать authlib-injector|authlib-injector konnte nicht heruntergeladen werden|Не вдалося завантажити authlib-injector
""".strip().splitlines())}

ITEMS={"Mod":("mods","mod",".jar"),"ResourcePack":("resourcePacks","resourcepack",".zip"),"ShaderPack":("shaderPacks","shader",".zip")}
LANGUAGES=["English","Русский","Deutsch","Українська"]
RAM_PRESETS=["1GB","2GB","4GB","8GB","16GB"]
javaComponents={8:"jre-legacy",16:"java-runtime-alpha",17:"java-runtime-gamma",21:"java-runtime-delta",25:"java-runtime-epsilon"}
DEFAULT_SETTINGS={"language":"English","ramAllocation":"4GB","showSnapshots":False,"hideLauncher":True,"gameLogs":True}
RESET_OPTIONS=["settings","resetMemory","gameLogs","versions","mods","resourcePacks","shaderPacks"]
SETTINGS={"language":"language","ramUsage":"ramAllocation","showSnapshots":"showSnapshots","hideLauncher":"hideLauncher","gameLogs":"gameLogs"}

adjectives="Angry Brave Clever Dark Epic Fast Giant Happy Iron King Lone Mad Noble Old Pro Quick Red Silent True Wild Young Crazy Elder Fire Golden Hidden Icy Magic Night Ocean Royal Shadow Thunder Void Ancient Cosmic Deadly Frozen Heroic Jade Legendary Mystic Neon Omega Raging Savage Toxic Ultra Wise Alpha Chaos".split()
nouns="Steve Creeper Zombie Skeleton Enderman Warrior Builder Miner Hunter Dragon Ninja Wizard Knight Archer Master Legend Hero Titan Ghost Demon Phoenix Wolf Bear Tiger Eagle Viper Falcon Raven Lion Fox Hawk Spider Reaper Samurai Viking Pirate Sniper Soldier Raider Ranger Scout Bandit Rogue Thief Agent Player Gamer Fighter Striker".split()
generateRandomUsername=lambda:f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(0,9999):04d}"

def loaderOf(name):
    if"-forge-"in name:return name.split("-forge-")[0],"forge"
    if m:=re.fullmatch(r"neoforge-(\d+\.\d+).*",name):return("1.20.1"if m[1].startswith("47.")else"1."+m[1].removesuffix(".0")),"neoforge"
    if name.startswith("fabric-loader-"):return name.rsplit("-",1)[1],"fabric"
    if name.startswith("quilt-loader-"):return name.rsplit("-",1)[1],"quilt"

def moveJars(src,dst):
    for jar in src.glob("*.jar"):
        if not(dst/jar.name).exists():shutil.move(str(jar),str(dst/jar.name))

def appDataDir():
    if os.name=='nt':return Path(os.environ.get("APPDATA")or Path.home()/"AppData"/"Roaming")
    if sys.platform=='darwin':return Path.home()/"Library"/"Application Support"
    return Path(os.environ.get("XDG_CONFIG_HOME")or Path.home()/".config")

pointerFile,defaultRoot=appDataDir()/"DO-NOT-TOUCH.json",Path.home()/".launcher"

def setHidden(path,hidden):
    try:
        if os.name=='nt':
            attrs=ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs!=-1:ctypes.windll.kernel32.SetFileAttributesW(str(path),attrs|2 if hidden else attrs&~2)
        elif hasattr(os,"chflags"):
            flags=os.stat(path).st_flags;os.chflags(path,flags|stat.UF_HIDDEN if hidden else flags&~stat.UF_HIDDEN)
    except:pass

def isLauncherRoot(path):return path.is_dir()and(path/"config.json").is_file()

def writePointer(root):
    try:
        pointerFile.parent.mkdir(parents=True,exist_ok=True);setHidden(pointerFile,False)
        pointerFile.write_text(json.dumps({"rootDir":str(root)},indent=2));setHidden(pointerFile,True)
    except:pass

def resolveRoot():
    try:
        if(root:=Path(json.loads(pointerFile.read_text())["rootDir"])).is_absolute()and isLauncherRoot(root):return root
    except:pass
    writePointer(defaultRoot)
    return defaultRoot

def modrinth(path,**params):
    try:r=requests.get("https://api.modrinth.com/v2/"+path,params=params,headers=headers,timeout=15);r.raise_for_status();return r.json()
    except:return None

def elyPost(path,**data):
    r=requests.post(f"https://authserver.ely.by/auth/{path}",json=data,headers=headers,timeout=15)
    try:return r.status_code,r.json()
    except ValueError:return r.status_code,{}

def download(url,target):
    try:
        with requests.get(url,stream=True,headers=headers,timeout=60)as r:
            r.raise_for_status()
            with open(f"{target}.part",'wb')as f:
                for chunk in r.iter_content(chunk_size=8192):f.write(chunk)
        os.replace(f"{target}.part",target);return True
    except:return False

class MinecraftLauncher:
    def __init__(self):
        self.loaderSupport,self.cachedVersions={},None
        self.setRoot(resolveRoot())

    def setRoot(self,base):
        self.baseDir,self.minecraftDir,self.configFile=base,base/".minecraft",base/"config.json"
        self.modsDir,self.resourcepacksDir,self.shaderpacksDir,self.logsDir=base/"mods",base/"resourcepacks",base/"shaderpacks",base/"logs"
        self.setupDirectories();self.config=self.loadConfig()

    def applyRoot(self,root):self.setRoot(root);writePointer(root)

    def t(self,key):
        if key not in translations:return key
        return translations[key][LANGUAGES.index(self.config["language"])if self.config["language"]in LANGUAGES else 0]

    def setupDirectories(self):
        self.baseDir.mkdir(parents=True,exist_ok=True);self.minecraftDir.mkdir(exist_ok=True);self.logsDir.mkdir(exist_ok=True)
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
        default={"username":generateRandomUsername(),"selectedVersion":None,"loader":"vanilla","installedVersions":[],"ely":None,**DEFAULT_SETTINGS}
        try:
            cfg={**default,**json.loads(self.configFile.read_text())}
            for new,old in(("selectedVersion","selected_version"),("installedVersions","installed_versions")):
                if old in cfg:cfg[new]=cfg.pop(old)
            if re.fullmatch(r"\d+G",str(cfg["ramAllocation"])):cfg["ramAllocation"]+="B"
            if not re.fullmatch(r"\d+GB",str(cfg["ramAllocation"])):cfg["ramAllocation"]=default["ramAllocation"]
            if cfg["language"]not in LANGUAGES:cfg["language"]="English"
            if not(isinstance(cfg["ely"],dict)and{"accessToken","clientToken","uuid","name"}<=cfg["ely"].keys()):cfg["ely"]=None
            for k in("showSnapshots","hideLauncher","gameLogs"):
                if not isinstance(cfg[k],bool):cfg[k]=default[k]
            return cfg
        except:self.configFile.write_text(json.dumps(default,indent=2));return default

    def saveConfig(self):self.configFile.write_text(json.dumps(self.config,indent=2))

    def _javaMajor(self,exe):
        try:
            flags=0x08000000 if os.name=='nt' else 0
            result=subprocess.run([str(exe),"-version"],capture_output=True,text=True,timeout=20,creationflags=flags)
            match=re.search(r'version "(\d+)(?:\.(\d+))?',result.stderr or result.stdout or "")
            if not match:return None
            first=int(match.group(1))
            return int(match.group(2))if first==1 and match.group(2)else first
        except Exception:return None

    def _guessJava(self,mcVersion):
        nums=[int(n)for n in re.findall(r"\d+",mcVersion)[:3]]
        if not nums:return 21
        if nums[0]>1:return 25 if nums[0]>=26 else 21
        major=nums[1]if len(nums)>1 else 21
        minor=nums[2]if len(nums)>2 else 0
        return 8 if major<17 else 17 if major<=19 or(major==20 and minor<=4)else 21

    def _requiredJava(self,versionId):
        seen=set()
        while versionId and versionId not in seen:
            seen.add(versionId)
            try:data=json.loads((self.minecraftDir/"versions"/versionId/f"{versionId}.json").read_text(encoding="utf-8"))
            except Exception:return None
            if(info:=data.get("javaVersion"))and info.get("majorVersion"):return info.get("component"),int(info["majorVersion"])
            versionId=data.get("inheritsFrom")

    def _findJava(self,major):
        exeName="java.exe"if os.name=='nt'else"java"
        candidates=[p for p in sorted((self.minecraftDir/"runtime").rglob(exeName))if p.parent.name=="bin"]
        if javaHome:=os.environ.get("JAVA_HOME"):candidates.append(Path(javaHome)/"bin"/exeName)
        if javaInPath:=shutil.which("java"):candidates.append(Path(javaInPath))
        for p in candidates:
            if p.exists()and self._javaMajor(p)==major:return str(p)

    def _javaFor(self,mcVersion,versionId):
        required=self._requiredJava(versionId)if versionId else None
        component,major=required if required else(None,self._guessJava(mcVersion))
        if javaPath:=self._findJava(major):return javaPath
        component=component or javaComponents.get(major)
        self._showMessage(f"{self.t('javaNotFound')} {major}..",white,wait=False)
        callback=self._makeCallback(f"{self.t('installingJava')} {major}")
        try:
            minecraft_launcher_lib.runtime.install_jvm_runtime(component,str(self.minecraftDir),callback=callback)
            callback["finish"]();print()
            return self._findJava(major)
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
        if self.cachedVersions is None:self.cachedVersions=[(v["id"],v["type"])for v in minecraft_launcher_lib.utils.get_version_list()]
        kinds={"release","snapshot","old_beta"}if self.config["showSnapshots"]else{"release"}
        return[i for i,kind in self.cachedVersions if kind in kinds]

    def ask(self,title,choices,back=False,**kw):
        if back:choices=[*choices,Separator(),Choice(self.t("back"),value=False)]
        return select(title,choices,**kw)

    def menu(self,title,items,back=False):
        return self.ask(self.t(title),[Separator()if i is None else Choice(self.t(i[0]),value=i[1])for i in items],back)

    def selectVersion(self):
        self._showMessage(self.t("loadingVersions"),white,wait=False)
        allVersions,current=self.getVersions(),self.config["selectedVersion"]
        self._screen()
        if(selected:=prompt(self.t("version"),current if current in allVersions else"",choices=allVersions))and selected in allVersions:
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
        loaders=["vanilla"]+([l for l in("forge","neoforge","fabric","quilt")if self.loaderSupports(l,version)]if version else[])
        if selected:=self.ask(self.t("loader"),loaders,default=current if current in loaders else"vanilla"):
            self.config["loader"]=selected;self.saveConfig()

    def setUsername(self):
        if(username:=prompt(self.t("username"),self.config["username"]))and username.strip():
            self.config["username"]=username.strip();self.saveConfig()

    def accountMenu(self):
        self._screen()
        items=[("logoutEly",self.elyLogout)]if self.config["ely"]else[("username",self.setUsername),("loginEly",self.elyLogin)]
        if action:=self.menu("account",items,True):action()

    def elyLogin(self):
        self._screen()
        if not(login:=prompt(self.t("elyLogin")))or not(password:=prompt(self.t("password"),password=True)):return
        code,clientToken=None,uuid.uuid4().hex
        try:
            for _ in range(2):
                status,data=elyPost("authenticate",username=login.strip(),password=f"{password}:{code}"if code else password,clientToken=clientToken)
                if status==200 or"two factor"not in data.get("errorMessage","").lower():break
                if not(code:=(prompt(self.t("twoFactorCode"))or"").strip()):return
        except requests.RequestException as e:self._showMessage(f"{self.t('error')}: {e}",red);return
        if status!=200 or not(profile:=data.get("selectedProfile")):self._showMessage(f"{self.t('error')}: {data.get('errorMessage','')}",red);return
        self.config["ely"]={"accessToken":data["accessToken"],"clientToken":clientToken,"uuid":profile["id"],"name":profile["name"]}
        self.config["username"]=profile["name"];self.saveConfig()

    def elyLogout(self):
        try:elyPost("invalidate",accessToken=self.config["ely"]["accessToken"],clientToken=self.config["ely"]["clientToken"])
        except requests.RequestException:pass
        self.config["ely"]=None;self.saveConfig()

    def elyRefresh(self):
        ely=self.config["ely"]
        try:
            if elyPost("validate",accessToken=ely["accessToken"])[0]==200:return True
            status,data=elyPost("refresh",accessToken=ely["accessToken"],clientToken=ely["clientToken"])
        except requests.RequestException:return True
        if status!=200:return status>=500
        profile=data.get("selectedProfile")or{}
        ely.update(accessToken=data["accessToken"],uuid=profile.get("id",ely["uuid"]),name=profile.get("name",ely["name"]))
        self.config["username"]=ely["name"];self.saveConfig()
        return True

    def authlibInjector(self):
        jar=self.baseDir/"authlib-injector.jar"
        if jar.exists():return str(jar)
        self._showMessage(f"{self.t('downloading')} authlib-injector..",white,wait=False)
        try:
            info=requests.get("https://authlib-injector.yushi.moe/artifact/latest.json",headers=headers,timeout=15).json()
            if download(info["download_url"],jar)and hashlib.sha256(jar.read_bytes()).hexdigest()==info["checksums"]["sha256"]:return str(jar)
        except Exception:pass
        jar.unlink(missing_ok=True)

    def settingText(self,key):
        value=self.config[SETTINGS[key]]
        return self.t("on"if value else"off")if isinstance(value,bool)else value

    def settingsMenu(self):
        last=None
        while True:
            self._screen()
            keys=[k for k in SETTINGS if k!="hideLauncher"or os.name=='nt']
            choices=[Choice(f"{self.t(k)}: {self.settingText(k)}",value=k)for k in keys]+[Separator(),Choice(self.t("launcherFolder"),value="folder"),Choice(self.t("reset"),value="reset")]
            if not(key:=self.ask(self.t("settings"),choices,True,default=last)):return
            last=key;cfgKey=SETTINGS.get(key)
            if key=="folder":self.folderMenu()
            elif key=="reset":self.resetMenu()
            elif key=="ramUsage":self.setRam()
            elif isinstance(self.config[cfgKey],bool):self.config[cfgKey]=not self.config[cfgKey];self.saveConfig()
            elif value:=self.ask(self.t(key),LANGUAGES,default=self.config[cfgKey]):self.config[cfgKey]=value;self.saveConfig()

    def setRam(self):
        current=self.config["ramAllocation"]
        if not(choice:=self.ask(self.t("ramUsage"),[*RAM_PRESETS,Choice(self.t("custom"),value="custom")],True,default=current if current in RAM_PRESETS else"custom")):return
        if choice=="custom":
            self._screen()
            value=prompt(self.t("ramPrompt"),""if current in RAM_PRESETS else current[:-2],lambda v:v.strip().isascii()and v.strip().isdigit()and 0<int(v)<=128 or self.t("ramInvalid"))
            if not value:return
            choice=f"{int(value)}GB"
        self.config["ramAllocation"]=choice;self.saveConfig()

    def resetMenu(self):
        chosen,last=set(),None
        while True:
            self._screen()
            choices=[Choice(f"{self.t(k)} - {'Y'if k in chosen else'N'}",value=k)for k in RESET_OPTIONS]+[Separator(),Choice(self.t("resetConfirm"),value="go")]
            if not(key:=self.ask(self.t("reset"),choices,True,default=last)):return
            last=key
            if key!="go":chosen^={key}
            elif chosen and self.confirmReset(items:=[k for k in RESET_OPTIONS if k in chosen]):self.doReset(items);return

    def confirmReset(self,items):
        self._screen();print(f" {red}{self.t('resetWarning')}:{reset}\n"+"\n".join(f" {white}- {self.t(k)}{reset}"for k in items)+"\n")
        live,n=Live(),0
        out("\x1b[?25l")
        try:
            while n<5:
                live.draw([f" {red}{self.t('resetHint').format(n)}{reset}"])
                if(key:=readKey())=="enter":n+=1
                elif key in("esc","ctrl-c"):return False
            return True
        finally:live.clear();out("\x1b[?25h")

    def doReset(self,items):
        game=self.minecraftDir
        folders={"gameLogs":[self.logsDir],"versions":[game/"versions"],"mods":[self.modsDir,game/"mods"],"resourcePacks":[self.resourcepacksDir,game/"resourcepacks"],"shaderPacks":[self.shaderpacksDir,game/"shaderpacks"]}
        for key in items:
            if key=="settings":self.config.update(DEFAULT_SETTINGS)
            elif key=="resetMemory":self.config.update(selectedVersion=None,loader="vanilla")
            else:[shutil.rmtree(d,ignore_errors=True)for d in folders[key]]
            if key=="versions":self.config["installedVersions"]=[]
        self.setupDirectories();self.saveConfig();self._showMessage(self.t("resetDone"))

    def folderMenu(self):
        self._screen();print(f" {white}{self.baseDir}{reset}\n")
        action=self.ask(self.t("launcherFolder"),[Choice(self.t("moveFolder"),value="move"),Choice(self.t("useExistingFolder"),value="existing")],True)
        if action=="move":self.moveRoot()
        elif action=="existing":self.useExistingRoot()

    def moveRoot(self):
        if not(picked:=self._pick(self.t("selectFolder"),True)):return
        source,target=self.baseDir.resolve(),picked/".launcher"
        if target==source:return
        if target.exists():self._showMessage(f"{self.t('folderExists')}: {target}",red);return
        if source in target.parents:self._showMessage(self.t("folderInside"),red);return
        self._showMessage(f"{self.t('movingFolder')}..",white,wait=False)
        try:shutil.move(str(source),str(target))
        except Exception as e:self._showMessage(f"{self.t('error')}: {e}",red);return
        self.applyRoot(target);self._showMessage(f"{self.t('folderMoved')}: {target}")

    def useExistingRoot(self):
        if not(picked:=self._pick(self.t("selectFolder"),True)):return
        if not(root:=next((p for p in(picked,picked/".launcher")if isLauncherRoot(p)),None)):self._showMessage(self.t("notLauncherFolder"),red);return
        self.applyRoot(root)

    def _findOnline(self,item,target):
        _,projectType,_=ITEMS[item]
        self._screen()
        query=prompt(self.t(f"search{item}"))
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
        modrinthLoaders=["minecraft"]if item=="ResourcePack"else([loader,"fabric"]if loader=="quilt"else[loader])if item=="Mod"and loader!="vanilla"else None
        versions=modrinth(f"project/{projectId}/version",game_versions=json.dumps([mcVersion]),loaders=json.dumps(modrinthLoaders)if modrinthLoaders else None)
        if not versions:self._showMessage(self.t("noCompatibleVersions"),red);return
        if not(files:=versions[0].get("files",[])):self._showMessage(self.t("noFilesAvailable"),red);return
        primary=next((f for f in files if f.get("primary")),files[0])
        url,fileName=primary.get("url"),primary.get("filename")
        if not url or not fileName:self._showMessage(self.t("invalidFileData"),red);return
        self._showMessage(f"{self.t('downloading')} {fileName}..",white,wait=False)
        self._showMessage(f"+ {fileName}"if download(url,target/fileName)else self.t("downloadFailed"),red)

    def _pick(self,title,folder=False,suffix=None):
        path=None
        try:
            import tkinter as tk
            from tkinter import filedialog
            if os.name=='nt':
                try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except Exception:pass
            root=tk.Tk();root.withdraw();root.attributes("-topmost",True);root.update()
            try:
                if folder:path=filedialog.askdirectory(parent=root,title=title,initialdir=str(self.baseDir.parent),mustexist=True)
                else:
                    fileTypes=[(f"{suffix[1:].capitalize()} files",f"*{suffix}"),("All files","*.*")]if suffix else[("All files","*.*")]
                    path=filedialog.askopenfilename(parent=root,title=title,filetypes=fileTypes)
            finally:root.destroy()
        except Exception:
            self._screen();path=(prompt(title)or"").strip().strip("\"'")
        return Path(path).expanduser().resolve()if path else None

    def _filesMenu(self,item,target):
        title,_,suffix=ITEMS[item]
        while True:
            self._screen()
            files=sorted(p.name for p in target.glob(f"*{suffix}"))
            print(f" {bold}{white}{self.t('advancedMenu')} {self.t(title)}{reset}\n")
            if files:print("\n".join(f" {white}{f}{reset}"for f in files)+"\n")
            sel=self.ask("",[Choice(self.t(f"add{item}"),"add",red),Choice(self.t(f"remove{item}"),"remove",red),Separator(),Choice(self.t("back"),value=False)])
            if sel=="add":
                self._screen()
                source=self.ask(self.t(f"add{item}"),[Choice(self.t("importFromFile"),value="file"),Choice(self.t("findOnline"),value="online")],True)
                if source=="file":
                    picked=self._pick(self.t(f"select{item}"),suffix=suffix)
                    if picked and picked.suffix.lower()==suffix and picked.is_file():
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
            versionId=self.resolveInstalledVersion(version,loader)
            if not(javaPath:=self._javaFor(version,versionId)):self._showMessage(f"{self.t('error')}: Java",red);return
            if not versionId:
                versionId=self.installVersion(version,loader,javaPath)
                if versionId and versionId not in installed:installed.append(versionId);self.saveConfig()
                if not(javaPath:=self._javaFor(version,versionId)):self._showMessage(f"{self.t('error')}: Java",red);return
            if loader!="vanilla":self._syncToGame([self.modsDir/"universal",self.modsDir/version/loader],"mods","*.jar")
            for storeDir,gameSubdir in((self.resourcepacksDir,"resourcepacks"),(self.shaderpacksDir,"shaderpacks")):
                (storeDir/version).mkdir(exist_ok=True);self._syncToGame([storeDir/"universal",storeDir/version],gameSubdir,"*.zip")
            ram=self.config["ramAllocation"].removesuffix("B")
            jvm,player=[f"-Xmx{ram}"],{"username":self.config["username"],"uuid":"","token":""}
            if ely:=self.config["ely"]:
                if not self.elyRefresh():self._showMessage(self.t("elySessionExpired"),red);return
                if not(agent:=self.authlibInjector()):self._showMessage(self.t("authlibFailed"),red);return
                jvm.insert(0,f"-javaagent:{agent}=ely.by");player={"username":ely["name"],"uuid":ely["uuid"],"token":ely["accessToken"]}
            options={**player,"gameDirectory":str(self.minecraftDir),"jvmArguments":jvm,"executablePath":javaPath}
            command=minecraft_launcher_lib.command.get_minecraft_command(versionId,str(self.minecraftDir),options)
            self._showMessage(f"{self.t('launching')} {self._formatVersionName(versionId)}",white,wait=False)
            log=self._openLog(versionId)if self.config["gameLogs"]else None
            console=self._hideConsole()if self.config["hideLauncher"]else None
            try:subprocess.run(command,cwd=str(self.minecraftDir),stdout=log or subprocess.DEVNULL,stderr=subprocess.STDOUT if log else subprocess.DEVNULL)
            finally:
                if console:self._showConsole(console)
                if log:log.close()
        except KeyboardInterrupt:return
        except Exception as e:print();self._showMessage(f"{self.t('error')}: {e}",red)

    def _openLog(self,versionId):
        try:
            self.logsDir.mkdir(exist_ok=True)
            for old in sorted(self.logsDir.glob("*.log"))[:-19]:old.unlink(missing_ok=True)
            log=open(self.logsDir/f"{time.strftime('%Y-%m-%d_%H-%M-%S')}.log","wb")
            log.write(f"Flint Launcher | {versionId} | {self.config['username']} | {self.config['ramAllocation']}\n\n".encode());log.flush()
            return log
        except OSError:return None

    def _hideConsole(self):
        try:
            if os.name=='nt'and(hwnd:=ctypes.windll.kernel32.GetConsoleWindow())and ctypes.windll.user32.IsWindowVisible(hwnd):ctypes.windll.user32.ShowWindow(hwnd,0);return hwnd
        except:pass

    def _showConsole(self,hwnd):
        try:ctypes.windll.user32.ShowWindow(hwnd,5);ctypes.windll.user32.SetForegroundWindow(hwnd)
        except:pass

    def _clear(self):os.system('cls'if os.name=='nt'else'clear')
    def _header(self):c=self.config;print(f"\n {bold}{white}Flint Launcher{reset}\n {red}{c['username']}{' (Ely.by)'if c['ely']else''}{white}, {c['selectedVersion']} {white}{c['loader'].capitalize()}{reset}\n")
    def _screen(self):self._clear();self._header()
    def _showMessage(self,message,color=white,wait=True):self._screen();print(f" {color}{message}{reset}");wait and input()

    def advancedMenu(self):
        items=[("account",self.accountMenu),("mods",self.modsMenu),("resourcePacks",lambda:self.packsMenu("ResourcePack",self.resourcepacksDir)),("shaderPacks",lambda:self.packsMenu("ShaderPack",self.shaderpacksDir))]
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

