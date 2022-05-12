import json
import os
import pickle
import re
import zlib
from datetime import datetime, timedelta
from time import perf_counter


T_DELTA = timedelta(seconds=100)
T_DELTA_SHORT = timedelta(seconds=15)
T_DELTA_SEP = timedelta(minutes=20)

LOGS_CUT_NAME = "LOGS_CUT"

FLAG_ORDER = [
    "SPELL_DISPEL", "SPELL_CAST_SUCCESS", "SPELL_EXTRA_ATTACKS",  "SPELL_ENERGIZE",
    "SPELL_DAMAGE", "SPELL_PERIODIC_DAMAGE", "SPELL_HEAL",
    "SPELL_AURA_APPLIED", "SPELL_AURA_REFRESH", "SPELL_AURA_REMOVED",
    "SPELL_MISSED", "SPELL_CAST_START", ]

BOSSES = [
    "Lord Marrowgar", "Lady Deathwhisper", "Gunship", "Deathbringer Saurfang",
    "Festergut", "Rotface", "Professor Putricide",
    "Blood Prince Council", "Blood-Queen Lana'thel",
    "Valithria Dreamwalker", "Sindragosa",
    "The Lich King",

    "Baltharus the Warborn", "Saviana Ragefire", "General Zarithrian", "Halion",

    "Northrend Beasts", "Lord Jaraxxus", "Faction Champions", "Twin Val'kyr", "Anub'arak",

    "Sartharion", "Onixia", "Malygos",
    "Archavon the Stone Watcher", "Emalon the Storm Watcher", "Koralon the Flame Watcher", "Toravon the Ice Watcher",
]

BOSSES_FROM_HTML = {
    "the-lich-king": "The Lich King",
    "halion": "Halion",
    "deathbringer-saurfang": "Deathbringer Saurfang",
    "festergut": "Festergut",
    "rotface": "Rotface",
    "professor-putricide": "Professor Putricide",
    "blood-queen-lanathel": "Blood-Queen Lana'thel",
    "sindragosa": "Sindragosa",
    "lord-marrowgar": "Lord Marrowgar",
    "lady-deathwhisper": "Lady Deathwhisper",
    "gunship-battle": "Gunship Battle",
    "blood-prince-council": "Blood Prince Council",
    "valithria-dreamwalker": "Valithria Dreamwalker",
    "northrend-beasts": "Northrend Beasts",
    "lord-jaraxxus": "Lord Jaraxxus",
    "faction-champions": "Faction Champions",
    "twin-valkyr": "Twin Val'kyr",
    "anubarak": "Anub'arak",
    "onyxia": "Onyxia",
    "malygos": "Malygos",
    "sartharion": "Sartharion",
    "baltharus-the-warborn": "Baltharus the Warborn",
    "general-zarithrian": "General Zarithrian",
    "saviana-ragefire": "Saviana Ragefire",
    "archavon-the-stone-watcher": "Archavon the Stone Watcher",
    "emalon-the-storm-watcher": "Emalon the Storm Watcher",
    "koralon-the-flame-watcher": "Koralon the Flame Watcher",
    "toravon-the-ice-watcher": "Toravon the Ice Watcher",
    "anubrekhan": "Anub'Rekhan",
    "grand-widow-faerlina": "Grand Widow Faerlina",
    "maexxna": "Maexxna",
    "noth-the-plaguebringer": "Noth the Plaguebringer",
    "heigan-the-unclean": "Heigan the Unclean",
    "loatheb": "Loatheb",
    "patchwerk": "Patchwerk",
    "grobbulus": "Grobbulus",
    "gluth": "Gluth",
    "thaddius": "Thaddius",
    "instructor-razuvious": "Instructor Razuvious",
    "gothik-the-harvester": "Gothik the Harvester",
    "the-four-horsemen": "The Four Horsemen",
    "sapphiron": "Sapphiron",
    "kelthuzad": "Kel'Thuzad",
    "flame-leviathan": "Flame Leviathan",
    "ignis-the-furnace-master": "Ignis the Furnace Master",
    "razorscale": "Razorscale",
    "xt-002-deconstructor": "XT-002 Deconstructor",
    "assembly-of-iron": "Assembly of Iron",
    "kologarn": "Kologarn",
    "auriaya": "Auriaya",
    "hodir": "Hodir",
    "thorim": "Thorim",
    "freya": "Freya",
    "mimiron": "Mimiron",
    "general-vezax": "General Vezax",
    "yogg-saron": "Yogg-Saron",
    "algalon-the-observer": "Algalon the Observer"
}

BOSSES_GUIDS = {
    "007995": "Archavon the Stone Watcher",
    "0084C9": "Emalon the Storm Watcher",
    "0088C5": "Koralon the Flame Watcher",
    "009621": "Toravon the Ice Watcher",

    "0070BB": "Malygos",
    "0070BC": "Sartharion",
    "0027C8": "Onyxia",

    "008F04": "Lord Marrowgar",
    "008FF7": "Lady Deathwhisper",
    "0092A4": "The Skybreaker",
    "00915F": "Orgrim's Hammer",
    "0093B5": "Deathbringer Saurfang",
    "008F12": "Festergut",
    "008F13": "Rotface",
    "008F46": "Professor Putricide",
    "009454": "Prince Keleseth",
    "009455": "Prince Taldaram",
    "009452": "Prince Valanar",
    "009443": "Blood-Queen Lana'thel",
    "008FB5": "Valithria Dreamwalker",
    # "0093EC": "Risen Archmage",
    "008FF5": "Sindragosa",
    "008EF5": "The Lich King",
    
    "009B42": "General Zarithrian",
    "009B43": "Saviana Ragefire",
    "009B47": "Baltharus the Warborn",
    "009BB7": "Halion",
    "009CD2": "Halion",
    
    "0087EC": "Gormok the Impaler",
    "008948": "Acidmaw",
    "0087EF": "Dreadscale",
    "0087ED": "Icehowl",
    "0087DC": "Lord Jaraxxus",
    "0086C0": "Eydis Darkbane",
    "0086C1": "Fjola Lightbane",
    "008704": "Anub'arak",
}

TOC_CHAMPIONS = {
    "00869D": "Tyrius Duskblade <DK>",
    "00869C": "Kavina Grovesong <Druid>",
    "0086A5": "Melador Valestrider <Druid>",
    "0086A3": "Alyssia Moonstalker <Hunter>",
    "0086A4": "Noozle Whizzlestick <Mage>",
    "0086A1": "Velanaa <Paladin>",
    "0086A7": "Baelnor Lightbearer <Paladin>",
    "0086A2": "Anthar Forgemender <Priest>",
    "0086A9": "Brienna Nightfell <Priest>",
    "0086A8": "Irieth Shadowstep <Rogue>",
    "00869F": "Shaabad <Shaman>",
    "0086A6": "Saamul <Shaman>",
    "0086AA": "Serissa Grimdabbler <Warlock>",
    "0086AB": "Shocuul <Warrior>",
    
    "00869A": "Gorgrim Shadowcleave <DK>",
    "008693": "Birana Stormhoof <Druid>",
    "00869B": "Erin Misthoof <Druid>",
    "008690": "Ruj'kah <Hunter>",
    "008691": "Ginselle Blightslinger <Mage>",
    "00868D": "Liandra Suncaller <Paladin>",
    "008698": "Malithas Brightblade <Paladin>",
    "00868F": "Caiphus the Stern <Priest>",
    "008689": "Vivienne Blackwhisper <Priest>",
    "008696": "Maz'dinah <Rogue>",
    "008697": "Broln Stouthorn <Shaman>",
    "00868C": "Thrakgar <Shaman>",
    "008692": "Harkzog <Warlock>",
    "008695": "Narrhok Steelbreaker <Warrior>",
}
BOSSES_GUIDS.update(TOC_CHAMPIONS)

MUTLIBOSSES = {
    "Halion": ['009BB7', '009CCE', '009CD2'],
    "Gunship": ['0092A4', '00915F'],
    "Blood Prince Council": ['009454', '009455', '009452'],
    "Northrend Beasts": ['0087EC', '008948', '0087EF', '0087ED'],
    "Faction Champions": list(TOC_CHAMPIONS),
    "Twin Val'kyr": ['0086C0', '0086C1'],
}

SPELLS_SCHOOLS = {
    0: "",
    1: "physical", #FFFF00   255, 255, 0
    2: "holy", ##FFE680   255, 230, 128
    4: "fire", ##FF8000   255, 128, 0
    8: "nature", ##4DFF4D   77, 255, 77
    16: "frost", ##80FFFF   128, 255, 255
    32: "shadow", ##8080FF   128, 128, 255
    64: "arcane", ##FF80FF   255, 128, 255
    3: "holystrike", #Holy + Physical
    5: "flamestrike", #-- Fire + Physical
    # 6: "holyfire", #-- Fire + Holy (Radiant)
    # 9: "stormstrike", #-- Nature + Physical
    # 10: "holystorm", #-- Nature + Holy
    12: "firestorm", #Nature + Fire
    17: "froststrike", #Frost + Physical
    # 18: "holyfrost", #-- Frost + Holy
    20: "frostfire", #Frost + Fire
    # 24: "froststorm", #-- Frost + Nature
    33: "shadowstrike", #Shadow + Physical
    34: "shadowlight", #Shadow + Holy
    # 36: "shadowflame", #-- Shadow + Fire
    40: "shadowstorm", #Shadow + Nature
    48: "shadowfrost", #Shadow + Frost
    # 65: "spellstrike", #-- Arcane + Physical
    66: "divine", #Arcane + Holy
    68: "spellfire", #-- Arcane + Fire
    # 72: "spellstorm", #-- Arcane + Nature
    80: "spellfrost", #-- Arcane + Frost
    96: "spellshadow", #Arcane + Shadow
    # 28: "elemental", #-- Frost + Nature + Fire
    # 124: "chromatic", #-- Arcane + Shadow + Frost + Nature + Fire
    # 126: "magic", #-- Arcane + Shadow + Frost + Nature + Fire + Holy
    127: "chaos", # Arcane + Shadow + Frost + Nature + Fire + Holy + Physical
}

UNUSUAL_SPELLS = {
    6: "holyfire", #-- Fire + Holy (Radiant)
    9: "stormstrike", #-- Nature + Physical
    10: "holystorm", #-- Nature + Holy
    18: "holyfrost", #-- Frost + Holy
    24: "froststorm", #-- Frost + Nature
    36: "shadowflame", #-- Shadow + Fire
    65: "spellstrike", #-- Arcane + Physical
    72: "spellstorm", #-- Arcane + Nature
    28: "elemental", #-- Frost + Nature + Fire
    124: "chromatic", #-- Arcane + Shadow + Frost + Nature + Fire
    126: "magic", #-- Arcane + Shadow + Frost + Nature + Fire + Holy
}

ENV_DAMAGE = {
    'FALLING': "90001",
    'LAVA': "90002",
    'DROWNING': "90003",
    'FIRE': "90004",
    'FATIGUE': "90005",
    'SLIME': "90006",
}


def sort_dict_by_value(d: dict):
    return dict(sorted(d.items(), key=lambda x: x[1], reverse=True))

def running_time(f):
    def inner(*args, **kwargs):
        st = perf_counter()
        q = f(*args, **kwargs)
        fin = int((perf_counter() - st) * 1000)
        print(f'[PERF]: Done in {fin:>6,} ms with {f.__module__}.{f.__name__}')
        return q
    return inner


@running_time
def json_read(path: str):
    if not path.endswith('.json'):
        path = f"{path}.json"
    print("[LOAD JSON]:", path)
    try:
        with open(path) as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

@running_time
def json_read_no_exception(path: str):
    if not path.endswith('.json'):
        path = f"{path}.json"
    print("[LOAD JSON]:", path)
    with open(path) as file:
        return json.load(file)

def json_write(path: str, data, indent=2):
    if not path.endswith('.json'):
        path = f"{path}.json"
    with open(path, 'w') as file:
        json.dump(data, file, default=sorted, indent=indent)


@running_time
def file_read(path: str):
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""

@running_time
def file_write(path: str, data: str):
    with open(path, 'w') as f:
        f.write(data)

@running_time
def bytes_write(path: str, data: bytes):
    with open(path, 'wb') as file:
        file.write(data)

@running_time
def bytes_read(path: str):
    try:
        with open(path, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        return b''

@running_time
def zlib_compress(__data, level=7):
    return zlib.compress(__data, level=level)

def pickle_dumps(data):
    return pickle.dumps(data)

@running_time
def zlib_pickle_write(data_raw, path: str):
    if not path.endswith('.pickle.zlib'):
        path = f"{path}.pickle.zlib"
    data_pickle = pickle_dumps(data_raw)
    comresesed = zlib_compress(data_pickle)
    bytes_write(path, comresesed)

@running_time
def zlib_text_write(data_raw: str, path: str, check_exists: bool=False):
    if not path.endswith('.zlib'):
        path = f"{path}.zlib"
    data_enc = data_raw.encode()
    comresesed = zlib_compress(data_enc)
    if not check_exists:
        bytes_write(path, comresesed)
        return
    old_data = bytes_read(path)
    exists = old_data == comresesed
    if not exists:
        bytes_write(path, comresesed)
    return exists

@running_time
def zlib_text_write_check_exists(data_raw: str, path: str):
    if not path.endswith('.zlib'):
        path = f"{path}.zlib"
    data_enc = data_raw.encode()
    comresesed = zlib_compress(data_enc)
    old_data = bytes_read(path)
    exists = old_data == comresesed
    if not exists:
        bytes_write(path, comresesed)
    return exists


@running_time
def zlib_decompress(data: bytes):
    return zlib.decompress(data)

@running_time
def pickle_from_bytes(data: bytes):
    return pickle.loads(data)

@running_time
def zlib_pickle_read(path: str):
    if not path.endswith('.pickle.zlib'):
        path = f"{path}.pickle.zlib"
    data_raw = bytes_read(path)
    data = zlib_decompress(data_raw)
    return pickle_from_bytes(data)

@running_time
def zlib_text_read(path: str):
    if not path.endswith('.zlib'):
        path = f"{path}.zlib"
    data_raw = bytes_read(path)
    data = zlib_decompress(data_raw)
    return data.decode()


@running_time
def logs_splitlines(logs: str):
    return logs.splitlines()

def pickle_read(path: str):
    if not path.endswith('.pickle'):
        path = f"{path}.pickle"
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print('[ERROR]: FILE DOESNT EXISTS:', path)

def pickle_write(path: str, data):
    if not path.endswith('.pickle'):
        path = f"{path}.pickle"
    with open(path, 'wb') as f:
        pickle.dump(data, f)



EXT_OPEN = {
    '.pickle': pickle_read,
    '.zlib': zlib_text_read,
    '.pickle.zlib': zlib_pickle_read,
    '.json': json_read,
}

def ext_strip(ext: str):
    return f".{ext.strip().strip('.')}"

def __open(path: str, ext: str):
    ext = ext_strip(ext)
    func = EXT_OPEN[ext]
    try:
        return func(path)
    except FileNotFoundError:
        if not path.endswith(ext):
            return __open(func, f"{path}{ext}")
        print('[ERROR]: FILE DOESNT EXISTS:', path)



def get_now():
    return datetime.now()

# Z = re.compile('(\d{1,2})/(\d{1,2}) (\d\d):(\d\d):(\d\d).(\d\d\d)')
def to_dt_closure():
    Z = re.compile('(\d+)')
    current = get_now()
    year = current.year
    month = current.month
    day = current.day
    def inner(s: str):
        q = list(map(int, Z.findall(s, endpos=18)))
        q[-1] *= 1000
        if q[0] > month or q[0] == month and q[1] > day:
            return datetime(year-1, *q)
        return datetime(year, *q)
    return inner

to_dt = to_dt_closure()

def get_time_delta(s: str, f: str):
    return to_dt(f) - to_dt(s)

def get_fight_duration(s, f):
    return get_time_delta(s, f).total_seconds()

def convert_duration(t):
    milliseconds = int(t % 1 * 1000)
    t = int(t)
    seconds = t % 60
    minutes = t // 60 % 60
    hours = t // 3600
    return f"{hours}:{minutes:0>2}:{seconds:0>2}.{milliseconds:0<3}"
    
def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print('[LOG]: Created folder:', path)

def get_folders(dir) -> list[str]:
    return next(os.walk(dir))[1]

def get_files(dir):
    return next(os.walk(dir))[2]

def get_all_files(folder=None, ext=None):
    if folder is None:
        folder = '.'
    files = next(os.walk(folder))[2]
    files = sorted(files)
    if ext is None:
        return files
    return [file for file in files if file.rsplit('.', 1)[-1] == ext]

    
def redo_data(redo_func, multi=True, startfrom=None, end=None):
    folders = get_folders('LogsDir')

    if startfrom:
        folders = folders[folders.index(startfrom):]
    if end:
        folders = folders[:folders.index(end)]
    
    if multi:
        from multiprocessing import Pool
        with Pool(6) as p:
            p.map(redo_func, folders)
    else:
        for x in folders:
            redo_func(x)


CLASSES = {
  "Death Knight": {
    "": "class_deathknight",
    "Blood": "spell_deathknight_bloodpresence",
    "Frost": "spell_deathknight_frostpresence",
    "Unholy": "spell_deathknight_unholypresence"
  },
  "Druid": {
    "": "class_druid",
    "Balance": "spell_nature_starfall",
    "Feral Combat": "ability_racial_bearform",
    "Restoration": "spell_nature_healingtouch"
  },
  "Hunter": {
    "": "class_hunter",
    "Beast Mastery": "ability_hunter_beasttaming",
    "Marksmanship": "ability_marksmanship",
    "Survival": "ability_hunter_swiftstrike"
  },
  "Mage": {
    "": "class_mage",
    "Arcane": "spell_holy_magicalsentry",
    "Fire": "spell_fire_firebolt02",
    "Frost": "spell_frost_frostbolt02"
  },
  "Paladin": {
    "": "class_paladin",
    "Holy": "spell_holy_holybolt",
    "Protection": "spell_holy_devotionaura",
    "Retribution": "spell_holy_auraoflight"
  },
  "Priest": {
    "": "class_priest",
    "Discipline": "spell_holy_wordfortitude",
    "Holy": "spell_holy_guardianspirit",
    "Shadow": "spell_shadow_shadowwordpain"
  },
  "Rogue": {
    "": "class_rogue",
    "Assassination": "ability_rogue_eviscerate",
    "Combat": "ability_backstab",
    "Subtlety": "ability_stealth"
  },
  "Shaman": {
    "": "class_shaman",
    "Elemental": "spell_nature_lightning",
    "Enhancement": "spell_nature_lightningshield",
    "Restoration": "spell_nature_magicimmunity"
  },
  "Warlock": {
    "": "class_warlock",
    "Affliction": "spell_shadow_deathcoil",
    "Demonology": "spell_shadow_metamorphosis",
    "Destruction": "spell_shadow_rainoffire"
  },
  "Warrior": {
    "": "class_warrior",
    "Arms": "ability_rogue_eviscerate",
    "Fury": "ability_warrior_innerrage",
    "Protection": "ability_warrior_defensivestance"
  }
}

CLASS_TO_HTML = {
    'Death Knight': 'death-knight',
    'Druid': 'druid',
    'Hunter': 'hunter',
    'Mage': 'mage',
    'Paladin': 'paladin',
    'Priest': 'priest',
    'Rogue': 'rogue',
    'Shaman': 'shaman',
    'Warlock': 'warlock',
    'Warrior': 'warrior'
}

CLASS_FROM_HTML = {
    "death-knight": "Death Knight",
    "druid": "Druid",
    "hunter": "Hunter",
    "mage": "Mage",
    "paladin": "Paladin",
    "priest": "Priest",
    "rogue": "Rogue",
    "shaman": "Shaman",
    "warlock": "Warlock",
    "warrior": "Warrior"
}


CLASSES_LIST = list(CLASSES)
# SPECS_LIST = {name: list(v) for name, v in CLASSES.items()}
# SPECS_LIST = [icon for v in CLASSES.values() for icon in v.values()]
SPECS_LIST = [(sname or cname, icon) for cname, v in CLASSES.items() for sname, icon in v.items()]




DATES_CACHE = {}

def get_dates():
    if not DATES_CACHE:
        dates = json_read("WarmaneBossFights/__dates")
        DATES_CACHE["DATES"] = dates
        DATES_CACHE["REVERSED"] = list(reversed(dates.items()))
    return DATES_CACHE

def find_date(report_id: int) -> str:
    dates: list[tuple[str, int]] = get_dates()["REVERSED"]
    for date, date_report_id in dates:
        if report_id > date_report_id:
            return date

