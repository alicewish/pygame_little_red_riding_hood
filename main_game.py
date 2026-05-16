import json
import random
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import imageio.v2 as imageio
import networkx as nx
import numpy as np
import pygame
import pyttsx3
from humanize import naturalsize, precisedelta
from loguru import logger
from more_itertools import chunked, windowed
from PIL import Image, ImageDraw, ImageFont
from prettytable import PrettyTable

from momofont_general_dev import get_target_filenames, kind2fontpaths, choose_light_font, choose_regular_font, \
    choose_bold_font, get_font_dirs, load_all_fonts_metadata

PY_PATH = Path(__file__).resolve()
IS_DEV = PY_PATH.stem.endswith('_dev')
IS_DUP = PY_PATH.stem.endswith('_dup')
DEBUG_MODE = False

SCRIPT_FILE_NAME = 'momogame_little_red_hood_dev.py'
SCRIPT_VERSION = '25.0.0'
SCRIPT_TITLE_EN = 'Little Red Riding Hood RPG: Hotel Conspiracy, Matchbox Prison, and Drawer Cell Deluxe'
SCRIPT_TITLE_CN = '小红帽RPG：酒店密谋、火柴盒监狱与抽屉囚室豪华版'

GITHUB_REPO_NAME = 'little-red-riding-hood-hotel-conspiracy-rpg'

WINDOW_TITLE = '小红帽RPG'
SAVE_FILE_NAME = 'little_red_hotel_conspiracy_matchbox_prison.save.json'
STORYLINE_OUTPUT_FILE_NAME = 'little_red_hotel_conspiracy_matchbox_prison_storyline.txt'
ORIGINAL_STORY_OUTPUT_FILE_NAME = 'little_red_riding_hood_original_story.txt'
FOUNTAIN_OUTPUT_FILE_NAME = 'little_red_hotel_conspiracy_matchbox_prison_screenplay.fountain'
RECORD_OUTPUT_FILE_NAME = 'little_red_hotel_conspiracy_matchbox_prison_autoplay.mp4'
PUBLISH_ICON_FILE_NAME = 'little_red_hotel_conspiracy_icon.png'
PUBLISH_COVER_FILE_NAME = 'little_red_hotel_conspiracy_cover.png'
SAVE_PATH = PY_PATH.with_name(SAVE_FILE_NAME)
STORYLINE_PATH = PY_PATH.with_name(STORYLINE_OUTPUT_FILE_NAME)
ORIGINAL_STORY_PATH = PY_PATH.with_name(ORIGINAL_STORY_OUTPUT_FILE_NAME)
FOUNTAIN_PATH = PY_PATH.with_name(FOUNTAIN_OUTPUT_FILE_NAME)
RECORD_PATH = PY_PATH.with_name(RECORD_OUTPUT_FILE_NAME)
PUBLISH_ICON_PATH = PY_PATH.with_name(PUBLISH_ICON_FILE_NAME)
PUBLISH_COVER_PATH = PY_PATH.with_name(PUBLISH_COVER_FILE_NAME)

font_dirs = get_font_dirs()
all_fonts_metadata = load_all_fonts_metadata(font_dirs)
kind = 'microsoft_yahei'
yahei_target_filenames = get_target_filenames(kind)
yahei_fonts_metadata = kind2fontpaths(font_dirs, yahei_target_filenames)
yahei_regular_font = choose_regular_font(yahei_fonts_metadata)
yahei_bold_font = choose_bold_font(yahei_fonts_metadata)
yahei_light_font = choose_light_font(yahei_fonts_metadata)

ENABLE_NON_CANON_SCENES = True
ENABLE_NON_CANON_CHARACTERS = True
ENABLE_NON_CANON_ITEMS = True
ENABLE_MEDIUM_IMPORTANCE_CONTENT = True
ENABLE_OPTIONAL_IMPORTANCE_CONTENT = True
ENABLE_SIDE_QUESTS = True
ENABLE_SHOP_SYSTEM = True
ENABLE_SOUND_EFFECTS = True
ENABLE_PARTICLES = True
ENABLE_ENDING_CG_BY_CHIEF = True
AUTO_PICKUP_REACHABLE_ITEMS_DEFAULT = True
RECORD_AUTO_PICKUP_REACHABLE_ITEMS_DEFAULT = False
AUTO_PLAY_REQUIRE_CHIEF_ENDING_CG = True
RECORD_STOP_WHEN_AUTO_PLAY_FINISHED = True

NORMAL_START_SKIP_ACTS_DEFAULT = 0
AUTO_PLAY_SKIP_ACTS_DEFAULT = 1
RECORD_SKIP_ACTS_DEFAULT = 2

VIEW_COLS = 20
VIEW_ROWS = 15
TILE = 32
VIEW_W = VIEW_COLS * TILE
VIEW_H = VIEW_ROWS * TILE
LEFT_BAR_W = 232
RIGHT_BAR_W = 300
MENU_BAR_H = 30
TOP_BAR_H = 72
STATUS_BAR_H = 34
BOTTOM_BAR_H = 104
VW = LEFT_BAR_W + VIEW_W + RIGHT_BAR_W
VH = TOP_BAR_H + VIEW_H + STATUS_BAR_H + BOTTOM_BAR_H
SCALE = 1
SCREEN_W = VW * SCALE
SCREEN_H = VH * SCALE
FPS = 60
PLAYER_MAX_HP = 72
AUTO_SPEEDS = [1, 2, 4, 8]
BATTLE_AUTO_FRAMES = 90
DIALOGUE_BASE_FRAMES = 110
DIALOGUE_CHAR_FRAMES = 3
SOUND_SAMPLE_RATE = 22050
SCROLL_STEP = 36
RECORD_ENDING_HOLD_FRAMES = 240
RECORD_ENABLE_VOICE = False
RECORD_AUTO_SPEED_INDEX = 3
TOOLTIP_MARGIN = 12
TOOLTIP_MAX_W = 360
TOOLTIP_PAD = 8

CONTROL_HINT = 'WASD/方向键移动  Space互动  P暂停  J札记  I背包  M地图  L图鉴  R指引线  O自动  T朗读  Y音效  V换装  G自动拾取  F5存档  F9读档'
BATTLE_HINT = '战斗：A攻击 H蜂蜜 D防御 B银铃 Q三问 F油灯 K清醒卡 S防烟布 W木哨'
JUDGEMENT_HINT = '灰狼处置：1囚禁并听他求饶  2放逐  O自动选择囚禁'
SCROLL_HINT = '长文本：鼠标滚轮 / PageUp / PageDown 滚动'

KEY_SAVE = pygame.K_F5
KEY_LOAD = pygame.K_F9
KEY_ESCAPE = pygame.K_ESCAPE
KEY_TOGGLE_VOICE = pygame.K_t
KEY_TOGGLE_SOUND = pygame.K_y
KEY_TOGGLE_AUTO_PLAY = pygame.K_o
KEY_OPEN_JOURNAL = pygame.K_j
KEY_OPEN_INVENTORY = pygame.K_i
KEY_OPEN_WORLD_MAP = pygame.K_m
KEY_OPEN_CODEX = pygame.K_l
KEY_OPEN_PAUSE = pygame.K_p
KEY_TOGGLE_HERO = pygame.K_v
KEY_TOGGLE_AUTO_PICKUP = pygame.K_g
KEY_TOGGLE_PATH_HINT = pygame.K_r
KEY_RESTART = pygame.K_r
KEY_SCROLL_UP = pygame.K_PAGEUP
KEY_SCROLL_DOWN = pygame.K_PAGEDOWN

KEYS_CONFIRM = (pygame.K_RETURN, pygame.K_SPACE)
KEYS_TITLE_START = (pygame.K_RETURN, pygame.K_SPACE)
KEYS_DIALOGUE_ADVANCE = (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE)
KEYS_PANEL_CLOSE = (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_p)
KEYS_SHOP_CLOSE = (pygame.K_ESCAPE, pygame.K_p, pygame.K_RETURN, pygame.K_SPACE)
KEYS_PAUSE_CLOSE = (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE)
KEYS_MOVE_LEFT = (pygame.K_LEFT, pygame.K_a)
KEYS_MOVE_RIGHT = (pygame.K_RIGHT, pygame.K_d)
KEYS_MOVE_UP = (pygame.K_UP, pygame.K_w)
KEYS_MOVE_DOWN = (pygame.K_DOWN, pygame.K_s)

AUTO_SPEED_INDEX_BY_KEY = {
    pygame.K_1: 0,
    pygame.K_2: 1,
    pygame.K_3: 2,
    pygame.K_4: 3,
}
SHOP_BUY_INDEX_BY_KEY = {
    pygame.K_1: 0,
    pygame.K_2: 1,
    pygame.K_3: 2,
    pygame.K_4: 3,
    pygame.K_5: 4,
}
SHOP_SELL_INDEX_BY_KEY = {
    pygame.K_7: 0,
    pygame.K_8: 1,
    pygame.K_9: 2,
}
BATTLE_ACTION_BY_KEY = {
    pygame.K_a: 'attack',
    pygame.K_RETURN: 'attack',
    pygame.K_SPACE: 'attack',
    pygame.K_h: 'heal',
    pygame.K_d: 'defend',
    pygame.K_b: 'bell',
    pygame.K_q: 'question',
    pygame.K_f: 'lamp',
    pygame.K_k: 'card',
    pygame.K_s: 'cloth',
    pygame.K_w: 'whistle',
}
JUDGEMENT_CHOICE_BY_KEY = {
    pygame.K_1: 'cage',
    pygame.K_2: 'exile',
}
CONTROL_TABLE_ROWS = [
    ['方向键 / WASD', '移动当前主视角角色'],
    ['Space / Enter', '互动、推进对白、战斗普通攻击'],
    ['鼠标左键', '点击菜单、按钮、战斗动作、商店按钮和标题起始幕按钮'],
    ['鼠标滚轮 / PageUp / PageDown', '滚动长文本面板'],
    ['P / Esc', '暂停或返回'],
    ['J / I / M / L', '打开札记、背包、世界地图、图鉴'],
    ['G', '切换自动拾取当前地图所有可达物品'],
    ['R', '切换非自动模式寻路指示线'],
    ['O', '开启、暂停或恢复自动游玩'],
    ['1 / 2 / 3 / 4', '自动对白速度；商店买入；处置界面选择'],
    ['5', '商店中购买木哨'],
    ['7 / 8 / 9', '商店中卖出蜂蜜、野花、防烟布'],
    ['T', '开启或关闭台词朗读'],
    ['Y', '开启或关闭音效'],
    ['V', '探索中切换小红帽形象'],
    ['F5 / F9', '保存游戏 / 读取游戏'],
    ['A / H / D', '战斗中攻击、蜂蜜恢复、防御'],
    ['B / Q / F / K / S / W', '战斗中使用银铃、三问、油灯、清醒卡、防烟布、木哨'],
]

C_BLACK = (15, 13, 18)
C_WHITE = (240, 240, 228)
C_CREAM = (249, 229, 184)
C_RED = (196, 38, 48)
C_DARK_RED = (113, 22, 33)
C_BROWN = (101, 67, 40)
C_DARK_BROWN = (58, 40, 28)
C_GREEN = (54, 128, 72)
C_DARK_GREEN = (30, 85, 54)
C_LIGHT_GREEN = (107, 168, 88)
C_BLUE = (58, 98, 170)
C_PURPLE = (102, 69, 143)
C_GRAY = (97, 105, 116)
C_DARK_GRAY = (48, 52, 64)
C_YELLOW = (235, 197, 83)
C_ORANGE = (221, 126, 52)
C_SKIN = (238, 183, 137)
C_PATH = (168, 127, 74)
C_PALE = (232, 229, 183)
C_SILVER = (190, 200, 210)
C_PANEL = (20, 18, 24)
C_PANEL_DARK = (12, 10, 16)
C_PANEL_LINE = (74, 63, 75)
C_GOLD = (222, 181, 82)
C_ROUTE = (230, 230, 150)
C_LOCKED = (102, 69, 143)
C_BUTTON = (48, 42, 58)
C_BUTTON_LINE = (112, 94, 118)
C_BUTTON_HOVER = (72, 58, 88)
C_TOOLTIP_BG = (10, 9, 14)
C_TOOLTIP_LINE = (235, 197, 83)

IMPORTANCE_MANDATORY = '必需'
IMPORTANCE_CORE = '核心'
IMPORTANCE_HIGH = '高'
IMPORTANCE_MEDIUM = '中'
IMPORTANCE_OPTIONAL = '可选'
IMPORTANCE_LEVELS = [
    IMPORTANCE_MANDATORY,
    IMPORTANCE_CORE,
    IMPORTANCE_HIGH,
    IMPORTANCE_MEDIUM,
    IMPORTANCE_OPTIONAL,
]

TIME_OF_DAY_SPECS = {
    'morning': {'name': '清晨', 'overlay': (250, 216, 140, 18)},
    'day': {'name': '白天', 'overlay': (255, 255, 255, 0)},
    'dusk': {'name': '黄昏', 'overlay': (190, 90, 55, 42)},
    'night': {'name': '黑夜', 'overlay': (18, 28, 82, 78)},
    'deep_night': {'name': '深夜', 'overlay': (8, 12, 55, 104)},
    'dawn': {'name': '黎明', 'overlay': (230, 175, 120, 26)},
}

MATCHBOX_PRISON_SECRET_LINES = [
    '火柴盒监狱不是普通牢房，而是可以像火柴盒内胆一样抽拉的隐藏结构。',
    '艾琳只知道自己有私人监狱，不知道囚室能被拉进墙体深处。',
    '艾琳的俊美男卧底维克托也不知道结构秘密，所以他以为把人送进去后外侧空牢就是普通空牢。',
    '露比和莱昂知道抽拉结构：囚室被推入内层后，从走廊外面看起来像空囚室，真实囚室藏在墙体深处。',
    '莱昂救援时利用艾琳丢下的钥匙和抽屉式结构，把一格一格的囚室拉回可逃脱位置。',
]
MATCHBOX_PRISON_SECRET_TEXT = '\n'.join(MATCHBOX_PRISON_SECRET_LINES)

MAPS = {
    'home': [
        '####################',
        '#..................#',
        '#..bbb.......tt....#',
        '#..b.b.......t.....#',
        '#..................#',
        '#.....rrrr.........#',
        '#.....r..r.........#',
        '#.....rrrr.........#',
        '#............sss...#',
        '#............s.s...#',
        '#..................#',
        '#..................#',
        '#.........P........#',
        '#.........D........#',
        '##########D#########',
    ],
    'village': [
        '##########D#########',
        '#..H..P.....P..H...#',
        '#..H..P..S..P..H...#',
        '#.....P.....P......#',
        '#..bbbb..P..rrrr...#',
        '#..b..b..P..r..r...#',
        '#..bbbb..P..rrrr...#',
        'D........P.........D',
        '#..tt....P.....ss..#',
        '#..tt....P.....s.s.#',
        '#........P.........#',
        '#..H..P.....P..H...#',
        '#.....P.....P......#',
        '#........P.........#',
        '##########D#########',
    ],
    'forest': [
        '##########D#########',
        '#GGGGGGGGP.GGGGGGGG#',
        '#GGG.....P.....GGGG#',
        '#GG..XXX.P.XXX..GGG#',
        '#G...X.......X....G#',
        '#....X.......X.....#',
        '#....XXX...XXX.....#',
        'D.........P........D',
        '#..GGG.....P..GG...#',
        '#..G.......P...G...#',
        '#..........P.......#',
        '#GG....GG..P....GGG#',
        '#GGGG......P.....GG#',
        '#GGGGGGGG..P..GGGGG#',
        '##########D#########',
    ],
    'cottage': [
        '##########D#########',
        '#..................#',
        '#..bbbb............#',
        '#..b..b............#',
        '#..bbbb............#',
        '#..................#',
        '#............wwww..#',
        'D............w..w..D',
        '#............wwww..#',
        '#..................#',
        '#......tt..........#',
        '#......tt..........#',
        '#..................#',
        '#.........D........#',
        '##########D#########',
    ],
    'cage_yard': [
        '##########D#########',
        '#GGGG....P....GGGGG#',
        '#G..G....P....G...G#',
        '#........P.........#',
        '#..AAAA..P..AAAA...#',
        '#..A..A..P..A..A...#',
        '#..AAAA..P..AAAA...#',
        'D........P.........D',
        '#........P.........#',
        '#..AAAA..P..AAAA...#',
        '#..A..A..P..A..A...#',
        '#..AAAA..P..AAAA...#',
        '#........P.........#',
        '#GGGG....P....GGGGG#',
        '##########D#########',
    ],
    'winter_street': [
        '##########D#########',
        '#..................#',
        '#..SSS......LLL....#',
        '#..S.S......L.L....#',
        '#..................#',
        '#.....PPPPPP.......#',
        '#.....P....P.......#',
        'D.....P....P.......D',
        '#.....PPPPPP.......#',
        '#..................#',
        '#..GGGG......MMMM..#',
        '#..G..G......M..M..#',
        '#..................#',
        '#.........D........#',
        '##########D#########',
    ],
    'whisper_hotel': [
        '##########D#########',
        '#........P.........#',
        '#..HHH......HHH....#',
        '#..H.H......H.H....#',
        '#..................#',
        '#....tt....tt......#',
        '#....t......t......#',
        'D........P.........D',
        '#..................#',
        '#..bbb......bbb....#',
        '#..b.b......b.b....#',
        '#..................#',
        '#........P.........#',
        '#........D.........#',
        '##########D#########',
    ],
    'matchbox_prison': [
        '####################',
        '#........P.........#',
        '#..AAAA..P..AAAA...#',
        '#..A..A..P..A..A...#',
        '#..AAAA..P..AAAA...#',
        '#..................#',
        '#..MMMM..P..MMMM...#',
        '#..M..M..P..M..M...D',
        '#..MMMM..P..MMMM...#',
        '#..................#',
        '#..AAAA..P..AAAA...#',
        '#..A..A..P..A..A...#',
        '#..AAAA..P..AAAA...#',
        '#........D.........#',
        '##########D#########',
    ],
    'match_market': [
        '##########D#########',
        '#..................#',
        '#..SSS......SSS....#',
        '#..S.S......S.S....#',
        '#..................#',
        '#.....PPPPPP.......#',
        '#.....P....P.......#',
        'D.....P....P.......D',
        '#.....PPPPPP.......#',
        '#..................#',
        '#..mmmm......mmmm..#',
        '#..m..m......m..m..#',
        '#..................#',
        '#.........D........#',
        '##########D#########',
    ],
    'royal_square': [
        '##########D#########',
        '#..................#',
        '#..MMMM......MMMM..#',
        '#..M..M......M..M..#',
        '#..................#',
        '#.....PPPPPP.......#',
        '#.....P....P.......#',
        'D.....P....P.......D',
        '#.....PPPPPP.......#',
        '#..................#',
        '#..SSS......SSS....#',
        '#..S.S......S.S....#',
        '#..................#',
        '#........D.........#',
        '##########D#########',
    ],
}

SCENE_META = {
    'home': {'name': '妈妈的小屋', 'canon': True, 'system': False, 'intent': '第一幕出发点，建立妈妈叮嘱与篮子任务', 'importance': IMPORTANCE_MANDATORY, 'location_type': 'INT', 'default_time_key': 'morning'},
    'village': {'name': '森林村口', 'canon': False, 'system': True, 'intent': '商店、补给、村长和结局 CG 入口', 'importance': IMPORTANCE_HIGH, 'location_type': 'EXT', 'default_time_key': 'day'},
    'forest': {'name': '森林小路', 'canon': True, 'system': False, 'intent': '第二幕灰狼第一次诱导小红帽，并引入猎人银铃', 'importance': IMPORTANCE_CORE, 'location_type': 'EXT', 'default_time_key': 'day'},
    'cottage': {'name': '外婆的小屋', 'canon': True, 'system': False, 'intent': '第三幕假外婆揭露、大灰狼最终战和下半部悲剧触发点', 'importance': IMPORTANCE_MANDATORY, 'location_type': 'INT', 'default_time_key': 'dusk'},
    'cage_yard': {'name': '灰狼囚笼院', 'canon': False, 'system': False, 'intent': '第四幕战后处置灰狼，听灰狼求饶', 'importance': IMPORTANCE_CORE, 'location_type': 'EXT', 'default_time_key': 'night'},
    'winter_street': {'name': '雪夜街口', 'canon': False, 'system': False, 'intent': '第五幕听见关于艾琳店铺和蓝色火柴的闲言碎语', 'importance': IMPORTANCE_CORE, 'location_type': 'EXT', 'default_time_key': 'night'},
    'whisper_hotel': {'name': '密语酒店', 'canon': False, 'system': False, 'intent': '第六幕多位 NPC 参加反对艾琳的密会，随后被男性俊美卧底维克托暴露', 'importance': IMPORTANCE_CORE, 'location_type': 'INT', 'default_time_key': 'night'},
    'matchbox_prison': {'name': '火柴盒监狱', 'canon': False, 'system': False, 'intent': '第七幕艾琳视角巡视私人监狱；第八幕莱昂利用结构和钥匙救出小红帽', 'importance': IMPORTANCE_CORE, 'location_type': 'INT', 'default_time_key': 'deep_night'},
    'match_market': {'name': '火柴总店街', 'canon': False, 'system': False, 'intent': '第九幕十几个卖火柴店铺被红斗篷同时袭击', 'importance': IMPORTANCE_CORE, 'location_type': 'EXT', 'default_time_key': 'dawn'},
    'royal_square': {'name': '王城火柴广场', 'canon': False, 'system': False, 'intent': '第十幕国王和军队谴责艾琳，开启最终战并发现艾琳结局', 'importance': IMPORTANCE_MANDATORY, 'location_type': 'EXT', 'default_time_key': 'dawn'},
}
SCENE_NAMES = {}
for scene_key, scene_meta in SCENE_META.items():
    SCENE_NAMES[scene_key] = scene_meta['name']
SCENE_ORDER = [
    'home',
    'village',
    'forest',
    'cottage',
    'cage_yard',
    'winter_street',
    'whisper_hotel',
    'matchbox_prison',
    'match_market',
    'royal_square',
]

TILE_SPECS = {
    '.': {'name': '泥地', 'blocking': False, 'color': (128, 91, 63), 'intent': '普通可走地面'},
    'G': {'name': '草丛', 'blocking': False, 'color': C_GREEN, 'intent': '森林可走地面'},
    'P': {'name': '小路', 'blocking': False, 'color': C_PATH, 'intent': '主路径'},
    '#': {'name': '树墙', 'blocking': True, 'color': C_DARK_GREEN, 'intent': '边界阻挡'},
    'D': {'name': '木门', 'blocking': False, 'color': (126, 81, 49), 'intent': '单格传送门'},
    'H': {'name': '旅店墙', 'blocking': True, 'color': (62, 72, 88), 'intent': '酒店或村庄阻挡'},
    'M': {'name': '石墙', 'blocking': True, 'color': (72, 72, 88), 'intent': '石柱或建筑阻挡，也可作为火柴盒监狱外壳'},
    'S': {'name': '市场摊位', 'blocking': False, 'color': (172, 112, 62), 'intent': '市场提示'},
    'b': {'name': '柜子', 'blocking': True, 'color': (95, 60, 38), 'intent': '室内家具：柜子'},
    'r': {'name': '床铺', 'blocking': True, 'color': (142, 54, 42), 'intent': '室内家具：床'},
    's': {'name': '椅子', 'blocking': True, 'color': (111, 87, 65), 'intent': '室内家具：椅子'},
    't': {'name': '餐桌', 'blocking': True, 'color': (105, 66, 42), 'intent': '室内家具：餐桌'},
    'w': {'name': '窗帘', 'blocking': True, 'color': (83, 63, 86), 'intent': '室内家具：窗帘'},
    'L': {'name': '路灯', 'blocking': True, 'color': (80, 98, 72), 'intent': '雪夜街口照明阻挡'},
    'A': {'name': '铁栅栏', 'blocking': True, 'color': (84, 84, 94), 'intent': '囚笼或监狱阻挡'},
    'X': {'name': '荆棘影', 'blocking': True, 'color': (50, 78, 52), 'intent': '灰狼留下的阻挡'},
    'm': {'name': '火柴木箱', 'blocking': True, 'color': (80, 58, 44), 'intent': '火柴箱子阻挡'},
}
BLOCKING_TILES = set()
TILE_COLORS = {}
for tile_key, tile_spec in TILE_SPECS.items():
    if tile_spec['blocking']:
        BLOCKING_TILES.add(tile_key)
    TILE_COLORS[tile_key] = tile_spec['color']

CHARACTER_PROFILES = {
    'red': {'name': '露比', 'title': '小红帽', 'pixel_role': 'red', 'portrait_role': 'red', 'language_style': '先观察、再发问，句子短而清醒，关键时会用妈妈教的三问拆穿谎言。', 'bio': '穿红斗篷的女孩，带着面包、蜂蜜和红缎带去看外婆，后来卷入艾琳致幻性火柴事件，并知道火柴盒监狱的抽拉结构。', 'personality': '善良但不盲信，害怕时会把恐惧变成问题和行动。'},
    'mother': {'name': '玛莲娜', 'title': '妈妈', 'pixel_role': 'mother', 'portrait_role': 'mother', 'language_style': '温柔、坚定，常用生活化比喻提醒孩子保持清醒。', 'bio': '露比的妈妈，交给她篮子，也教给她识破伪装的三个问题。', 'personality': '保护欲强，谨慎，重视边界和事实。'},
    'merchant': {'name': '露塔', 'title': '村口行商', 'pixel_role': 'merchant', 'portrait_role': 'merchant', 'language_style': '像市场摊主一样直接，喜欢把风险说成账本。', 'bio': '森林村口的行商，提供蜂蜜、野花、防烟布、面包和木哨。', 'personality': '现实、精明，但愿意帮助准备出发的孩子。'},
    'chief': {'name': '奥伦', 'title': '村长', 'pixel_role': 'chief', 'portrait_role': 'chief', 'language_style': '像讲村史一样说话，重视证词、秩序和公共记忆。', 'bio': '村口的长者，在危机结束后为露比开启结局 CG。', 'personality': '稳重、善于总结，愿意把个人痛苦变成村庄教训。'},
    'wolf': {'name': '格雷姆', 'title': '灰狼', 'pixel_role': 'wolf', 'portrait_role': 'wolf', 'language_style': '前期假装礼貌，暴露后夸张、饥饿、带威胁感。', 'bio': '学会模仿亲人声音的灰狼，上半部核心反派。', 'personality': '贪婪、狡猾、怕被看穿，失败后会求饶。'},
    'hunter': {'name': '伊沃', 'title': '猎人', 'pixel_role': 'hunter', 'portrait_role': 'hunter', 'language_style': '简短、可靠，习惯把危险说成痕迹、路线和工具。', 'bio': '原著救援者，也给露比银铃、油灯和清醒卡片。', 'personality': '沉着、守护型，行动比语言更多。'},
    'grandma': {'name': '阿黛拉', 'title': '外婆', 'pixel_role': 'grandma', 'portrait_role': 'grandma', 'language_style': '虚弱、诚实，讲真相时带着悔意和告别感。', 'bio': '露比的外婆，受到艾琳蓝色火柴幻觉伤害。', 'personality': '慈爱、脆弱、最终选择说出真相。'},
    'newspaper_boy': {'name': '尼克', 'title': '报童', 'pixel_role': 'boy', 'portrait_role': 'boy', 'language_style': '急促、街头化，经常用“号外”开头。', 'bio': '雪夜街口的报童，知道艾琳店铺和密语酒店的传闻。', 'personality': '机灵、胆小但消息灵通。'},
    'resistance_leader': {'name': '瑟琳', 'title': '反对势力领袖', 'pixel_role': 'resistance', 'portrait_role': 'resistance', 'language_style': '低声、计划感强，常提路线、名单和同时行动。', 'bio': '在密语酒店组织反击艾琳火柴店铺的人。', 'personality': '果断、隐忍、愿意冒险。'},
    'hotel_keeper': {'name': '贝尔纳', 'title': '密语酒店掌柜', 'pixel_role': 'merchant', 'portrait_role': 'merchant', 'language_style': '表面像普通掌柜，实际每句话都在确认暗号和风险。', 'bio': '把酒店后厅借给反对势力的人，负责观察门口是否有艾琳的人。', 'personality': '谨慎、圆滑、把恐惧藏在账本后。'},
    'resistance_scout': {'name': '卡萝', 'title': '红斗篷侦察员', 'pixel_role': 'red_cloak', 'portrait_role': 'red_cloak', 'language_style': '短句、低声、总是先说方位和人数。', 'bio': '密语酒店里的侦察员，负责确认十几个店铺的出口和换装路线。', 'personality': '专注、敏捷、行动优先。'},
    'secret_medic': {'name': '梅琳', 'title': '秘密药师', 'pixel_role': 'grandma', 'portrait_role': 'grandma', 'language_style': '冷静、细致，喜欢把烟、药、火和症状拆开说。', 'bio': '研究蓝色火柴烟雾的人，准备给红斗篷们防烟布。', 'personality': '理性、耐心、对受害者很温柔。'},
    'spy': {'name': '维克托', 'title': '俊美男卧底', 'pixel_role': 'spy', 'portrait_role': 'spy', 'language_style': '礼貌、优雅、带一点危险的笑意，揭露身份时像在朗读舞台台词。', 'bio': '艾琳安插在密语酒店的男性俊美青年。他知道艾琳有私人监狱，却不知道囚室可以像火柴盒一样抽拉。', 'personality': '冷静、迷人、表演欲强，服从艾琳但低估了露比和莱昂。'},
    'aileen': {'name': '艾琳', 'title': '蓝火柴店主', 'pixel_role': 'aileen', 'portrait_role': 'aileen', 'language_style': '骄傲、强势，常把昔日贫穷和卑微说成自己统治别人的理由。', 'bio': '曾经贫穷到在雪夜里卑微卖火柴的小女孩，如今掌握蓝色火柴店铺和私人监狱；她害怕再次低头，所以把致幻性火柴包装成慈悲，把控制包装成救赎。', 'personality': '强势、偏执、骄傲，内心深处害怕重新变回那个没人看见的穷孩子。'},
    'blond_friend': {'name': '莱昂', 'title': '金发贫嘴男', 'pixel_role': 'blond_friend', 'portrait_role': 'blond_friend', 'language_style': '嘴上轻佻、动作很快，喜欢用玩笑缓解危险。', 'bio': '露比旅途中遇见的朋友，金发、贫嘴，但在关键时刻捡起钥匙打开牢门，并知道火柴盒监狱的抽拉秘密。', 'personality': '外表散漫，内心可靠，越紧张越爱吐槽。'},
    'red_cloak': {'name': '托马', 'title': '红斗篷传信人', 'pixel_role': 'red_cloak', 'portrait_role': 'red_cloak', 'language_style': '像暗号一样简洁，句子里常有数量、标记和路线。', 'bio': '反对势力成员，报告十几个火柴店铺被同时袭击。', 'personality': '谨慎、忠诚、执行力强。'},
    'king': {'name': '埃德蒙', 'title': '国王', 'pixel_role': 'king', 'portrait_role': 'king', 'language_style': '正式、法律化，习惯用罪名、证词和命令说话。', 'bio': '带军队在王城火柴广场谴责艾琳的人。', 'personality': '威严、重秩序，愿意在证据充分时行动。'},
    'blue_match_messenger': {'name': '莉雅', 'title': '蓝火柴信使', 'pixel_role': 'red_cloak', 'portrait_role': 'red_cloak', 'language_style': '汇报时紧张而短促，习惯先说数量再说危险。', 'bio': '艾琳店铺的信使，把十几个店铺同时被袭击的消息带进监狱。', 'personality': '慌张、服从命令、害怕艾琳发怒。'},
}

ACTOR_SPECS = {
    'red': {'role': 'red', 'profile_key': 'red'},
    'aileen': {'role': 'aileen', 'profile_key': 'aileen'},
    'blond_friend': {'role': 'blond_friend', 'profile_key': 'blond_friend'},
}

HERO_VARIANTS = [
    {'key': 'classic', 'name': '经典红斗篷', 'desc': '均衡，最接近童话印象。', 'attack_bonus': 0, 'defense_bonus': 0, 'kindness_bonus': 0},
    {'key': 'scarlet', 'name': '猩红短披风', 'desc': '更勇敢，普通攻击略强。', 'attack_bonus': 2, 'defense_bonus': 0, 'kindness_bonus': 0},
    {'key': 'berry', 'name': '莓红软帽', 'desc': '更亲近森林，善意和清醒更突出。', 'attack_bonus': 0, 'defense_bonus': 0, 'kindness_bonus': 1},
    {'key': 'snow', 'name': '雪边红斗篷', 'desc': '更谨慎，受到伤害略低。', 'attack_bonus': 0, 'defense_bonus': 2, 'kindness_bonus': 0},
]

START_ACT_OPTIONS = [
    {'skip_acts': 0, 'title': '第一幕：红斗篷出发', 'scene': 'home', 'note': '从妈妈的小屋和第一段对白开始。'},
    {'skip_acts': 1, 'title': '第二幕：森林小路与灰狼诱导', 'scene': 'forest', 'note': '跳过出发教学，直接调查灰狼。'},
    {'skip_acts': 2, 'title': '第三幕：外婆小屋与灰狼最终战', 'scene': 'cottage', 'note': '跳过森林前置，直接进入假外婆段落。'},
    {'skip_acts': 3, 'title': '第四幕：灰狼囚笼与外婆真相', 'scene': 'cage_yard', 'note': '跳过灰狼战，直接处理灰狼与外婆真相。'},
    {'skip_acts': 4, 'title': '第五幕：雪夜街口与蓝火柴传闻', 'scene': 'winter_street', 'note': '从艾琳线索的街口调查开始。'},
    {'skip_acts': 5, 'title': '第六幕：密语酒店多 NPC 密会与男卧底暴露', 'scene': 'whisper_hotel', 'note': '直接进入酒店密会，多位 NPC 在场，维克托暴露身份。'},
    {'skip_acts': 6, 'title': '第七幕：艾琳视角的火柴盒监狱', 'scene': 'matchbox_prison', 'note': '直接切换到艾琳视角巡视监狱；她不知道囚室的火柴盒抽拉结构。'},
    {'skip_acts': 7, 'title': '第八幕：莱昂救援与牢门打开', 'scene': 'matchbox_prison', 'note': '直接切换到莱昂视角，利用钥匙和火柴盒抽拉结构救人。'},
    {'skip_acts': 8, 'title': '第九幕：火柴总店街与红斗篷袭击', 'scene': 'match_market', 'note': '直接调查十几个店铺被袭击的结果。'},
    {'skip_acts': 9, 'title': '第十幕：王城火柴广场与艾琳结局', 'scene': 'royal_square', 'note': '直接进入国王、军队和艾琳最终战。'},
    {'skip_acts': 10, 'title': '第十一幕：村口灯与结局 CG', 'scene': 'village', 'note': '跳到艾琳危机结束后，找村长开启结局 CG。'},
]
MAX_START_SKIP_ACTS = len(START_ACT_OPTIONS) - 1

MENU_BUTTONS = [
    {'label': '札记 J', 'action': 'open_journal', 'tooltip': '区域：顶部菜单按钮｜代码定位：MENU_BUTTONS / handle_button_action / draw_menu_bar'},
    {'label': '背包 I', 'action': 'open_inventory', 'tooltip': '区域：顶部菜单按钮｜代码定位：MENU_BUTTONS / handle_button_action / draw_menu_bar'},
    {'label': '地图 M', 'action': 'open_map', 'tooltip': '区域：顶部菜单按钮｜代码定位：MENU_BUTTONS / handle_button_action / draw_menu_bar'},
    {'label': '图鉴 L', 'action': 'open_codex', 'tooltip': '区域：顶部菜单按钮｜代码定位：MENU_BUTTONS / handle_button_action / draw_menu_bar'},
    {'label': '暂停 P', 'action': 'open_pause', 'tooltip': '区域：顶部菜单按钮｜代码定位：MENU_BUTTONS / handle_button_action / draw_menu_bar'},
    {'label': '自动 O', 'action': 'toggle_auto', 'tooltip': '区域：顶部菜单按钮｜代码定位：toggle_auto_play / update_auto_play'},
    {'label': '提示', 'action': 'toggle_tooltip', 'tooltip': '区域：顶部菜单按钮｜代码定位：toggle_tooltip / current_tooltip_text / draw_tooltip'},
    {'label': '存档 F5', 'action': 'save', 'tooltip': '区域：顶部菜单按钮｜代码定位：save_game_state'},
]

PORTAL_BLUEPRINTS = [
    {'scene': 'home', 'point': (10, 14), 'to_scene': 'village', 'to_x': 10, 'to_y': 1, 'required_flag': 'got_basket', 'missing_text': '妈妈还没有把篮子交给你。先和妈妈说话吧。', 'canon': False, 'system': True, 'importance': IMPORTANCE_HIGH},
    {'scene': 'village', 'point': (10, 0), 'to_scene': 'home', 'to_x': 10, 'to_y': 13, 'required_flag': None, 'missing_text': '', 'canon': False, 'system': True, 'importance': IMPORTANCE_HIGH},
    {'scene': 'village', 'point': (19, 7), 'to_scene': 'forest', 'to_x': 1, 'to_y': 7, 'required_flag': 'mother_hint', 'missing_text': '森林很会说谎。先回想妈妈教你的三问规则。', 'canon': False, 'system': False, 'importance': IMPORTANCE_HIGH},
    {'scene': 'forest', 'point': (0, 7), 'to_scene': 'village', 'to_x': 18, 'to_y': 7, 'required_flag': None, 'missing_text': '', 'canon': False, 'system': False, 'importance': IMPORTANCE_HIGH},
    {'scene': 'forest', 'point': (19, 7), 'to_scene': 'cottage', 'to_x': 1, 'to_y': 7, 'required_flag': 'met_hunter', 'missing_text': '去外婆家的路很危险。先找到猎人取得银铃。', 'canon': True, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'cottage', 'point': (0, 7), 'to_scene': 'forest', 'to_x': 18, 'to_y': 7, 'required_flag': None, 'missing_text': '', 'canon': True, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'cottage', 'point': (10, 14), 'to_scene': 'cage_yard', 'to_x': 10, 'to_y': 1, 'required_flag': 'wolf_caged', 'missing_text': '只有决定囚禁灰狼后，囚笼院才会打开。', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'cage_yard', 'point': (10, 0), 'to_scene': 'cottage', 'to_x': 10, 'to_y': 13, 'required_flag': None, 'missing_text': '', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'cottage', 'point': (19, 7), 'to_scene': 'winter_street', 'to_x': 1, 'to_y': 7, 'required_flag': 'chapter_two_started', 'missing_text': '外婆的小屋还没有出现通往雪夜街口的线索。先和外婆说话。', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'winter_street', 'point': (0, 7), 'to_scene': 'cottage', 'to_x': 18, 'to_y': 7, 'required_flag': None, 'missing_text': '', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'winter_street', 'point': (19, 7), 'to_scene': 'whisper_hotel', 'to_x': 1, 'to_y': 7, 'required_flag': 'heard_gossip', 'missing_text': '雪夜街口的人还没说出密语酒店的方向。先问报童。', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'whisper_hotel', 'point': (0, 7), 'to_scene': 'winter_street', 'to_x': 18, 'to_y': 7, 'required_flag': None, 'missing_text': '', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'matchbox_prison', 'point': (19, 7), 'to_scene': 'match_market', 'to_x': 1, 'to_y': 7, 'required_flag': 'prison_escaped', 'missing_text': '牢门还没有打开。等莱昂捡起钥匙，利用火柴盒抽拉结构救你。', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'match_market', 'point': (0, 7), 'to_scene': 'matchbox_prison', 'to_x': 18, 'to_y': 7, 'required_flag': None, 'missing_text': '', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'match_market', 'point': (19, 7), 'to_scene': 'royal_square', 'to_x': 1, 'to_y': 7, 'required_flag': 'shop_attacks_reported', 'missing_text': '还不知道红斗篷袭击店铺的计划结果。先调查火柴总店街。', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'royal_square', 'point': (0, 7), 'to_scene': 'match_market', 'to_x': 18, 'to_y': 7, 'required_flag': None, 'missing_text': '', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE},
    {'scene': 'royal_square', 'point': (19, 7), 'to_scene': 'village', 'to_x': 18, 'to_y': 7, 'required_flag': 'ending_ready', 'missing_text': '审判还没结束。先和国王、军队一起谴责艾琳。', 'canon': False, 'system': True, 'importance': IMPORTANCE_CORE},
    {'scene': 'village', 'point': (0, 7), 'to_scene': 'royal_square', 'to_x': 18, 'to_y': 7, 'required_flag': 'ending_ready', 'missing_text': '只有艾琳危机结束后，村口才会记住通往王城火柴广场的路。', 'canon': False, 'system': True, 'importance': IMPORTANCE_OPTIONAL},
]

ITEMS = [
    {'key': 'honey_1', 'scene': 'village', 'x': 6, 'y': 10, 'kind': 'honey', 'name': '蜂蜜小瓶', 'color': C_GOLD, 'canon': False, 'system': True, 'importance': IMPORTANCE_HIGH, 'intent': '战斗恢复补给'},
    {'key': 'honey_2', 'scene': 'match_market', 'x': 12, 'y': 12, 'kind': 'honey', 'name': '醒神蜂蜜', 'color': C_GOLD, 'canon': False, 'system': False, 'importance': IMPORTANCE_HIGH, 'intent': '对抗幻觉补给'},
    {'key': 'flower_1', 'scene': 'forest', 'x': 3, 'y': 12, 'kind': 'flower', 'name': '蓝色野花', 'color': (93, 141, 245), 'canon': False, 'system': False, 'importance': IMPORTANCE_MEDIUM, 'intent': '收藏与结局评价'},
    {'key': 'flower_2', 'scene': 'winter_street', 'x': 6, 'y': 12, 'kind': 'flower', 'name': '雪边野花', 'color': (225, 225, 240), 'canon': False, 'system': False, 'importance': IMPORTANCE_MEDIUM, 'intent': '收藏与结局评价'},
    {'key': 'cloth_1', 'scene': 'matchbox_prison', 'x': 12, 'y': 5, 'kind': 'cloth', 'name': '防烟湿布', 'color': C_SILVER, 'canon': False, 'system': False, 'importance': IMPORTANCE_HIGH, 'intent': '现实向防护道具'},
    {'key': 'clue_1', 'scene': 'forest', 'x': 2, 'y': 2, 'kind': 'truth_clue', 'name': '狼爪印', 'color': (230, 230, 170), 'canon': True, 'system': False, 'importance': IMPORTANCE_CORE, 'intent': '灰狼线索'},
    {'key': 'clue_2', 'scene': 'winter_street', 'x': 12, 'y': 8, 'kind': 'match_clue', 'name': '烧焦蓝火柴灰', 'color': (120, 180, 255), 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE, 'intent': '艾琳火柴线索'},
    {'key': 'clue_3', 'scene': 'whisper_hotel', 'x': 14, 'y': 12, 'kind': 'match_clue', 'name': '密谋名单碎页', 'color': C_GOLD, 'canon': False, 'system': False, 'importance': IMPORTANCE_HIGH, 'intent': '酒店密谋证据'},
]

NPC_SPECS = [
    {'key': 'mother', 'scene': 'home', 'x': 5, 'y': 6, 'role': 'mother', 'profile_key': 'mother', 'name': '玛莲娜', 'title': '妈妈', 'gender': '女', 'intro': '露比的妈妈，负责交代主线目标和三问规则。', 'visible_rule': 'always', 'action': 'mother', 'canon': True, 'system': False, 'importance': IMPORTANCE_MANDATORY, 'intent': '出发任务与核心规则'},
    {'key': 'merchant', 'scene': 'village', 'x': 2, 'y': 12, 'role': 'merchant', 'profile_key': 'merchant', 'name': '露塔', 'title': '村口行商', 'gender': '女', 'intro': '森林村口的行商，负责市场采购与卖出教学。', 'visible_rule': 'merchant', 'action': 'merchant', 'canon': False, 'system': True, 'importance': IMPORTANCE_HIGH, 'intent': '市场和商店系统'},
    {'key': 'village_chief', 'scene': 'village', 'x': 15, 'y': 12, 'role': 'chief', 'profile_key': 'chief', 'name': '奥伦', 'title': '村长', 'gender': '男', 'intro': '村长最终确认灰狼与艾琳危机结束并开启结局 CG。', 'visible_rule': 'ending_chief', 'action': 'ending_chief', 'canon': False, 'system': True, 'importance': IMPORTANCE_CORE, 'intent': '最终结局 CG 触发'},
    {'key': 'wolf', 'scene': 'forest', 'x': 14, 'y': 5, 'role': 'wolf', 'profile_key': 'wolf', 'name': '格雷姆', 'title': '灰狼', 'gender': '男', 'intro': '伪装温柔的灰狼，上半部核心反派。', 'visible_rule': 'wolf_intro', 'action': 'wolf', 'canon': True, 'system': False, 'importance': IMPORTANCE_CORE, 'intent': '诱导露比'},
    {'key': 'hunter', 'scene': 'forest', 'x': 5, 'y': 7, 'role': 'hunter', 'profile_key': 'hunter', 'name': '伊沃', 'title': '猎人', 'gender': '男', 'intro': '原著中的救援者，也是在监狱线中帮助过金发贫嘴男的人。', 'visible_rule': 'hunter_before', 'action': 'hunter', 'canon': True, 'system': False, 'importance': IMPORTANCE_CORE, 'intent': '银铃与救援'},
    {'key': 'fake_grandma', 'scene': 'cottage', 'x': 17, 'y': 7, 'role': 'fake_grandma', 'profile_key': 'wolf', 'name': '格雷姆', 'title': '伪装成外婆', 'gender': '男', 'intro': '灰狼假扮的外婆，最终战入口。', 'visible_rule': 'fake_grandma', 'action': 'fake_grandma', 'canon': True, 'system': False, 'importance': IMPORTANCE_MANDATORY, 'intent': '最终冲突'},
    {'key': 'grandma', 'scene': 'cottage', 'x': 17, 'y': 7, 'role': 'grandma', 'profile_key': 'grandma', 'name': '阿黛拉', 'title': '外婆', 'gender': '女', 'intro': '露比真正的外婆，揭示艾琳火柴导致的悲剧。', 'visible_rule': 'grandma_after', 'action': 'grandma_after', 'canon': True, 'system': False, 'importance': IMPORTANCE_MANDATORY, 'intent': '下半部触发'},
    {'key': 'wolf_prisoner', 'scene': 'cage_yard', 'x': 10, 'y': 7, 'role': 'wolf', 'profile_key': 'wolf', 'name': '格雷姆', 'title': '囚笼里的灰狼', 'gender': '男', 'intro': '被囚禁的灰狼，请求露比不要让村民报复他。', 'visible_rule': 'wolf_prisoner', 'action': 'prisoner', 'canon': False, 'system': False, 'importance': IMPORTANCE_HIGH, 'intent': '反派处置'},
    {'key': 'newspaper_boy', 'scene': 'winter_street', 'x': 8, 'y': 6, 'role': 'boy', 'profile_key': 'newspaper_boy', 'name': '尼克', 'title': '报童', 'gender': '男', 'intro': '雪夜街口的报童，知道艾琳店铺和密语酒店的传闻。', 'visible_rule': 'newspaper_boy', 'action': 'newspaper_boy', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE, 'intent': '调查入口'},
    {'key': 'hotel_keeper', 'scene': 'whisper_hotel', 'x': 6, 'y': 8, 'role': 'merchant', 'profile_key': 'hotel_keeper', 'name': '贝尔纳', 'title': '密语酒店掌柜', 'gender': '男', 'intro': '守门、听暗号、把后厅让给反对势力的掌柜。', 'visible_rule': 'hotel_gathering', 'action': 'hotel_keeper', 'canon': False, 'system': False, 'importance': IMPORTANCE_HIGH, 'intent': '酒店多 NPC 场面'},
    {'key': 'resistance_scout', 'scene': 'whisper_hotel', 'x': 7, 'y': 6, 'role': 'red_cloak', 'profile_key': 'resistance_scout', 'name': '卡萝', 'title': '红斗篷侦察员', 'gender': '女', 'intro': '确认十几个店铺路线的侦察员。', 'visible_rule': 'hotel_gathering', 'action': 'resistance_scout', 'canon': False, 'system': False, 'importance': IMPORTANCE_HIGH, 'intent': '酒店多 NPC 场面'},
    {'key': 'resistance_leader', 'scene': 'whisper_hotel', 'x': 9, 'y': 6, 'role': 'resistance', 'profile_key': 'resistance_leader', 'name': '瑟琳', 'title': '反对势力领袖', 'gender': '女', 'intro': '在酒店组织密谋的人，准备反击艾琳的火柴店铺。', 'visible_rule': 'resistance_leader', 'action': 'resistance_leader', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE, 'intent': '酒店密谋'},
    {'key': 'secret_medic', 'scene': 'whisper_hotel', 'x': 13, 'y': 8, 'role': 'grandma', 'profile_key': 'secret_medic', 'name': '梅琳', 'title': '秘密药师', 'gender': '女', 'intro': '研究蓝火柴烟雾并准备防烟布的药师。', 'visible_rule': 'hotel_gathering', 'action': 'secret_medic', 'canon': False, 'system': False, 'importance': IMPORTANCE_HIGH, 'intent': '酒店多 NPC 场面'},
    {'key': 'spy', 'scene': 'whisper_hotel', 'x': 14, 'y': 6, 'role': 'spy', 'profile_key': 'spy', 'name': '维克托', 'title': '俊美男卧底', 'gender': '男', 'intro': '外表像温和贵族青年的艾琳卧底，知道私人监狱却不知道抽拉结构。', 'visible_rule': 'hotel_gathering', 'action': 'spy_youth', 'canon': False, 'system': False, 'importance': IMPORTANCE_MANDATORY, 'intent': '男性俊美卧底'},
    {'key': 'prison_cell', 'scene': 'matchbox_prison', 'x': 11, 'y': 7, 'role': 'cell_door', 'profile_key': 'aileen', 'name': '看似空着的牢房门', 'title': '互动物', 'gender': '无', 'intro': '艾琳视角下的牢房门；她不知道囚室被拉进内层后，外侧会看起来像空囚室。', 'visible_rule': 'aileen_prison', 'action': 'aileen_prison', 'canon': False, 'system': False, 'importance': IMPORTANCE_MANDATORY, 'intent': '艾琳主视角监狱探查'},
    {'key': 'dropped_key', 'scene': 'matchbox_prison', 'x': 11, 'y': 7, 'role': 'dropped_key', 'profile_key': 'blond_friend', 'name': '走廊边的钥匙', 'title': '互动物', 'gender': '无', 'intro': '艾琳急怒离开时丢下的钥匙，莱昂捡起后拉出火柴盒式囚室并打开牢门。', 'visible_rule': 'male_companion', 'action': 'male_companion', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE, 'intent': '金发贫嘴男救援'},
    {'key': 'market_messenger', 'scene': 'match_market', 'x': 9, 'y': 6, 'role': 'red_cloak', 'profile_key': 'red_cloak', 'name': '托马', 'title': '红斗篷传信人', 'gender': '男', 'intro': '告诉露比十几个卖火柴店铺同时被红斗篷袭击。', 'visible_rule': 'market_messenger', 'action': 'market_messenger', 'canon': False, 'system': False, 'importance': IMPORTANCE_CORE, 'intent': '店铺袭击结果'},
    {'key': 'king', 'scene': 'royal_square', 'x': 8, 'y': 6, 'role': 'king', 'profile_key': 'king', 'name': '埃德蒙', 'title': '国王', 'gender': '男', 'intro': '带军队谴责艾琳售卖致幻性火柴并触发最终战。', 'visible_rule': 'king', 'action': 'king', 'canon': False, 'system': False, 'importance': IMPORTANCE_MANDATORY, 'intent': '法律谴责与最终战'},
]

INVENTORY_KEYS = [
    '铜币',
    '面包',
    '蜂蜜',
    '红缎带',
    '猎人银铃',
    '油灯',
    '清醒卡片',
    '防烟布',
    '真相线索',
    '火柴证据',
    '酒店名单',
    '牢房钥匙',
    '野花',
    '木哨',
]
SHOP_BUY_CATALOG = [
    {'key': 'buy_honey', 'hotkey': '1', 'name': '蜂蜜', 'inventory_key': '蜂蜜', 'flag_key': 'honeys', 'price': 3, 'count': 1, 'intent': '提高战斗恢复次数和恢复量'},
    {'key': 'buy_flower', 'hotkey': '2', 'name': '野花', 'inventory_key': '野花', 'flag_key': 'wildflowers', 'price': 4, 'count': 1, 'intent': '收藏和结局评价'},
    {'key': 'buy_cloth', 'hotkey': '3', 'name': '防烟布', 'inventory_key': '防烟布', 'flag_key': 'cloths', 'price': 6, 'count': 1, 'intent': '现实向防护道具'},
    {'key': 'buy_bread', 'hotkey': '4', 'name': '暖面包', 'inventory_key': '面包', 'flag_key': None, 'price': 5, 'count': 1, 'intent': '提高战斗最大生命'},
    {'key': 'buy_whistle', 'hotkey': '5', 'name': '木哨', 'inventory_key': '木哨', 'flag_key': None, 'price': 8, 'count': 1, 'intent': '战斗中可用一次扰乱敌人'},
]
SHOP_SELL_CATALOG = [
    {'key': 'sell_honey', 'hotkey': '7', 'name': '蜂蜜', 'inventory_key': '蜂蜜', 'flag_key': 'honeys', 'price': 1, 'count': 1, 'intent': '卖出多余蜂蜜'},
    {'key': 'sell_flower', 'hotkey': '8', 'name': '野花', 'inventory_key': '野花', 'flag_key': 'wildflowers', 'price': 2, 'count': 1, 'intent': '卖出多余野花'},
    {'key': 'sell_cloth', 'hotkey': '9', 'name': '防烟布', 'inventory_key': '防烟布', 'flag_key': 'cloths', 'price': 3, 'count': 1, 'intent': '卖出多余防护布'},
]
BADGE_NAMES = {
    'basket': '出发的篮子',
    'first_honey': '第一瓶蜂蜜',
    'truth_seeker': '真相追问者',
    'bell_guardian': '银铃守护',
    'clear_minded': '保持清醒',
    'wolf_defeated': '假面退散',
    'wolf_caged': '灰狼不再伤人',
    'chapter_two': '雪夜火柴线索',
    'hotel_conspiracy': '密语酒店的桌布下',
    'hotel_crowd': '密语酒店多人密会',
    'matchbox_prison': '火柴盒监狱逃脱',
    'shop_raids': '红斗篷并非一个人',
    'aileen_defeated': '王城火柴广场之后',
    'true_ending': '红斗篷照亮两场黑夜',
    'collector': '森林收藏家',
    'autoplayer': '自动旅人',
    'voice_reader': '会说话的森林',
    'first_trade': '第一次市场交易',
    'ending_cg': '村长讲完结局',
    'pov_aileen': '艾琳视角',
    'pov_blond_friend': '贫嘴救援',
    'male_spy': '俊美男卧底',
}

STORY_ACTION_SPECS = {
    'intro': {
        'section': '第一幕：红斗篷出发',
        'scene': 'home',
        'location_type': 'INT',
        'time_key': 'morning',
        'actions': [
            '妈妈的小屋里有面包和蜂蜜的气味。露比站在门口，红斗篷像一盏小灯。',
            '这一段说明本游戏不是只复述原著，而是把灰狼故事和艾琳蓝火柴阴谋合成多幕结构。',
        ],
        'dialogue': [
            ('narrator', '很久以前，森林还会在夜里唱歌。', 'narrator', 'left'),
            ('narrator', '后来，一只灰狼学会模仿亲人的声音，森林的歌声就变得很轻。', 'narrator', 'left'),
            ('red', '今天我要去看外婆。妈妈说，她病了，需要面包和蜂蜜。', 'red', 'left'),
            ('narrator', '但这不是故事的全部。灰狼之后，还有艾琳、密语酒店、男性俊美卧底、火柴盒监狱、红斗篷袭击、主视角切换和国王的军队。', 'narrator', 'left'),
        ],
        'end_key': 'intro',
    },
    'mother_first': {
        'section': '第一幕：红斗篷出发',
        'scene': 'home',
        'location_type': 'INT',
        'time_key': 'morning',
        'actions': ['玛莲娜把篮子放到桌上，篮子里有面包、蜂蜜、红缎带和一点铜币。'],
        'dialogue': [
            ('mother', '露比，外婆住在森林另一边。她病了，需要这篮面包和蜂蜜。', 'mother', 'right'),
            ('mother', '森林很漂亮，也很会说谎。不要离开小路，不要被甜言蜜语骗走。', 'mother', 'right'),
            ('mother', '如果影子装成亲人，就问三个问题。真正爱你的人不会害怕答案。', 'mother', 'right'),
            ('red', '我会把篮子送到外婆手里，也会记住你的声音。', 'red', 'left'),
            ('narrator', '你获得了：装着面包、蜂蜜、红缎带和铜币的篮子。', 'narrator', 'left'),
        ],
        'end_key': 'mother_first',
    },
    'mother_hint': {
        'section': '第一幕：红斗篷出发',
        'scene': 'home',
        'location_type': 'INT',
        'time_key': 'morning',
        'actions': ['玛莲娜补充三问规则。这个规则会在假外婆段落与战斗系统中变成清醒道具。'],
        'dialogue': [
            ('mother', '再听我说一次：耳朵、手掌、牙齿，都是影子藏不住的地方。', 'mother', 'right'),
            ('mother', '慢慢问，不要急着相信。坏心眼最怕清醒的孩子。', 'mother', 'right'),
            ('red', '我会记住三个问题，也会记住你的声音。', 'red', 'left'),
        ],
        'end_key': 'mother_hint',
    },
    'mother_after': {
        'section': '第一幕：红斗篷出发',
        'scene': 'home',
        'location_type': 'INT',
        'time_key': 'morning',
        'actions': ['完成出发教学后，玛莲娜只留下鼓励对白。'],
        'dialogue': [
            ('mother', '去吧，红斗篷会在树影里像灯一样亮。', 'mother', 'right'),
            ('mother', '真正的勇敢不是不害怕，而是在害怕时仍然看清路。', 'mother', 'right'),
        ],
        'end_key': None,
    },
    'merchant': {
        'section': '第一幕：红斗篷出发',
        'scene': 'village',
        'location_type': 'EXT',
        'time_key': 'day',
        'actions': ['露塔在村口摆开摊位，商店系统只在手动游玩时打开，自动游玩不会主动购物。'],
        'dialogue': [
            ('merchant', '红斗篷，市场不是让你贪心的地方，是让你在出发前知道自己还缺什么。', 'merchant', 'right'),
            ('red', '我可以买蜂蜜、野花、防烟布、暖面包和木哨，也可以卖出多余材料吗？', 'red', 'left'),
            ('merchant', '当然。自动游玩不会打开商店，但玩家可以手动补给。', 'merchant', 'right'),
        ],
        'end_key': 'merchant',
    },
    'wolf': {
        'section': '第二幕：森林小路与灰狼诱导',
        'scene': 'forest',
        'location_type': 'EXT',
        'time_key': 'day',
        'actions': ['格雷姆从树影里出现，礼貌得像一封写错地址的信。'],
        'dialogue': [
            ('wolf', '早安，小姑娘。你的篮子闻起来像蜂蜜、面包，还有一点点勇气。', 'wolf', 'right'),
            ('red', '我要去看外婆。妈妈说，不能离开小路。', 'red', 'left'),
            ('wolf', '当然，当然。只是小路有两条：一条很短，一条开满花。外婆会喜欢花的。', 'wolf', 'right'),
            ('red', '花很美，但我先记住你的眼睛。它们看篮子的时候，比看花更亮。', 'red', 'left'),
            ('wolf', '哈哈，聪明的孩子。礼貌只是我的皮毛，饥饿才是我的牙齿。我们很快再见。', 'wolf', 'right'),
        ],
        'end_key': 'wolf_first',
    },
    'hunter': {
        'section': '第二幕：森林小路与灰狼诱导',
        'scene': 'forest',
        'location_type': 'EXT',
        'time_key': 'day',
        'actions': [
            '伊沃发现新鲜狼爪印，并给露比银铃、油灯和清醒卡。',
            '第三方库考点：NetworkX 的 shortest_path 在无权图中对应 Breadth First Search（广度优先搜索，BFS）。推荐书：中文《算法图解》，英文 The Algorithm Design Manual。',
        ],
        'dialogue': [
            ('hunter', '停一下，露比。我在泥地里看见新鲜狼爪印，它们正朝外婆的小屋去。', 'hunter', 'right'),
            ('red', '那只狼知道我的目的地。它说话很有礼貌，可我不相信它。', 'red', 'left'),
            ('hunter', '把这个小铃铛系在篮子上。遇到危险就摇响，我会循声赶来。', 'hunter', 'right'),
            ('hunter', '再拿这盏油灯和一张清醒卡。烟雾和幻觉最怕稳定的光线与写下来的事实。', 'hunter', 'right'),
        ],
        'end_key': 'hunter',
    },
    'fake_grandma': {
        'section': '第三幕：外婆小屋与灰狼最终战',
        'scene': 'cottage',
        'location_type': 'INT',
        'time_key': 'dusk',
        'actions': ['假外婆躺在床上，窗帘不动。露比用三个问题撕开伪装，灰狼扑出，最终战开始。'],
        'dialogue': [
            ('wolf', '进来吧，红斗篷。把篮子放近一点，我的眼睛看不清。', 'fake_grandma', 'right'),
            ('narrator', '露比想起妈妈和森林线索，决定一个问题一个问题地问。', 'narrator', 'left'),
            ('red', '外婆，为什么你的耳朵这么尖？', 'red', 'left'),
            ('wolf', '为了听见你篮子里的蜂蜜在唱歌。', 'fake_grandma', 'right'),
            ('red', '外婆，为什么你的手掌这么大？', 'red', 'left'),
            ('wolf', '为了更快接过你的礼物。', 'fake_grandma', 'right'),
            ('red', '外婆，为什么你的牙齿像刀？', 'red', 'left'),
            ('wolf', '为了一口吃掉你的恐惧！', 'wolf', 'right'),
            ('narrator', '上半部最终战开始。前半段灰狼占优势，坚持到银铃、油灯与问题连成反击。', 'narrator', 'left'),
        ],
        'end_key': 'start_wolf_battle',
    },
    'wolf_victory': {
        'section': '第三幕：外婆小屋与灰狼最终战',
        'scene': 'cottage',
        'location_type': 'INT',
        'time_key': 'night',
        'actions': ['灰狼战败，猎人赶到。露比必须决定灰狼之后如何被处置。'],
        'dialogue': [
            ('wolf', '嗷！这不是普通的篮子，是装满勇气、蜂蜜和真相的篮子！', 'wolf', 'right'),
            ('hunter', '我听见铃铛声就赶来了。干得好，红斗篷！', 'hunter', 'left'),
            ('red', '灰狼不能继续伤害村民。我们需要决定怎样处置它。', 'red', 'left'),
        ],
        'end_key': 'wolf_victory',
    },
    'prisoner': {
        'section': '第四幕：灰狼囚笼与外婆真相',
        'scene': 'cage_yard',
        'location_type': 'EXT',
        'time_key': 'night',
        'actions': ['格雷姆被关进铁栅栏。村庄暂时安静下来，但更远处的雪夜亮起蓝火柴。'],
        'dialogue': [
            ('wolf', '别让村民把我赶进火里……我知道错了，我再也不学亲人的声音骗人了。', 'wolf', 'right'),
            ('red', '你会被关在这里，直到你学会不伤害别人。求饶不是答案，停止伤害才是。', 'red', 'left'),
            ('hunter', '铁栅栏会有人看守。村民安全，森林也不需要再被恐惧统治。', 'hunter', 'left'),
        ],
        'end_key': 'prisoner',
    },
    'grandma_after': {
        'section': '第四幕：灰狼囚笼与外婆真相',
        'scene': 'cottage',
        'location_type': 'INT',
        'time_key': 'deep_night',
        'actions': ['真正的外婆阿黛拉说出蓝色火柴的秘密。她终于睡去，再也没有醒来。'],
        'dialogue': [
            ('grandma', '你救了我一次，红斗篷。可是我还欠你一个真相。', 'grandma', 'right'),
            ('grandma', '那天，一个叫艾琳的小女孩卖给我一盒蓝色火柴。点燃时，我看见了最甜的幻觉。', 'grandma', 'right'),
            ('grandma', '我以为那只是温暖，可每一根火柴都让我更想继续点燃。后来我分不清幻觉和醒着的房间。', 'grandma', 'right'),
            ('red', '外婆……你为什么不早告诉我？', 'red', 'left'),
            ('grandma', '因为致幻性火柴会让人相信：只要再点一根，痛苦就会消失。孩子，别让它继续害人。', 'grandma', 'right'),
            ('grandma', '假梦再甜，也不能替人活过真实的一天。', 'grandma', 'right'),
            ('narrator', '外婆握着红缎带，声音越来越轻。窗外天色发白，她终于睡去，再也没有醒来。', 'narrator', 'left'),
            ('red', '我会找到艾琳，也会找到她身后那些店铺和监狱。', 'red', 'left'),
        ],
        'end_key': 'grandma_after',
    },
    'newspaper_boy': {
        'section': '第五幕：雪夜街口与蓝火柴传闻',
        'scene': 'winter_street',
        'location_type': 'EXT',
        'time_key': 'night',
        'actions': ['尼克在雪夜街口喊号外，蓝火柴的甜味在空气里发冷。'],
        'dialogue': [
            ('newspaper_boy', '号外！号外！雪夜里有人排队买蓝火柴，还说艾琳的十几个店铺都开到邻国边界了。', 'boy', 'right'),
            ('red', '外婆说蓝火柴会让人看见幻觉，也会让人再也不愿醒来。有人反对艾琳吗？', 'red', 'left'),
            ('newspaper_boy', '密语酒店里有人反对她，那里不是一个人在密谋，而是一整桌人。他们说要让红斗篷不止一个。', 'boy', 'right'),
        ],
        'end_key': 'newspaper_boy',
    },
    'hotel_keeper': {
        'section': '第六幕：密语酒店多 NPC 密会',
        'scene': 'whisper_hotel',
        'location_type': 'INT',
        'time_key': 'night',
        'actions': ['贝尔纳守着酒店门口，用账本遮住后厅密会名单。'],
        'dialogue': [
            ('hotel_keeper', '红斗篷进门时别看门牌，看桌布下面第三道红线。那才是今晚的路。', 'merchant', 'right'),
            ('red', '这里有这么多人，艾琳会不会已经派人混进来了？', 'red', 'left'),
            ('hotel_keeper', '如果没有混进来，我们反而该担心她太安静。', 'merchant', 'right'),
        ],
        'end_key': None,
    },
    'resistance_scout': {
        'section': '第六幕：密语酒店多 NPC 密会',
        'scene': 'whisper_hotel',
        'location_type': 'INT',
        'time_key': 'night',
        'actions': ['卡萝把十几个店铺路线画在杯垫背面。'],
        'dialogue': [
            ('resistance_scout', '东街三家，北桥四家，边境七家。我们会同时披上红斗篷。', 'red_cloak', 'right'),
            ('red', '这样艾琳就不能只盯着我一个人。', 'red', 'left'),
            ('resistance_scout', '对。今晚红斗篷不是一个名字，是一条路线。', 'red_cloak', 'right'),
        ],
        'end_key': None,
    },
    'secret_medic': {
        'section': '第六幕：密语酒店多 NPC 密会',
        'scene': 'whisper_hotel',
        'location_type': 'INT',
        'time_key': 'night',
        'actions': ['梅琳把防烟布和蓝火柴灰分开放在桌上。'],
        'dialogue': [
            ('secret_medic', '蓝火柴的问题不只是火焰，而是烟。人吸进去以后，会把逃避误认成温暖。', 'grandma', 'right'),
            ('red', '所以防烟布不是魔法，是让人保住呼吸的工具。', 'red', 'left'),
            ('secret_medic', '没错。面试时也可以这么讲：游戏道具不是随机奖励，而是剧情主题的机械化表达。', 'grandma', 'right'),
        ],
        'end_key': None,
    },
    'spy_youth': {
        'section': '第六幕：密语酒店多 NPC 密会',
        'scene': 'whisper_hotel',
        'location_type': 'INT',
        'time_key': 'night',
        'actions': ['维克托站在灯下，看起来像温和俊美的贵族青年。'],
        'dialogue': [
            ('spy', '小姐，后厅风冷，我替你把门关上。', 'spy', 'right'),
            ('red', '你的手套上有蓝色火柴灰。', 'red', 'left'),
            ('spy', '真敏锐。可惜敏锐不等于自由。', 'spy', 'right'),
            ('narrator', '维克托笑得很礼貌。他知道艾琳有私人监狱，却不知道那座监狱真正能像火柴盒一样抽拉。', 'narrator', 'left'),
        ],
        'end_key': None,
    },
    'resistance_leader': {
        'section': '第六幕：密语酒店多 NPC 密会与卧底暴露',
        'scene': 'whisper_hotel',
        'location_type': 'INT',
        'time_key': 'night',
        'actions': [
            '瑟琳摊开路线图，酒店里有掌柜、侦察员、药师、红斗篷和看似温柔的俊美青年。',
            '维克托露出艾琳店铺的蓝火柴印章，密语酒店的密谋被暴露。',
            '注意：维克托知道艾琳有私人监狱，但他不知道火柴盒监狱的抽拉囚室结构。',
        ],
        'dialogue': [
            ('resistance_leader', '红斗篷，你终于来了。看清楚这里的人：掌柜守门，侦察员记路线，药师准备防烟布。', 'resistance', 'right'),
            ('red', '这里不是一场单人密谋，是很多人都不愿继续被蓝火柴骗。', 'red', 'left'),
            ('resistance_leader', '计划今晚同时开始。一个红斗篷会被抓住，十几个红斗篷会变成路。', 'resistance', 'right'),
            ('spy', '真感人。可惜这张桌子旁边也有艾琳的人。', 'spy', 'right'),
            ('narrator', '维克托摘下白手套，露出艾琳店铺的蓝火柴印章。酒店里所有人都暴露了。', 'narrator', 'left'),
            ('red', '你是卧底。', 'red', 'left'),
            ('spy', '也是一把很会微笑的锁。艾琳的私人监狱正等着你们，我只要把人送进去就够了。', 'spy', 'right'),
            ('narrator', '维克托不知道，那座监狱深处的囚室并不是普通牢房，而是能像火柴盒内胆一样被抽拉。', 'narrator', 'left'),
            ('narrator', '蓝色药烟从门缝灌进来，露比和反对势力的人被抓走。主视角即将切换为艾琳。', 'narrator', 'left'),
        ],
        'end_key': 'hotel_conspiracy',
    },
    'aileen_prison': {
        'section': '第七幕：艾琳视角的火柴盒监狱',
        'scene': 'matchbox_prison',
        'location_type': 'INT',
        'time_key': 'deep_night',
        'actions': [
            '主视角切换为艾琳。露比不出现在可操控场景中，玩家操控艾琳巡视私人监狱。',
            '艾琳不知道自己的监狱具备火柴盒式抽拉结构；在她眼里，走廊外侧只是一排有时空着、有时关人的普通囚室。',
            '艾琳听说十几个卖火柴店铺同时被红斗篷袭击，急怒离开，把钥匙扔在走廊边。',
        ],
        'dialogue': [
            ('narrator', '主视角切换为艾琳。火柴盒监狱在结构上像可以抽拉的纸盒，但艾琳只以为那是普通的秘密牢区。', 'narrator', 'left'),
            ('aileen', '我曾在雪夜跪着卖最后一盒火柴，连求一句暖话都觉得卑微。现在，这些墙、这些锁、这些店铺，终于都听我的。', 'aileen', 'right'),
            ('aileen', '红斗篷被关进去了。反对势力也被关进去了。我的私人监狱，总算安静了。', 'aileen', 'right'),
            ('aileen', '奇怪，这间外侧囚室看起来空着，可门缝里像刚有人呼吸过。', 'aileen', 'right'),
            ('narrator', '她不知道真正的囚室已经被推入墙体深处，外侧空牢只是火柴盒抽屉留下的假象。', 'narrator', 'left'),
            ('blue_match_messenger', '艾琳小姐，十几个卖火柴店铺同时被身穿红斗篷的人袭击！总店也可能被围住！', 'red_cloak', 'left'),
            ('aileen', '十几个？她被关在这里，外面怎么还有十几个红斗篷？', 'aileen', 'right'),
            ('narrator', '艾琳急怒转身，钥匙从手套边滑落，掉在走廊石缝旁。主视角即将切换为莱昂。', 'narrator', 'left'),
        ],
        'end_key': 'aileen_prison',
    },
    'male_companion': {
        'section': '第八幕：莱昂救援与牢门打开',
        'scene': 'matchbox_prison',
        'location_type': 'INT',
        'time_key': 'deep_night',
        'actions': ['主视角切换为莱昂。他捡起艾琳丢下的钥匙，利用火柴盒抽拉结构打开牢门。'],
        'dialogue': [
            ('narrator', '主视角切换为莱昂。红斗篷仍在牢房里，玩家现在操控这个嘴上很轻、手上很快的朋友。', 'narrator', 'left'),
            ('blond_friend', '好消息：她真的很急。坏消息：她急到连钥匙都不会好好拿。', 'blond_friend', 'left'),
            ('blond_friend', '钥匙在这儿。火柴盒、火柴盒……让我猜猜，肯定有个爱炫耀的人把所有锁做成同一把钥匙能开。', 'blond_friend', 'left'),
            ('blond_friend', '露比，你还记得吗？外面看着像空牢，里面其实是一层被推走的抽屉。', 'blond_friend', 'left'),
            ('red', '记得。维克托不知道，艾琳也不知道。他们以为门关上就结束了。', 'red', 'right'),
            ('narrator', '钥匙转动，牢门内部像火柴盒抽屉一样一格一格拉回走廊。', 'narrator', 'left'),
            ('blond_friend', '女士们、先生们、还有不想承认自己被关错格子的各位，请排队出盒。', 'blond_friend', 'left'),
            ('red', '你来得正好。', 'red', 'right'),
            ('blond_friend', '我通常都来得正好，只是发型先到。', 'blond_friend', 'left'),
            ('narrator', '露比和被关的人鱼贯而出。火柴盒监狱的长廊第一次透进真实的冷风。主视角切回红斗篷。', 'narrator', 'left'),
        ],
        'end_key': 'male_companion',
    },
    'market_messenger': {
        'section': '第九幕：火柴总店街与红斗篷袭击',
        'scene': 'match_market',
        'location_type': 'EXT',
        'time_key': 'dawn',
        'actions': ['十几个店铺留下红斗篷记号。艾琳以为抓住了露比，其实只抓住了计划的一部分。'],
        'dialogue': [
            ('red_cloak', '十几个店铺都留下红斗篷记号。艾琳现在只想守住总店。', 'red_cloak', 'right'),
            ('red', '这说明反对势力还有很多人，也说明艾琳并不是不可战胜。', 'red', 'left'),
            ('red_cloak', '国王已经收到证据。邻国投诉说蓝火柴让边境村民成瘾并出现幻觉。军队正在王城火柴广场集结。', 'red_cloak', 'right'),
        ],
        'end_key': 'market_messenger',
    },
    'king': {
        'section': '第十幕：王城火柴广场与艾琳结局',
        'scene': 'royal_square',
        'location_type': 'EXT',
        'time_key': 'dawn',
        'actions': ['埃德蒙国王和军队围住艾琳总店。艾琳点燃最后一整盒蓝火柴，下半部最终战开始。'],
        'dialogue': [
            ('king', '艾琳，你售卖致幻性火柴，违背本国法律，也让邻国发来投诉。', 'king', 'right'),
            ('red', '外婆死在你的假梦里。酒店的人被维克托暴露，随后被抓进私人监狱。十几个店铺都在卖同样的蓝火柴。', 'red', 'left'),
            ('aileen', '我曾经穷到只能把最后一盒火柴举给路人，他们连看都不看。现在你们终于全都看着我了。', 'aileen', 'right'),
            ('king', '火光不能夺走清醒，买卖也不能越过生命和法律。军队会封锁店铺。', 'king', 'right'),
            ('aileen', '那就看看红斗篷、国王和军队，能不能从我的最后一盒火柴里醒过来！', 'aileen', 'right'),
            ('narrator', '下半部最终战开始。艾琳点燃一整盒蓝火柴，广场被烟雾和假梦包围。', 'narrator', 'left'),
        ],
        'end_key': 'start_aileen_battle',
    },
    'aileen_victory': {
        'section': '第十幕：王城火柴广场与艾琳结局',
        'scene': 'royal_square',
        'location_type': 'EXT',
        'time_key': 'dawn',
        'actions': ['艾琳逃走后，尸体被发现，身边散落一地用完的火柴。'],
        'dialogue': [
            ('aileen', '如果没有那些假梦，我该怎么熬过那些冷夜？如果我不强势，谁会记得那个冻到发抖的穷孩子？', 'aileen', 'right'),
            ('red', '梦可以温暖人，但不能夺走别人的清醒和生命。你曾经卑微，不代表你现在可以让别人跪下。', 'red', 'left'),
            ('narrator', '艾琳转身逃进蓝色烟雾。天亮后，人们在巷尾发现她的尸体，身边散落一地用完的火柴。', 'narrator', 'left'),
            ('king', '封锁所有致幻性火柴店铺。记录外婆、监狱、酒店和邻国受害者的证词。', 'king', 'right'),
        ],
        'end_key': 'aileen_victory',
    },
    'ending_chief': {
        'section': '第十一幕：村口灯与结局 CG',
        'scene': 'village',
        'location_type': 'EXT',
        'time_key': 'morning',
        'actions': ['奥伦村长在村口讲完整个故事，结局 CG 打开。'],
        'dialogue': [
            ('chief', '红斗篷，灰狼不再伤人，艾琳的火柴店铺也已经被封。你愿意让村口的灯讲完这个故事吗？', 'chief', 'right'),
            ('red', '我愿意。但故事里要记住外婆，也要记住：逃进假梦不能以清醒和生命为代价。', 'red', 'left'),
            ('chief', '村庄不能只记住胜利，也要记住代价。结局 CG 会打开，但你仍然可以回来继续闲逛。', 'chief', 'right'),
        ],
        'end_key': 'ending_chief',
    },
    'battle_loss': {
        'section': '系统段落：战败回到安全位置',
        'scene': 'cottage',
        'location_type': 'INT',
        'time_key': 'dusk',
        'actions': ['战败不是坏结局，而是把玩家送回安全点重新整理篮子。'],
        'dialogue': [
            ('narrator', '红斗篷退到安全的小路上，重新整理篮子。', 'narrator', 'left'),
            ('red', '我不能就这样放弃。再整理一下篮子，重新挑战！', 'red', 'left'),
            ('narrator', '提示：多准备蜂蜜、寻找线索、使用防御、银铃、油灯、清醒卡、防烟布和木哨，会让战斗更轻松。', 'narrator', 'left'),
        ],
        'end_key': 'battle_loss',
    },
}

action_story_pairs = [
    ('merchant', 'merchant'),
    ('wolf', 'wolf'),
    ('hunter', 'hunter'),
    ('fake_grandma', 'fake_grandma'),
    ('grandma_after', 'grandma_after'),
    ('prisoner', 'prisoner'),
    ('newspaper_boy', 'newspaper_boy'),
    ('hotel_keeper', 'hotel_keeper'),
    ('resistance_scout', 'resistance_scout'),
    ('secret_medic', 'secret_medic'),
    ('spy_youth', 'spy_youth'),
    ('resistance_leader', 'resistance_leader'),
    ('aileen_prison', 'aileen_prison'),
    ('male_companion', 'male_companion'),
    ('market_messenger', 'market_messenger'),
    ('king', 'king'),
    ('ending_chief', 'ending_chief'),
]
ACTION_TO_STORY_KEY = {}
for action_key, story_key in action_story_pairs:
    ACTION_TO_STORY_KEY[action_key] = story_key
FOUNTAIN_STORY_SEQUENCE = [
    'intro',
    'mother_first',
    'mother_hint',
    'merchant',
    'wolf',
    'hunter',
    'fake_grandma',
    'wolf_victory',
    'prisoner',
    'grandma_after',
    'newspaper_boy',
    'hotel_keeper',
    'resistance_scout',
    'secret_medic',
    'spy_youth',
    'resistance_leader',
    'aileen_prison',
    'male_companion',
    'market_messenger',
    'king',
    'aileen_victory',
    'ending_chief',
]

PORTALS = []
SCENE_GRAPH = nx.Graph()


def profile_display_text(profile_key):
    """生成角色姓名与头衔组合文本。

    :param profile_key: 角色档案编号。
    :return: 适合日志、札记和图鉴显示的角色文本。
    """
    profile = CHARACTER_PROFILES[profile_key]
    profile_name = profile['name']
    profile_title = profile['title']
    if profile_title != '':
        display_text = f'{profile_name}｜{profile_title}'
    else:
        display_text = profile_name
    return display_text


def speaker_name_and_title(speaker_key):
    """把对白说话人编号转换为姓名和副标题。

    :param speaker_key: 对白说话人编号。
    :return: 角色姓名与副标题。
    """
    if speaker_key == 'narrator':
        speaker_name = '旁白'
        speaker_title = ''
    else:
        profile = CHARACTER_PROFILES[speaker_key]
        speaker_name = profile['name']
        speaker_title = profile['title']
    return speaker_name, speaker_title


def fountain_speaker_text(speaker_key):
    """生成 Fountain 剧本中的角色名。

    Fountain 是影视剧本常用的纯文本格式。
    第三方库考点：本脚本不依赖 Fountain 专用库，而是把结构化剧情数据渲染成 Fountain 文本，面试时可强调“数据层”和“表现层”分离。
    推荐书：中文《游戏编程模式》，英文 Game Programming Patterns。

    :param speaker_key: 对白说话人编号。
    :return: Fountain 使用的说话人文本。
    """
    speaker_name, speaker_title = speaker_name_and_title(speaker_key)
    if speaker_title != '':
        speaker_text = f'{speaker_name}（{speaker_title}）'
    else:
        speaker_text = speaker_name
    return speaker_text


def importance_enabled(importance):
    """判断重要性等级是否启用。

    :param importance: 重要性等级。
    :return: True 表示启用，False 表示关闭。
    """
    if importance == IMPORTANCE_MANDATORY:
        enabled = True
    elif importance == IMPORTANCE_CORE:
        enabled = True
    elif importance == IMPORTANCE_HIGH:
        enabled = True
    elif importance == IMPORTANCE_MEDIUM:
        enabled = ENABLE_MEDIUM_IMPORTANCE_CONTENT
    elif importance == IMPORTANCE_OPTIONAL:
        enabled = ENABLE_OPTIONAL_IMPORTANCE_CONTENT
    else:
        enabled = False
    return enabled


def content_enabled(entity_spec):
    """判断场景、门、角色或物品是否启用。

    :param entity_spec: 带 canon、system、importance 字段的配置。
    :return: True 表示启用，False 表示关闭。
    """
    entity_system = entity_spec['system']
    entity_canon = entity_spec['canon']
    entity_importance = entity_spec['importance']
    if entity_system:
        if entity_canon:
            enabled = ENABLE_SHOP_SYSTEM and importance_enabled(entity_importance)
        else:
            enabled = (ENABLE_SHOP_SYSTEM or ENABLE_NON_CANON_SCENES) and importance_enabled(entity_importance)
    elif entity_canon:
        enabled = importance_enabled(entity_importance)
    else:
        enabled = ENABLE_NON_CANON_SCENES and importance_enabled(entity_importance)
    return enabled


def scene_enabled(scene_key):
    """判断场景是否启用。

    :param scene_key: 场景编号。
    :return: True 表示启用，False 表示关闭。
    """
    scene_meta = SCENE_META[scene_key]
    enabled = content_enabled(scene_meta)
    return enabled


def npc_enabled(npc_spec):
    """判断 NPC 是否启用。

    NPC 指 Non-Player Character（非玩家角色）。
    面试考点：角色配置是数据，角色行为是状态机动作，渲染只是表现层。

    :param npc_spec: NPC 配置。
    :return: True 表示启用，False 表示关闭。
    """
    if npc_spec['system']:
        enabled = ENABLE_SHOP_SYSTEM and importance_enabled(npc_spec['importance'])
    elif npc_spec['canon']:
        enabled = importance_enabled(npc_spec['importance'])
    else:
        enabled = ENABLE_NON_CANON_CHARACTERS and ENABLE_SIDE_QUESTS and importance_enabled(npc_spec['importance'])
    return enabled


def item_enabled(collectible):
    """判断道具是否启用。

    :param collectible: 道具配置。
    :return: True 表示启用，False 表示关闭。
    """
    if collectible['system']:
        enabled = ENABLE_SHOP_SYSTEM and importance_enabled(collectible['importance'])
    elif collectible['canon']:
        enabled = importance_enabled(collectible['importance'])
    else:
        enabled = ENABLE_NON_CANON_ITEMS and importance_enabled(collectible['importance'])
    return enabled


def build_portals(portal_blueprints):
    """根据传送门蓝图生成单格传送门数据。

    :param portal_blueprints: 传送门蓝图列表。
    :return: 可直接用于踩格检测的传送门列表。
    """
    portals = []
    for portal_blueprint in portal_blueprints:
        scene = portal_blueprint['scene']
        to_scene = portal_blueprint['to_scene']
        if content_enabled(portal_blueprint) and scene_enabled(scene) and scene_enabled(to_scene):
            portal_x, portal_y = portal_blueprint['point']
            portal = {
                'scene': scene,
                'x': portal_x,
                'y': portal_y,
                'to_scene': to_scene,
                'to_x': portal_blueprint['to_x'],
                'to_y': portal_blueprint['to_y'],
                'required_flag': portal_blueprint['required_flag'],
                'missing_text': portal_blueprint['missing_text'],
                'canon': portal_blueprint['canon'],
                'system': portal_blueprint['system'],
                'importance': portal_blueprint['importance'],
            }
            portals.append(portal)
    return portals


def build_scene_graph(portal_blueprints):
    """创建场景图。

    NetworkX 是成熟第三方图库，Graph 节点表示场景，边表示传送门。
    shortest_path 在无权图里可对应 Breadth First Search（广度优先搜索，BFS）。
    面试考点：把故事地点抽象为图后，自动游玩只需要先找到下一条边，再在局部地图上寻路。
    推荐书：中文《算法图解》，英文 The Algorithm Design Manual。

    :param portal_blueprints: 传送门蓝图列表。
    :return: NetworkX 无向图。
    """
    scene_graph = nx.Graph()
    for scene_key in SCENE_ORDER:
        if scene_enabled(scene_key):
            scene_graph.add_node(scene_key)
    for portal_blueprint in portal_blueprints:
        scene = portal_blueprint['scene']
        to_scene = portal_blueprint['to_scene']
        if content_enabled(portal_blueprint) and scene_enabled(scene) and scene_enabled(to_scene):
            scene_graph.add_edge(scene, to_scene)
    return scene_graph


def build_storyline_text():
    """生成完整剧情线文本。

    :return: 完整剧情线文本。
    """
    enabled_scene_names = []
    for scene_key in SCENE_ORDER:
        if scene_enabled(scene_key):
            scene_name = SCENE_NAMES[scene_key]
            enabled_scene_names.append(scene_name)
    storyline_lines = [
        '小红帽RPG',
        '',
        '一、运行模式',
        f'当前 RUN_MODE：{RUN_MODE}',
        '可选值：normal / storyline / original_story / fountain / record / publish_info',
        f'普通模式默认跳过幕数：{NORMAL_START_SKIP_ACTS_DEFAULT}',
        f'自动模式默认跳过幕数：{AUTO_PLAY_SKIP_ACTS_DEFAULT}',
        f'录制模式默认跳过幕数：{RECORD_SKIP_ACTS_DEFAULT}',
        f'录制模式是否自动捡可达道具：{RECORD_AUTO_PICKUP_REACHABLE_ITEMS_DEFAULT}',
        '',
        '二、多幕剧情',
        '第一幕：红斗篷出发，妈妈交付篮子和三问规则。',
        '第二幕：森林小路中灰狼诱导露比，猎人给出银铃、油灯和清醒卡。',
        '第三幕：外婆小屋中假外婆揭露为灰狼，进入上半部最终战。',
        '第四幕：灰狼被处置后，外婆揭示艾琳蓝火柴导致的悲剧。',
        '第五幕：雪夜街口听见艾琳店铺和密语酒店的传闻。',
        '第六幕：密语酒店里多位 NPC 参加反对艾琳的密会，但被俊美男卧底维克托暴露。',
        '第七幕：主视角切换为艾琳，玩家操控艾琳巡视火柴盒监狱；艾琳不知道囚室能抽拉。',
        '第八幕：主视角切换为莱昂，他捡起钥匙并利用火柴盒抽拉结构打开牢门。',
        '第九幕：火柴总店街确认十几个店铺被红斗篷同时袭击。',
        '第十幕：王城火柴广场上，国王和军队谴责艾琳并触发最终战。',
        '第十一幕：村口村长开启结局 CG。',
        '',
        '三、火柴盒监狱信息差',
    ]
    storyline_lines.extend(MATCHBOX_PRISON_SECRET_LINES)
    scene_title_lines = [
        '',
        '四、启用场景',
        f'启用场景总数：{len(enabled_scene_names)}',
        f'启用场景顺序：{" → ".join(enabled_scene_names)}',
    ]
    storyline_lines.extend(scene_title_lines)
    for scene_key in SCENE_ORDER:
        scene_meta = SCENE_META[scene_key]
        scene_name = scene_meta['name']
        scene_intent = scene_meta['intent']
        scene_importance = scene_meta['importance']
        scene_canon = scene_meta['canon']
        scene_system = scene_meta['system']
        scene_location_type = scene_meta['location_type']
        time_key = scene_meta['default_time_key']
        time_name = TIME_OF_DAY_SPECS[time_key]['name']
        if scene_enabled(scene_key):
            scene_status = '启用'
        else:
            scene_status = '关闭'
        scene_line = f'· {scene_name}｜状态：{scene_status}｜内外景：{scene_location_type}｜默认时间：{time_name}｜原著：{scene_canon}｜系统：{scene_system}｜重要性：{scene_importance}｜意图：{scene_intent}'
        storyline_lines.append(scene_line)
    role_title_lines = [
        '',
        '五、角色档案',
    ]
    storyline_lines.extend(role_title_lines)
    for profile_key, profile in CHARACTER_PROFILES.items():
        profile_name = profile['name']
        profile_title = profile['title']
        language_style = profile['language_style']
        bio = profile['bio']
        personality = profile['personality']
        profile_line = f'· {profile_name}｜副标题：{profile_title}｜语言风格：{language_style}｜人物小传：{bio}｜性格：{personality}'
        storyline_lines.append(profile_line)
    story_flow_lines = [
        '',
        '六、面试讲解重点',
        'Pygame 事件循环、按钮悬停、tooltip 区域登记、NetworkX 无权图最短路、状态机、确定性自动游玩、ImageIO 录制、NumPy 帧维度转换与合成音效采样、Pillow 发布图生成、Loguru 中文日志、PrettyTable 控制表、Humanize 时间跨度展示、More Itertools 分组布局。',
        '推荐书：中文《游戏编程模式》《算法图解》《数据结构与算法分析》；英文 Game Programming Patterns、The Algorithm Design Manual、Python Data Science Handbook。',
    ]
    storyline_lines.extend(story_flow_lines)
    storyline_text = '\n'.join(storyline_lines)
    return storyline_text


def build_original_story_text():
    """生成小红帽传统故事文本。

    :return: 小红帽传统故事文本。
    """
    original_story_lines = [
        '小红帽传统故事',
        '',
        '从前，有一个小女孩总戴着一顶红色的小帽子，大家都叫她小红帽。',
        '一天，妈妈把一篮面包和点心交给她，让她去看望住在森林另一边的外婆。',
        '妈妈叮嘱她走在路上不要乱跑，不要离开小路，也不要和陌生人闲谈。',
        '小红帽提着篮子进了森林。她遇见一只灰狼。灰狼假装亲切地问她要去哪里。',
        '小红帽说自己要去外婆家。灰狼听后，先一步跑到外婆家，把外婆吞进肚子里，又穿上外婆的衣服躺在床上。',
        '小红帽来到外婆家，看见床上的“外婆”很奇怪。',
        '她问：外婆，为什么你的耳朵这么大？灰狼回答：为了更好地听你说话。',
        '她问：外婆，为什么你的眼睛这么大？灰狼回答：为了更好地看见你。',
        '她问：外婆，为什么你的手这么大？灰狼回答：为了更好地抱住你。',
        '她问：外婆，为什么你的牙齿这么大？灰狼回答：为了把你吃掉。',
        '后来猎人经过小屋，听见屋里异常的声音，救出了小红帽和外婆。',
        '从那以后，小红帽记住了妈妈的叮嘱：不要轻信陌生人的甜言蜜语，也不要离开安全的小路。',
    ]
    original_story_text = '\n'.join(original_story_lines)
    return original_story_text


def build_fountain_text():
    """生成 Fountain 格式完整游戏剧本。

    面试考点：代码里的剧情数据可以渲染为游戏对白，也可以渲染为外部稳定文本协议。
    推荐书：中文《游戏编程模式》，英文 Game Programming Patterns。

    :return: Fountain 格式剧本文本。
    """
    fountain_lines = [
        'Title: 小红帽RPG',
        'Credit: Game Screenplay Export / 游戏剧本导出',
        'Author: momo project',
        '',
        '# 使用说明',
        '',
        '这是由 RUN_MODE = fountain 生成的完整游戏剧本。',
        '场景标题由 STORY_ACTION_SPECS 中的 scene、location_type 和 time_key 合成。',
        '对白和动作说明也直接来自 STORY_ACTION_SPECS，因此游戏内对白和剧本导出保持一致。',
        '',
        '# 火柴盒监狱信息差',
        '',
    ]
    fountain_lines.extend(MATCHBOX_PRISON_SECRET_LINES)
    role_title_lines = [
        '',
        '# 角色档案',
        '',
    ]
    fountain_lines.extend(role_title_lines)
    for profile_key, profile in CHARACTER_PROFILES.items():
        profile_name = profile['name']
        profile_title = profile['title']
        language_style = profile['language_style']
        bio = profile['bio']
        personality = profile['personality']
        profile_lines = [
            f'## {profile_name}｜{profile_title}',
            '',
            f'语言风格：{language_style}',
            f'人物小传：{bio}',
            f'性格：{personality}',
            '',
        ]
        fountain_lines.extend(profile_lines)
    current_section = ''
    for story_key in FOUNTAIN_STORY_SEQUENCE:
        story_spec = STORY_ACTION_SPECS[story_key]
        section = story_spec['section']
        if current_section != section:
            current_section = section
            section_lines = [
                f'# {section}',
                '',
            ]
            fountain_lines.extend(section_lines)
        scene_key = story_spec['scene']
        scene_name = SCENE_NAMES[scene_key]
        location_type = story_spec['location_type']
        time_key = story_spec['time_key']
        time_name = TIME_OF_DAY_SPECS[time_key]['name']
        heading = f'{location_type}. {scene_name} - {time_name}'
        scene_lines = [
            heading,
            '',
        ]
        fountain_lines.extend(scene_lines)
        actions = story_spec['actions']
        for action in actions:
            action_lines = [
                action,
                '',
            ]
            fountain_lines.extend(action_lines)
        dialogue_entries = story_spec['dialogue']
        for dialogue_entry in dialogue_entries:
            speaker_key = dialogue_entry[0]
            speech = dialogue_entry[1]
            speaker_text = fountain_speaker_text(speaker_key)
            dialogue_lines = [
                speaker_text,
                speech,
                '',
            ]
            fountain_lines.extend(dialogue_lines)
    appendix_lines = [
        '# 系统化剧情节点',
        '',
        '[[自动游玩目标顺序]]',
        '和妈妈说话 -> 听妈妈三问提示 -> 认识村口行商 -> 遇见灰狼 -> 找猎人 -> 揭开假外婆 -> 囚禁灰狼 -> 听灰狼求饶 -> 听外婆说出艾琳火柴真相 -> 雪夜街口问报童 -> 密语酒店多人密会 -> 男性俊美卧底维克托暴露 -> 艾琳视角巡视监狱 -> 金发贫嘴男救援 -> 火柴总店街确认袭击 -> 王城火柴广场最终战 -> 回村口找村长开启结局 CG',
        '',
        '[[录制模式道具策略]]',
        f'RECORD_AUTO_PICKUP_REACHABLE_ITEMS_DEFAULT = {RECORD_AUTO_PICKUP_REACHABLE_ITEMS_DEFAULT}',
        '',
        '[[火柴盒监狱结构秘密]]',
        MATCHBOX_PRISON_SECRET_TEXT,
        '',
        'THE END',
    ]
    fountain_lines.extend(appendix_lines)
    fountain_text = '\n'.join(fountain_lines)
    return fountain_text


def output_storyline_text(storyline_text):
    """输出剧情线文本。

    :param storyline_text: 完整剧情线文本。
    """
    print(storyline_text)
    STORYLINE_PATH.write_text(storyline_text, encoding='utf-8')
    logger.info(f'剧情线已输出到：{STORYLINE_PATH}')


def output_original_story_text(original_story_text):
    """输出小红帽传统故事文本。

    :param original_story_text: 小红帽传统故事文本。
    """
    print(original_story_text)
    ORIGINAL_STORY_PATH.write_text(original_story_text, encoding='utf-8')
    logger.info(f'小红帽传统故事已输出到：{ORIGINAL_STORY_PATH}')


def output_fountain_text(fountain_text):
    """输出 Fountain 格式游戏剧本。

    :param fountain_text: Fountain 格式游戏剧本文本。
    """
    print(fountain_text)
    FOUNTAIN_PATH.write_text(fountain_text, encoding='utf-8')
    logger.info(f'Fountain 格式游戏剧本已输出到：{FOUNTAIN_PATH}')


def create_initial_flags():
    """创建初始剧情标记。

    :return: 初始剧情标记字典。
    """
    flags = {
        'got_basket': False,
        'mother_hint': False,
        'met_merchant': False,
        'wolf_met': False,
        'met_hunter': False,
        'wolf_defeated': False,
        'wolf_caged': False,
        'wolf_exiled': False,
        'heard_wolf_plea': False,
        'met_grandma_after': False,
        'chapter_two_started': False,
        'grandma_lost': False,
        'heard_gossip': False,
        'met_hotel_keeper': False,
        'met_resistance_scout': False,
        'met_secret_medic': False,
        'met_spy_youth': False,
        'met_resistance': False,
        'exposed_by_spy': False,
        'captured_by_aileen': False,
        'pov_aileen_started': False,
        'prison_aileen_visit': False,
        'key_dropped': False,
        'pov_blond_friend_started': False,
        'prison_rooms_opened': False,
        'prisoners_released': False,
        'prison_escaped': False,
        'shop_attacks_reported': False,
        'royal_accusation': False,
        'aileen_defeated': False,
        'aileen_fled': False,
        'aileen_found_dead': False,
        'ending_ready': False,
        'ending_cg_seen': False,
        'honeys': 0,
        'wildflowers': 0,
        'truth_clues': 0,
        'match_clues': 0,
        'cloths': 0,
        'kindness': 0,
        'shop_trades': 0,
        'steps_taken': 0,
        'auto_actions': 0,
        'battles_won': 0,
        'final_battle_rounds': 0,
    }
    return flags


def create_initial_inventory():
    """创建初始背包。

    :return: 初始背包字典。
    """
    inventory = {}
    for inventory_key in INVENTORY_KEYS:
        inventory[inventory_key] = 0
    return inventory


def create_player():
    """创建玩家状态。

    :return: 玩家状态字典。
    """
    player = {
        'x': 10,
        'y': 11,
        'px': 10 * TILE,
        'py': 11 * TILE,
        'target_x': 10,
        'target_y': 11,
        'dir': (0, 1),
        'moving': False,
        'speed': 8,
        'step_timer': 0,
        'max_hp': PLAYER_MAX_HP,
        'hp': PLAYER_MAX_HP,
    }
    return player


def create_settings():
    """创建游戏设置。

    :return: 设置字典。
    """
    settings = {
        'auto_pickup_reachable_items': AUTO_PICKUP_REACHABLE_ITEMS_DEFAULT,
        'show_minimap': True,
        'show_story_progress': True,
        'show_path_hint': True,
        'sound_enabled': True,
        'particles_enabled': ENABLE_PARTICLES,
        'tooltip_enabled': False,
    }
    return settings


def create_scroll_offsets():
    """创建面板滚动偏移。

    :return: 面板滚动偏移字典。
    """
    scroll_offsets = {
        'journal': 0,
        'inventory': 0,
        'map': 0,
        'codex': 0,
        'pause': 0,
        'shop': 0,
    }
    return scroll_offsets


def create_game_state():
    """创建完整游戏状态。

    :return: 完整游戏状态字典。
    """
    player = create_player()
    flags = create_initial_flags()
    inventory = create_initial_inventory()
    settings = create_settings()
    scroll_offsets = create_scroll_offsets()
    game_state = {
        'scene': 'home',
        'time_of_day': 'morning',
        'view_actor': 'red',
        'ui_state': 'title',
        'previous_ui_state': 'explore',
        'player': player,
        'dialogue': None,
        'battle': None,
        'tick': 0,
        'message': '',
        'message_timer': 0,
        'auto_play': False,
        'auto_paused_by_user': False,
        'voice_enabled': False,
        'auto_speed_index': 0,
        'auto_timer': 0,
        'battle_auto_timer': 0,
        'hero_index': 0,
        'hero_key': HERO_VARIANTS[0]['key'],
        'title_skip_acts': NORMAL_START_SKIP_ACTS_DEFAULT,
        'flags': flags,
        'inventory': inventory,
        'settings': settings,
        'scroll_offsets': scroll_offsets,
        'collected': set(),
        'badges': set(),
        'visited_scenes': {'home'},
        'codex': {'露比｜小红帽', '妈妈的小屋'},
        'story_log': ['妈妈的小屋里飘着面包香，红斗篷还不知道两场黑夜正等着她。'],
        'sound_events': [],
        'buttons': [],
        'ui_areas': [],
        'mouse_pos': (0, 0),
        'judgement_choice': None,
    }
    return game_state


def create_tone_sound(frequency, duration, volume):
    """创建脚本内合成短音效。

    Pygame mixer 可以直接播放采样数据。
    NumPy 是第三方数值计算库，本函数用 NumPy 批量生成正弦波采样，而不是手写逐样本循环。
    面试考点：NumPy 的优势是把逐点计算变成数组运算，代码更短，也更接近音频与图像处理中常见的张量思维。
    int16 对应 16 位有符号整数采样；采样率 SOUND_SAMPLE_RATE 表示每秒采样点数量。
    推荐书：中文《利用 Python 进行数据分析》，英文 Python Data Science Handbook。

    :param frequency: 声音频率。
    :param duration: 声音秒数。
    :param volume: 声音音量。
    :return: Pygame Sound 音效对象。
    """
    frame_count = int(SOUND_SAMPLE_RATE * duration)
    sample_indexes = np.arange(frame_count)
    angle_values = 2 * np.pi * frequency * sample_indexes / SOUND_SAMPLE_RATE
    amplitude_values = np.sin(angle_values)
    scaled_samples = 32767 * volume * amplitude_values
    int_samples = scaled_samples.astype(np.int16)
    sample_bytes = int_samples.tobytes()
    sound = pygame.mixer.Sound(buffer=sample_bytes)
    return sound


def create_sound_bank():
    """创建音效库。

    :return: 音效字典。
    """
    sounds = {}
    if ENABLE_SOUND_EFFECTS:
        sounds['click'] = create_tone_sound(520, 0.06, 0.18)
        sounds['pickup'] = create_tone_sound(760, 0.09, 0.20)
        sounds['badge'] = create_tone_sound(980, 0.12, 0.22)
        sounds['portal_open'] = create_tone_sound(640, 0.12, 0.18)
        sounds['portal_closed'] = create_tone_sound(180, 0.10, 0.16)
        sounds['battle'] = create_tone_sound(260, 0.10, 0.18)
        sounds['heal'] = create_tone_sound(700, 0.11, 0.18)
        sounds['shop'] = create_tone_sound(880, 0.07, 0.18)
        sounds['judgement'] = create_tone_sound(440, 0.16, 0.18)
    return sounds


def create_app_state():
    """创建 Pygame 应用状态。

    Pygame 是第三方游戏开发库。Surface 可以理解为画布，display Surface 是窗口，canvas Surface 是逻辑画布。
    Clock 控制帧率，事件循环处理键盘、鼠标和窗口关闭。
    面试考点：Pygame 不是完整 GUI 框架，它更接近游戏循环底层工具，所以按钮 hover、tooltip、面板都由 Rect 命中测试和每帧重绘实现。
    pyttsx3 是离线 Text To Speech（文本转语音，TTS）第三方库；本脚本只在 Windows 初始化它，macOS 走系统 say 命令。
    推荐书：英文 Making Games with Python & Pygame；中文可结合《游戏编程模式》理解状态机与渲染分层。

    :return: 应用状态字典。
    """
    pygame.mixer.pre_init(SOUND_SAMPLE_RATE, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    canvas = pygame.Surface((VW, VH))
    clock = pygame.time.Clock()
    tiny_font = pygame.font.Font(yahei_regular_font, 14)
    small_font = pygame.font.Font(yahei_regular_font, 16)
    normal_font = pygame.font.Font(yahei_regular_font, 18)
    big_font = pygame.font.Font(yahei_bold_font, 24)
    title_font = pygame.font.Font(yahei_bold_font, 36)
    fonts = {
        'tiny': tiny_font,
        'small': small_font,
        'normal': normal_font,
        'big': big_font,
        'title': title_font,
    }
    title_stars = []
    star_rng = random.Random(9)
    for star_index in range(140):
        star_x = star_rng.randint(0, VW - 1)
        star_y = star_rng.randint(0, VH - 1)
        star = (star_x, star_y, star_index)
        title_stars.append(star)
    particle_seed = random.Random(31)
    particles = []
    for particle_index in range(90):
        particle_x = particle_seed.randint(0, VIEW_W - 1)
        particle_y = particle_seed.randint(0, VIEW_H - 1)
        particle_speed = 1 + particle_seed.randint(0, 2)
        particle = (particle_x, particle_y, particle_speed, particle_index)
        particles.append(particle)
    if sys.platform == 'win32':
        tts_engine = pyttsx3.init()
    else:
        tts_engine = None
    game_state = create_game_state()
    sounds = create_sound_bank()
    app_state = {
        'screen': screen,
        'canvas': canvas,
        'clock': clock,
        'fonts': fonts,
        'game_state': game_state,
        'tts_engine': tts_engine,
        'sounds': sounds,
        'title_stars': title_stars,
        'particles': particles,
        'running': True,
    }
    logger.info('Pygame 已初始化：窗口、字体、状态字典、按钮系统、tooltip 默认关闭、标题跳幕、自动游玩、录制帧源、多视角主角和朗读准备完成。')
    return app_state


def queue_sound(game_state, sound_key):
    """排队播放音效。

    :param game_state: 游戏状态字典。
    :param sound_key: 音效编号。
    """
    settings = game_state['settings']
    if ENABLE_SOUND_EFFECTS and settings['sound_enabled']:
        sound_events = game_state['sound_events']
        sound_events.append(sound_key)


def play_queued_sounds(sounds, game_state):
    """播放游戏状态里排队的音效。

    :param sounds: 音效字典。
    :param game_state: 游戏状态字典。
    """
    sound_events = game_state['sound_events']
    while sound_events:
        sound_key = sound_events.pop(0)
        sound = sounds[sound_key]
        sound.play()


def set_player_tile(player, x, y):
    """把玩家直接放到某个瓦片坐标。

    :param player: 玩家状态字典。
    :param x: 目标瓦片横坐标。
    :param y: 目标瓦片纵坐标。
    """
    player['x'] = x
    player['y'] = y
    player['target_x'] = x
    player['target_y'] = y
    player['px'] = x * TILE
    player['py'] = y * TILE
    player['moving'] = False


def set_time_of_day(game_state, time_key):
    """设置当前时段。

    游戏表现清晨、白天、黄昏、黑夜、深夜和黎明。
    这里把时间作为游戏状态保存，渲染层再根据状态叠加不同颜色遮罩。

    :param game_state: 游戏状态字典。
    :param time_key: 时间编号。
    """
    game_state['time_of_day'] = time_key
    time_name = TIME_OF_DAY_SPECS[time_key]['name']
    logger.info(f'游戏时间切换为：{time_name}')


def set_view_actor(game_state, actor_key):
    """切换当前主视角角色。

    多视角剧情只改 view_actor，不改 player 结构。
    面试考点：表现层角色和物理控制器解耦后，剧情主视角切换不会破坏底层移动系统。

    :param game_state: 游戏状态字典。
    :param actor_key: 主视角角色编号。
    """
    game_state['view_actor'] = actor_key
    actor_spec = ACTOR_SPECS[actor_key]
    profile_key = actor_spec['profile_key']
    actor_name = profile_display_text(profile_key)
    add_codex(game_state, actor_name)
    logger.info(f'主视角切换为：{actor_name}')


def show_message(game_state, text, frames=150):
    """显示短提示。

    :param game_state: 游戏状态字典。
    :param text: 提示文本。
    :param frames: 显示帧数。
    """
    game_state['message'] = text
    game_state['message_timer'] = frames


def set_flag(game_state, key, value):
    """设置剧情标记。

    :param game_state: 游戏状态字典。
    :param key: 标记名。
    :param value: 标记值。
    """
    flags = game_state['flags']
    flags[key] = value
    logger.info(f'剧情标记更新：{key} = {value}')


def add_story(game_state, text):
    """向森林札记追加剧情记录。

    :param game_state: 游戏状态字典。
    :param text: 需要记录的剧情文本。
    """
    story_log = game_state['story_log']
    story_log.append(text)
    logger.info(f'森林札记更新：{text}')


def add_codex(game_state, entry_name):
    """向森林图鉴追加条目。

    :param game_state: 游戏状态字典。
    :param entry_name: 图鉴条目名称。
    """
    codex = game_state['codex']
    if entry_name not in codex:
        codex.add(entry_name)
        logger.info(f'森林图鉴新增：{entry_name}')


def add_profile_codex_by_key(game_state, profile_key):
    """按角色档案编号把角色加入图鉴。

    :param game_state: 游戏状态字典。
    :param profile_key: 角色档案编号。
    """
    profile_text = profile_display_text(profile_key)
    add_codex(game_state, profile_text)


def award_badge(game_state, badge_key):
    """授予成就徽章。

    :param game_state: 游戏状态字典。
    :param badge_key: 成就编号。
    """
    badges = game_state['badges']
    if badge_key not in badges:
        badges.add(badge_key)
        badge_name = BADGE_NAMES[badge_key]
        logger.info(f'获得成就：{badge_name}')
        badge_text = f'获得成就：{badge_name}'
        show_message(game_state, badge_text, 170)
        queue_sound(game_state, 'badge')


def apply_start_skip_to_game_state(game_state, skip_acts, source_name):
    """按照跳过幕数初始化剧情进度。

    这个函数是标题跳幕、自动模式跳幕和录制模式跳幕的核心。
    它采用逐幕累积 flags 的方式，而不是直接创建多套存档模板。
    TODO：如果以后剧情继续扩展，可以把这里改成更严格的数据表驱动 checkpoint 系统。

    :param game_state: 游戏状态字典。
    :param skip_acts: 跳过的幕数，0 表示不跳过。
    :param source_name: 触发来源，用于中文日志说明。
    """
    if skip_acts < 0 or skip_acts > MAX_START_SKIP_ACTS:
        raise ValueError(f'跳过幕数超出范围：{skip_acts}')
    if skip_acts > 0:
        flags = game_state['flags']
        inventory = game_state['inventory']
        collected = game_state['collected']
        badges = game_state['badges']
        codex = game_state['codex']
        visited_scenes = game_state['visited_scenes']
        story_log = game_state['story_log']
        flags['got_basket'] = True
        flags['mother_hint'] = True
        flags['met_merchant'] = True
        flags['honeys'] = 2
        flags['truth_clues'] = 1
        flags['kindness'] = 1
        inventory['铜币'] = 18
        inventory['面包'] = 1
        inventory['蜂蜜'] = 2
        inventory['红缎带'] = 1
        inventory['真相线索'] = 1
        badges.add('basket')
        badges.add('first_honey')
        codex.add('妈妈的篮子')
        codex.add('三问识伪')
        codex.add('村口市场')
        codex.add(profile_display_text('mother'))
        codex.add(profile_display_text('merchant'))
        visited_scenes.add('home')
        visited_scenes.add('village')
        story_log.append('跳幕起始：已完成第一幕，露比拿到篮子、记住三问，并认识村口行商。')
        if skip_acts >= 2:
            flags['wolf_met'] = True
            flags['met_hunter'] = True
            flags['truth_clues'] = 2
            inventory['猎人银铃'] = 1
            inventory['油灯'] = 1
            inventory['清醒卡片'] = 1
            inventory['真相线索'] = 2
            badges.add('clear_minded')
            badges.add('truth_seeker')
            codex.add(profile_display_text('wolf'))
            codex.add(profile_display_text('hunter'))
            codex.add('猎人银铃')
            codex.add('清醒卡片')
            collected.add('clue_1')
            visited_scenes.add('forest')
            story_log.append('跳幕起始：已完成第二幕，露比见过灰狼，并从猎人伊沃处取得银铃、油灯和清醒卡片。')
        if skip_acts >= 3:
            flags['wolf_defeated'] = True
            flags['wolf_caged'] = True
            flags['battles_won'] = 1
            flags['final_battle_rounds'] = 4
            badges.add('wolf_defeated')
            badges.add('wolf_caged')
            codex.add('灰狼囚笼')
            visited_scenes.add('cottage')
            visited_scenes.add('cage_yard')
            story_log.append('跳幕起始：已完成第三幕，灰狼被击败并囚禁。')
        if skip_acts >= 4:
            flags['heard_wolf_plea'] = True
            flags['met_grandma_after'] = True
            flags['chapter_two_started'] = True
            flags['grandma_lost'] = True
            flags['match_clues'] = 1
            inventory['火柴证据'] = 1
            badges.add('chapter_two')
            codex.add(profile_display_text('grandma'))
            codex.add('致幻性火柴')
            visited_scenes.add('winter_street')
            story_log.append('跳幕起始：已完成第四幕，外婆说出艾琳蓝火柴真相，雪夜调查开启。')
        if skip_acts >= 5:
            flags['heard_gossip'] = True
            codex.add(profile_display_text('newspaper_boy'))
            codex.add('雪夜闲言')
            collected.add('clue_2')
            visited_scenes.add('whisper_hotel')
            story_log.append('跳幕起始：已完成第五幕，报童说出密语酒店方向。')
        if skip_acts >= 6:
            flags['met_hotel_keeper'] = True
            flags['met_resistance_scout'] = True
            flags['met_secret_medic'] = True
            flags['met_spy_youth'] = True
            flags['met_resistance'] = True
            flags['exposed_by_spy'] = True
            flags['captured_by_aileen'] = True
            flags['pov_aileen_started'] = True
            inventory['酒店名单'] = 1
            badges.add('hotel_crowd')
            badges.add('hotel_conspiracy')
            badges.add('male_spy')
            badges.add('pov_aileen')
            codex.add(profile_display_text('hotel_keeper'))
            codex.add(profile_display_text('resistance_scout'))
            codex.add(profile_display_text('secret_medic'))
            codex.add(profile_display_text('resistance_leader'))
            codex.add(profile_display_text('spy'))
            codex.add(profile_display_text('aileen'))
            codex.add('密语酒店多人密会')
            codex.add('艾琳男卧底')
            visited_scenes.add('matchbox_prison')
            story_log.append('跳幕起始：已完成第六幕，密语酒店多人密会被俊美男卧底维克托暴露，主视角切换为艾琳。')
        if skip_acts >= 7:
            flags['prison_aileen_visit'] = True
            flags['key_dropped'] = True
            flags['pov_blond_friend_started'] = True
            badges.add('pov_blond_friend')
            codex.add(profile_display_text('blond_friend'))
            codex.add(profile_display_text('blue_match_messenger'))
            codex.add('火柴盒监狱')
            codex.add('火柴盒抽拉结构')
            story_log.append('跳幕起始：已完成第七幕，艾琳得知店铺被袭击并丢下钥匙，主视角切换为莱昂。')
        if skip_acts >= 8:
            flags['prison_rooms_opened'] = True
            flags['prisoners_released'] = True
            flags['prison_escaped'] = True
            inventory['牢房钥匙'] = 1
            badges.add('matchbox_prison')
            visited_scenes.add('match_market')
            story_log.append('跳幕起始：已完成第八幕，莱昂利用火柴盒抽拉结构打开牢门，露比和被关的人逃出监狱。')
        if skip_acts >= 9:
            flags['shop_attacks_reported'] = True
            flags['match_clues'] = 2
            inventory['火柴证据'] = 2
            badges.add('shop_raids')
            codex.add(profile_display_text('red_cloak'))
            codex.add('红斗篷袭击')
            collected.add('clue_3')
            visited_scenes.add('royal_square')
            story_log.append('跳幕起始：已完成第九幕，十几个火柴店铺被红斗篷同时袭击。')
        if skip_acts >= 10:
            flags['royal_accusation'] = True
            flags['aileen_defeated'] = True
            flags['aileen_fled'] = True
            flags['aileen_found_dead'] = True
            flags['ending_ready'] = True
            flags['battles_won'] = 2
            badges.add('aileen_defeated')
            codex.add(profile_display_text('king'))
            story_log.append('跳幕起始：已完成第十幕，艾琳被击败并被发现死在用完的火柴旁。')
        if skip_acts == 1:
            game_state['scene'] = 'forest'
            set_view_actor(game_state, 'red')
            set_time_of_day(game_state, 'day')
            player = game_state['player']
            set_player_tile(player, 10, 7)
        elif skip_acts == 2:
            game_state['scene'] = 'cottage'
            set_view_actor(game_state, 'red')
            set_time_of_day(game_state, 'dusk')
            player = game_state['player']
            set_player_tile(player, 10, 13)
        elif skip_acts == 3:
            game_state['scene'] = 'cage_yard'
            set_view_actor(game_state, 'red')
            set_time_of_day(game_state, 'night')
            player = game_state['player']
            set_player_tile(player, 10, 1)
        elif skip_acts == 4:
            game_state['scene'] = 'winter_street'
            set_view_actor(game_state, 'red')
            set_time_of_day(game_state, 'night')
            player = game_state['player']
            set_player_tile(player, 1, 7)
        elif skip_acts == 5:
            game_state['scene'] = 'whisper_hotel'
            set_view_actor(game_state, 'red')
            set_time_of_day(game_state, 'night')
            player = game_state['player']
            set_player_tile(player, 1, 7)
        elif skip_acts == 6:
            game_state['scene'] = 'matchbox_prison'
            set_view_actor(game_state, 'aileen')
            set_time_of_day(game_state, 'deep_night')
            player = game_state['player']
            set_player_tile(player, 10, 10)
        elif skip_acts == 7:
            game_state['scene'] = 'matchbox_prison'
            set_view_actor(game_state, 'blond_friend')
            set_time_of_day(game_state, 'deep_night')
            player = game_state['player']
            set_player_tile(player, 10, 10)
        elif skip_acts == 8:
            game_state['scene'] = 'match_market'
            set_view_actor(game_state, 'red')
            set_time_of_day(game_state, 'dawn')
            player = game_state['player']
            set_player_tile(player, 1, 7)
        elif skip_acts == 9:
            game_state['scene'] = 'royal_square'
            set_view_actor(game_state, 'red')
            set_time_of_day(game_state, 'dawn')
            player = game_state['player']
            set_player_tile(player, 1, 7)
        else:
            game_state['scene'] = 'village'
            set_view_actor(game_state, 'red')
            set_time_of_day(game_state, 'morning')
            player = game_state['player']
            set_player_tile(player, 10, 7)
        game_state['ui_state'] = 'explore'
        act_title = START_ACT_OPTIONS[skip_acts]['title']
        show_message(game_state, f'{source_name}：已跳过 {skip_acts} 幕，从「{act_title}」开始。', 220)
        logger.info(f'{source_name}应用起始幕：跳过 {skip_acts} 幕，起始为 {act_title}。')


def prepare_record_mode(app_state):
    """准备自动游玩录制模式。

    :param app_state: 应用状态字典。
    """
    game_state = app_state['game_state']
    settings = game_state['settings']
    game_state['auto_play'] = True
    game_state['auto_paused_by_user'] = False
    game_state['voice_enabled'] = RECORD_ENABLE_VOICE
    game_state['auto_speed_index'] = RECORD_AUTO_SPEED_INDEX
    game_state['title_skip_acts'] = RECORD_SKIP_ACTS_DEFAULT
    settings['sound_enabled'] = False
    settings['particles_enabled'] = ENABLE_PARTICLES
    settings['auto_pickup_reachable_items'] = RECORD_AUTO_PICKUP_REACHABLE_ITEMS_DEFAULT
    award_badge(game_state, 'autoplayer')
    apply_start_skip_to_game_state(game_state, RECORD_SKIP_ACTS_DEFAULT, '录制模式')
    logger.info(f'录制模式已启动：默认跳过 {RECORD_SKIP_ACTS_DEFAULT} 幕，自动游玩开启，自动拾取可达道具={RECORD_AUTO_PICKUP_REACHABLE_ITEMS_DEFAULT}，输出文件为 {RECORD_PATH}。')


def write_recording_frame(record_writer, canvas):
    """把当前画布写入录制器。

    Pygame surfarray 默认维度是宽、高、通道；视频编码器通常需要高、宽、通道。
    NumPy 的 swapaxes 在这里负责维度转换，是面试中解释“图像张量维度”的好例子。
    ImageIO 是第三方图像与视频 I/O 库，适合快速把游戏自动演示保存为 MP4。
    推荐书：英文 Python Data Science Handbook；中文可参考《利用 Python 进行数据分析》。

    :param record_writer: ImageIO 视频写入器。
    :param canvas: Pygame 逻辑画布。
    """
    frame_array = pygame.surfarray.array3d(canvas)
    video_frame = np.swapaxes(frame_array, 0, 1)
    record_writer.append_data(video_frame)


def pressed_any_key(pressed_keys, key_codes):
    """判断一组按键里是否有任意键处于按下状态。

    :param pressed_keys: Pygame 当前按键状态序列。
    :param key_codes: 需要检查的按键编号集合。
    :return: True 表示至少一个按键被按下，False 表示没有按下。
    """
    pressed = False
    for key_code in key_codes:
        if pressed_keys[key_code]:
            pressed = True
    return pressed


def start_player_move(player, dx, dy):
    """开始向相邻瓦片移动。

    :param player: 玩家状态字典。
    :param dx: 横向移动方向。
    :param dy: 纵向移动方向。
    """
    player['dir'] = (dx, dy)
    player['target_x'] = player['x'] + dx
    player['target_y'] = player['y'] + dy
    player['moving'] = True


def update_player_move(player):
    """更新玩家移动动画。

    :param player: 玩家状态字典。
    :return: True 表示刚刚到达目标格，False 表示还在移动或没有移动。
    """
    arrived = False
    if player['moving']:
        target_px = player['target_x'] * TILE
        target_py = player['target_y'] * TILE
        if player['px'] < target_px:
            player['px'] = min(player['px'] + player['speed'], target_px)
        elif player['px'] > target_px:
            player['px'] = max(player['px'] - player['speed'], target_px)
        if player['py'] < target_py:
            player['py'] = min(player['py'] + player['speed'], target_py)
        elif player['py'] > target_py:
            player['py'] = max(player['py'] - player['speed'], target_py)
        player['step_timer'] = (player['step_timer'] + 1) % 32
        if player['px'] == target_px and player['py'] == target_py:
            player['x'] = player['target_x']
            player['y'] = player['target_y']
            player['moving'] = False
            arrived = True
    return arrived


def current_hero_name(game_state):
    """取得当前小红帽形象名称。

    :param game_state: 游戏状态字典。
    :return: 当前小红帽形象名称。
    """
    hero_index = game_state['hero_index']
    hero_variant = HERO_VARIANTS[hero_index]
    hero_name = hero_variant['name']
    return hero_name


def current_hero_desc(game_state):
    """取得当前小红帽形象描述。

    :param game_state: 游戏状态字典。
    :return: 当前小红帽形象描述。
    """
    hero_index = game_state['hero_index']
    hero_variant = HERO_VARIANTS[hero_index]
    hero_desc = hero_variant['desc']
    return hero_desc


def current_view_actor_name(game_state):
    """取得当前主视角角色名称。

    :param game_state: 游戏状态字典。
    :return: 当前主视角角色名称。
    """
    actor_key = game_state['view_actor']
    actor_spec = ACTOR_SPECS[actor_key]
    profile_key = actor_spec['profile_key']
    actor_name = profile_display_text(profile_key)
    return actor_name


def current_view_actor_role(game_state):
    """取得当前主视角角色绘制类型。

    :param game_state: 游戏状态字典。
    :return: 当前主视角角色绘制类型。
    """
    actor_key = game_state['view_actor']
    actor_spec = ACTOR_SPECS[actor_key]
    actor_role = actor_spec['role']
    return actor_role


def current_hero_attack_bonus(game_state):
    """取得当前小红帽攻击加成。

    :param game_state: 游戏状态字典。
    :return: 当前小红帽攻击加成。
    """
    hero_index = game_state['hero_index']
    hero_variant = HERO_VARIANTS[hero_index]
    attack_bonus = hero_variant['attack_bonus']
    return attack_bonus


def current_hero_defense_bonus(game_state):
    """取得当前小红帽防御加成。

    :param game_state: 游戏状态字典。
    :return: 当前小红帽防御加成。
    """
    hero_index = game_state['hero_index']
    hero_variant = HERO_VARIANTS[hero_index]
    defense_bonus = hero_variant['defense_bonus']
    return defense_bonus


def current_hero_kindness_bonus(game_state):
    """取得当前小红帽善意加成。

    :param game_state: 游戏状态字典。
    :return: 当前小红帽善意加成。
    """
    hero_index = game_state['hero_index']
    hero_variant = HERO_VARIANTS[hero_index]
    kindness_bonus = hero_variant['kindness_bonus']
    return kindness_bonus


def select_next_hero(game_state):
    """选择下一个小红帽形象。

    :param game_state: 游戏状态字典。
    """
    if game_state['view_actor'] == 'red':
        hero_index = game_state['hero_index']
        game_state['hero_index'] = (hero_index + 1) % len(HERO_VARIANTS)
        new_hero_index = game_state['hero_index']
        hero_variant = HERO_VARIANTS[new_hero_index]
        game_state['hero_key'] = hero_variant['key']
        queue_sound(game_state, 'click')
    else:
        show_message(game_state, '当前主视角不是红斗篷，暂时不能换装。')


def select_previous_hero(game_state):
    """选择上一个小红帽形象。

    :param game_state: 游戏状态字典。
    """
    if game_state['view_actor'] == 'red':
        hero_index = game_state['hero_index']
        game_state['hero_index'] = (hero_index - 1) % len(HERO_VARIANTS)
        new_hero_index = game_state['hero_index']
        hero_variant = HERO_VARIANTS[new_hero_index]
        game_state['hero_key'] = hero_variant['key']
        queue_sound(game_state, 'click')
    else:
        show_message(game_state, '当前主视角不是红斗篷，暂时不能换装。')


def select_title_start_act(game_state, delta):
    """在标题界面调整起始幕。

    :param game_state: 游戏状态字典。
    :param delta: 起始幕变化量，正数表示向后，负数表示向前。
    """
    next_skip_acts = game_state['title_skip_acts'] + delta
    if 0 <= next_skip_acts <= MAX_START_SKIP_ACTS:
        game_state['title_skip_acts'] = next_skip_acts
        act_title = START_ACT_OPTIONS[next_skip_acts]['title']
        show_message(game_state, f'起始幕已切换为：{act_title}。')
        queue_sound(game_state, 'click')
    else:
        show_message(game_state, '已经到达可选起始幕边界。')


def current_auto_speed(game_state):
    """取得当前自动对白速度。

    :param game_state: 游戏状态字典。
    :return: 自动对白速度倍率。
    """
    auto_speed_index = game_state['auto_speed_index']
    auto_speed = AUTO_SPEEDS[auto_speed_index]
    return auto_speed


def set_auto_speed(game_state, auto_speed_index):
    """设置自动对白速度。

    :param game_state: 游戏状态字典。
    :param auto_speed_index: 速度索引。
    """
    game_state['auto_speed_index'] = auto_speed_index
    auto_speed = current_auto_speed(game_state)
    text = f'自动对白速度：{auto_speed} 倍速。'
    show_message(game_state, text)
    logger.info(f'自动对白速度调整为 {auto_speed} 倍速。')
    queue_sound(game_state, 'click')


def toggle_auto_pickup_reachable(game_state):
    """切换自动拾取当前地图所有可达物品设置。

    :param game_state: 游戏状态字典。
    """
    settings = game_state['settings']
    settings['auto_pickup_reachable_items'] = not settings['auto_pickup_reachable_items']
    if settings['auto_pickup_reachable_items']:
        show_message(game_state, '自动拾取当前地图所有可达物品：开启。')
    else:
        show_message(game_state, '自动拾取当前地图所有可达物品：关闭。')
    queue_sound(game_state, 'click')


def toggle_path_hint(game_state):
    """切换非自动模式下的寻路指示线。

    :param game_state: 游戏状态字典。
    """
    settings = game_state['settings']
    settings['show_path_hint'] = not settings['show_path_hint']
    if settings['show_path_hint']:
        show_message(game_state, '寻路指示线已开启。')
    else:
        show_message(game_state, '寻路指示线已关闭。')
    queue_sound(game_state, 'click')


def toggle_sound(game_state):
    """切换音效开关。

    :param game_state: 游戏状态字典。
    """
    settings = game_state['settings']
    settings['sound_enabled'] = not settings['sound_enabled']
    if settings['sound_enabled']:
        show_message(game_state, '音效已开启。')
    else:
        show_message(game_state, '音效已关闭。')


def toggle_voice(game_state):
    """切换台词朗读。

    Text To Speech（文本转语音，TTS）在这里仅用于演示。
    Windows 使用 pyttsx3，macOS 使用 say。
    pyttsx3 是离线语音合成第三方库，适合面试中说明“功能演示”和“跨平台适配边界”。
    推荐书：中文《Python 自动化办公与实战》，英文 Automate the Boring Stuff with Python。

    :param game_state: 游戏状态字典。
    """
    game_state['voice_enabled'] = not game_state['voice_enabled']
    if game_state['voice_enabled']:
        award_badge(game_state, 'voice_reader')
        show_message(game_state, '台词朗读已开启。Mac 使用 say，Windows 使用 pyttsx3。')
    else:
        show_message(game_state, '台词朗读已关闭。')
    queue_sound(game_state, 'click')


def toggle_auto_play(game_state):
    """切换自动游玩。

    :param game_state: 游戏状态字典。
    """
    game_state['auto_play'] = not game_state['auto_play']
    if game_state['auto_play']:
        game_state['auto_paused_by_user'] = False
        game_state['voice_enabled'] = True
        award_badge(game_state, 'autoplayer')
        if game_state['ui_state'] == 'title':
            game_state['title_skip_acts'] = AUTO_PLAY_SKIP_ACTS_DEFAULT
            act_title = START_ACT_OPTIONS[AUTO_PLAY_SKIP_ACTS_DEFAULT]['title']
            show_message(game_state, f'自动游玩已开启：默认跳过 {AUTO_PLAY_SKIP_ACTS_DEFAULT} 幕，将从「{act_title}」开始。')
        else:
            show_message(game_state, '自动游玩已开启：会自动寻路、对话、收集、战斗，并自动朗读台词；自动游玩不会打开商店。')
    else:
        game_state['auto_paused_by_user'] = True
        show_message(game_state, '自动游玩已暂停。再次按 O 可恢复。')
    queue_sound(game_state, 'click')


def toggle_tooltip(game_state):
    """切换区域 tooltip。

    tooltip 默认关闭，目的是避免普通玩家被代码定位信息打扰。
    Pygame 里的 tooltip 本质上是矩形命中测试 hit-test 加上一层浮动文本绘制。
    推荐书：中文《游戏编程模式》；英文 Game Programming Patterns。

    :param game_state: 游戏状态字典。
    """
    settings = game_state['settings']
    settings['tooltip_enabled'] = not settings['tooltip_enabled']
    if settings['tooltip_enabled']:
        show_message(game_state, '区域 tooltip 已开启：鼠标悬停可查看区域名称和代码定位。')
        logger.info('区域 tooltip 已开启。')
    else:
        show_message(game_state, '区域 tooltip 已关闭。')
        logger.info('区域 tooltip 已关闭。')
    queue_sound(game_state, 'click')


def speak_dialogue_entry(voice_enabled, dialogue, tts_engine):
    """朗读当前对白。

    :param voice_enabled: 是否启用朗读。
    :param dialogue: 当前对白状态。
    :param tts_engine: Windows 下的 pyttsx3 引擎。
    """
    if voice_enabled and dialogue is not None:
        index = dialogue['index']
        if dialogue['spoken_index'] != index:
            entries = dialogue['entries']
            entry = entries[index]
            speaker_key = entry[0]
            text = entry[1]
            speaker_name, speaker_title = speaker_name_and_title(speaker_key)
            if speaker_title != '':
                speech_text = f'{speaker_name}，{speaker_title}。{text}'
            else:
                speech_text = f'{speaker_name}。{text}'
            if sys.platform == 'darwin':
                command = ['say', speech_text]
                subprocess.Popen(command)
            elif sys.platform == 'win32':
                tts_engine.say(speech_text)
                tts_engine.runAndWait()
            else:
                logger.warning('当前系统未配置台词朗读适配，只保留文字对白。')
            dialogue['spoken_index'] = index


def is_npc_visible(flags, npc_spec):
    """判断 NPC 是否可见。

    :param flags: 剧情标记字典。
    :param npc_spec: NPC 配置。
    :return: True 表示可见，False 表示不可见。
    """
    visible = False
    rule = npc_spec['visible_rule']
    if rule == 'always':
        visible = True
    elif rule == 'merchant':
        visible = flags['got_basket'] and ENABLE_SHOP_SYSTEM
    elif rule == 'ending_chief':
        visible = flags['ending_ready'] and not flags['ending_cg_seen'] and ENABLE_ENDING_CG_BY_CHIEF
    elif rule == 'wolf_intro':
        visible = flags['mother_hint'] and not flags['wolf_met']
    elif rule == 'hunter_before':
        visible = flags['wolf_met'] and not flags['met_hunter']
    elif rule == 'fake_grandma':
        visible = flags['met_hunter'] and not flags['wolf_defeated']
    elif rule == 'grandma_after':
        visible = flags['wolf_defeated'] and not flags['met_grandma_after']
    elif rule == 'wolf_prisoner':
        visible = flags['wolf_caged'] and not flags['heard_wolf_plea']
    elif rule == 'newspaper_boy':
        visible = flags['chapter_two_started'] and not flags['heard_gossip']
    elif rule == 'hotel_gathering':
        visible = flags['heard_gossip'] and not flags['captured_by_aileen']
    elif rule == 'resistance_leader':
        visible = flags['heard_gossip'] and not flags['captured_by_aileen']
    elif rule == 'aileen_prison':
        visible = flags['captured_by_aileen'] and flags['pov_aileen_started'] and not flags['prison_aileen_visit']
    elif rule == 'male_companion':
        visible = flags['prison_aileen_visit'] and flags['pov_blond_friend_started'] and not flags['prison_escaped']
    elif rule == 'market_messenger':
        visible = flags['prison_escaped'] and not flags['shop_attacks_reported']
    elif rule == 'king':
        visible = flags['shop_attacks_reported'] and not flags['aileen_defeated']
    return visible


def visible_npcs(game_state):
    """取得当前场景可见 NPC。

    :param game_state: 游戏状态字典。
    :return: 当前场景可见 NPC 配置列表。
    """
    npcs = []
    scene = game_state['scene']
    flags = game_state['flags']
    for npc_spec in NPC_SPECS:
        npc_scene = npc_spec['scene']
        if npc_scene == scene and npc_enabled(npc_spec):
            visible = is_npc_visible(flags, npc_spec)
            if visible:
                npcs.append(npc_spec)
    return npcs


def visible_npc_points(game_state):
    """取得可见 NPC 阻挡点集合。

    :param game_state: 游戏状态字典。
    :return: NPC 坐标集合。
    """
    points = set()
    npcs = visible_npcs(game_state)
    for npc_spec in npcs:
        npc_x = npc_spec['x']
        npc_y = npc_spec['y']
        point = (npc_x, npc_y)
        points.add(point)
    return points


def find_visible_npc_by_action(game_state, action):
    """根据行为编号查找当前可见 NPC。

    :param game_state: 游戏状态字典。
    :param action: NPC 行为编号。
    :return: NPC 配置；没有时返回 None。
    """
    found_npc = None
    npcs = visible_npcs(game_state)
    for npc_spec in npcs:
        npc_action = npc_spec['action']
        if found_npc is None and npc_action == action:
            found_npc = npc_spec
    return found_npc


def is_scene_tile_walkable(scene, x, y):
    """判断指定场景内某个瓦片是否本身可走，不考虑 NPC。

    :param scene: 场景编号。
    :param x: 瓦片横坐标。
    :param y: 瓦片纵坐标。
    :return: True 表示可走，False 表示不可走。
    """
    walkable = True
    current_map = MAPS[scene]
    if y < 0 or y >= len(current_map):
        walkable = False
    elif x < 0 or x >= len(current_map[0]):
        walkable = False
    else:
        tile = current_map[y][x]
        if tile in BLOCKING_TILES:
            walkable = False
    return walkable


def can_walk(game_state, x, y):
    """判断某个瓦片是否可走。

    :param game_state: 游戏状态字典。
    :param x: 瓦片横坐标。
    :param y: 瓦片纵坐标。
    :return: True 表示可以走，False 表示不能走。
    """
    walkable = True
    scene = game_state['scene']
    if not is_scene_tile_walkable(scene, x, y):
        walkable = False
    else:
        npcs = visible_npcs(game_state)
        for npc_spec in npcs:
            npc_x = npc_spec['x']
            npc_y = npc_spec['y']
            if npc_x == x and npc_y == y:
                walkable = False
    return walkable


def can_walk_for_path(game_state, x, y):
    """判断自动寻路候选点是否可走。

    自动寻路候选点不把 NPC 当作阻挡，因为目标 NPC 的相邻格需要先被列为候选。
    真正生成瓦片图时，build_tile_graph 会再把所有可见 NPC 作为阻挡点，避免路径穿过角色身体。

    :param game_state: 游戏状态字典。
    :param x: 瓦片横坐标。
    :param y: 瓦片纵坐标。
    :return: True 表示可以走，False 表示不能走。
    """
    scene = game_state['scene']
    walkable = is_scene_tile_walkable(scene, x, y)
    return walkable


def bump(game_state, x, y):
    """撞到不可走格子时给出提示。

    :param game_state: 游戏状态字典。
    :param x: 尝试进入的瓦片横坐标。
    :param y: 尝试进入的瓦片纵坐标。
    """
    scene = game_state['scene']
    current_map = MAPS[scene]
    if 0 <= y < len(current_map) and 0 <= x < len(current_map[0]):
        tile = current_map[y][x]
        if tile == '#':
            show_message(game_state, '边界太密，红斗篷被轻轻拦住。')
        elif tile in {'b', 'r', 's', 't', 'w'}:
            show_message(game_state, '这里摆着床、餐桌或家具，绕一下吧。')
        elif tile == 'H':
            show_message(game_state, '旅店墙挡住了路。')
        elif tile == 'M':
            show_message(game_state, '石墙挡住了路。在火柴盒监狱里，它也可能是抽拉囚室的外壳。')
        elif tile == 'X':
            show_message(game_state, '荆棘影挡住了路。它像灰狼留下的坏念头。')
        elif tile == 'A':
            show_message(game_state, '铁栅栏很结实，这是防止危险再伤人的地方。')
        elif tile == 'm':
            show_message(game_state, '火柴木箱挡住了路。')
        elif tile == 'L':
            show_message(game_state, '雪夜路灯很冷，绕开它。')
        queue_sound(game_state, 'portal_closed')


def find_portal_at(game_state):
    """查找玩家脚下传送门。

    :param game_state: 游戏状态字典。
    :return: 传送门配置；没有时返回 None。
    """
    found_portal = None
    scene = game_state['scene']
    player = game_state['player']
    player_x = player['x']
    player_y = player['y']
    for portal_spec in PORTALS:
        portal_scene = portal_spec['scene']
        portal_x = portal_spec['x']
        portal_y = portal_spec['y']
        if found_portal is None and portal_scene == scene and portal_x == player_x and portal_y == player_y:
            found_portal = portal_spec
    return found_portal


def find_portal_to_scene(game_state, to_scene):
    """查找当前场景通向目标场景的传送门。

    :param game_state: 游戏状态字典。
    :param to_scene: 目标场景编号。
    :return: 传送门配置；没有时返回 None。
    """
    found_portal = None
    scene = game_state['scene']
    for portal_spec in PORTALS:
        portal_scene = portal_spec['scene']
        portal_to_scene = portal_spec['to_scene']
        if found_portal is None and portal_scene == scene and portal_to_scene == to_scene:
            found_portal = portal_spec
    return found_portal


def portal_is_open(game_state, portal_spec):
    """判断某个传送门当前是否可通过。

    :param game_state: 游戏状态字典。
    :param portal_spec: 传送门配置。
    :return: True 表示可通过，False 表示被剧情锁住。
    """
    flags = game_state['flags']
    required_flag = portal_spec['required_flag']
    if required_flag is None:
        opened = True
    elif flags[required_flag]:
        opened = True
    else:
        opened = False
    return opened


def current_scene_portal_lines(game_state):
    """生成当前场景每个单格门通向哪个场景的说明。

    :param game_state: 游戏状态字典。
    :return: 门说明文本列表。
    """
    lines = []
    scene = game_state['scene']
    for portal_spec in PORTALS:
        portal_scene = portal_spec['scene']
        if portal_scene == scene:
            portal_x = portal_spec['x']
            portal_y = portal_spec['y']
            to_scene = portal_spec['to_scene']
            to_scene_name = SCENE_NAMES[to_scene]
            if portal_is_open(game_state, portal_spec):
                status = '可通行'
            else:
                status = '未开启'
            line = f'({portal_x},{portal_y}) → {to_scene_name}：{status}'
            lines.append(line)
    return lines


def show_scene_message(game_state):
    """根据当前场景显示到达提示。

    :param game_state: 游戏状态字典。
    """
    scene = game_state['scene']
    scene_messages = {
        'home': '温暖的小屋让你想起妈妈的叮嘱。',
        'village': '村口有人守着行商摊位，市场和村长的小灯都亮着。',
        'forest': '森林小路上，树叶像绿色的像素一样闪烁。',
        'cottage': '外婆的小屋到了。屋里安静得不太对劲。',
        'cage_yard': '灰狼被关在铁栅栏后，村庄暂时睡了一个安稳觉。',
        'winter_street': '雪夜街口有蓝火柴烧过的甜味，甜得让人害怕。',
        'whisper_hotel': '密语酒店的后厅挤着多位 NPC：掌柜、侦察员、药师、领袖和俊美男卧底都在场。',
        'matchbox_prison': '私人监狱像一只竖起来的火柴盒：艾琳不知道它能抽拉，露比和莱昂知道。',
        'match_market': '火柴总店街一片混乱，十几个店铺都被红斗篷留下记号。',
        'royal_square': '王城火柴广场上，国王、军队、邻国信使和艾琳的总店同时出现。',
    }
    message = scene_messages[scene]
    show_message(game_state, message)


def check_portal(game_state):
    """检查玩家是否踩到传送格。

    :param game_state: 游戏状态字典。
    """
    found_portal = find_portal_at(game_state)
    if found_portal is not None:
        if not portal_is_open(game_state, found_portal):
            missing_text = found_portal['missing_text']
            show_message(game_state, missing_text)
            player = game_state['player']
            dx, dy = player['dir']
            back_x = player['x'] - dx
            back_y = player['y'] - dy
            set_player_tile(player, back_x, back_y)
            queue_sound(game_state, 'portal_closed')
        else:
            previous_scene = game_state['scene']
            game_state['scene'] = found_portal['to_scene']
            new_scene = game_state['scene']
            scene_meta = SCENE_META[new_scene]
            time_key = scene_meta['default_time_key']
            set_time_of_day(game_state, time_key)
            to_x = found_portal['to_x']
            to_y = found_portal['to_y']
            player = game_state['player']
            set_player_tile(player, to_x, to_y)
            visited_scenes = game_state['visited_scenes']
            visited_scenes.add(new_scene)
            previous_name = SCENE_NAMES[previous_scene]
            new_name = SCENE_NAMES[new_scene]
            logger.info(f'场景切换：{previous_name} -> {new_name}')
            show_scene_message(game_state)
            queue_sound(game_state, 'portal_open')


def find_collectible_by_key(item_key):
    """根据道具编号查找道具配置。

    :param item_key: 道具编号。
    :return: 道具配置；没有时返回 None。
    """
    found_collectible = None
    for collectible in ITEMS:
        collectible_key = collectible['key']
        if found_collectible is None and collectible_key == item_key and item_enabled(collectible):
            found_collectible = collectible
    return found_collectible


def find_collectible_at(game_state, x, y):
    """查找指定坐标上的未收集道具。

    :param game_state: 游戏状态字典。
    :param x: 瓦片横坐标。
    :param y: 瓦片纵坐标。
    :return: 道具配置；没有时返回 None。
    """
    found_collectible = None
    scene = game_state['scene']
    collected = game_state['collected']
    for collectible in ITEMS:
        collectible_key = collectible['key']
        collectible_scene = collectible['scene']
        collectible_x = collectible['x']
        collectible_y = collectible['y']
        if found_collectible is None and item_enabled(collectible) and collectible_scene == scene and collectible_x == x and collectible_y == y and collectible_key not in collected:
            found_collectible = collectible
    return found_collectible


def check_item_pickup(game_state):
    """检查脚下是否有道具。

    :param game_state: 游戏状态字典。
    """
    player = game_state['player']
    player_x = player['x']
    player_y = player['y']
    found_collectible = find_collectible_at(game_state, player_x, player_y)
    if found_collectible is not None:
        collect_item(game_state, found_collectible)


def collect_item(game_state, collectible):
    """收集道具。

    :param game_state: 游戏状态字典。
    :param collectible: 道具配置。
    """
    collected = game_state['collected']
    flags = game_state['flags']
    inventory = game_state['inventory']
    collectible_key = collectible['key']
    kind = collectible['kind']
    name = collectible['name']
    collected.add(collectible_key)
    queue_sound(game_state, 'pickup')
    if kind == 'honey':
        flags['honeys'] += 1
        inventory['蜂蜜'] += 1
        honey_count = flags['honeys']
        text = f'找到 {name}。蜂蜜 {honey_count}/3。'
        show_message(game_state, text)
        logger.info(f'道具收集：{name}，当前蜂蜜数量 {honey_count}/3。')
        if honey_count == 1:
            award_badge(game_state, 'first_honey')
    elif kind == 'flower':
        flags['wildflowers'] += 1
        inventory['野花'] = flags['wildflowers']
        flower_count = flags['wildflowers']
        text = f'采到 {name}。野花 {flower_count}/2。'
        show_message(game_state, text)
    elif kind == 'cloth':
        flags['cloths'] += 1
        inventory['防烟布'] = flags['cloths']
        cloth_count = flags['cloths']
        text = f'收集到 {name}。防烟布 {cloth_count}/2。'
        show_message(game_state, text)
    elif kind == 'truth_clue':
        flags['truth_clues'] += 1
        inventory['真相线索'] = flags['truth_clues']
        clue_count = flags['truth_clues']
        text = f'发现 {name}。真相线索 {clue_count}/2。'
        show_message(game_state, text)
        story_text = f'露比发现了{name}，它让灰狼的伪装多了一道裂缝。'
        add_story(game_state, story_text)
        if clue_count >= 2:
            award_badge(game_state, 'truth_seeker')
    elif kind == 'match_clue':
        flags['match_clues'] += 1
        inventory['火柴证据'] = flags['match_clues']
        if name == '密谋名单碎页':
            inventory['酒店名单'] += 1
        match_count = flags['match_clues']
        text = f'发现 {name}。火柴证据 {match_count}/2。'
        show_message(game_state, text)
        story_text = f'露比发现了{name}，艾琳火柴阴谋的真相更清楚了。'
        add_story(game_state, story_text)
        award_badge(game_state, 'chapter_two')
    collected_count = len(collected)
    if collected_count >= 6:
        award_badge(game_state, 'collector')


def buy_shop_entry(game_state, shop_entry):
    """购买商店条目。

    :param game_state: 游戏状态字典。
    :param shop_entry: 商店购买条目。
    """
    flags = game_state['flags']
    inventory = game_state['inventory']
    price = shop_entry['price']
    count = shop_entry['count']
    inventory_key = shop_entry['inventory_key']
    flag_key = shop_entry['flag_key']
    name = shop_entry['name']
    if inventory['铜币'] >= price:
        inventory['铜币'] -= price
        inventory[inventory_key] += count
        if flag_key is not None:
            flags[flag_key] += count
        flags['shop_trades'] += 1
        set_flag(game_state, 'met_merchant', True)
        message = f'买到 {name} × {count}，花费 {price} 铜币。'
        show_message(game_state, message)
        logger.info(message)
        award_badge(game_state, 'first_trade')
        queue_sound(game_state, 'shop')
    else:
        show_message(game_state, '铜币不够，先探索或卖出多余材料。')
        queue_sound(game_state, 'portal_closed')


def sell_shop_entry(game_state, shop_entry):
    """卖出商店条目。

    :param game_state: 游戏状态字典。
    :param shop_entry: 商店卖出条目。
    """
    flags = game_state['flags']
    inventory = game_state['inventory']
    price = shop_entry['price']
    count = shop_entry['count']
    inventory_key = shop_entry['inventory_key']
    flag_key = shop_entry['flag_key']
    name = shop_entry['name']
    if inventory[inventory_key] >= count:
        inventory[inventory_key] -= count
        inventory['铜币'] += price
        if flag_key is not None and flags[flag_key] >= count:
            flags[flag_key] -= count
        flags['shop_trades'] += 1
        set_flag(game_state, 'met_merchant', True)
        message = f'卖出 {name} × {count}，获得 {price} 铜币。'
        show_message(game_state, message)
        logger.info(message)
        award_badge(game_state, 'first_trade')
        queue_sound(game_state, 'shop')
    else:
        text = f'{name} 数量不足，不能卖出。'
        show_message(game_state, text)
        queue_sound(game_state, 'portal_closed')


def build_tile_graph(scene, blocked_points):
    """为当前地图创建瓦片图。

    NetworkX 的图也能表达单张地图里的每个可走格。
    自动寻路本质是在瓦片图上找最短路径，面试时可解释为“把二维网格转化为图，再调用图算法”。
    推荐书：英文 The Algorithm Design Manual；中文《数据结构与算法分析》。
    TODO：如果继续扩展地图编辑器，可以在启动时扫描每个剧情 NPC 的相邻格是否至少有一个可达。

    :param scene: 场景编号。
    :param blocked_points: 需要视为阻挡的 NPC 坐标集合。
    :return: 当前场景的瓦片图。
    """
    graph = nx.Graph()
    current_map = MAPS[scene]
    for tile_y, row in enumerate(current_map):
        for tile_x, tile in enumerate(row):
            point = (tile_x, tile_y)
            if tile not in BLOCKING_TILES and point not in blocked_points:
                graph.add_node(point)
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    graph_nodes = list(graph.nodes)
    for node in graph_nodes:
        node_x, node_y = node
        for direction in directions:
            dx, dy = direction
            neighbor = (node_x + dx, node_y + dy)
            if neighbor in graph:
                graph.add_edge(node, neighbor)
    return graph


def find_path_to_candidates(game_state, candidates):
    """从候选目标中找到当前场景内最短路径。

    :param game_state: 游戏状态字典。
    :param candidates: 候选瓦片坐标列表。
    :return: 路径坐标列表；无路时返回空列表。
    """
    blocked_points = visible_npc_points(game_state)
    scene = game_state['scene']
    player = game_state['player']
    start = (player['x'], player['y'])
    graph = build_tile_graph(scene, blocked_points)
    best_path = []
    for candidate in candidates:
        if start in graph and candidate in graph and nx.has_path(graph, start, candidate):
            path = nx.shortest_path(graph, start, candidate)
            if not best_path:
                best_path = path
            elif len(path) < len(best_path):
                best_path = path
    return best_path


def find_next_step_to_candidates(game_state, candidates):
    """从候选目标中找到当前场景内下一步。

    :param game_state: 游戏状态字典。
    :param candidates: 候选瓦片坐标列表。
    :return: 下一步坐标；无路时返回 None。
    """
    next_step = None
    best_path = find_path_to_candidates(game_state, candidates)
    if best_path:
        if len(best_path) > 1:
            next_step = best_path[1]
    return next_step


def auto_step_to_best_candidate(game_state, candidates):
    """自动向候选点中路径最短的点移动一步。

    :param game_state: 游戏状态字典。
    :param candidates: 候选点列表。
    """
    next_step = find_next_step_to_candidates(game_state, candidates)
    if next_step is not None:
        player = game_state['player']
        next_x, next_y = next_step
        dx = next_x - player['x']
        dy = next_y - player['y']
        if can_walk(game_state, next_x, next_y):
            start_player_move(player, dx, dy)
    else:
        scene = game_state['scene']
        player = game_state['player']
        player_x = player['x']
        player_y = player['y']
        logger.warning(f'自动寻路失败：场景={SCENE_NAMES[scene]}，玩家=({player_x},{player_y})，候选点={candidates}。请检查 NPC 是否被墙体隔离，或传送门剧情锁是否与当前目标冲突。')
        game_state['auto_play'] = False
        show_message(game_state, '自动寻路暂时找不到可走路径，已停止自动游玩。')


def auto_step_to_point(game_state, target_x, target_y):
    """自动走到指定格。

    :param game_state: 游戏状态字典。
    :param target_x: 目标瓦片横坐标。
    :param target_y: 目标瓦片纵坐标。
    """
    candidates = [(target_x, target_y)]
    auto_step_to_best_candidate(game_state, candidates)


def auto_step_to_adjacent(game_state, target_x, target_y):
    """自动走到目标相邻格。

    :param game_state: 游戏状态字典。
    :param target_x: 目标瓦片横坐标。
    :param target_y: 目标瓦片纵坐标。
    """
    candidates = []
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for direction in directions:
        dx, dy = direction
        candidate = (target_x + dx, target_y + dy)
        candidate_x, candidate_y = candidate
        if can_walk_for_path(game_state, candidate_x, candidate_y):
            candidates.append(candidate)
    if candidates:
        auto_step_to_best_candidate(game_state, candidates)
    else:
        scene = game_state['scene']
        logger.warning(f'自动目标周围没有可走互动格：场景={SCENE_NAMES[scene]}，目标=({target_x},{target_y})。')
        game_state['auto_play'] = False
        show_message(game_state, '自动目标周围没有可走互动格，已停止自动游玩。')


def item_tile_is_walkable(collectible):
    """判断道具所在瓦片是否可走。

    :param collectible: 道具配置。
    :return: True 表示道具可站上去拾取，False 表示道具位置不可走。
    """
    scene = collectible['scene']
    collectible_x = collectible['x']
    collectible_y = collectible['y']
    if scene_enabled(scene):
        walkable = is_scene_tile_walkable(scene, collectible_x, collectible_y)
    else:
        walkable = False
    return walkable


def next_reachable_uncollected_in_current_scene(game_state):
    """找到当前场景内未收集且可达的道具。

    :param game_state: 游戏状态字典。
    :return: 道具编号；没有时返回 None。
    """
    found_key = None
    scene = game_state['scene']
    collected = game_state['collected']
    for collectible in ITEMS:
        collectible_key = collectible['key']
        collectible_scene = collectible['scene']
        if found_key is None and item_enabled(collectible) and collectible_scene == scene and collectible_key not in collected and item_tile_is_walkable(collectible):
            target_x = collectible['x']
            target_y = collectible['y']
            candidates = [(target_x, target_y)]
            path = find_path_to_candidates(game_state, candidates)
            if path:
                found_key = collectible_key
    return found_key


def next_walkable_uncollected_kind(game_state, kind):
    """找到某类未收集且瓦片可走的道具。

    :param game_state: 游戏状态字典。
    :param kind: 道具类型。
    :return: 道具编号；没有时返回 None。
    """
    found_key = None
    collected = game_state['collected']
    scene = game_state['scene']
    for collectible in ITEMS:
        collectible_kind = collectible['kind']
        collectible_key = collectible['key']
        collectible_scene = collectible['scene']
        if found_key is None and item_enabled(collectible) and collectible_kind == kind and collectible_key not in collected and item_tile_is_walkable(collectible):
            if collectible_scene == scene:
                target_x = collectible['x']
                target_y = collectible['y']
                candidates = [(target_x, target_y)]
                path = find_path_to_candidates(game_state, candidates)
                if path:
                    found_key = collectible_key
            elif scene in SCENE_GRAPH and collectible_scene in SCENE_GRAPH and nx.has_path(SCENE_GRAPH, scene, collectible_scene):
                found_key = collectible_key
    return found_key


def current_auto_goal(game_state):
    """取得自动游玩当前目标。

    自动游玩是确定性规则 + 最短路径 + 状态机，不是神经网络。
    面试考点：AI 控制器的工程实现可以拆成感知当前状态、选择目标、规划路径、执行动作。
    多视角段落中，目标不再强制是露比行动，而是根据 view_actor 继续推进同一条剧情状态机。

    :param game_state: 游戏状态字典。
    :return: 自动目标字典。
    """
    flags = game_state['flags']
    settings = game_state['settings']
    view_actor = game_state['view_actor']
    scene_item_key = next_reachable_uncollected_in_current_scene(game_state)
    if settings['auto_pickup_reachable_items'] and view_actor == 'red' and scene_item_key is not None:
        collectible = find_collectible_by_key(scene_item_key)
        collectible_name = collectible['name']
        goal = {'kind': 'item', 'scene': game_state['scene'], 'item_key': scene_item_key, 'description': f'拾取当前地图可达道具：{collectible_name}'}
    elif not flags['got_basket']:
        goal = {'kind': 'action', 'scene': 'home', 'action': 'mother', 'description': '和妈妈说话，拿到篮子'}
    elif not flags['mother_hint']:
        goal = {'kind': 'action', 'scene': 'home', 'action': 'mother', 'description': '听妈妈补充三问提示'}
    elif not flags['met_merchant']:
        goal = {'kind': 'action', 'scene': 'village', 'action': 'merchant', 'description': '认识村口行商露塔'}
    elif not flags['wolf_met']:
        goal = {'kind': 'action', 'scene': 'forest', 'action': 'wolf', 'description': '询问灰狼格雷姆'}
    elif not flags['met_hunter']:
        goal = {'kind': 'action', 'scene': 'forest', 'action': 'hunter', 'description': '寻找猎人伊沃和银铃'}
    elif flags['honeys'] < 2 and next_walkable_uncollected_kind(game_state, 'honey') is not None:
        item_key = next_walkable_uncollected_kind(game_state, 'honey')
        collectible = find_collectible_by_key(item_key)
        scene = collectible['scene']
        goal = {'kind': 'item', 'scene': scene, 'item_key': item_key, 'description': '准备更多蜂蜜'}
    elif not flags['wolf_defeated']:
        goal = {'kind': 'action', 'scene': 'cottage', 'action': 'fake_grandma', 'description': '揭开假外婆真面目'}
    elif flags['wolf_defeated'] and not flags['wolf_caged'] and not flags['wolf_exiled']:
        goal = {'kind': 'judgement', 'scene': game_state['scene'], 'description': '处置灰狼：囚禁或放逐'}
    elif flags['wolf_caged'] and not flags['heard_wolf_plea']:
        goal = {'kind': 'action', 'scene': 'cage_yard', 'action': 'prisoner', 'description': '听囚笼里的灰狼求饶'}
    elif not flags['met_grandma_after']:
        goal = {'kind': 'action', 'scene': 'cottage', 'action': 'grandma_after', 'description': '和外婆确认安全，并触发下半部'}
    elif not flags['heard_gossip']:
        goal = {'kind': 'action', 'scene': 'winter_street', 'action': 'newspaper_boy', 'description': '听雪夜街口关于艾琳的闲言碎语'}
    elif not flags['captured_by_aileen']:
        goal = {'kind': 'action', 'scene': 'whisper_hotel', 'action': 'resistance_leader', 'description': '去密语酒店参加多 NPC 密会，并揭露俊美男卧底维克托'}
    elif not flags['prison_aileen_visit']:
        goal = {'kind': 'action', 'scene': 'matchbox_prison', 'action': 'aileen_prison', 'description': '切到艾琳视角，巡视她并不了解真实结构的火柴盒监狱'}
    elif not flags['prison_escaped']:
        goal = {'kind': 'action', 'scene': 'matchbox_prison', 'action': 'male_companion', 'description': '切到莱昂视角，捡钥匙并利用火柴盒抽拉结构打开牢门'}
    elif not flags['shop_attacks_reported']:
        goal = {'kind': 'action', 'scene': 'match_market', 'action': 'market_messenger', 'description': '确认红斗篷同时袭击店铺的计划'}
    elif not flags['aileen_defeated']:
        goal = {'kind': 'action', 'scene': 'royal_square', 'action': 'king', 'description': '带国王和军队谴责艾琳并开启最终战'}
    elif flags['ending_ready'] and not flags['ending_cg_seen'] and AUTO_PLAY_REQUIRE_CHIEF_ENDING_CG:
        goal = {'kind': 'action', 'scene': 'village', 'action': 'ending_chief', 'description': '回森林村口找村长开启结局 CG'}
    else:
        if flags['ending_ready'] and not AUTO_PLAY_REQUIRE_CHIEF_ENDING_CG:
            description = 'ending_ready = True，自动游玩按全局参数直接结束'
        else:
            description = '当前可处理目标已完成'
        goal = {'kind': 'idle', 'scene': game_state['scene'], 'description': description}
    return goal


def auto_walk_to_scene(game_state, goal_scene):
    """自动走向某个目标场景。

    :param game_state: 游戏状态字典。
    :param goal_scene: 目标场景编号。
    """
    scene = game_state['scene']
    scene_route = nx.shortest_path(SCENE_GRAPH, scene, goal_scene)
    next_scene = scene_route[1]
    portal = find_portal_to_scene(game_state, next_scene)
    portal_x = portal['x']
    portal_y = portal['y']
    auto_step_to_point(game_state, portal_x, portal_y)


def auto_walk_to_local_goal(game_state, goal):
    """自动走向当前场景内的目标。

    :param game_state: 游戏状态字典。
    :param goal: 自动目标字典。
    """
    goal_kind = goal['kind']
    if goal_kind == 'action':
        action = goal['action']
        npc_spec = find_visible_npc_by_action(game_state, action)
        if npc_spec is None:
            game_state['auto_play'] = False
            show_message(game_state, '自动目标暂时不可见，自动游玩已暂停。')
            logger.warning(f'自动目标不可见：{action}')
        else:
            npc_x = npc_spec['x']
            npc_y = npc_spec['y']
            player = game_state['player']
            distance = abs(npc_x - player['x']) + abs(npc_y - player['y'])
            if distance == 1:
                talk_by_action(game_state, action)
            else:
                auto_step_to_adjacent(game_state, npc_x, npc_y)
    elif goal_kind == 'item':
        item_key = goal['item_key']
        collectible = find_collectible_by_key(item_key)
        target_x = collectible['x']
        target_y = collectible['y']
        player = game_state['player']
        if player['x'] == target_x and player['y'] == target_y:
            collect_item(game_state, collectible)
        else:
            auto_step_to_point(game_state, target_x, target_y)
    elif goal_kind == 'judgement':
        apply_wolf_judgement(game_state, 'cage')


def auto_explore_action(game_state):
    """执行自动探索一步。

    :param game_state: 游戏状态字典。
    """
    goal = current_auto_goal(game_state)
    goal_kind = goal['kind']
    if goal_kind == 'idle':
        game_state['auto_play'] = False
        show_message(game_state, f'自动游玩结束：{goal["description"]}。')
        logger.info(f'自动游玩结束：{goal["description"]}。')
    else:
        goal_scene = goal['scene']
        scene = game_state['scene']
        if goal_scene != scene:
            auto_walk_to_scene(game_state, goal_scene)
        else:
            auto_walk_to_local_goal(game_state, goal)
        flags = game_state['flags']
        flags['auto_actions'] += 1


def current_target_scene(game_state):
    """取得当前建议目标场景。

    :param game_state: 游戏状态字典。
    :return: 场景编号。
    """
    goal = current_auto_goal(game_state)
    target_scene = goal['scene']
    return target_scene


def current_route_text(game_state):
    """取得当前场景到目标场景的路线文字。

    :param game_state: 游戏状态字典。
    :return: 路线文字。
    """
    scene = game_state['scene']
    target_scene = current_target_scene(game_state)
    route = nx.shortest_path(SCENE_GRAPH, scene, target_scene)
    route_names = []
    for scene_key in route:
        scene_name = SCENE_NAMES[scene_key]
        route_names.append(scene_name)
    route_text = ' → '.join(route_names)
    return route_text


def main_story_progress(game_state):
    """取得主线剧情进度。

    :param game_state: 游戏状态字典。
    :return: 主线进度文字。
    """
    flags = game_state['flags']
    main_steps = [
        ('got_basket', '拿到篮子'),
        ('mother_hint', '记住三问'),
        ('met_merchant', '认识行商'),
        ('wolf_met', '遇见灰狼'),
        ('met_hunter', '取得银铃'),
        ('wolf_defeated', '击败灰狼'),
        ('wolf_caged', '囚禁灰狼'),
        ('met_grandma_after', '外婆悲剧'),
        ('heard_gossip', '雪夜闲言'),
        ('met_spy_youth', '识别维克托'),
        ('captured_by_aileen', '密谋暴露'),
        ('pov_aileen_started', '艾琳视角'),
        ('pov_blond_friend_started', '贫嘴男救援'),
        ('prison_escaped', '监狱逃脱'),
        ('shop_attacks_reported', '店铺袭击'),
        ('royal_accusation', '国王谴责'),
        ('aileen_defeated', '击败艾琳'),
        ('aileen_found_dead', '火柴尸体'),
        ('ending_cg_seen', '村长开启结局'),
    ]
    finished = 0
    for flag_key, step_name in main_steps:
        if flags[flag_key]:
            finished += 1
    total = len(main_steps)
    progress_text = f'主线进度：{finished}/{total}'
    return progress_text


def current_task(game_state):
    """取得当前任务提示。

    :param game_state: 游戏状态字典。
    :return: 当前任务文本。
    """
    goal = current_auto_goal(game_state)
    goal_description = goal['description']
    actor_name = current_view_actor_name(game_state)
    if goal['kind'] == 'idle':
        task = '终幕：当前可处理目标已完成，可自由探索或重新开始'
    else:
        task = f'主视角：{actor_name}｜推荐：{goal_description}'
    return task


def quest_entries(game_state):
    """生成任务清单。

    :param game_state: 游戏状态字典。
    :return: 任务条目列表。
    """
    flags = game_state['flags']
    inventory = game_state['inventory']
    quests = []
    if flags['ending_cg_seen'] or (flags['ending_ready'] and not AUTO_PLAY_REQUIRE_CHIEF_ENDING_CG):
        main_status = '已完成'
    else:
        main_status = '进行中'
    main_detail = current_task(game_state)
    main_quest = (main_status, '主线：灰狼与艾琳火柴阴谋多幕剧情', main_detail)
    quests.append(main_quest)
    if flags['wolf_defeated']:
        wolf_status = '已击败'
    else:
        wolf_status = '进行中'
    wolf_detail = '通过三问、银铃、油灯和蜂蜜恢复，在外婆小屋击败灰狼。'
    wolf_quest = (wolf_status, '上半部：大灰狼', wolf_detail)
    quests.append(wolf_quest)
    if flags['captured_by_aileen']:
        hotel_status = '已暴露'
    elif flags['heard_gossip']:
        hotel_status = '进行中'
    else:
        hotel_status = '未开启'
    hotel_detail = '密语酒店现在有掌柜、侦察员、药师、领袖和俊美男卧底维克托等多位 NPC；维克托知道私人监狱，但不知道抽拉结构。'
    hotel_quest = (hotel_status, '中段：密语酒店多人密会', hotel_detail)
    quests.append(hotel_quest)
    if flags['aileen_defeated']:
        aileen_status = '已击败'
    elif flags['chapter_two_started']:
        aileen_status = '进行中'
    else:
        aileen_status = '未开启'
    aileen_detail = '听雪夜闲言、参加酒店密谋、艾琳视角误判空囚室、莱昂利用火柴盒抽拉结构救援、带国王和军队谴责艾琳。'
    aileen_quest = (aileen_status, '下半部：艾琳与致幻性火柴', aileen_detail)
    quests.append(aileen_quest)
    prison_detail = MATCHBOX_PRISON_SECRET_TEXT
    if flags['prison_escaped']:
        prison_status = '已破解'
    elif flags['captured_by_aileen']:
        prison_status = '进行中'
    else:
        prison_status = '未开启'
    prison_quest = (prison_status, '关键场景：火柴盒监狱结构秘密', prison_detail)
    quests.append(prison_quest)
    if ENABLE_SHOP_SYSTEM:
        if flags['met_merchant']:
            shop_status = '已认识'
            shop_detail = f'铜币 {inventory["铜币"]}，可在森林村口手动打开市场买入或卖出补给。'
        else:
            shop_status = '未认识'
            shop_detail = '带上篮子后，在森林村口和露塔说话；自动游玩不会打开商店。'
        shop_quest = (shop_status, '系统：村口市场', shop_detail)
        quests.append(shop_quest)
    collect_detail = f'蜂蜜 {flags["honeys"]}/3，野花 {flags["wildflowers"]}/2，真相线索 {flags["truth_clues"]}/2，火柴证据 {flags["match_clues"]}/2，防烟布 {flags["cloths"]}/2。'
    collect_quest = ('长期', '收集：森林与艾琳线索', collect_detail)
    quests.append(collect_quest)
    if flags['ending_ready']:
        ending_status = '可触发'
        if AUTO_PLAY_REQUIRE_CHIEF_ENDING_CG:
            ending_detail = '自动游玩会回森林村口找奥伦村长开启结局 CG。'
        else:
            ending_detail = '自动游玩会在 ending_ready = True 后直接结束；玩家仍可手动找村长。'
    else:
        ending_status = '未开启'
        ending_detail = '击败艾琳并发现她身边散落用完的火柴后开启。'
    ending_quest = (ending_status, '终幕：村长开启结局 CG', ending_detail)
    quests.append(ending_quest)
    return quests


def create_dialogue(entries, end_key):
    """创建对白状态。

    :param entries: 对白条目列表。
    :param end_key: 对白结束效果编号。
    :return: 对白状态字典。
    """
    dialogue = {
        'entries': entries,
        'index': 0,
        'end_key': end_key,
        'spoken_index': -1,
        'auto_timer': 0,
    }
    return dialogue


def start_dialogue(game_state, entries, end_key):
    """进入对白状态。

    :param game_state: 游戏状态字典。
    :param entries: 对白条目列表。
    :param end_key: 对白结束效果编号。
    """
    game_state['dialogue'] = create_dialogue(entries, end_key)
    game_state['previous_ui_state'] = game_state['ui_state']
    game_state['ui_state'] = 'dialogue'
    queue_sound(game_state, 'click')


def start_story_dialogue(game_state, story_key):
    """从共享剧情数据启动对白。

    :param game_state: 游戏状态字典。
    :param story_key: STORY_ACTION_SPECS 中的剧情编号。
    """
    story_spec = STORY_ACTION_SPECS[story_key]
    time_key = story_spec['time_key']
    set_time_of_day(game_state, time_key)
    entries = story_spec['dialogue']
    end_key = story_spec['end_key']
    start_dialogue(game_state, entries, end_key)


def advance_dialogue(game_state):
    """推进对白。

    :param game_state: 游戏状态字典。
    """
    dialogue = game_state['dialogue']
    dialogue['index'] += 1
    entries = dialogue['entries']
    if dialogue['index'] >= len(entries):
        end_key = dialogue['end_key']
        game_state['dialogue'] = None
        game_state['ui_state'] = 'explore'
        if end_key is not None:
            apply_dialogue_end(game_state, end_key)
    else:
        queue_sound(game_state, 'click')


def story_key_for_action(game_state, action):
    """根据 NPC 行为编号选择剧情数据编号。

    :param game_state: 游戏状态字典。
    :param action: NPC 行为编号。
    :return: STORY_ACTION_SPECS 中的剧情编号。
    """
    flags = game_state['flags']
    if action == 'mother':
        if not flags['got_basket']:
            story_key = 'mother_first'
        elif not flags['mother_hint']:
            story_key = 'mother_hint'
        else:
            story_key = 'mother_after'
    else:
        story_key = ACTION_TO_STORY_KEY[action]
    return story_key


def talk_by_action(game_state, action):
    """根据 NPC 行为编号触发对白。

    :param game_state: 游戏状态字典。
    :param action: NPC 行为编号。
    """
    story_key = story_key_for_action(game_state, action)
    start_story_dialogue(game_state, story_key)


def try_interact(game_state):
    """尝试与面前或脚下的 NPC、道具互动。

    :param game_state: 游戏状态字典。
    """
    player = game_state['player']
    dx, dy = player['dir']
    front_target = (player['x'] + dx, player['y'] + dy)
    self_target = (player['x'], player['y'])
    targets = [front_target, self_target]
    found_action = None
    found_collectible = None
    for target in targets:
        if found_action is None and found_collectible is None:
            target_x, target_y = target
            npcs = visible_npcs(game_state)
            for npc_spec in npcs:
                if found_action is None:
                    npc_x = npc_spec['x']
                    npc_y = npc_spec['y']
                    if npc_x == target_x and npc_y == target_y:
                        found_action = npc_spec['action']
            if found_action is None and found_collectible is None:
                found_collectible = find_collectible_at(game_state, target_x, target_y)
    if found_action is not None:
        talk_by_action(game_state, found_action)
    elif found_collectible is not None:
        collect_item(game_state, found_collectible)
    else:
        show_message(game_state, '这里没有可以互动的东西。')
        queue_sound(game_state, 'portal_closed')


def start_intro_dialogue(game_state):
    """开始第一幕开场对白。

    :param game_state: 游戏状态字典。
    """
    start_story_dialogue(game_state, 'intro')


def start_game_from_title(game_state):
    """从标题界面的起始幕设置开始游戏。

    :param game_state: 游戏状态字典。
    """
    skip_acts = game_state['title_skip_acts']
    if skip_acts == 0:
        start_intro_dialogue(game_state)
    else:
        apply_start_skip_to_game_state(game_state, skip_acts, '标题菜单')


def apply_dialogue_end(game_state, end_key):
    """应用对白结束后的剧情效果。

    :param game_state: 游戏状态字典。
    :param end_key: 白结束效果编号。
    """
    flags = game_state['flags']
    inventory = game_state['inventory']
    if end_key == 'intro':
        game_state['ui_state'] = 'explore'
        show_message(game_state, '先和妈妈说话，拿到篮子。')
        add_story(game_state, '露比决定穿过森林，把面包和蜂蜜送给外婆。')
    elif end_key == 'mother_first':
        set_flag(game_state, 'got_basket', True)
        inventory['铜币'] = 18
        inventory['面包'] = 1
        inventory['蜂蜜'] = 1
        inventory['红缎带'] = 1
        flags['honeys'] += 1
        award_badge(game_state, 'basket')
        award_badge(game_state, 'first_honey')
        add_profile_codex_by_key(game_state, 'mother')
        add_codex(game_state, '妈妈的篮子')
        add_story(game_state, '玛莲娜交给露比一只篮子，里面有面包、蜂蜜、红缎带和一点铜币。')
        show_message(game_state, '获得篮子。可以出门了。')
    elif end_key == 'mother_hint':
        set_flag(game_state, 'mother_hint', True)
        flags['truth_clues'] += 1
        inventory['真相线索'] = flags['truth_clues']
        add_codex(game_state, '三问识伪')
        add_story(game_state, '玛莲娜提醒露比：真正爱你的人不会害怕三个问题。')
        show_message(game_state, '获得真相线索：三问识伪。')
    elif end_key == 'merchant':
        set_flag(game_state, 'met_merchant', True)
        add_profile_codex_by_key(game_state, 'merchant')
        add_codex(game_state, '村口市场')
        add_story(game_state, '露比认识了村口行商露塔，学会买入缺少的补给，也能卖出多余材料。')
        if game_state['auto_play']:
            game_state['ui_state'] = 'explore'
            show_message(game_state, '已认识露塔。自动游玩不会打开商店。')
        else:
            game_state['previous_ui_state'] = 'explore'
            game_state['ui_state'] = 'shop'
            show_message(game_state, '村口市场已打开。数字键或按钮买卖，Esc 返回。')
    elif end_key == 'wolf_first':
        set_flag(game_state, 'wolf_met', True)
        add_profile_codex_by_key(game_state, 'wolf')
        add_codex(game_state, '陌生灰狼')
        add_story(game_state, '格雷姆用礼貌的话诱导露比，露比记住了它贪婪的眼神。')
        show_message(game_state, '继续找猎人确认狼爪印。')
    elif end_key == 'hunter':
        set_flag(game_state, 'met_hunter', True)
        inventory['猎人银铃'] = 1
        inventory['油灯'] = 1
        inventory['清醒卡片'] = 1
        flags['truth_clues'] += 1
        inventory['真相线索'] = flags['truth_clues']
        add_profile_codex_by_key(game_state, 'hunter')
        add_codex(game_state, '猎人银铃')
        add_codex(game_state, '清醒卡片')
        add_story(game_state, '伊沃把银铃系在篮子上，又给了露比油灯和清醒卡片。')
        award_badge(game_state, 'clear_minded')
        show_message(game_state, '获得猎人的银铃、油灯和清醒卡片。前往外婆的小屋。')
    elif end_key == 'start_wolf_battle':
        start_battle(game_state, 'gray_wolf')
    elif end_key == 'wolf_victory':
        apply_final_battle_victory_position(game_state)
    elif end_key == 'grandma_after':
        set_flag(game_state, 'met_grandma_after', True)
        set_flag(game_state, 'chapter_two_started', True)
        set_flag(game_state, 'grandma_lost', True)
        add_profile_codex_by_key(game_state, 'grandma')
        award_badge(game_state, 'chapter_two')
        add_codex(game_state, '致幻性火柴')
        add_story(game_state, '阿黛拉讲出艾琳蓝色火柴的真相：它能让人看见幻觉，却会让人上瘾并沉入混乱。外婆最终没有醒来。')
        show_message(game_state, '下半部开启：去雪夜街口听关于艾琳的闲言碎语。')
    elif end_key == 'prisoner':
        set_flag(game_state, 'heard_wolf_plea', True)
        add_story(game_state, '囚笼里的格雷姆低声求饶，露比告诉他：停止伤害别人，比求饶更重要。')
        show_message(game_state, '灰狼已经求饶。回外婆的小屋确认安全。')
    elif end_key == 'newspaper_boy':
        set_flag(game_state, 'heard_gossip', True)
        add_profile_codex_by_key(game_state, 'newspaper_boy')
        add_codex(game_state, '雪夜闲言')
        add_story(game_state, '报童尼克告诉露比：艾琳的蓝火柴店铺扩张很快，密语酒店里有多位 NPC 参与反对她。')
        show_message(game_state, '密语酒店方向出现了。那里有多位 NPC，也可能有卧底。')
    elif end_key == 'hotel_conspiracy':
        set_flag(game_state, 'met_hotel_keeper', True)
        set_flag(game_state, 'met_resistance_scout', True)
        set_flag(game_state, 'met_secret_medic', True)
        set_flag(game_state, 'met_spy_youth', True)
        set_flag(game_state, 'met_resistance', True)
        set_flag(game_state, 'exposed_by_spy', True)
        set_flag(game_state, 'captured_by_aileen', True)
        set_flag(game_state, 'pov_aileen_started', True)
        inventory['酒店名单'] += 1
        award_badge(game_state, 'hotel_crowd')
        award_badge(game_state, 'hotel_conspiracy')
        award_badge(game_state, 'male_spy')
        award_badge(game_state, 'pov_aileen')
        add_profile_codex_by_key(game_state, 'hotel_keeper')
        add_profile_codex_by_key(game_state, 'resistance_scout')
        add_profile_codex_by_key(game_state, 'secret_medic')
        add_profile_codex_by_key(game_state, 'resistance_leader')
        add_profile_codex_by_key(game_state, 'spy')
        add_profile_codex_by_key(game_state, 'aileen')
        add_codex(game_state, '密语酒店多人密会')
        add_codex(game_state, '艾琳男卧底')
        add_story(game_state, '露比在密语酒店参与多人密会，但艾琳的俊美男卧底维克托暴露了所有人。维克托知道监狱存在，却不知道火柴盒抽拉结构。')
        add_story(game_state, '主视角切换为艾琳。此时露比被关在可抽拉的内层囚室中，不作为地图操控角色出现。')
        set_view_actor(game_state, 'aileen')
        game_state['scene'] = 'matchbox_prison'
        set_time_of_day(game_state, 'deep_night')
        visited_scenes = game_state['visited_scenes']
        visited_scenes.add('matchbox_prison')
        player = game_state['player']
        set_player_tile(player, 10, 10)
        show_message(game_state, '主视角切换为艾琳。她不知道监狱的火柴盒结构。')
    elif end_key == 'aileen_prison':
        set_flag(game_state, 'prison_aileen_visit', True)
        set_flag(game_state, 'key_dropped', True)
        set_flag(game_state, 'pov_blond_friend_started', True)
        award_badge(game_state, 'pov_blond_friend')
        add_profile_codex_by_key(game_state, 'blond_friend')
        add_profile_codex_by_key(game_state, 'blue_match_messenger')
        add_codex(game_state, '火柴盒监狱')
        add_codex(game_state, '艾琳误判空囚室')
        add_story(game_state, '艾琳误把外侧空牢当成普通空牢，不知道真正囚室被推入火柴盒内层。')
        add_story(game_state, '艾琳听说十几个店铺被身穿红斗篷的人同时袭击，急怒赶回店铺，却把钥匙丢在监狱走廊。')
        add_story(game_state, '主视角切换为莱昂。他知道抽拉结构，准备捡起钥匙打开牢门。')
        set_view_actor(game_state, 'blond_friend')
        player = game_state['player']
        set_player_tile(player, 10, 10)
        show_message(game_state, '主视角切换为莱昂。利用钥匙和火柴盒抽拉结构救人。')
    elif end_key == 'male_companion':
        inventory['牢房钥匙'] += 1
        set_flag(game_state, 'prison_rooms_opened', True)
        set_flag(game_state, 'prisoners_released', True)
        set_flag(game_state, 'prison_escaped', True)
        award_badge(game_state, 'matchbox_prison')
        add_codex(game_state, '火柴盒抽拉结构')
        add_story(game_state, '莱昂捡起艾琳丢下的钥匙，拉出火柴盒一样的内层囚室并打开牢门。露比和被关的人鱼贯而出。')
        add_story(game_state, '主视角切回露比。她从火柴盒监狱走出，继续追查艾琳的总店。')
        set_view_actor(game_state, 'red')
        player = game_state['player']
        set_player_tile(player, 18, 7)
        show_message(game_state, '主视角切回红斗篷。牢门打开，前往火柴总店街。')
    elif end_key == 'market_messenger':
        set_flag(game_state, 'shop_attacks_reported', True)
        award_badge(game_state, 'shop_raids')
        flags['match_clues'] += 1
        inventory['火柴证据'] = flags['match_clues']
        add_profile_codex_by_key(game_state, 'red_cloak')
        add_codex(game_state, '红斗篷袭击')
        add_story(game_state, '十几个卖火柴店铺同时被红斗篷袭击，证明反对势力还有很多人，并且早就准备了计划。')
        show_message(game_state, '国王和军队在王城火柴广场集结。')
    elif end_key == 'start_aileen_battle':
        set_flag(game_state, 'royal_accusation', True)
        add_profile_codex_by_key(game_state, 'king')
        start_battle(game_state, 'aileen')
    elif end_key == 'aileen_victory':
        apply_battle_victory_position(game_state, 'royal_square')
    elif end_key == 'battle_loss':
        scene = game_state['scene']
        apply_battle_loss_position(game_state, scene)
    elif end_key == 'ending_chief':
        set_flag(game_state, 'ending_cg_seen', True)
        award_badge(game_state, 'ending_cg')
        enter_ending(game_state)


def battle_add_log(game_state, text):
    """添加战斗日志。

    :param game_state: 游戏状态字典。
    :param text: 战斗日志文本。
    """
    battle = game_state['battle']
    battle_log = battle['log']
    battle_log.append(text)
    while len(battle_log) > 6:
        battle_log.pop(0)
    logger.info(text)


def current_player_battle_max_hp(game_state):
    """根据背包补给计算当前战斗最大生命。

    商店出售的暖面包会直接提高战斗稳定性。这个函数把“商店加强主角战斗力”落实为战斗属性变化。

    :param game_state: 游戏状态字典。
    :return: 当前战斗最大生命。
    """
    inventory = game_state['inventory']
    bread_bonus = inventory['面包'] * 4
    honey_bonus = inventory['蜂蜜'] * 2
    battle_max_hp = PLAYER_MAX_HP + bread_bonus + honey_bonus
    return battle_max_hp


def start_battle(game_state, battle_key):
    """进入战斗。

    :param game_state: 游戏状态字典。
    :param battle_key: 战斗编号。
    """
    flags = game_state['flags']
    set_view_actor(game_state, 'red')
    if battle_key == 'gray_wolf':
        enemy_name = '格雷姆'
        enemy_max_hp = 104
        if flags['truth_clues'] >= 2:
            enemy_max_hp -= 8
        stage = 'disadvantage'
        first_log = '假外婆掀开被子，灰狼先扑向篮子。上半部最终战进入劣势阶段！'
    else:
        enemy_name = '艾琳'
        enemy_max_hp = 132
        if flags['match_clues'] >= 2:
            enemy_max_hp -= 10
        stage = 'smoke_dream'
        first_log = '艾琳点燃一整盒致幻性火柴。下半部最终战进入烟雾幻觉阶段！'
    inventory = game_state['inventory']
    heals = inventory['蜂蜜']
    battle = {
        'battle_key': battle_key,
        'enemy_name': enemy_name,
        'enemy_max_hp': enemy_max_hp,
        'enemy_hp': enemy_max_hp,
        'stage': stage,
        'log': [],
        'heals': heals,
        'finished': False,
        'guard': False,
        'bell_used': False,
        'question_used': False,
        'lamp_used': False,
        'card_used': False,
        'cloth_used': False,
        'whistle_used': False,
        'round': 0,
        'comeback_triggered': False,
    }
    game_state['battle'] = battle
    player = game_state['player']
    player['max_hp'] = current_player_battle_max_hp(game_state)
    player['hp'] = player['max_hp']
    battle_add_log(game_state, first_log)
    game_state['ui_state'] = 'battle'
    logger.info(f'进入战斗状态：露比对战{enemy_name}。')
    queue_sound(game_state, 'battle')


def battle_player_attack(game_state):
    """玩家普通攻击。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    if battle['finished']:
        battle_add_log(game_state, '战斗已经结束。')
    else:
        flags = game_state['flags']
        inventory = game_state['inventory']
        damage = random.randint(8, 12)
        if flags['met_hunter']:
            damage += 2
        if flags['wildflowers'] >= 2:
            damage += 1
        if flags['kindness'] >= 3:
            damage += 1
        if inventory['木哨'] > 0:
            damage += 1
        damage += current_hero_attack_bonus(game_state)
        if battle['battle_key'] == 'gray_wolf' and battle['stage'] == 'disadvantage':
            damage = max(2, damage // 2)
            battle_add_log(game_state, '灰狼压住篮子，露比的攻击被迫变轻。')
        if battle['battle_key'] == 'aileen' and battle['stage'] == 'smoke_dream':
            damage = max(2, damage // 2)
            battle_add_log(game_state, '致幻性火柴让距离变得模糊，露比的攻击被烟雾削弱。')
        battle['enemy_hp'] = max(0, battle['enemy_hp'] - damage)
        enemy_name = battle['enemy_name']
        battle_add_log(game_state, f'露比挥起篮子，打掉{enemy_name} {damage} 点生命。')
        queue_sound(game_state, 'battle')
        battle_after_player_action(game_state)


def battle_player_heal(game_state):
    """玩家使用蜂蜜恢复。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    if battle['finished']:
        battle_add_log(game_state, '战斗已经结束。')
    elif battle['heals'] <= 0:
        battle_add_log(game_state, '篮子里的蜂蜜已经用完了。')
    else:
        flags = game_state['flags']
        player = game_state['player']
        battle['heals'] -= 1
        amount = 12 + min(18, flags['honeys'] * 3)
        old_hp = player['hp']
        player['hp'] = min(player['max_hp'], player['hp'] + amount)
        healed = player['hp'] - old_hp
        battle_add_log(game_state, f'你使用蜂蜜，恢复 {healed} 点生命。')
        queue_sound(game_state, 'heal')
        battle_enemy_attack(game_state)


def battle_player_defend(game_state):
    """玩家防御。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    if battle['finished']:
        battle_add_log(game_state, '战斗已经结束。')
    else:
        battle['guard'] = True
        battle_add_log(game_state, '露比把红斗篷裹紧，准备挡住下一次攻击。')
        queue_sound(game_state, 'click')
        battle_enemy_attack(game_state)


def trigger_final_comeback(game_state, text):
    """触发最终战反击阶段或清醒阶段。

    :param game_state: 游戏状态字典。
    :param text: 触发文本。
    """
    battle = game_state['battle']
    player = game_state['player']
    if battle['battle_key'] in ('gray_wolf', 'aileen') and not battle['comeback_triggered']:
        battle['stage'] = 'comeback'
        battle['comeback_triggered'] = True
        player['hp'] = min(player['max_hp'], player['hp'] + 18)
        battle_add_log(game_state, text)
        if battle['battle_key'] == 'gray_wolf':
            battle_add_log(game_state, '露比从劣势中站稳，银铃、油灯与三问连成反击机会！')
        else:
            battle_add_log(game_state, '露比从烟雾幻觉里醒来，国王的钟声和外婆的红缎带同时把她拉回现实！')


def battle_player_bell(game_state):
    """玩家摇响猎人的银铃。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    flags = game_state['flags']
    if battle['finished']:
        battle_add_log(game_state, '战斗已经结束。')
    elif not flags['met_hunter']:
        battle_add_log(game_state, '你还没有猎人的银铃。')
        battle_enemy_attack(game_state)
    elif battle['bell_used']:
        battle_add_log(game_state, '银铃已经响过一次，余音还在回荡。')
    else:
        battle['bell_used'] = True
        bell_damage = 10 + flags['truth_clues'] + flags['match_clues']
        if battle['battle_key'] in ('gray_wolf', 'aileen') and battle['stage'] in ('disadvantage', 'smoke_dream'):
            trigger_final_comeback(game_state, '银铃响起，真实的声音刺破伪装和烟雾。')
            bell_damage += 8
        battle['enemy_hp'] = max(0, battle['enemy_hp'] - bell_damage)
        battle['guard'] = True
        award_badge(game_state, 'bell_guardian')
        enemy_name = battle['enemy_name']
        battle_add_log(game_state, f'银铃响起，{enemy_name}失去 {bell_damage} 点生命。')
        queue_sound(game_state, 'badge')
        battle_after_player_action(game_state)


def battle_player_question(game_state):
    """玩家使用三问识破伪装或幻觉。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    flags = game_state['flags']
    clue_total = flags['truth_clues'] + flags['match_clues']
    if battle['finished']:
        battle_add_log(game_state, '战斗已经结束。')
    elif battle['question_used']:
        battle_add_log(game_state, '谎言已经被问题逼得露出破绽，不能重复三问。')
    elif clue_total < 2:
        battle_add_log(game_state, '你掌握的线索还不够，问题没能刺破伪装或幻觉。')
        battle_enemy_attack(game_state)
    else:
        battle['question_used'] = True
        clue_damage = 10 + clue_total * 3
        if battle['battle_key'] in ('gray_wolf', 'aileen') and battle['stage'] in ('disadvantage', 'smoke_dream'):
            trigger_final_comeback(game_state, '三个问题连成红线，伪装和烟雾同时露出裂缝。')
            clue_damage += 8
        battle['enemy_hp'] = max(0, battle['enemy_hp'] - clue_damage)
        enemy_name = battle['enemy_name']
        battle_add_log(game_state, f'露比连问三个真相，{enemy_name}慌乱后退，失去 {clue_damage} 点生命。')
        queue_sound(game_state, 'battle')
        battle_after_player_action(game_state)


def battle_player_lamp(game_state):
    """玩家举起油灯。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    inventory = game_state['inventory']
    flags = game_state['flags']
    if battle['finished']:
        battle_add_log(game_state, '战斗已经结束。')
    elif inventory['油灯'] <= 0:
        battle_add_log(game_state, '你还没有油灯。')
        battle_enemy_attack(game_state)
    elif battle['lamp_used']:
        battle_add_log(game_state, '油灯已经照亮过房间，灯火需要休息。')
    else:
        battle['lamp_used'] = True
        lamp_damage = 8 + flags['match_clues'] + flags['truth_clues']
        if battle['battle_key'] in ('gray_wolf', 'aileen') and battle['stage'] in ('disadvantage', 'smoke_dream'):
            trigger_final_comeback(game_state, '油灯照出真正的影子，火柴烟雾被照薄了。')
            lamp_damage += 8
        battle['enemy_hp'] = max(0, battle['enemy_hp'] - lamp_damage)
        battle['guard'] = True
        enemy_name = battle['enemy_name']
        battle_add_log(game_state, f'油灯照见影子，{enemy_name}失去 {lamp_damage} 点生命。')
        queue_sound(game_state, 'battle')
        battle_after_player_action(game_state)


def battle_player_card(game_state):
    """玩家使用清醒卡片。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    inventory = game_state['inventory']
    flags = game_state['flags']
    if battle['finished']:
        battle_add_log(game_state, '战斗已经结束。')
    elif inventory['清醒卡片'] <= 0:
        battle_add_log(game_state, '你还没有清醒卡片。')
        battle_enemy_attack(game_state)
    elif battle['card_used']:
        battle_add_log(game_state, '清醒卡片已经读过一次，不能重复使用。')
    else:
        player = game_state['player']
        battle['card_used'] = True
        card_damage = 11 + flags['truth_clues'] * 2 + flags['match_clues'] * 2
        if battle['battle_key'] in ('gray_wolf', 'aileen') and battle['stage'] in ('disadvantage', 'smoke_dream'):
            trigger_final_comeback(game_state, '露比读出卡片上的事实，劣势和幻觉终于被反转。')
            card_damage += 10
        battle['enemy_hp'] = max(0, battle['enemy_hp'] - card_damage)
        player['hp'] = min(player['max_hp'], player['hp'] + 9)
        enemy_name = battle['enemy_name']
        battle_add_log(game_state, f'清醒卡片提醒事实，{enemy_name}失去 {card_damage} 点生命，露比恢复 9 点生命。')
        queue_sound(game_state, 'heal')
        battle_after_player_action(game_state)


def battle_player_cloth(game_state):
    """玩家使用防烟布。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    flags = game_state['flags']
    inventory = game_state['inventory']
    if battle['finished']:
        battle_add_log(game_state, '战斗已经结束。')
    elif inventory['防烟布'] <= 0:
        battle_add_log(game_state, '你还没有防烟布。')
        battle_enemy_attack(game_state)
    elif battle['cloth_used']:
        battle_add_log(game_state, '防烟布已经挡过一次烟雾，不能重复使用。')
    else:
        battle['cloth_used'] = True
        cloth_damage = 9 + flags['cloths'] + flags['match_clues']
        if battle['battle_key'] in ('gray_wolf', 'aileen') and battle['stage'] in ('disadvantage', 'smoke_dream'):
            trigger_final_comeback(game_state, '防烟布挡住扑击和烟雾，红斗篷找到反击空隙。')
            cloth_damage += 8
        battle['enemy_hp'] = max(0, battle['enemy_hp'] - cloth_damage)
        battle['guard'] = True
        enemy_name = battle['enemy_name']
        battle_add_log(game_state, f'防烟布护住口鼻，{enemy_name}失去 {cloth_damage} 点生命，你获得一次防御。')
        queue_sound(game_state, 'badge')
        battle_after_player_action(game_state)


def battle_player_whistle(game_state):
    """玩家吹响木哨。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    inventory = game_state['inventory']
    if battle['finished']:
        battle_add_log(game_state, '战斗已经结束。')
    elif inventory['木哨'] <= 0:
        battle_add_log(game_state, '你还没有木哨。')
        battle_enemy_attack(game_state)
    elif battle['whistle_used']:
        battle_add_log(game_state, '木哨已经吹过一次，敌人不会再被同样声音骗到。')
    else:
        battle['whistle_used'] = True
        whistle_damage = 7
        if battle['battle_key'] in ('gray_wolf', 'aileen') and battle['stage'] in ('disadvantage', 'smoke_dream'):
            trigger_final_comeback(game_state, '木哨声把扑击和烟雾的节奏打乱，红斗篷找到反击空隙。')
            whistle_damage += 7
        battle['enemy_hp'] = max(0, battle['enemy_hp'] - whistle_damage)
        battle['guard'] = True
        enemy_name = battle['enemy_name']
        battle_add_log(game_state, f'木哨声让{enemy_name}踉跄，失去 {whistle_damage} 点生命。')
        queue_sound(game_state, 'click')
        battle_after_player_action(game_state)


def battle_after_player_action(game_state):
    """玩家行动后检查胜负与阶段变化。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    if battle['enemy_hp'] <= 0:
        battle_win(game_state)
    else:
        if battle['battle_key'] == 'gray_wolf' and battle['stage'] == 'disadvantage':
            player = game_state['player']
            if player['hp'] <= 28 or battle['round'] >= 3:
                trigger_final_comeback(game_state, '红斗篷几乎被逼到墙角，但妈妈的三问在心里响起来。')
        if battle['battle_key'] == 'aileen' and battle['stage'] == 'smoke_dream':
            player = game_state['player']
            if player['hp'] <= 30 or battle['round'] >= 3:
                trigger_final_comeback(game_state, '烟雾里出现外婆的影子，露比终于想起自己必须醒着。')
        battle_enemy_attack(game_state)


def battle_enemy_attack(game_state):
    """敌人攻击玩家。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    if not battle['finished']:
        flags = game_state['flags']
        inventory = game_state['inventory']
        player = game_state['player']
        battle['round'] += 1
        if battle['battle_key'] == 'gray_wolf':
            damage = random.randint(9, 13)
            if battle['stage'] == 'disadvantage':
                damage += 4
            else:
                damage -= 2
        else:
            damage = random.randint(10, 14)
            if battle['stage'] == 'smoke_dream':
                damage += 4
            else:
                damage -= 2
        if flags['met_hunter']:
            damage -= 2
        if flags['wildflowers'] >= 2:
            damage -= 1
        if inventory['防烟布'] > 0:
            damage -= 1
        if inventory['木哨'] > 0:
            damage -= 1
        damage -= current_hero_defense_bonus(game_state)
        if battle['guard']:
            damage -= 5
            battle['guard'] = False
        damage = max(1, damage)
        player['hp'] = max(0, player['hp'] - damage)
        enemy_name = battle['enemy_name']
        battle_add_log(game_state, f'{enemy_name}发动攻击，造成 {damage} 点伤害。')
        queue_sound(game_state, 'battle')
        if battle['battle_key'] == 'gray_wolf' and battle['stage'] == 'disadvantage':
            if player['hp'] <= 28 or battle['round'] >= 3:
                trigger_final_comeback(game_state, '露比被迫后退，却终于看清灰狼每一次扑击的节奏。')
        if battle['battle_key'] == 'aileen' and battle['stage'] == 'smoke_dream':
            if player['hp'] <= 30 or battle['round'] >= 3:
                trigger_final_comeback(game_state, '致幻性火柴越烧越亮，露比却抓住了清醒的红缎带。')
        if player['hp'] <= 0:
            battle_lose(game_state)


def battle_win(game_state):
    """玩家胜利。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    battle['finished'] = True
    flags = game_state['flags']
    battle_key = battle['battle_key']
    if battle_key == 'gray_wolf':
        set_flag(game_state, 'wolf_defeated', True)
        flags['final_battle_rounds'] = battle['round']
        flags['battles_won'] += 1
        award_badge(game_state, 'wolf_defeated')
        add_story(game_state, '灰狼被勇气、银铃、油灯和真相逼退，外婆暂时得救。')
        game_state['battle'] = None
        start_story_dialogue(game_state, 'wolf_victory')
    else:
        set_flag(game_state, 'aileen_defeated', True)
        set_flag(game_state, 'aileen_fled', True)
        set_flag(game_state, 'aileen_found_dead', True)
        set_flag(game_state, 'ending_ready', True)
        flags['battles_won'] += 1
        award_badge(game_state, 'aileen_defeated')
        add_story(game_state, '艾琳在王城火柴广场被红斗篷、国王和军队逼退。她逃跑后，尸体被发现，身边散落一地用完的火柴。')
        game_state['battle'] = None
        start_story_dialogue(game_state, 'aileen_victory')


def battle_lose(game_state):
    """玩家失败后回到安全位置。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    battle['finished'] = True
    game_state['battle'] = None
    start_story_dialogue(game_state, 'battle_loss')


def apply_final_battle_victory_position(game_state):
    """灰狼战胜利后进入灰狼处置界面。

    :param game_state: 游戏状态字典。
    """
    game_state['scene'] = 'cottage'
    set_time_of_day(game_state, 'night')
    visited_scenes = game_state['visited_scenes']
    visited_scenes.add('cottage')
    player = game_state['player']
    set_player_tile(player, 10, 13)
    player['max_hp'] = PLAYER_MAX_HP
    player['hp'] = player['max_hp']
    game_state['ui_state'] = 'judgement'
    show_message(game_state, '最终战胜利。选择如何处置灰狼。')
    logger.info('灰狼战胜利后进入灰狼处置界面。')


def apply_battle_victory_position(game_state, scene):
    """普通战斗胜利后回到探索状态。

    :param game_state: 游戏状态字典。
    :param scene: 回到的场景编号。
    """
    game_state['scene'] = scene
    scene_meta = SCENE_META[scene]
    time_key = scene_meta['default_time_key']
    set_time_of_day(game_state, time_key)
    visited_scenes = game_state['visited_scenes']
    visited_scenes.add(scene)
    player = game_state['player']
    set_player_tile(player, 10, 13)
    player['max_hp'] = PLAYER_MAX_HP
    player['hp'] = player['max_hp']
    game_state['ui_state'] = 'explore'
    show_message(game_state, '战斗胜利。王城火柴广场通往村口的路已经打开。')


def apply_battle_loss_position(game_state, scene):
    """战斗失败后回到安全位置。

    :param game_state: 游戏状态字典。
    :param scene: 回到的场景编号。
    """
    game_state['scene'] = scene
    scene_meta = SCENE_META[scene]
    time_key = scene_meta['default_time_key']
    set_time_of_day(game_state, time_key)
    visited_scenes = game_state['visited_scenes']
    visited_scenes.add(scene)
    player = game_state['player']
    set_player_tile(player, 10, 13)
    player['max_hp'] = PLAYER_MAX_HP
    player['hp'] = player['max_hp']
    game_state['ui_state'] = 'explore'
    show_message(game_state, '整理好篮子后，再和战斗目标互动即可重新挑战。')
    logger.info('战败重置完成：玩家回到安全位置。')


def apply_wolf_judgement(game_state, choice):
    """应用灰狼处置选择。

    :param game_state: 游戏状态字典。
    :param choice: 处置选择。
    """
    if choice == 'cage':
        set_flag(game_state, 'wolf_caged', True)
        game_state['judgement_choice'] = 'cage'
        award_badge(game_state, 'wolf_caged')
        add_story(game_state, '露比没有让灰狼继续伤害村民。伊沃把灰狼关进铁栅栏，让村庄从恐惧中安静下来。')
        game_state['scene'] = 'cottage'
        set_time_of_day(game_state, 'night')
        player = game_state['player']
        set_player_tile(player, 10, 13)
        game_state['ui_state'] = 'explore'
        show_message(game_state, '你选择囚禁灰狼。外婆小屋南门通向灰狼囚笼院。')
        queue_sound(game_state, 'judgement')
    else:
        set_flag(game_state, 'wolf_exiled', True)
        game_state['judgement_choice'] = 'exile'
        add_story(game_state, '露比选择放逐灰狼。伊沃会在森林边界巡逻，防止它再回来伤人。')
        game_state['ui_state'] = 'explore'
        show_message(game_state, '你选择放逐灰狼。可以和外婆确认安全。')
        queue_sound(game_state, 'judgement')


def ending_name(game_state):
    """取得结局名称。

    :param game_state: 游戏状态字典。
    :return: 结局名称。
    """
    flags = game_state['flags']
    inventory = game_state['inventory']
    if flags['truth_clues'] >= 2 and flags['match_clues'] >= 2 and flags['honeys'] >= 3 and inventory['防烟布'] > 0 and flags['wolf_caged'] and flags['aileen_found_dead'] and flags['prisoners_released']:
        name = '真结局：红斗篷照亮两场黑夜'
    elif flags['aileen_found_dead'] and flags['wolf_caged']:
        name = '结局：灰狼囚笼与蓝火柴审判'
    elif flags['aileen_found_dead']:
        name = '结局：火柴用尽的雪夜'
    else:
        name = '结局：银铃响过小屋'
    return name


def ending_lines(game_state):
    """取得结局描述。

    :param game_state: 游戏状态字典。
    :return: 结局文本列表。
    """
    flags = game_state['flags']
    inventory = game_state['inventory']
    if flags['truth_clues'] >= 2 and flags['match_clues'] >= 2 and flags['honeys'] >= 3 and inventory['防烟布'] > 0 and flags['wolf_caged'] and flags['aileen_found_dead'] and flags['prisoners_released']:
        lines = [
            '露比让灰狼不再伤人，也让艾琳的致幻性火柴店铺被封。',
            '莱昂打开火柴盒监狱，被关的人重新走回真实的冷风里。',
            '外婆没有醒来，但她留下的红缎带提醒村庄：逃进假梦不能夺走清醒。',
        ]
    elif flags['aileen_found_dead'] and flags['wolf_caged']:
        lines = [
            '露比救下村庄两次：一次挡住灰狼，一次让艾琳的店铺暴露在法律前。',
            '灰狼在铁栅栏里求饶，艾琳在逃跑后死于自己点尽的火柴旁。',
            '红斗篷站在晨光里，明白善良必须和边界一起保存。',
        ]
    elif flags['aileen_found_dead']:
        lines = [
            '国王和军队封锁了卖火柴的店铺，致幻性火柴不再吞掉人们的清醒。',
            '艾琳逃走后被发现死在用完的火柴旁。',
            '露比记住外婆，也记住寒冷本身不能成为伤害别人的理由。',
        ]
    else:
        lines = [
            '露比赶走了灰狼，外婆的小屋暂时安全。',
            '但远处的雪夜仍有蓝色火柴亮起，故事还没有真正结束。',
            '红斗篷会继续走下去。',
        ]
    return lines


def enter_ending(game_state):
    """进入结局界面。

    :param game_state: 游戏状态字典。
    """
    game_state['ui_state'] = 'ending'
    set_time_of_day(game_state, 'morning')
    add_story(game_state, '天快亮时，红斗篷、猎人、莱昂、村长、国王和村民站在村口，看见森林与雪夜街口重新安静下来。')
    flags = game_state['flags']
    inventory = game_state['inventory']
    if flags['truth_clues'] >= 2 and flags['match_clues'] >= 2 and flags['honeys'] >= 3 and inventory['防烟布'] > 0 and flags['wolf_caged'] and flags['aileen_found_dead'] and flags['prisoners_released']:
        award_badge(game_state, 'true_ending')
    logger.info('进入结局界面。')


def save_game_state(game_state):
    """保存游戏。

    JSON 是 JavaScript Object Notation（JavaScript 对象表示法）。
    JSON 是轻量级文本格式，适合保存简单游戏状态。
    本项目把 set 转为列表保存，再在读档时还原为 set。
    面试考点：JSON 只支持有限基础类型，因此集合、Path、Surface 等对象不能直接写入。
    推荐书：中文《Python 编程：从入门到实践》，英文 Fluent Python。

    :param game_state: 游戏状态字典。
    """
    player = game_state['player']
    save_player = {
        'x': player['x'],
        'y': player['y'],
        'dir': list(player['dir']),
        'hp': player['hp'],
    }
    save_state = {
        'scene': game_state['scene'],
        'time_of_day': game_state['time_of_day'],
        'view_actor': game_state['view_actor'],
        'ui_state': 'explore',
        'player': save_player,
        'flags': game_state['flags'],
        'inventory': game_state['inventory'],
        'settings': game_state['settings'],
        'scroll_offsets': game_state['scroll_offsets'],
        'collected': list(game_state['collected']),
        'badges': list(game_state['badges']),
        'visited_scenes': list(game_state['visited_scenes']),
        'codex': list(game_state['codex']),
        'story_log': game_state['story_log'],
        'hero_index': game_state['hero_index'],
        'hero_key': game_state['hero_key'],
        'title_skip_acts': game_state['title_skip_acts'],
        'auto_play': game_state['auto_play'],
        'auto_paused_by_user': game_state['auto_paused_by_user'],
        'voice_enabled': game_state['voice_enabled'],
        'auto_speed_index': game_state['auto_speed_index'],
        'judgement_choice': game_state['judgement_choice'],
    }
    save_text = json.dumps(save_state, ensure_ascii=False, indent=2)
    SAVE_PATH.write_text(save_text, encoding='utf-8')
    logger.info(f'游戏已保存到：{SAVE_PATH}')
    show_message(game_state, '存档完成：F9 可以读取。')
    queue_sound(game_state, 'pickup')


def load_game_state():
    """读取游戏。

    :return: 读取后的游戏状态字典。
    """
    save_text = SAVE_PATH.read_text(encoding='utf-8')
    save_state = json.loads(save_text)
    game_state = create_game_state()
    game_state['scene'] = save_state['scene']
    game_state['time_of_day'] = save_state['time_of_day']
    game_state['view_actor'] = save_state['view_actor']
    game_state['ui_state'] = save_state['ui_state']
    game_state['flags'] = save_state['flags']
    game_state['inventory'] = save_state['inventory']
    game_state['settings'] = save_state['settings']
    game_state['scroll_offsets'] = save_state['scroll_offsets']
    game_state['collected'] = set(save_state['collected'])
    game_state['badges'] = set(save_state['badges'])
    game_state['visited_scenes'] = set(save_state['visited_scenes'])
    game_state['codex'] = set(save_state['codex'])
    game_state['story_log'] = save_state['story_log']
    game_state['hero_index'] = save_state['hero_index']
    game_state['hero_key'] = save_state['hero_key']
    game_state['title_skip_acts'] = save_state['title_skip_acts']
    game_state['auto_play'] = save_state['auto_play']
    game_state['auto_paused_by_user'] = save_state['auto_paused_by_user']
    game_state['voice_enabled'] = save_state['voice_enabled']
    game_state['auto_speed_index'] = save_state['auto_speed_index']
    game_state['judgement_choice'] = save_state['judgement_choice']
    player_state = save_state['player']
    player = game_state['player']
    player_x = player_state['x']
    player_y = player_state['y']
    set_player_tile(player, player_x, player_y)
    player['dir'] = tuple(player_state['dir'])
    player['hp'] = player_state['hp']
    game_state['dialogue'] = None
    game_state['battle'] = None
    logger.info(f'游戏已从存档读取：{SAVE_PATH}')
    show_message(game_state, '读档完成。')
    return game_state


def register_ui_area(game_state, rect, title, source_hint):
    """登记鼠标 tooltip 区域。

    这个函数是定位系统核心。绘制函数画到哪里，就把对应矩形登记到 ui_areas。
    鼠标移动时 draw_tooltip 会倒序检查这些区域，越晚绘制的区域优先级越高。
    tooltip 默认关闭，但区域登记仍持续进行。
    面试考点：这是轻量 hit-test（命中测试）表，不需要额外 GUI 框架，也能做到“可视区域 -> 代码位置”的映射。

    :param game_state: 游戏状态字典。
    :param rect: Pygame 矩形或四元组。
    :param title: 区域名称。
    :param source_hint: 代码定位提示。
    """
    area = {
        'rect': rect,
        'title': title,
        'source_hint': source_hint,
    }
    game_state['ui_areas'].append(area)


def current_tooltip_text(game_state):
    """根据鼠标位置取得当前 tooltip 文本。

    :param game_state: 游戏状态字典。
    :return: tooltip 文本；没有命中或功能关闭时返回空字符串。
    """
    tooltip_text = ''
    settings = game_state['settings']
    if settings['tooltip_enabled']:
        mouse_pos = game_state['mouse_pos']
        reversed_areas = list(reversed(game_state['ui_areas']))
        for area in reversed_areas:
            if tooltip_text == '':
                rect = area['rect']
                rect_obj = pygame.Rect(rect)
                if rect_obj.collidepoint(mouse_pos):
                    title = area['title']
                    source_hint = area['source_hint']
                    tooltip_text = f'{title}｜代码定位：{source_hint}'
    return tooltip_text


def draw_text(surface, text, font, color, x, y):
    """绘制文本。

    :param surface: 目标画布。
    :param text: 文本内容。
    :param font: Pygame 字体对象。
    :param color: RGB 颜色。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))


def draw_center_text(surface, text, font, color, y):
    """居中绘制文本。

    :param surface: 目标画布。
    :param text: 文本内容。
    :param font: Pygame 字体对象。
    :param color: RGB 颜色。
    :param y: 像素纵坐标。
    """
    if text:
        text_surface = font.render(text, True, color)
        text_x = (VW - text_surface.get_width()) // 2
        surface.blit(text_surface, (text_x, y))


def draw_center_in_rect(surface, text, font, color, rect):
    """在指定矩形内居中绘制文本。

    :param surface: 目标画布。
    :param text: 文本内容。
    :param font: Pygame 字体对象。
    :param color: RGB 颜色。
    :param rect: 矩形区域。
    """
    x, y, w, h = rect
    text_surface = font.render(text, True, color)
    text_x = x + (w - text_surface.get_width()) // 2
    text_y = y + (h - text_surface.get_height()) // 2
    surface.blit(text_surface, (text_x, text_y))


def wrap_text(text, font, max_width):
    """按像素宽度逐字换行，适合中文。

    Pygame 字体对象能直接计算字符串渲染后的像素宽度。
    中文文本通常没有英文那样稳定的空格分词，因此这里以像素宽度逐字扫描。
    TODO：如果以后转为网页 UI，可以改用浏览器排版或前端文本组件处理换行。

    :param text: 原始文本。
    :param font: Pygame 字体对象。
    :param max_width: 每行最大像素宽度。
    :return: 换行后的文本列表。
    """
    lines = []
    current = ''
    for char in text:
        test_line = current + char
        test_width = font.size(test_line)[0]
        if test_width <= max_width:
            current = test_line
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def draw_tooltip(surface, game_state, fonts):
    """绘制鼠标 tooltip。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    tooltip_text = current_tooltip_text(game_state)
    if tooltip_text != '':
        mouse_x, mouse_y = game_state['mouse_pos']
        font = fonts['tiny']
        wrapped_lines = wrap_text(tooltip_text, font, TOOLTIP_MAX_W)
        line_h = 18
        box_w = 0
        for wrapped_line in wrapped_lines:
            line_w = font.size(wrapped_line)[0]
            if line_w > box_w:
                box_w = line_w
        box_w += TOOLTIP_PAD * 2
        box_h = len(wrapped_lines) * line_h + TOOLTIP_PAD * 2
        box_x = mouse_x + TOOLTIP_MARGIN
        box_y = mouse_y + TOOLTIP_MARGIN
        if box_x + box_w > VW:
            box_x = mouse_x - box_w - TOOLTIP_MARGIN
        if box_y + box_h > VH:
            box_y = mouse_y - box_h - TOOLTIP_MARGIN
        pygame.draw.rect(surface, C_TOOLTIP_BG, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(surface, C_TOOLTIP_LINE, (box_x, box_y, box_w, box_h), 1)
        text_y = box_y + TOOLTIP_PAD
        for wrapped_line in wrapped_lines:
            draw_text(surface, wrapped_line, font, C_CREAM, box_x + TOOLTIP_PAD, text_y)
            text_y += line_h


def draw_button(surface, game_state, rect, label, action, font, enabled=True, tooltip=''):
    """绘制按钮并登记点击区域。

    本版本按钮 hover 效果：鼠标进入按钮矩形时，按钮底色、描边和文字颜色会变化。
    Pygame 不自带 GUI 组件，这里通过 pygame.Rect.collidepoint 做命中测试。
    面试考点：GUI hover 本质是“鼠标位置 + 控件矩形 + 每帧重绘”。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param rect: 按钮矩形。
    :param label: 按钮文字。
    :param action: 点击动作编号。
    :param font: Pygame 字体对象。
    :param enabled: True 表示按钮可点。
    :param tooltip: 鼠标提示文本。
    """
    mouse_pos = game_state['mouse_pos']
    rect_obj = pygame.Rect(rect)
    hovered = rect_obj.collidepoint(mouse_pos)
    if enabled and hovered:
        fill_color = C_BUTTON_HOVER
        line_color = C_GOLD
        text_color = C_WHITE
    elif enabled:
        fill_color = C_BUTTON
        line_color = C_BUTTON_LINE
        text_color = C_CREAM
    else:
        fill_color = (32, 30, 36)
        line_color = (58, 54, 62)
        text_color = C_GRAY
    pygame.draw.rect(surface, fill_color, rect)
    pygame.draw.rect(surface, line_color, rect, 2)
    draw_center_in_rect(surface, label, font, text_color, rect)
    if enabled:
        button = {'rect': rect, 'action': action, 'label': label}
        game_state['buttons'].append(button)
        if tooltip != '':
            register_ui_area(game_state, rect, tooltip, f'按钮动作：{action}')
        else:
            register_ui_area(game_state, rect, f'按钮：{label}', f'按钮动作：{action}')


def draw_shadow(surface, x, y, width):
    """绘制角色脚下阴影。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    :param width: 阴影宽度。
    """
    pygame.draw.ellipse(surface, (20, 19, 24), (x + 4, y + 25, width, 8))


def draw_sprite_hero(surface, x, y, step, hero_key):
    """根据主角形象编号绘制小红帽探索小人。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    :param step: 是否显示第一种脚步帧。
    :param hero_key: 主角形象编号。
    """
    if hero_key == 'scarlet':
        cloak_color = (228, 45, 54)
        dark_color = (90, 16, 24)
        accent_color = C_GOLD
    elif hero_key == 'berry':
        cloak_color = (204, 45, 96)
        dark_color = (116, 21, 64)
        accent_color = (164, 82, 212)
    elif hero_key == 'snow':
        cloak_color = C_RED
        dark_color = C_DARK_RED
        accent_color = C_WHITE
    else:
        cloak_color = C_RED
        dark_color = C_DARK_RED
        accent_color = C_CREAM
    draw_shadow(surface, x, y, 24)
    pygame.draw.rect(surface, dark_color, (x + 8, y + 10, 16, 18))
    pygame.draw.rect(surface, cloak_color, (x + 6, y + 12, 20, 17))
    pygame.draw.rect(surface, cloak_color, (x + 10, y + 4, 12, 10))
    pygame.draw.rect(surface, C_SKIN, (x + 12, y + 10, 8, 8))
    pygame.draw.rect(surface, C_BLACK, (x + 13, y + 12, 2, 2))
    pygame.draw.rect(surface, C_BLACK, (x + 18, y + 12, 2, 2))
    pygame.draw.rect(surface, C_WHITE, (x + 15, y + 16, 4, 1))
    pygame.draw.rect(surface, accent_color, (x + 23, y + 18, 7, 8))
    pygame.draw.rect(surface, C_DARK_BROWN, (x + 7, y + 28, 7, 4))
    if step:
        pygame.draw.rect(surface, C_DARK_BROWN, (x + 20, y + 28, 7, 4))
    else:
        pygame.draw.rect(surface, C_DARK_BROWN, (x + 18, y + 28, 7, 4))


def draw_sprite_humanoid(surface, x, y, body_color, hair_color, accessory_color):
    """绘制通用探索人形小人。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    :param body_color: 身体颜色。
    :param hair_color: 头发或帽子颜色。
    :param accessory_color: 配饰颜色。
    """
    draw_shadow(surface, x, y, 22)
    pygame.draw.rect(surface, body_color, (x + 8, y + 14, 18, 16))
    pygame.draw.rect(surface, C_SKIN, (x + 10, y + 6, 12, 12))
    pygame.draw.rect(surface, hair_color, (x + 8, y + 4, 16, 6))
    pygame.draw.rect(surface, accessory_color, (x + 24, y + 16, 7, 7))
    pygame.draw.rect(surface, C_BLACK, (x + 12, y + 10, 2, 2))
    pygame.draw.rect(surface, C_BLACK, (x + 18, y + 10, 2, 2))
    pygame.draw.rect(surface, C_WHITE, (x + 14, y + 15, 5, 1))


def draw_sprite_wolf(surface, x, y):
    """绘制灰狼探索小人。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    draw_shadow(surface, x, y, 25)
    pygame.draw.polygon(surface, C_GRAY, [(x + 8, y + 8), (x + 12, y), (x + 17, y + 10)])
    pygame.draw.polygon(surface, C_GRAY, [(x + 20, y + 9), (x + 25, y), (x + 28, y + 10)])
    pygame.draw.rect(surface, C_GRAY, (x + 8, y + 8, 20, 18))
    pygame.draw.rect(surface, C_DARK_GRAY, (x + 6, y + 16, 24, 10))
    pygame.draw.rect(surface, C_YELLOW, (x + 12, y + 12, 4, 2))
    pygame.draw.rect(surface, C_YELLOW, (x + 22, y + 12, 4, 2))
    pygame.draw.rect(surface, C_WHITE, (x + 18, y + 22, 2, 5))
    pygame.draw.rect(surface, C_WHITE, (x + 25, y + 22, 2, 5))


def draw_sprite_fake_grandma(surface, x, y):
    """绘制假外婆探索小人。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    draw_shadow(surface, x, y, 25)
    pygame.draw.rect(surface, (198, 190, 208), (x + 6, y + 10, 24, 20))
    pygame.draw.rect(surface, (232, 221, 231), (x + 10, y + 6, 16, 8))
    pygame.draw.rect(surface, C_GRAY, (x + 12, y + 12, 14, 10))
    pygame.draw.rect(surface, C_YELLOW, (x + 14, y + 14, 2, 2))
    pygame.draw.rect(surface, C_YELLOW, (x + 22, y + 14, 2, 2))
    pygame.draw.rect(surface, C_WHITE, (x + 20, y + 20, 2, 5))


def draw_sprite_red_cloak(surface, x, y):
    """绘制反对势力红斗篷小人。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    draw_shadow(surface, x, y, 22)
    pygame.draw.rect(surface, C_DARK_RED, (x + 8, y + 10, 18, 20))
    pygame.draw.rect(surface, C_RED, (x + 7, y + 12, 20, 18))
    pygame.draw.rect(surface, C_BLACK, (x + 12, y + 8, 10, 8))
    pygame.draw.rect(surface, C_GOLD, (x + 24, y + 20, 6, 6))


def draw_sprite_aileen(surface, x, y):
    """绘制艾琳探索小人。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    draw_sprite_humanoid(surface, x, y, (45, 72, 130), (230, 210, 120), (90, 170, 255))
    pygame.draw.circle(surface, (90, 170, 255), (x + 27, y + 12), 4)


def draw_sprite_blond_friend(surface, x, y):
    """绘制金发贫嘴男探索小人。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    draw_sprite_humanoid(surface, x, y, (84, 95, 150), (235, 205, 86), C_GOLD)
    pygame.draw.rect(surface, C_WHITE, (x + 13, y + 15, 8, 2))


def draw_sprite_cell_door(surface, x, y):
    """绘制火柴盒牢房门互动物。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    pygame.draw.rect(surface, C_DARK_GRAY, (x + 5, y + 4, 22, 28))
    for bar_x in (x + 9, x + 15, x + 21):
        pygame.draw.rect(surface, C_SILVER, (bar_x, y + 5, 3, 26))
    pygame.draw.rect(surface, (90, 170, 255), (x + 25, y + 15, 4, 5))
    pygame.draw.line(surface, C_GOLD, (x + 3, y + 30), (x + 29, y + 30), 2)


def draw_sprite_dropped_key(surface, x, y):
    """绘制掉落钥匙互动物。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    pygame.draw.circle(surface, C_GOLD, (x + 16, y + 16), 7, 2)
    pygame.draw.rect(surface, C_GOLD, (x + 22, y + 15, 10, 3))
    pygame.draw.rect(surface, C_GOLD, (x + 28, y + 18, 3, 5))


def draw_sprite_npc_by_role(surface, x, y, role):
    """根据角色类型绘制 NPC 探索小人。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    :param role: NPC 角色类型。
    """
    if role == 'mother':
        draw_sprite_humanoid(surface, x, y, C_BLUE, (95, 58, 34), C_WHITE)
    elif role == 'merchant':
        draw_sprite_humanoid(surface, x, y, (72, 94, 154), C_PALE, C_GOLD)
    elif role == 'hunter':
        draw_sprite_humanoid(surface, x, y, (65, 110, 61), (44, 71, 38), C_DARK_BROWN)
    elif role == 'grandma':
        draw_sprite_humanoid(surface, x, y, C_PURPLE, (232, 232, 232), C_CREAM)
    elif role == 'chief':
        draw_sprite_humanoid(surface, x, y, C_ORANGE, (84, 52, 32), C_GOLD)
    elif role == 'fake_grandma':
        draw_sprite_fake_grandma(surface, x, y)
    elif role == 'wolf':
        draw_sprite_wolf(surface, x, y)
    elif role == 'boy':
        draw_sprite_humanoid(surface, x, y, (48, 88, 144), (42, 36, 28), C_CREAM)
    elif role == 'resistance':
        draw_sprite_humanoid(surface, x, y, (80, 40, 96), (70, 45, 36), C_RED)
    elif role == 'spy':
        draw_sprite_humanoid(surface, x, y, (58, 52, 82), (235, 218, 160), (90, 170, 255))
        pygame.draw.rect(surface, C_WHITE, (x + 11, y + 15, 10, 2))
    elif role == 'red_cloak':
        draw_sprite_red_cloak(surface, x, y)
    elif role == 'king':
        draw_sprite_humanoid(surface, x, y, C_GOLD, C_DARK_BROWN, C_RED)
    elif role == 'aileen':
        draw_sprite_aileen(surface, x, y)
    elif role == 'blond_friend':
        draw_sprite_blond_friend(surface, x, y)
    elif role == 'cell_door':
        draw_sprite_cell_door(surface, x, y)
    elif role == 'dropped_key':
        draw_sprite_dropped_key(surface, x, y)
    else:
        draw_sprite_humanoid(surface, x, y, C_GRAY, C_DARK_GRAY, C_CREAM)


def draw_large_portrait_base(surface, rect, body_color, hair_color, accent_color, expression):
    """绘制区别于像素小人的大立绘基础人形。

    本函数不复用 draw_sprite_humanoid，而是用更大的头身比例、肩部、眼睛、衣领和表情线条重画角色。
    面试考点：同一个角色可以有“探索小人”和“对白立绘”两套表现层资源，逻辑层只传角色 role，不把表现层耦合到剧情数据。
    推荐书：中文《游戏编程模式》；英文 Game Programming Patterns。

    :param surface: 目标画布。
    :param rect: 立绘区域矩形。
    :param body_color: 身体主色。
    :param hair_color: 头发或帽子颜色。
    :param accent_color: 配饰颜色。
    :param expression: 表情编号。
    """
    x, y, w, h = rect
    pygame.draw.ellipse(surface, (8, 7, 12), (x + 38, y + 178, w - 76, 18))
    pygame.draw.rect(surface, body_color, (x + 48, y + 118, w - 96, 86))
    pygame.draw.polygon(surface, accent_color, [(x + 50, y + 122), (x + 98, y + 188), (x + 146, y + 122)])
    pygame.draw.circle(surface, C_SKIN, (x + w // 2, y + 78), 48)
    pygame.draw.arc(surface, hair_color, (x + 48, y + 24, w - 96, 84), 3.05, 6.25, 16)
    pygame.draw.rect(surface, hair_color, (x + 42, y + 48, w - 84, 28))
    pygame.draw.circle(surface, C_BLACK, (x + 78, y + 76), 5)
    pygame.draw.circle(surface, C_BLACK, (x + 118, y + 76), 5)
    if expression == 'smile':
        pygame.draw.arc(surface, C_DARK_RED, (x + 78, y + 88, 40, 24), 0.15, 2.95, 3)
    elif expression == 'serious':
        pygame.draw.line(surface, C_DARK_RED, (x + 82, y + 104), (x + 116, y + 104), 3)
    elif expression == 'worried':
        pygame.draw.arc(surface, C_DARK_RED, (x + 82, y + 94, 36, 26), 3.15, 6.05, 3)
    else:
        pygame.draw.rect(surface, C_DARK_RED, (x + 88, y + 101, 28, 3))


def draw_large_portrait_red(surface, rect, hero_key):
    """绘制小红帽大立绘。

    :param surface: 目标画布。
    :param rect: 立绘区域矩形。
    :param hero_key: 当前小红帽形象编号。
    """
    x, y, w, h = rect
    if hero_key == 'scarlet':
        cloak_color = (228, 45, 54)
        trim_color = C_GOLD
    elif hero_key == 'berry':
        cloak_color = (204, 45, 96)
        trim_color = (164, 82, 212)
    elif hero_key == 'snow':
        cloak_color = C_RED
        trim_color = C_WHITE
    else:
        cloak_color = C_RED
        trim_color = C_CREAM
    pygame.draw.ellipse(surface, (8, 7, 12), (x + 34, y + 178, w - 68, 18))
    pygame.draw.polygon(surface, C_DARK_RED, [(x + 32, y + 200), (x + 98, y + 72), (x + 166, y + 200)])
    pygame.draw.polygon(surface, cloak_color, [(x + 42, y + 198), (x + 98, y + 82), (x + 156, y + 198)])
    pygame.draw.circle(surface, C_SKIN, (x + 98, y + 84), 43)
    pygame.draw.arc(surface, cloak_color, (x + 48, y + 16, 100, 92), 3.05, 6.25, 18)
    pygame.draw.polygon(surface, cloak_color, [(x + 48, y + 64), (x + 98, y + 12), (x + 148, y + 64)])
    pygame.draw.circle(surface, C_BLACK, (x + 82, y + 82), 5)
    pygame.draw.circle(surface, C_BLACK, (x + 116, y + 82), 5)
    pygame.draw.arc(surface, C_DARK_RED, (x + 82, y + 94, 38, 22), 0.25, 2.85, 3)
    pygame.draw.rect(surface, trim_color, (x + 146, y + 132, 28, 44))
    pygame.draw.line(surface, C_GOLD, (x + 56, y + 190), (x + 142, y + 190), 3)


def draw_large_portrait_wolf(surface, rect, disguised):
    """绘制灰狼或假外婆大立绘。

    :param surface: 目标画布。
    :param rect: 立绘区域矩形。
    :param disguised: True 表示假外婆伪装，False 表示灰狼本体。
    """
    x, y, w, h = rect
    pygame.draw.ellipse(surface, (8, 7, 12), (x + 34, y + 180, w - 68, 18))
    if disguised:
        pygame.draw.rect(surface, (196, 188, 206), (x + 36, y + 110, w - 72, 88))
        pygame.draw.rect(surface, (232, 221, 231), (x + 44, y + 42, w - 88, 44))
    else:
        pygame.draw.rect(surface, C_DARK_GRAY, (x + 42, y + 118, w - 84, 80))
    pygame.draw.polygon(surface, C_GRAY, [(x + 56, y + 56), (x + 76, y + 8), (x + 98, y + 70)])
    pygame.draw.polygon(surface, C_GRAY, [(x + 122, y + 70), (x + 150, y + 8), (x + 166, y + 58)])
    pygame.draw.rect(surface, C_GRAY, (x + 46, y + 54, w - 92, 72))
    pygame.draw.rect(surface, C_DARK_GRAY, (x + 38, y + 88, w - 76, 38))
    pygame.draw.circle(surface, C_YELLOW, (x + 78, y + 82), 6)
    pygame.draw.circle(surface, C_YELLOW, (x + 120, y + 82), 6)
    pygame.draw.polygon(surface, C_WHITE, [(x + 102, y + 108), (x + 110, y + 136), (x + 116, y + 108)])
    pygame.draw.polygon(surface, C_WHITE, [(x + 122, y + 108), (x + 130, y + 136), (x + 136, y + 108)])


def draw_large_portrait_aileen(surface, rect):
    """绘制艾琳大立绘。

    :param surface: 目标画布。
    :param rect: 立绘区域矩形。
    """
    x, y, w, h = rect
    draw_large_portrait_base(surface, rect, (45, 72, 130), (230, 210, 120), (90, 170, 255), 'serious')
    pygame.draw.circle(surface, (90, 170, 255), (x + 154, y + 118), 18)
    pygame.draw.line(surface, C_CREAM, (x + 64, y + 42), (x + 136, y + 42), 3)
    pygame.draw.rect(surface, C_GOLD, (x + 91, y + 116, 16, 54))


def draw_large_portrait_blond_friend(surface, rect):
    """绘制莱昂大立绘。

    :param surface: 目标画布。
    :param rect: 立绘区域矩形。
    """
    x, y, w, h = rect
    draw_large_portrait_base(surface, rect, (84, 95, 150), (235, 205, 86), C_GOLD, 'smile')
    pygame.draw.line(surface, C_WHITE, (x + 76, y + 104), (x + 122, y + 104), 3)
    pygame.draw.circle(surface, C_GOLD, (x + 152, y + 128), 10)


def draw_large_portrait_spy(surface, rect):
    """绘制维克托大立绘。

    :param surface: 目标画布。
    :param rect: 立绘区域矩形。
    """
    x, y, w, h = rect
    draw_large_portrait_base(surface, rect, (58, 52, 82), (235, 218, 160), (90, 170, 255), 'smile')
    pygame.draw.rect(surface, C_WHITE, (x + 70, y + 116, 56, 16))
    pygame.draw.circle(surface, (90, 170, 255), (x + 144, y + 124), 9)
    pygame.draw.line(surface, C_SILVER, (x + 56, y + 146), (x + 144, y + 146), 2)


def draw_large_portrait_red_cloak(surface, rect):
    """绘制红斗篷组织成员大立绘。

    :param surface: 目标画布。
    :param rect: 立绘区域矩形。
    """
    x, y, w, h = rect
    pygame.draw.ellipse(surface, (8, 7, 12), (x + 34, y + 180, w - 68, 18))
    pygame.draw.polygon(surface, C_DARK_RED, [(x + 32, y + 200), (x + 98, y + 54), (x + 166, y + 200)])
    pygame.draw.polygon(surface, C_RED, [(x + 44, y + 196), (x + 98, y + 70), (x + 154, y + 196)])
    pygame.draw.rect(surface, C_BLACK, (x + 72, y + 62, 56, 44))
    pygame.draw.circle(surface, C_CREAM, (x + 82, y + 88), 4)
    pygame.draw.circle(surface, C_CREAM, (x + 116, y + 88), 4)
    pygame.draw.rect(surface, C_GOLD, (x + 136, y + 140, 22, 20))


def draw_large_portrait_by_role(surface, game_state, rect, portrait_role):
    """根据对白立绘 role 绘制大立绘。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param rect: 立绘区域矩形。
    :param portrait_role: 立绘角色类型。
    """
    hero_key = game_state['hero_key']
    if portrait_role == 'red':
        draw_large_portrait_red(surface, rect, hero_key)
    elif portrait_role == 'wolf':
        draw_large_portrait_wolf(surface, rect, False)
    elif portrait_role == 'fake_grandma':
        draw_large_portrait_wolf(surface, rect, True)
    elif portrait_role == 'aileen':
        draw_large_portrait_aileen(surface, rect)
    elif portrait_role == 'blond_friend':
        draw_large_portrait_blond_friend(surface, rect)
    elif portrait_role == 'spy':
        draw_large_portrait_spy(surface, rect)
    elif portrait_role == 'red_cloak':
        draw_large_portrait_red_cloak(surface, rect)
    elif portrait_role == 'mother':
        draw_large_portrait_base(surface, rect, C_BLUE, (95, 58, 34), C_WHITE, 'worried')
    elif portrait_role == 'merchant':
        draw_large_portrait_base(surface, rect, (72, 94, 154), C_PALE, C_GOLD, 'smile')
    elif portrait_role == 'hunter':
        draw_large_portrait_base(surface, rect, (65, 110, 61), (44, 71, 38), C_DARK_BROWN, 'serious')
    elif portrait_role == 'grandma':
        draw_large_portrait_base(surface, rect, C_PURPLE, (232, 232, 232), C_CREAM, 'worried')
    elif portrait_role == 'resistance':
        draw_large_portrait_base(surface, rect, (80, 40, 96), (70, 45, 36), C_RED, 'serious')
    elif portrait_role == 'king':
        draw_large_portrait_base(surface, rect, C_GOLD, C_DARK_BROWN, C_RED, 'serious')
        x, y, w, h = rect
        pygame.draw.polygon(surface, C_GOLD, [(x + 62, y + 40), (x + 82, y + 12), (x + 98, y + 40), (x + 118, y + 12), (x + 140, y + 40)])
    elif portrait_role == 'boy':
        draw_large_portrait_base(surface, rect, (48, 88, 144), (42, 36, 28), C_CREAM, 'worried')
    else:
        draw_large_portrait_base(surface, rect, C_GRAY, C_DARK_GRAY, C_CREAM, 'neutral')


def draw_menu_bar(surface, game_state, fonts):
    """绘制顶部菜单栏按钮。

    顶部菜单栏独立占用 MENU_BAR_H，不和中央顶栏、侧边栏或地图区域共用坐标。
    “提示”按钮用于开关 tooltip，默认关闭，避免普通游玩时被代码定位文字打扰。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    pygame.draw.rect(surface, (10, 9, 14), (0, 0, VW, MENU_BAR_H))
    register_ui_area(game_state, (0, 0, VW, MENU_BAR_H), '区域：顶部菜单栏', 'draw_menu_bar / MENU_BUTTONS')
    x = 8
    for menu_button in MENU_BUTTONS:
        label = menu_button['label']
        action = menu_button['action']
        tooltip = menu_button['tooltip']
        rect = (x, 4, 78, 22)
        font = fonts['tiny']
        draw_button(surface, game_state, rect, label, action, font, True, tooltip)
        x += 84


def draw_furniture_tile(surface, tile, px, py):
    """绘制室内家具瓦片。

    本函数专门强化“房间等室内场景中应该有床、餐桌、家具”的需求。
    每种家具仍然由 MAPS 里的单个字符驱动，这样地图编辑时只需要改字符串。
    面试考点：这是典型的 tile symbol -> renderer rule 映射。

    :param surface: 目标画布。
    :param tile: 瓦片字符。
    :param px: 像素横坐标。
    :param py: 像素纵坐标。
    """
    if tile == 'b':
        pygame.draw.rect(surface, (76, 44, 28), (px + 4, py + 5, 24, 24))
        pygame.draw.rect(surface, (126, 82, 48), (px + 7, py + 8, 18, 18))
        pygame.draw.rect(surface, C_GOLD, (px + 13, py + 13, 4, 4))
    elif tile == 'r':
        pygame.draw.rect(surface, C_DARK_BROWN, (px + 4, py + 6, 24, 22))
        pygame.draw.rect(surface, C_DARK_RED, (px + 6, py + 10, 20, 16))
        pygame.draw.rect(surface, C_CREAM, (px + 7, py + 7, 11, 8))
    elif tile == 't':
        pygame.draw.ellipse(surface, (112, 70, 43), (px + 4, py + 7, 24, 18))
        pygame.draw.ellipse(surface, (154, 101, 56), (px + 7, py + 9, 18, 12))
    elif tile == 's':
        pygame.draw.rect(surface, (92, 66, 48), (px + 9, py + 10, 15, 9))
        pygame.draw.rect(surface, (72, 48, 34), (px + 11, py + 5, 11, 9))
    elif tile == 'w':
        pygame.draw.rect(surface, (70, 48, 78), (px + 6, py + 3, 20, 27))
        pygame.draw.line(surface, (132, 102, 148), (px + 9, py + 4), (px + 9, py + 29), 2)


def current_matchbox_drawer_progress(game_state):
    """计算火柴盒囚室抽屉拉动进度。

    Pygame 每帧都会重绘，因此不需要额外动画对象；用 tick 与剧情 flags 就能确定当前帧应该画到哪个位置。
    面试考点：很多 2D 游戏动画并不是复杂物理模拟，而是“状态 + 时间参数 + 插值位置”的组合。
    TODO：后续可以把抽屉拉动做成带缓动曲线的剧情镜头，例如使用专门的 tween/easing 第三方库。

    :param game_state: 游戏状态字典。
    :return: 0 到 1 之间的抽屉拉动进度。
    """
    flags = game_state['flags']
    view_actor = game_state['view_actor']
    if flags['prison_rooms_opened'] or flags['prison_escaped']:
        progress = 1.0
    elif view_actor == 'blond_friend' and flags['pov_blond_friend_started']:
        tick = game_state['tick']
        cycle_frame = tick % 120
        if cycle_frame <= 80:
            progress = cycle_frame / 80
        else:
            progress = 1.0
    elif view_actor == 'aileen' and flags['pov_aileen_started']:
        progress = 0.0
    else:
        progress = 0.0
    return progress


def draw_matchbox_drawer_layer(surface, game_state, px, py, drawer_w, drawer_h, direction, progress, drawer_name):
    """绘制单个火柴盒抽屉囚室层。

    这里使用带 alpha 通道的临时 Surface 绘制透明抽屉，再 blit 到主画布。
    Pygame Surface with SRCALPHA 可以表达半透明轨道、幽暗内胆和蓝色火柴烟线。
    面试考点：在 Pygame 中做局部透明效果通常不是直接给主画布画 alpha 颜色，而是先画到带 SRCALPHA 的临时 Surface 再合成。
    推荐书：英文 Making Games with Python & Pygame；中文可结合《游戏编程模式》理解表现层叠加。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param px: 外壳左上角像素横坐标。
    :param py: 外壳左上角像素纵坐标。
    :param drawer_w: 外壳宽度。
    :param drawer_h: 外壳高度。
    :param direction: 抽屉拉动方向，1 表示向右，-1 表示向左。
    :param progress: 抽屉拉动进度。
    :param drawer_name: 抽屉名称，用于 tooltip。
    """
    pygame.draw.rect(surface, C_GOLD, (px + 2, py + 2, drawer_w - 4, drawer_h - 4), 2)
    pygame.draw.line(surface, (90, 170, 255), (px + 10, py + drawer_h - 10), (px + drawer_w - 10, py + drawer_h - 10), 2)
    for ghost_index in range(1, 4):
        ghost_offset = direction * ghost_index * 18
        ghost_rect = (px + ghost_offset + 5, py + 8, drawer_w - 10, drawer_h - 16)
        pygame.draw.rect(surface, (92, 80, 104), ghost_rect, 1)
    move_offset = int(direction * 82 * progress)
    drawer_x = px + move_offset
    drawer_surface = pygame.Surface((drawer_w + 20, drawer_h + 16), pygame.SRCALPHA)
    pygame.draw.rect(drawer_surface, (18, 16, 28, 210), (10, 6, drawer_w, drawer_h))
    pygame.draw.rect(drawer_surface, (222, 181, 82, 230), (10, 6, drawer_w, drawer_h), 3)
    pygame.draw.rect(drawer_surface, (72, 72, 88, 220), (22, 18, drawer_w - 24, drawer_h - 24))
    for bar_index in range(5):
        bar_x = 30 + bar_index * 24
        pygame.draw.rect(drawer_surface, (190, 200, 210, 230), (bar_x, 14, 4, drawer_h - 16))
    smoke_y = drawer_h - 12
    pygame.draw.line(drawer_surface, (90, 170, 255, 230), (18, smoke_y), (drawer_w - 4, smoke_y), 3)
    surface.blit(drawer_surface, (drawer_x - 10, py - 6))
    if progress > 0:
        start_x = px + drawer_w // 2
        end_x = drawer_x + drawer_w // 2
        arrow_y = py + drawer_h + 8
        pygame.draw.line(surface, C_GOLD, (start_x, arrow_y), (end_x, arrow_y), 3)
        pygame.draw.circle(surface, C_GOLD, (end_x, arrow_y), 5)
    area_x = min(px, drawer_x) - 12
    area_w = drawer_w + abs(move_offset) + 24
    area_rect = (area_x, py - 8, area_w, drawer_h + 24)
    tooltip = f'区域：火柴盒监狱抽屉囚室｜{drawer_name}｜进度 {progress:.2f}'
    register_ui_area(game_state, area_rect, tooltip, 'draw_matchbox_drawer_layer / current_matchbox_drawer_progress')


def draw_matchbox_prison_seams(surface, game_state):
    """绘制火柴盒监狱抽拉缝隙与抽屉动画。

    这些金色和蓝色线条不是普通装饰，而是剧情信息。
    艾琳在第七幕看不懂它们，以为只是牢房墙缝；露比和莱昂知道这些缝隙代表囚室可以像火柴盒抽屉一样被拉出或推入。
    本版新增：中层囚室会随剧情进度出现明显抽屉拉动效果，满足“囚室像抽屉拉动一样”的视觉需求。
    面试考点：同一个地图瓦片可以叠加剧情语义层，底层碰撞不变，表现层额外绘制信息差。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    """
    scene = game_state['scene']
    if scene == 'matchbox_prison':
        drawer_specs = [
            (2, 2, 6, 3, 1, '左上备用抽拉囚室', False),
            (11, 2, 6, 3, -1, '右上备用抽拉囚室', False),
            (2, 6, 6, 3, 1, '左中真实囚室抽屉', True),
            (11, 6, 6, 3, -1, '右中真实囚室抽屉', True),
            (2, 10, 6, 3, 1, '左下备用抽拉囚室', False),
            (11, 10, 6, 3, -1, '右下备用抽拉囚室', False),
        ]
        active_progress = current_matchbox_drawer_progress(game_state)
        for drawer_spec in drawer_specs:
            tile_x, tile_y, tile_w, tile_h, direction, drawer_name, active = drawer_spec
            px = LEFT_BAR_W + tile_x * TILE
            py = TOP_BAR_H + tile_y * TILE
            drawer_w = tile_w * TILE
            drawer_h = tile_h * TILE
            if active:
                progress = active_progress
            else:
                progress = 0.0
            draw_matchbox_drawer_layer(surface, game_state, px, py, drawer_w, drawer_h, direction, progress, drawer_name)


def draw_tile_map(surface, game_state):
    """绘制瓦片地图。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    """
    scene = game_state['scene']
    current_map = MAPS[scene]
    map_rect = (LEFT_BAR_W, TOP_BAR_H, VIEW_W, VIEW_H)
    register_ui_area(game_state, map_rect, f'区域：主地图 {SCENE_NAMES[scene]}', 'draw_tile_map / MAPS / TILE_SPECS')
    for tile_y, row in enumerate(current_map):
        for tile_x, tile in enumerate(row):
            px = LEFT_BAR_W + tile_x * TILE
            py = TOP_BAR_H + tile_y * TILE
            color = TILE_COLORS[tile]
            pygame.draw.rect(surface, color, (px, py, TILE, TILE))
            tile_spec = TILE_SPECS[tile]
            tile_name = tile_spec['name']
            tile_intent = tile_spec['intent']
            tooltip = f'区域：地图瓦片 {SCENE_NAMES[scene]} ({tile_x},{tile_y})｜{tile_name}｜{tile_intent}'
            register_ui_area(game_state, (px, py, TILE, TILE), tooltip, f"MAPS['{scene}'] / TILE_SPECS['{tile}']")
            if tile == 'G':
                pygame.draw.rect(surface, C_LIGHT_GREEN, (px + 4, py + 6, 8, 5))
            elif tile == 'P':
                pygame.draw.rect(surface, (188, 145, 87), (px + 2, py + 4, 8, 4))
            elif tile == '#':
                pygame.draw.polygon(surface, C_DARK_GREEN, [(px, py + 24), (px + 16, py), (px + 32, py + 24)])
                pygame.draw.rect(surface, (72, 45, 26), (px + 14, py + 18, 4, 14))
            elif tile == 'D':
                pygame.draw.rect(surface, (88, 48, 34), (px + 6, py + 4, 20, 28))
                pygame.draw.rect(surface, C_YELLOW, (px + 22, py + 16, 4, 4))
            elif tile == 'S':
                pygame.draw.rect(surface, (94, 58, 30), (px + 14, py + 15, 4, 17))
                pygame.draw.rect(surface, (189, 119, 58), (px + 6, py + 4, 20, 12))
            elif tile == 'X':
                pygame.draw.line(surface, (32, 72, 40), (px + 4, py + 26), (px + 28, py + 6), 4)
                pygame.draw.line(surface, (32, 72, 40), (px + 5, py + 6), (px + 28, py + 26), 4)
            elif tile == 'A':
                pygame.draw.rect(surface, C_DARK_GRAY, (px + 4, py + 4, 24, 28))
                for bar_x in (px + 7, px + 13, px + 19, px + 25):
                    pygame.draw.rect(surface, C_SILVER, (bar_x, py + 4, 3, 28))
            elif tile == 'm':
                pygame.draw.rect(surface, (95, 65, 44), (px + 5, py + 8, 22, 20))
            elif tile == 'L':
                pygame.draw.rect(surface, C_DARK_GRAY, (px + 15, py + 8, 3, 24))
                pygame.draw.circle(surface, C_PALE, (px + 16, py + 8), 6)
            elif tile == 'H':
                pygame.draw.rect(surface, (70, 78, 96), (px + 4, py + 5, 24, 24))
            elif tile == 'M':
                pygame.draw.rect(surface, (84, 84, 100), (px + 5, py + 4, 22, 28))
            elif tile in {'b', 'r', 's', 't', 'w'}:
                draw_furniture_tile(surface, tile, px, py)
            pygame.draw.rect(surface, (0, 0, 0), (px, py, TILE, TILE), 1)
    draw_matchbox_prison_seams(surface, game_state)
    draw_portal_effects(surface, game_state)


def draw_portal_effects(surface, game_state):
    """绘制传送门静态标记。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    """
    scene = game_state['scene']
    for portal_spec in PORTALS:
        portal_scene = portal_spec['scene']
        if portal_scene == scene:
            portal_x = portal_spec['x']
            portal_y = portal_spec['y']
            px = LEFT_BAR_W + portal_x * TILE
            py = TOP_BAR_H + portal_y * TILE
            to_scene = portal_spec['to_scene']
            to_scene_name = SCENE_NAMES[to_scene]
            tooltip = f'区域：传送门 {SCENE_NAMES[scene]}({portal_x},{portal_y}) → {to_scene_name}'
            register_ui_area(game_state, (px, py, TILE, TILE), tooltip, 'PORTAL_BLUEPRINTS / check_portal / portal_is_open')
            if portal_is_open(game_state, portal_spec):
                pygame.draw.rect(surface, C_YELLOW, (px + 4, py + 4, TILE - 8, TILE - 8), 2)
                pygame.draw.circle(surface, C_PALE, (px + 16, py + 16), 3)
            else:
                pygame.draw.rect(surface, C_LOCKED, (px + 4, py + 4, TILE - 8, TILE - 8), 2)
                pygame.draw.line(surface, C_LOCKED, (px + 7, py + 7), (px + 25, py + 25), 2)


def draw_time_overlay(surface, game_state):
    """根据当前时段给地图叠加颜色。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    """
    time_key = game_state['time_of_day']
    time_spec = TIME_OF_DAY_SPECS[time_key]
    overlay_color = time_spec['overlay']
    overlay_surface = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
    overlay_surface.fill(overlay_color)
    surface.blit(overlay_surface, (LEFT_BAR_W, TOP_BAR_H))


def draw_particles(surface, app_state):
    """绘制粒子特效。

    :param surface: 目标画布。
    :param app_state: 应用状态字典。
    """
    game_state = app_state['game_state']
    settings = game_state['settings']
    scene = game_state['scene']
    particle_scenes = ('forest', 'winter_street', 'whisper_hotel', 'matchbox_prison', 'match_market', 'royal_square')
    if settings['particles_enabled'] and scene in particle_scenes:
        tick = game_state['tick']
        particles = app_state['particles']
        for particle in particles:
            particle_x, particle_y, particle_speed, particle_index = particle
            mote_x = LEFT_BAR_W + (particle_x + tick // particle_speed) % VIEW_W
            mote_y = TOP_BAR_H + (particle_y + particle_index * 3) % VIEW_H
            if scene in ('matchbox_prison', 'match_market', 'royal_square'):
                surface.set_at((mote_x, mote_y), (90, 170, 255))
            else:
                surface.set_at((mote_x, mote_y), (170, 210, 140))


def draw_items(surface, game_state):
    """绘制未收集道具。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    """
    scene = game_state['scene']
    collected = game_state['collected']
    tick = game_state['tick']
    for collectible in ITEMS:
        collectible_key = collectible['key']
        collectible_scene = collectible['scene']
        if item_enabled(collectible) and collectible_scene == scene and collectible_key not in collected:
            item_x = LEFT_BAR_W + collectible['x'] * TILE
            item_y = TOP_BAR_H + collectible['y'] * TILE
            kind = collectible['kind']
            color = collectible['color']
            item_name = collectible['name']
            item_intent = collectible['intent']
            tooltip = f'区域：可收集物 {item_name}｜类型：{kind}｜用途：{item_intent}'
            register_ui_area(game_state, (item_x, item_y, TILE, TILE), tooltip, 'ITEMS / draw_items / collect_item')
            if kind == 'honey':
                pygame.draw.rect(surface, (120, 78, 28), (item_x + 12, item_y + 10, 12, 18))
                pygame.draw.rect(surface, color, (item_x + 14, item_y + 13, 8, 12))
                pygame.draw.rect(surface, C_CREAM, (item_x + 14, item_y + 8, 8, 4))
            elif kind == 'flower':
                pygame.draw.rect(surface, (57, 145, 76), (item_x + 15, item_y + 18, 4, 10))
                pygame.draw.circle(surface, color, (item_x + 17, item_y + 14), 7)
                pygame.draw.circle(surface, C_YELLOW, (item_x + 17, item_y + 14), 3)
            elif kind == 'truth_clue':
                pygame.draw.rect(surface, color, (item_x + 12, item_y + 10, 11, 11))
                pygame.draw.rect(surface, C_CREAM, (item_x + 14, item_y + 12, 7, 7))
            elif kind == 'match_clue':
                pygame.draw.rect(surface, (38, 36, 50), (item_x + 12, item_y + 8, 12, 18))
                pygame.draw.circle(surface, color, (item_x + 18, item_y + 8), 5)
            elif kind == 'cloth':
                pulse = (tick // 12) % 3
                pygame.draw.rect(surface, color, (item_x + 10, item_y + 10, 14 + pulse, 14 + pulse))
                pygame.draw.line(surface, C_WHITE, (item_x + 11, item_y + 12), (item_x + 24, item_y + 24), 2)


def draw_npcs(surface, game_state, fonts):
    """绘制当前可见 NPC。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    player = game_state['player']
    npcs = visible_npcs(game_state)
    for npc_spec in npcs:
        x = LEFT_BAR_W + npc_spec['x'] * TILE
        y = TOP_BAR_H + npc_spec['y'] * TILE
        role = npc_spec['role']
        draw_sprite_npc_by_role(surface, x, y, role)
        npc_name = npc_spec['name']
        npc_title = npc_spec['title']
        npc_action = npc_spec['action']
        npc_intro = npc_spec['intro']
        tooltip = f'区域：NPC {npc_name}｜{npc_title}｜{npc_intro}'
        register_ui_area(game_state, (x, y, TILE, TILE), tooltip, f"NPC_SPECS action='{npc_action}' / visible_npcs / talk_by_action")
        npc_x = npc_spec['x']
        npc_y = npc_spec['y']
        distance = abs(npc_x - player['x']) + abs(npc_y - player['y'])
        if distance == 1:
            draw_text(surface, '!', fonts['big'], C_YELLOW, x + 12, y - 24)


def draw_player(surface, game_state):
    """绘制玩家。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    """
    player = game_state['player']
    player_x = LEFT_BAR_W + int(player['px'])
    player_y = TOP_BAR_H + int(player['py'])
    step = player['step_timer'] < 16
    actor_role = current_view_actor_role(game_state)
    tooltip = f'区域：当前可操控角色 {current_view_actor_name(game_state)}'
    register_ui_area(game_state, (player_x, player_y, TILE, TILE), tooltip, 'draw_player / game_state["view_actor"] / ACTOR_SPECS')
    if actor_role == 'red':
        hero_key = game_state['hero_key']
        draw_sprite_hero(surface, player_x, player_y, step, hero_key)
    else:
        draw_sprite_npc_by_role(surface, player_x, player_y, actor_role)


def path_hint_candidates(game_state, goal):
    """根据当前目标生成寻路指示候选点。

    :param game_state: 游戏状态字典。
    :param goal: 当前目标。
    :return: 候选点列表。
    """
    candidates = []
    scene = game_state['scene']
    goal_kind = goal['kind']
    goal_scene = goal['scene']
    if goal_kind == 'action' and scene == goal_scene:
        action = goal['action']
        npc_spec = find_visible_npc_by_action(game_state, action)
        if npc_spec is not None:
            npc_x = npc_spec['x']
            npc_y = npc_spec['y']
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for direction in directions:
                dx, dy = direction
                candidate = (npc_x + dx, npc_y + dy)
                candidate_x, candidate_y = candidate
                if can_walk_for_path(game_state, candidate_x, candidate_y):
                    candidates.append(candidate)
    elif goal_kind == 'item' and scene == goal_scene:
        item_key = goal['item_key']
        collectible = find_collectible_by_key(item_key)
        target_x = collectible['x']
        target_y = collectible['y']
        candidates.append((target_x, target_y))
    elif goal_kind != 'idle' and scene != goal_scene:
        scene_route = nx.shortest_path(SCENE_GRAPH, scene, goal_scene)
        next_scene = scene_route[1]
        portal = find_portal_to_scene(game_state, next_scene)
        portal_x = portal['x']
        portal_y = portal['y']
        candidates.append((portal_x, portal_y))
    return candidates


def draw_route_hint(surface, game_state):
    """绘制非自动模式下的寻路指示线。

    More Itertools 是第三方迭代工具库，windowed 能把路径点按相邻两点成组，避免手写索引管理。
    面试考点：more_itertools 这类迭代工具能减少边界错误，让“相邻元素配对”“分块布局”等代码更直观。
    推荐书：英文 Fluent Python；中文《流畅的 Python》中文版。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    """
    settings = game_state['settings']
    if settings['show_path_hint'] and not game_state['auto_play'] and game_state['ui_state'] == 'explore':
        goal = current_auto_goal(game_state)
        candidates = path_hint_candidates(game_state, goal)
        if candidates:
            path = find_path_to_candidates(game_state, candidates)
            if path:
                for point in path:
                    tile_x, tile_y = point
                    px = LEFT_BAR_W + tile_x * TILE + TILE // 2
                    py = TOP_BAR_H + tile_y * TILE + TILE // 2
                    pygame.draw.circle(surface, C_ROUTE, (px, py), 4)
                for pair in windowed(path, 2):
                    left_point, right_point = pair
                    left_x, left_y = left_point
                    right_x, right_y = right_point
                    left_px = LEFT_BAR_W + left_x * TILE + TILE // 2
                    left_py = TOP_BAR_H + left_y * TILE + TILE // 2
                    right_px = LEFT_BAR_W + right_x * TILE + TILE // 2
                    right_py = TOP_BAR_H + right_y * TILE + TILE // 2
                    pygame.draw.line(surface, C_ROUTE, (left_px, left_py), (right_px, right_py), 2)


def draw_side_bars(surface, game_state, fonts):
    """绘制左右侧栏。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    flags = game_state['flags']
    player = game_state['player']
    inventory = game_state['inventory']
    settings = game_state['settings']
    pygame.draw.rect(surface, C_PANEL, (0, MENU_BAR_H, LEFT_BAR_W, VH - MENU_BAR_H))
    pygame.draw.rect(surface, C_PANEL, (LEFT_BAR_W + VIEW_W, MENU_BAR_H, RIGHT_BAR_W, VH - MENU_BAR_H))
    pygame.draw.rect(surface, C_PANEL_LINE, (LEFT_BAR_W - 1, MENU_BAR_H, 1, VH - MENU_BAR_H))
    pygame.draw.rect(surface, C_PANEL_LINE, (LEFT_BAR_W + VIEW_W, MENU_BAR_H, 1, VH - MENU_BAR_H))
    register_ui_area(game_state, (0, MENU_BAR_H, LEFT_BAR_W, VH - MENU_BAR_H), '区域：左侧状态栏', 'draw_side_bars：主视角、时间、生命、自动状态、当前任务')
    register_ui_area(game_state, (LEFT_BAR_W + VIEW_W, MENU_BAR_H, RIGHT_BAR_W, VH - MENU_BAR_H), '区域：右侧资源栏', 'draw_side_bars：资源、单格门、成就')
    actor_role = current_view_actor_role(game_state)
    tick = game_state['tick']
    hero_step = (tick // 18) % 2 == 0
    if actor_role == 'red':
        hero_key = game_state['hero_key']
        draw_sprite_hero(surface, 98, 52, hero_step, hero_key)
    else:
        draw_sprite_npc_by_role(surface, 98, 52, actor_role)
    actor_name = current_view_actor_name(game_state)
    draw_center_in_rect(surface, f'主视角：{actor_name}', fonts['small'], C_CREAM, (8, 88, LEFT_BAR_W - 16, 24))
    time_key = game_state['time_of_day']
    time_name = TIME_OF_DAY_SPECS[time_key]['name']
    draw_center_in_rect(surface, f'时段：{time_name}', fonts['small'], C_YELLOW, (8, 112, LEFT_BAR_W - 16, 24))
    draw_text(surface, '生命', fonts['small'], C_WHITE, 14, 142)
    pygame.draw.rect(surface, C_BLACK, (14, 168, LEFT_BAR_W - 28, 16))
    hp_fill = int((LEFT_BAR_W - 34) * player['hp'] / player['max_hp'])
    pygame.draw.rect(surface, C_RED, (17, 172, hp_fill, 8))
    hp_text = f'{player["hp"]}/{player["max_hp"]}'
    draw_text(surface, hp_text, fonts['small'], C_WHITE, 14, 190)
    auto_speed = current_auto_speed(game_state)
    left_status = [
        f'起始跳幕：{game_state["title_skip_acts"]}',
        f'自动：{"开" if game_state["auto_play"] else "关"}',
        f'朗读：{"开" if game_state["voice_enabled"] else "关"}',
        f'音效：{"开" if settings["sound_enabled"] else "关"}',
        f'Tooltip：{"开" if settings["tooltip_enabled"] else "关"}',
        f'速度：{auto_speed} 倍',
        f'拾取：{"可达" if settings["auto_pickup_reachable_items"] else "关闭"}',
        f'男卧底：{CHARACTER_PROFILES["spy"]["name"]}',
    ]
    y = 218
    for line in left_status:
        draw_text(surface, line, fonts['small'], C_YELLOW, 14, y)
        y += 22
    y += 10
    left_lines = [
        '当前任务',
        current_task(game_state),
        '推荐路线',
        current_route_text(game_state),
        main_story_progress(game_state),
    ]
    for line in left_lines:
        wrapped = wrap_text(line, fonts['small'], LEFT_BAR_W - 28)
        for wrapped_line in wrapped:
            if y < VH - 112:
                draw_text(surface, wrapped_line, fonts['small'], C_WHITE, 14, y)
                y += 22
        y += 8
    right_x = LEFT_BAR_W + VIEW_W + 16
    draw_text(surface, '资源与系统', fonts['big'], C_CREAM, right_x, 48)
    resource_lines = [
        f'铜币 {inventory["铜币"]}',
        f'蜂蜜 {flags["honeys"]}/3',
        f'野花 {flags["wildflowers"]}/2',
        f'真相线索 {flags["truth_clues"]}/2',
        f'火柴证据 {flags["match_clues"]}/2',
        f'酒店名单 {inventory["酒店名单"]}',
        f'牢房钥匙 {inventory["牢房钥匙"]}',
        f'防烟布 {inventory["防烟布"]}',
        f'战斗胜利 {flags["battles_won"]}/2',
        f'木哨 {inventory["木哨"]}',
    ]
    y = 84
    for line in resource_lines:
        draw_text(surface, line, fonts['small'], C_WHITE, right_x, y)
        y += 22
    draw_text(surface, '本场景单格门', fonts['big'], C_CREAM, right_x, 302)
    y = 338
    portal_lines = current_scene_portal_lines(game_state)
    if portal_lines:
        for portal_line in portal_lines:
            wrapped = wrap_text(portal_line, fonts['tiny'], RIGHT_BAR_W - 32)
            for wrapped_line in wrapped:
                if y < 418:
                    draw_text(surface, wrapped_line, fonts['tiny'], C_WHITE, right_x, y)
                    y += 18
    else:
        draw_text(surface, '暂无', fonts['small'], C_WHITE, right_x, y)
    draw_text(surface, '成就', fonts['big'], C_CREAM, right_x, 436)
    badge_names = []
    for badge_key in game_state['badges']:
        badge_name = BADGE_NAMES[badge_key]
        badge_names.append(badge_name)
    badge_names.sort()
    y = 472
    if badge_names:
        for badge_name in badge_names:
            wrapped = wrap_text(badge_name, fonts['tiny'], RIGHT_BAR_W - 32)
            for wrapped_line in wrapped:
                if y < VH - 70:
                    draw_text(surface, f'· {wrapped_line}', fonts['tiny'], C_WHITE, right_x, y)
                    y += 18
    else:
        draw_text(surface, '暂无', fonts['small'], C_WHITE, right_x, y)


def draw_top_bar(surface, game_state, fonts):
    """绘制中央顶栏。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    flags = game_state['flags']
    pygame.draw.rect(surface, C_PANEL_DARK, (LEFT_BAR_W, MENU_BAR_H, VIEW_W, TOP_BAR_H - MENU_BAR_H))
    register_ui_area(game_state, (LEFT_BAR_W, MENU_BAR_H, VIEW_W, TOP_BAR_H - MENU_BAR_H), '区域：中央顶栏', 'draw_top_bar：场景名、当前任务、路线和进度')
    scene = game_state['scene']
    scene_name = SCENE_NAMES[scene]
    time_key = game_state['time_of_day']
    time_name = TIME_OF_DAY_SPECS[time_key]['name']
    top_text = f'{scene_name}｜{time_name}｜{current_task(game_state)}'
    top_lines = wrap_text(top_text, fonts['small'], VIEW_W - 180)
    if top_lines:
        top_line = top_lines[0]
        draw_text(surface, top_line, fonts['small'], C_WHITE, LEFT_BAR_W + 10, 38)
    status = f'步数:{flags["steps_taken"]}  自动动作:{flags["auto_actions"]}'
    status_w = fonts['small'].size(status)[0]
    status_x = LEFT_BAR_W + VIEW_W - status_w - 10
    draw_text(surface, status, fonts['small'], C_CREAM, status_x, 38)
    route_text = f'路线：{current_route_text(game_state)}'
    route_lines = wrap_text(route_text, fonts['small'], VIEW_W - 20)
    if route_lines:
        route_line = route_lines[0]
        draw_text(surface, route_line, fonts['small'], (190, 210, 185), LEFT_BAR_W + 10, 58)
    progress_text = main_story_progress(game_state)
    draw_text(surface, progress_text, fonts['small'], C_YELLOW, LEFT_BAR_W + VIEW_W - 154, 58)


def draw_status_bar(surface, game_state, fonts):
    """绘制独立状态栏。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    status_y = TOP_BAR_H + VIEW_H
    pygame.draw.rect(surface, (18, 16, 23), (LEFT_BAR_W, status_y, VIEW_W, STATUS_BAR_H))
    pygame.draw.rect(surface, C_PANEL_LINE, (LEFT_BAR_W, status_y, VIEW_W, 1))
    register_ui_area(game_state, (LEFT_BAR_W, status_y, VIEW_W, STATUS_BAR_H), '区域：中央状态栏', 'draw_status_bar：短消息与当前 UI 状态')
    if game_state['message_timer'] > 0:
        status_text = game_state['message']
    else:
        ui_state = game_state['ui_state']
        status_text = f'状态：{ui_state}｜按 P 暂停，按 R 切换寻路线，按 O 自动游玩，顶部“提示”开关 tooltip。'
    status_lines = wrap_text(status_text, fonts['small'], VIEW_W - 20)
    if status_lines:
        status_line = status_lines[0]
        draw_text(surface, status_line, fonts['small'], C_YELLOW, LEFT_BAR_W + 10, status_y + 8)


def draw_bottom_bar(surface, game_state, fonts):
    """绘制底部操作提示栏。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    bottom_y = TOP_BAR_H + VIEW_H + STATUS_BAR_H
    pygame.draw.rect(surface, C_PANEL_DARK, (LEFT_BAR_W, bottom_y, VIEW_W, BOTTOM_BAR_H))
    register_ui_area(game_state, (LEFT_BAR_W, bottom_y, VIEW_W, BOTTOM_BAR_H), '区域：底部操作提示栏', 'draw_bottom_bar：按键说明、战斗说明、自动目标')
    draw_text(surface, CONTROL_HINT, fonts['small'], C_CREAM, LEFT_BAR_W + 10, bottom_y + 10)
    draw_text(surface, BATTLE_HINT, fonts['small'], C_WHITE, LEFT_BAR_W + 10, bottom_y + 36)
    goal = current_auto_goal(game_state)
    goal_text = f'自动目标：{goal["description"]}'
    goal_lines = wrap_text(goal_text, fonts['small'], VIEW_W - 20)
    if goal_lines:
        goal_line = goal_lines[0]
        draw_text(surface, goal_line, fonts['small'], C_YELLOW, LEFT_BAR_W + 10, bottom_y + 62)
    record_text = f'标题跳幕：普通默认{NORMAL_START_SKIP_ACTS_DEFAULT}｜自动默认{AUTO_PLAY_SKIP_ACTS_DEFAULT}｜录制默认{RECORD_SKIP_ACTS_DEFAULT}｜卧底：维克托'
    draw_text(surface, record_text, fonts['tiny'], (190, 210, 185), LEFT_BAR_W + 10, bottom_y + 84)


def draw_minimap(surface, game_state, fonts):
    """绘制小地图。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    scene = game_state['scene']
    player = game_state['player']
    mini_x = LEFT_BAR_W + VIEW_W - 156
    mini_y = TOP_BAR_H + 12
    cell = 6
    minimap_rect = (mini_x - 8, mini_y - 8, VIEW_COLS * cell + 16, VIEW_ROWS * cell + 72)
    pygame.draw.rect(surface, (10, 9, 14), minimap_rect)
    pygame.draw.rect(surface, C_CREAM, minimap_rect, 1)
    register_ui_area(game_state, minimap_rect, '区域：小地图', 'draw_minimap：按当前 MAPS 场景缩小绘制')
    current_map = MAPS[scene]
    for tile_y, row in enumerate(current_map):
        for tile_x, tile in enumerate(row):
            if tile in BLOCKING_TILES:
                color = (45, 54, 45)
            elif tile == 'D':
                color = C_YELLOW
            else:
                color = (126, 118, 86)
            cell_x = mini_x + tile_x * cell
            cell_y = mini_y + tile_y * cell
            pygame.draw.rect(surface, color, (cell_x, cell_y, cell, cell))
    player_x = mini_x + player['x'] * cell
    player_y = mini_y + player['y'] * cell
    pygame.draw.rect(surface, C_RED, (player_x, player_y, cell, cell))
    draw_text(surface, '小地图 / 门见右栏', fonts['tiny'], C_CREAM, mini_x, mini_y + VIEW_ROWS * cell + 4)


def draw_world(surface, app_state):
    """绘制探索世界和固定 UI。

    固定 UI 的绘制顺序体现区域独立：先画顶端菜单和侧栏，再画地图世界，最后补中央顶栏、状态栏和底部提示栏。
    这种顺序可以保证地图不会覆盖 UI，面板也能在世界之上另行绘制。

    :param surface: 目标画布。
    :param app_state: 应用状态字典。
    """
    game_state = app_state['game_state']
    fonts = app_state['fonts']
    surface.fill(C_BLACK)
    draw_menu_bar(surface, game_state, fonts)
    draw_side_bars(surface, game_state, fonts)
    draw_tile_map(surface, game_state)
    draw_particles(surface, app_state)
    draw_items(surface, game_state)
    draw_time_overlay(surface, game_state)
    draw_npcs(surface, game_state, fonts)
    draw_route_hint(surface, game_state)
    draw_player(surface, game_state)
    draw_top_bar(surface, game_state, fonts)
    draw_status_bar(surface, game_state, fonts)
    draw_bottom_bar(surface, game_state, fonts)
    settings = game_state['settings']
    if settings['show_minimap']:
        draw_minimap(surface, game_state, fonts)


def draw_title(surface, app_state):
    """绘制标题界面。

    :param surface: 目标画布。
    :param app_state: 应用状态字典。
    """
    game_state = app_state['game_state']
    fonts = app_state['fonts']
    tick = game_state['tick']
    surface.fill((25, 22, 31))
    register_ui_area(game_state, (0, 0, VW, VH), '区域：标题界面', 'draw_title / start_game_from_title / START_ACT_OPTIONS')
    for star in app_state['title_stars']:
        star_x, star_y, star_index = star
        if (tick // 20 + star_index) % 4 != 0:
            surface.set_at((star_x, star_y), (210, 210, 180))
    pygame.draw.rect(surface, (234, 219, 147), (VW - 160, 48, 42, 42))
    pygame.draw.rect(surface, (25, 22, 31), (VW - 176, 44, 24, 48))
    for tree_x in range(0, VW, 32):
        tree_h = 60 + (tree_x * 7) % 90
        top_y = VH - 68 - tree_h
        pygame.draw.polygon(surface, (25, 63, 45), [(tree_x, VH - 68), (tree_x + 16, top_y), (tree_x + 32, VH - 68)])
        pygame.draw.rect(surface, (35, 45, 35), (tree_x + 14, VH - 76, 5, 42))
    hero_key = game_state['hero_key']
    draw_sprite_hero(surface, VW // 2 - 16, 300, True, hero_key)
    draw_center_text(surface, '露比｜小红帽', fonts['title'], C_RED, 72)
    draw_center_text(surface, '酒店密谋与火柴盒监狱 RPG 豪华版', fonts['big'], C_CREAM, 126)
    draw_center_text(surface, '本版重点：艾琳卧底改为男性俊美青年维克托，密语酒店加入多位 NPC', fonts['normal'], C_WHITE, 174)
    draw_center_text(surface, '函数式绘制 × 五级重要性 × 自动游玩 × 录制 × Fountain 剧本导出 × 多视角主角 × Tooltip 定位', fonts['normal'], (210, 210, 190), 212)
    hero_name = current_hero_name(game_state)
    hero_desc = current_hero_desc(game_state)
    hero_line = f'当前形象：{hero_name}｜{hero_desc}'
    draw_center_text(surface, hero_line, fonts['normal'], C_YELLOW, 366)
    skip_acts = game_state['title_skip_acts']
    act_spec = START_ACT_OPTIONS[skip_acts]
    act_title = act_spec['title']
    act_note = act_spec['note']
    act_line = f'起始选择：跳过 {skip_acts} 幕｜{act_title}'
    draw_center_text(surface, act_line, fonts['normal'], C_CREAM, 408)
    draw_center_text(surface, act_note, fonts['small'], C_YELLOW, 436)
    draw_center_text(surface, f'默认：普通 {NORMAL_START_SKIP_ACTS_DEFAULT} 幕｜自动 {AUTO_PLAY_SKIP_ACTS_DEFAULT} 幕｜录制 {RECORD_SKIP_ACTS_DEFAULT} 幕', fonts['small'], (205, 205, 185), 462)
    start_rect = (VW // 2 - 90, 500, 180, 34)
    prev_rect = (VW // 2 - 256, 500, 112, 34)
    next_rect = (VW // 2 + 144, 500, 112, 34)
    act_prev_rect = (VW // 2 - 256, 548, 112, 34)
    act_next_rect = (VW // 2 + 144, 548, 112, 34)
    draw_button(surface, game_state, start_rect, '开始冒险', 'start_title', fonts['normal'], True, '区域：标题按钮 开始冒险')
    draw_button(surface, game_state, prev_rect, '上个形象', 'hero_prev', fonts['small'], True, '区域：标题按钮 上个形象')
    draw_button(surface, game_state, next_rect, '下个形象', 'hero_next', fonts['small'], True, '区域：标题按钮 下个形象')
    draw_button(surface, game_state, act_prev_rect, '上个起始幕', 'title_act_prev', fonts['small'], True, '区域：标题按钮 上个起始幕')
    draw_button(surface, game_state, act_next_rect, '下个起始幕', 'title_act_next', fonts['small'], True, '区域：标题按钮 下个起始幕')
    draw_center_text(surface, '←/→ 切换形象；PageUp/PageDown 或按钮选择起始幕；Enter / Space 开始；O 自动游玩', fonts['normal'], C_WHITE, 604)
    draw_center_text(surface, CONTROL_HINT, fonts['small'], (205, 205, 185), 634)


def draw_portrait_dialogue(surface, game_state, fonts):
    """绘制对白期间的大立绘。

    对话框上方展示说话人立绘，旁白不需要立绘。
    本版不再复用像素小人，而是使用独立的大立绘几何绘制函数，保证“小人”和“立绘大图”视觉上不一样。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    dialogue = game_state['dialogue']
    entries = dialogue['entries']
    entry = entries[dialogue['index']]
    portrait_role = entry[2]
    side = entry[3]
    if portrait_role != 'narrator':
        if side == 'left':
            x = LEFT_BAR_W + 44
        else:
            x = LEFT_BAR_W + VIEW_W - 244
        y = TOP_BAR_H + 72
        portrait_rect = (x, y, 196, 242)
        pygame.draw.rect(surface, (16, 14, 20), portrait_rect)
        pygame.draw.rect(surface, C_CREAM, portrait_rect, 2)
        draw_large_portrait_by_role(surface, game_state, portrait_rect, portrait_role)
        draw_center_in_rect(surface, f'大立绘：{portrait_role}', fonts['small'], C_YELLOW, (x + 10, y + 208, 176, 24))
        tooltip = f'区域：对白大立绘 {portrait_role}｜独立绘制，不复用像素小人'
        register_ui_area(game_state, portrait_rect, tooltip, 'draw_portrait_dialogue / draw_large_portrait_by_role')


def draw_dialogue(surface, game_state, fonts):
    """绘制对白框。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    dialogue = game_state['dialogue']
    entries = dialogue['entries']
    entry = entries[dialogue['index']]
    speaker_key = entry[0]
    text = entry[1]
    speaker_name, speaker_title = speaker_name_and_title(speaker_key)
    box_h = 156
    y = VH - box_h - 12
    box_rect = (LEFT_BAR_W + 12, y, VIEW_W - 24, box_h)
    pygame.draw.rect(surface, (16, 14, 20), box_rect)
    pygame.draw.rect(surface, C_CREAM, box_rect, 2)
    register_ui_area(game_state, box_rect, f'区域：对白框｜说话人：{speaker_name}', 'draw_dialogue / STORY_ACTION_SPECS / advance_dialogue')
    speaker_w = fonts['normal'].size(speaker_name)[0] + 28
    title_w = 0
    if speaker_title != '':
        title_w = fonts['tiny'].size(speaker_title)[0] + 18
    label_w = max(92, speaker_w + title_w)
    label_rect = (LEFT_BAR_W + 24, y - 22, label_w, 28)
    pygame.draw.rect(surface, (55, 35, 42), label_rect)
    pygame.draw.rect(surface, C_CREAM, label_rect, 2)
    draw_text(surface, speaker_name, fonts['normal'], C_CREAM, LEFT_BAR_W + 36, y - 18)
    if speaker_title != '':
        title_x = LEFT_BAR_W + 44 + fonts['normal'].size(speaker_name)[0]
        draw_text(surface, speaker_title, fonts['tiny'], C_YELLOW, title_x, y - 13)
    lines = wrap_text(text, fonts['normal'], VIEW_W - 64)
    line_count = 0
    for line in lines:
        if line_count < 5:
            line_y = y + 24 + line_count * 26
            draw_text(surface, line, fonts['normal'], C_WHITE, LEFT_BAR_W + 30, line_y)
            line_count += 1
    tick = game_state['tick']
    if (tick // 20) % 2 == 0:
        blink = '▼'
    else:
        blink = ''
    draw_text(surface, blink, fonts['big'], C_YELLOW, LEFT_BAR_W + VIEW_W - 46, y + box_h - 40)
    next_rect = (LEFT_BAR_W + VIEW_W - 146, y + box_h - 44, 90, 28)
    draw_button(surface, game_state, next_rect, '继续', 'dialogue_next', fonts['small'], True, '区域：对白继续按钮')


def draw_panel_shell(surface, game_state, title, subtitle, fonts, rect, source_hint):
    """绘制通用面板外壳。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param title: 面板标题。
    :param subtitle: 面板副标题。
    :param fonts: 字体字典。
    :param rect: 面板矩形。
    :param source_hint: 代码定位提示。
    """
    pygame.draw.rect(surface, (12, 10, 16), rect)
    pygame.draw.rect(surface, C_CREAM, rect, 2)
    register_ui_area(game_state, rect, f'区域：面板 {title}', source_hint)
    title_y = rect[1] + 20
    subtitle_y = rect[1] + 56
    draw_center_text(surface, title, fonts['big'], C_CREAM, title_y)
    draw_center_text(surface, subtitle, fonts['small'], C_YELLOW, subtitle_y)


def draw_journal_panel(surface, game_state, fonts):
    """绘制森林札记。

    humanize.precisedelta 是第三方可读化格式库，在这里把旅程估算转为可读文本。
    面试考点：业务状态用数字保存，展示层再格式化，不要把展示格式写回状态。
    推荐书：英文 Fluent Python；中文《流畅的 Python》中文版。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    flags = game_state['flags']
    rect = (36, 36, VW - 72, VH - 72)
    subtitle = f'{SCROLL_HINT}｜按 J / Enter / Space / Esc / P 合上'
    draw_panel_shell(surface, game_state, '森林札记与任务', subtitle, fonts, rect, 'draw_journal_panel / quest_entries / story_log')
    scroll = game_state['scroll_offsets']['journal']
    y = 112 - scroll
    x = 58
    content_lines = [main_story_progress(game_state), '当前路线：', current_route_text(game_state), '任务清单：']
    for line in content_lines:
        wrapped = wrap_text(line, fonts['normal'], VW - 120)
        for wrapped_line in wrapped:
            if 106 < y < VH - 36:
                draw_text(surface, wrapped_line, fonts['normal'], C_YELLOW, x, y)
            y += 28
    quests = quest_entries(game_state)
    for quest in quests:
        status, title, detail = quest
        quest_line = f'[{status}] {title}：{detail}'
        quest_lines = wrap_text(quest_line, fonts['small'], VW - 140)
        for line in quest_lines:
            if 106 < y < VH - 36:
                draw_text(surface, f'· {line}', fonts['small'], C_WHITE, x + 12, y)
            y += 22
    y += 16
    if 106 < y < VH - 36:
        draw_text(surface, '旅途记录：', fonts['normal'], C_CREAM, x, y)
    y += 28
    for story in game_state['story_log']:
        lines = wrap_text(story, fonts['small'], VW - 140)
        for line in lines:
            if 106 < y < VH - 36:
                draw_text(surface, f'· {line}', fonts['small'], C_WHITE, x + 12, y)
            y += 22
    y += 16
    journey_minutes = 20 + flags['steps_taken'] // 2
    journey_span = timedelta(minutes=journey_minutes)
    journey_text = precisedelta(journey_span, minimum_unit='minutes')
    stats = [
        f'旅程估算：{journey_text}；善意值 {flags["kindness"]}；已访问地图 {len(game_state["visited_scenes"])}/{len(SCENE_ORDER)}。',
        f'当前主视角：{current_view_actor_name(game_state)}；火柴盒救援：{"完成" if flags["prisoners_released"] else "未完成"}。',
        '面试提示：NetworkX 可讲图搜索，ImageIO 可讲自动录制，NumPy 可讲图像张量维度和音频采样，Pillow 可讲发布图生成。',
        '火柴盒监狱提示：艾琳和维克托不知道抽拉结构；露比和莱昂知道，所以外侧空囚室并不代表里面没人。',
        '推荐书：中文《游戏编程模式》；英文 Game Programming Patterns、The Algorithm Design Manual。',
    ]
    for stat in stats:
        stat_lines = wrap_text(stat, fonts['small'], VW - 120)
        for stat_line in stat_lines:
            if 106 < y < VH - 36:
                draw_text(surface, stat_line, fonts['small'], C_YELLOW, x, y)
            y += 22
    close_rect = (VW - 126, 48, 82, 26)
    draw_button(surface, game_state, close_rect, '关闭', 'close_panel', fonts['small'], True, '区域：面板关闭按钮')


def draw_inventory_panel(surface, game_state, fonts):
    """绘制背包界面。

    more_itertools.chunked 用来把背包键分成三列，减少手写索引和边界错误。
    面试考点：chunked 属于第三方迭代工具，能让批量布局更清晰。
    推荐书：英文 Fluent Python；中文《流畅的 Python》中文版。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    inventory = game_state['inventory']
    rect = (48, 46, VW - 96, VH - 92)
    subtitle = f'{SCROLL_HINT}｜按 I / Enter / Space / Esc / P 合上'
    draw_panel_shell(surface, game_state, '红斗篷的背包', subtitle, fonts, rect, 'draw_inventory_panel / INVENTORY_KEYS / more_itertools.chunked')
    scroll = game_state['scroll_offsets']['inventory']
    rows = list(chunked(INVENTORY_KEYS, 3))
    y = 134 - scroll
    for row in rows:
        x = 76
        for inventory_key in row:
            count = inventory[inventory_key]
            count_text = f'{inventory_key} × {count}'
            item_rect = (x - 6, y - 5, 300, 30)
            if 110 < y < VH - 80:
                pygame.draw.rect(surface, (28, 24, 34), item_rect)
                pygame.draw.rect(surface, (70, 58, 75), item_rect, 1)
                draw_text(surface, count_text, fonts['small'], C_WHITE, x, y)
                register_ui_area(game_state, item_rect, f'区域：背包条目 {inventory_key}', 'draw_inventory_panel / inventory')
            x += 328
        y += 42
    tip_lines = ['背包显示资源，剧情标记仍由 flags 统一管理。', '面试讲解点：UI 状态与探索状态分离，可以避免输入互相干扰。']
    for tip in tip_lines:
        wrapped = wrap_text(tip, fonts['small'], VW - 120)
        for line in wrapped:
            if 110 < y < VH - 40:
                draw_text(surface, line, fonts['small'], C_CREAM, 76, y)
            y += 24
    close_rect = (VW - 136, 58, 82, 26)
    draw_button(surface, game_state, close_rect, '关闭', 'close_panel', fonts['small'], True, '区域：面板关闭按钮')


def draw_simple_text_panel(surface, game_state, fonts, ui_state, title, lines):
    """绘制通用长文本面板。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    :param ui_state: 当前面板状态。
    :param title: 面板标题。
    :param lines: 面板文本行列表。
    """
    rect = (56, 48, VW - 112, VH - 96)
    subtitle = f'{SCROLL_HINT}｜Enter / Space / Esc / P 合上'
    source_hint = f'draw_simple_text_panel / ui_state={ui_state}'
    draw_panel_shell(surface, game_state, title, subtitle, fonts, rect, source_hint)
    scroll = game_state['scroll_offsets'][ui_state]
    y = 132 - scroll
    for line in lines:
        wrapped = wrap_text(line, fonts['normal'], VW - 180)
        for wrapped_line in wrapped:
            if 112 < y < VH - 48:
                draw_text(surface, wrapped_line, fonts['normal'], C_WHITE, 86, y)
            y += 30
        y += 8
    close_rect = (VW - 146, 60, 82, 26)
    draw_button(surface, game_state, close_rect, '关闭', 'close_panel', fonts['small'], True, '区域：面板关闭按钮')


def draw_world_map_panel(surface, game_state, fonts):
    """绘制完整世界地图与场景关系。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    rect = (42, 42, VW - 84, VH - 84)
    subtitle = f'{SCROLL_HINT}｜展示所有启用场景及相互之间的传送关系'
    draw_panel_shell(surface, game_state, '森林世界地图', subtitle, fonts, rect, 'draw_world_map_panel / SCENE_GRAPH / PORTAL_BLUEPRINTS')
    positions = {
        'home': (120, 150),
        'village': (288, 150),
        'forest': (456, 150),
        'cottage': (624, 150),
        'cage_yard': (624, 282),
        'winter_street': (624, 414),
        'whisper_hotel': (456, 414),
        'matchbox_prison': (288, 414),
        'match_market': (120, 414),
        'royal_square': (120, 282),
    }
    scene = game_state['scene']
    target_scene = current_target_scene(game_state)
    route = nx.shortest_path(SCENE_GRAPH, scene, target_scene)
    for edge in SCENE_GRAPH.edges:
        left_scene, right_scene = edge
        if left_scene in positions and right_scene in positions:
            left_x, left_y = positions[left_scene]
            right_x, right_y = positions[right_scene]
            pygame.draw.line(surface, (115, 105, 86), (left_x, left_y), (right_x, right_y), 3)
    for scene_key in SCENE_ORDER:
        if scene_enabled(scene_key):
            node_x, node_y = positions[scene_key]
            if scene_key == scene:
                node_color = C_RED
            elif scene_key in route:
                node_color = C_YELLOW
            elif scene_key in game_state['visited_scenes']:
                node_color = C_CREAM
            else:
                node_color = C_DARK_GRAY
            pygame.draw.circle(surface, node_color, (node_x, node_y), 22)
            pygame.draw.circle(surface, C_BLACK, (node_x, node_y), 22, 2)
            scene_name = SCENE_NAMES[scene_key]
            draw_text(surface, scene_name, fonts['small'], C_WHITE, node_x - 56, node_y + 28)
            node_rect = (node_x - 24, node_y - 24, 48, 48)
            register_ui_area(game_state, node_rect, f'区域：世界地图节点 {scene_name}', 'draw_world_map_panel / positions / SCENE_GRAPH')
    scroll = game_state['scroll_offsets']['map']
    guide_y = 500 - scroll
    time_key = game_state['time_of_day']
    time_name = TIME_OF_DAY_SPECS[time_key]['name']
    guide_lines = [
        f'当前位置：{SCENE_NAMES[scene]}',
        f'当前时段：{time_name}',
        f'目标地点：{SCENE_NAMES[target_scene]}',
        f'推荐路线：{current_route_text(game_state)}',
        f'当前主视角：{current_view_actor_name(game_state)}',
        '火柴盒监狱：艾琳和维克托不知道抽拉结构，露比和莱昂知道。',
        '当前地图每个单格门：',
    ]
    portal_lines = current_scene_portal_lines(game_state)
    guide_lines.extend(portal_lines)
    for guide_line in guide_lines:
        wrapped_lines = wrap_text(guide_line, fonts['small'], VW - 120)
        for wrapped_line in wrapped_lines:
            if 112 < guide_y < VH - 50:
                draw_text(surface, wrapped_line, fonts['small'], C_WHITE, 70, guide_y)
            guide_y += 24
    close_rect = (VW - 136, 54, 82, 26)
    draw_button(surface, game_state, close_rect, '关闭', 'close_panel', fonts['small'], True, '区域：面板关闭按钮')


def draw_pause_panel(surface, game_state, fonts):
    """绘制暂停菜单。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    lines = [
        'J 打开森林札记：查看主线、支线、旅途记录和完成度。',
        'I 打开背包：查看所有资源和关键道具。',
        'M 打开世界地图：查看所有启用场景、传送关系、当前位置、目标地点和推荐路线。',
        'L 打开图鉴：查看已认识的角色、道具、线索、语言风格和人物小传。',
        '本版新增：艾琳卧底改为男性俊美青年维克托，密语酒店中有掌柜、侦察员、药师、领袖与卧底多位 NPC。',
        '顶部“提示”按钮用于开关 tooltip。tooltip 默认关闭；开启后，鼠标移动到任意区域会显示区域名称和代码定位。',
        'RUN_MODE 可设为 normal、storyline、original_story、fountain、record 或 publish_info。',
        'publish_info 会打印上架页面必填字段、建议填写值、候选项、PyInstaller 单文件 Pygame 打包说明，并生成图标与封面。',
        '火柴盒监狱段落会依次切换主视角：露比被关后切到艾琳，艾琳扔钥匙后切到莱昂，救出众人后切回露比。',
        '重要设定：艾琳不知道自己的监狱是火柴盒抽拉结构；男卧底维克托也不知道；露比和莱昂知道，并利用这个信息差逃脱。',
        '面试推荐书：中文《游戏编程模式》《算法图解》；英文 Game Programming Patterns、The Algorithm Design Manual。',
    ]
    draw_simple_text_panel(surface, game_state, fonts, 'pause', '暂停', lines)


def draw_codex_panel(surface, game_state, fonts):
    """绘制森林图鉴。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    entries = []
    for entry_name in game_state['codex']:
        entries.append(entry_name)
    for profile_key, profile in CHARACTER_PROFILES.items():
        profile_display = profile_display_text(profile_key)
        if profile_display in game_state['codex']:
            pixel_role = profile['pixel_role']
            portrait_role = profile['portrait_role']
            language_style = profile['language_style']
            bio = profile['bio']
            personality = profile['personality']
            profile_line = f'{profile_display}｜像素小人：{pixel_role}｜立绘：{portrait_role}｜语言风格：{language_style}｜小传：{bio}｜性格：{personality}'
            entries.append(profile_line)
    for scene_key in SCENE_ORDER:
        scene_meta = SCENE_META[scene_key]
        scene_name = scene_meta['name']
        if scene_key in game_state['visited_scenes']:
            time_key = scene_meta['default_time_key']
            time_name = TIME_OF_DAY_SPECS[time_key]['name']
            intro = f'{scene_name}｜内外景：{scene_meta["location_type"]}｜默认时间：{time_name}｜重要性：{scene_meta["importance"]}｜意图：{scene_meta["intent"]}'
            entries.append(intro)
    if 'matchbox_prison' in game_state['visited_scenes']:
        entries.append(f'火柴盒监狱结构秘密｜{MATCHBOX_PRISON_SECRET_TEXT}')
    entries.sort()
    lines = []
    for entry in entries:
        lines.append(f'· {entry}')
    lines.append('TODO：可继续扩展为敌人弱点、角色关系图、已读对白和 Fountain 分镜编号。')
    draw_simple_text_panel(surface, game_state, fonts, 'codex', '森林图鉴', lines)


def draw_shop_panel(surface, game_state, fonts):
    """绘制市场商店界面。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    inventory = game_state['inventory']
    rect = (80, 52, VW - 160, VH - 104)
    subtitle = '数字键或按钮买入卖出，Esc / P / Enter / Space 离开；自动游玩不会打开商店'
    draw_panel_shell(surface, game_state, '村口市场', subtitle, fonts, rect, 'draw_shop_panel / SHOP_BUY_CATALOG / SHOP_SELL_CATALOG')
    coin_line = f'当前铜币：{inventory["铜币"]}'
    draw_center_text(surface, coin_line, fonts['normal'], C_YELLOW, 134)
    scroll = game_state['scroll_offsets']['shop']
    y = 184 - scroll
    draw_text(surface, '买入', fonts['big'], C_CREAM, 120, y)
    y += 38
    for shop_entry in SHOP_BUY_CATALOG:
        hotkey = shop_entry['hotkey']
        name = shop_entry['name']
        price = shop_entry['price']
        intent = shop_entry['intent']
        line = f'{hotkey}｜{name}｜价格 {price} 铜币｜{intent}'
        if 118 < y < VH - 92:
            draw_text(surface, line, fonts['normal'], C_WHITE, 130, y)
            action = f'buy_{hotkey}'
            button_rect = (VW - 250, y - 2, 100, 26)
            draw_button(surface, game_state, button_rect, f'买 {hotkey}', action, fonts['small'], True, f'区域：商店买入按钮 {name}')
        y += 34
    y += 18
    if 118 < y < VH - 92:
        draw_text(surface, '卖出', fonts['big'], C_CREAM, 120, y)
    y += 38
    for shop_entry in SHOP_SELL_CATALOG:
        hotkey = shop_entry['hotkey']
        name = shop_entry['name']
        price = shop_entry['price']
        inventory_key = shop_entry['inventory_key']
        count = inventory[inventory_key]
        line = f'{hotkey}｜{name}｜卖价 {price} 铜币｜当前 {count}'
        if 118 < y < VH - 92:
            draw_text(surface, line, fonts['normal'], C_WHITE, 130, y)
            action = f'sell_{hotkey}'
            button_rect = (VW - 250, y - 2, 100, 26)
            draw_button(surface, game_state, button_rect, f'卖 {hotkey}', action, fonts['small'], True, f'区域：商店卖出按钮 {name}')
        y += 34
    leave_rect = (VW - 178, 64, 82, 26)
    draw_button(surface, game_state, leave_rect, '离开', 'close_panel', fonts['small'], True, '区域：商店离开按钮')


def draw_battle_bar(surface, fonts, x, y, name, hp, max_hp, color):
    """绘制战斗生命条。

    :param surface: 目标画布。
    :param fonts: 字体字典。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    :param name: 角色名称。
    :param hp: 当前生命值。
    :param max_hp: 最大生命值。
    :param color: 生命条颜色。
    """
    draw_text(surface, name, fonts['normal'], C_WHITE, x, y)
    pygame.draw.rect(surface, C_BLACK, (x, y + 32, 192, 18))
    fill = int(184 * hp / max_hp)
    pygame.draw.rect(surface, color, (x + 4, y + 36, fill, 10))
    pygame.draw.rect(surface, C_CREAM, (x, y + 32, 192, 18), 2)
    hp_text = f'{hp}/{max_hp}'
    draw_text(surface, hp_text, fonts['small'], C_WHITE, x, y + 58)


def draw_big_wolf(surface, x, y):
    """绘制战斗中的大型灰狼。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    pygame.draw.ellipse(surface, (20, 18, 22), (x + 12, y + 84, 108, 14))
    pygame.draw.polygon(surface, C_GRAY, [(x + 16, y + 36), (x + 36, y), (x + 56, y + 46)])
    pygame.draw.polygon(surface, C_GRAY, [(x + 84, y + 36), (x + 104, y), (x + 116, y + 48)])
    pygame.draw.rect(surface, C_GRAY, (x + 20, y + 32, 96, 68))
    pygame.draw.rect(surface, C_DARK_GRAY, (x + 8, y + 60, 108, 36))
    pygame.draw.rect(surface, C_YELLOW, (x + 40, y + 50, 14, 6))
    pygame.draw.rect(surface, C_YELLOW, (x + 84, y + 50, 14, 6))
    pygame.draw.rect(surface, C_WHITE, (x + 72, y + 78, 8, 18))
    pygame.draw.rect(surface, C_WHITE, (x + 92, y + 78, 8, 18))


def draw_big_aileen(surface, x, y):
    """绘制战斗中的艾琳。

    :param surface: 目标画布。
    :param x: 像素横坐标。
    :param y: 像素纵坐标。
    """
    pygame.draw.ellipse(surface, (20, 18, 22), (x + 12, y + 96, 100, 14))
    pygame.draw.rect(surface, (45, 72, 130), (x + 38, y + 42, 54, 72))
    pygame.draw.rect(surface, (230, 210, 120), (x + 32, y + 20, 66, 24))
    pygame.draw.rect(surface, C_SKIN, (x + 44, y + 28, 42, 34))
    pygame.draw.rect(surface, C_BLACK, (x + 54, y + 42, 4, 4))
    pygame.draw.rect(surface, C_BLACK, (x + 76, y + 42, 4, 4))
    pygame.draw.circle(surface, (90, 170, 255), (x + 108, y + 64), 14)


def draw_battle_panel(surface, game_state, fonts):
    """绘制战斗界面。

    战斗界面把文字日志区和按钮操作区分成两个独立矩形，按钮不再放在日志框内部。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    battle = game_state['battle']
    surface.fill((30, 25, 35))
    register_ui_area(game_state, (0, 0, VW, VH), '区域：战斗界面', 'draw_battle_panel / battle_player_* / battle_enemy_attack')
    for tile_y in range(0, VH, 32):
        for tile_x in range(0, VW, 32):
            if (tile_x // 32 + tile_y // 32) % 2 == 0:
                floor_color = (48, 39, 48)
            else:
                floor_color = (43, 34, 43)
            pygame.draw.rect(surface, floor_color, (tile_x, tile_y, 32, 32))
    tick = game_state['tick']
    little_red_step = (tick // 16) % 2 == 0
    hero_key = game_state['hero_key']
    draw_sprite_hero(surface, 240, 276, little_red_step, hero_key)
    if battle is not None:
        if battle['battle_key'] == 'gray_wolf':
            draw_big_wolf(surface, VW - 335, 220)
        else:
            draw_big_aileen(surface, VW - 335, 210)
    player = game_state['player']
    draw_battle_bar(surface, fonts, 56, 52, '露比｜小红帽', player['hp'], player['max_hp'], C_RED)
    if battle is not None:
        enemy_hp = battle['enemy_hp']
        enemy_max_hp = battle['enemy_max_hp']
        draw_battle_bar(surface, fonts, VW - 420, 52, battle['enemy_name'], enemy_hp, enemy_max_hp, C_GRAY)
        stage_text = f'阶段：{battle["stage"]}｜回合：{battle["round"]}'
        draw_center_text(surface, stage_text, fonts['normal'], C_YELLOW, 32)
    log_rect = (30, VH - 238, VW - 60, 130)
    action_rect = (30, VH - 96, VW - 60, 70)
    pygame.draw.rect(surface, (16, 14, 20), log_rect)
    pygame.draw.rect(surface, C_CREAM, log_rect, 2)
    pygame.draw.rect(surface, (20, 18, 24), action_rect)
    pygame.draw.rect(surface, C_BUTTON_LINE, action_rect, 2)
    register_ui_area(game_state, log_rect, '区域：战斗日志', 'draw_battle_panel / battle_add_log')
    register_ui_area(game_state, action_rect, '区域：战斗操作按钮区', 'draw_battle_panel / BATTLE_ACTION_BY_KEY')
    if battle is not None:
        log_index = 0
        for line in battle['log']:
            line_y = VH - 224 + log_index * 20
            draw_text(surface, line, fonts['small'], C_WHITE, 48, line_y)
            log_index += 1
        help_text = f'A攻击 H蜂蜜({battle["heals"]}) D防御 B银铃 Q三问 F油灯 K清醒卡 S防烟布 W木哨'
        draw_text(surface, help_text, fonts['small'], C_YELLOW, 48, VH - 88)
        button_specs = [
            ('攻击', 'battle_attack'),
            ('蜂蜜', 'battle_heal'),
            ('防御', 'battle_defend'),
            ('银铃', 'battle_bell'),
            ('三问', 'battle_question'),
            ('油灯', 'battle_lamp'),
            ('清醒卡', 'battle_card'),
            ('防烟布', 'battle_cloth'),
            ('木哨', 'battle_whistle'),
        ]
        button_x = 48
        button_y = VH - 60
        for label, action in button_specs:
            rect = (button_x, button_y, 74, 28)
            draw_button(surface, game_state, rect, label, action, fonts['small'], True, f'区域：战斗按钮 {label}')
            button_x += 82


def draw_judgement_panel(surface, game_state, fonts):
    """绘制灰狼处置界面。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    panel_rect = (92, 72, VW - 184, VH - 144)
    pygame.draw.rect(surface, (12, 10, 16), panel_rect)
    pygame.draw.rect(surface, C_GOLD, panel_rect, 2)
    register_ui_area(game_state, panel_rect, '区域：灰狼处置面板', 'draw_judgement_panel / apply_wolf_judgement')
    draw_center_text(surface, '如何处置灰狼格雷姆？', fonts['title'], C_CREAM, 106)
    lines = [
        '最终战中，露比从劣势中反击灰狼。现在灰狼倒在外婆的小屋门口。',
        '村民害怕它再次模仿亲人的声音，也害怕一时愤怒让自己变得和灰狼一样残忍。',
        '1｜囚禁灰狼并听他求饶：把灰狼关进铁栅栏，避免它继续伤害村民。',
        '2｜放逐灰狼：让猎人把灰狼赶到远山，同时继续巡逻边界。',
        JUDGEMENT_HINT,
    ]
    y = 178
    for line in lines:
        wrapped = wrap_text(line, fonts['normal'], VW - 260)
        for wrapped_line in wrapped:
            draw_text(surface, wrapped_line, fonts['normal'], C_WHITE, 130, y)
            y += 34
    cage_rect = (VW // 2 - 180, VH - 138, 150, 34)
    exile_rect = (VW // 2 + 30, VH - 138, 150, 34)
    draw_button(surface, game_state, cage_rect, '1 囚禁灰狼', 'judge_cage', fonts['normal'], True, '区域：处置按钮 囚禁灰狼')
    draw_button(surface, game_state, exile_rect, '2 放逐灰狼', 'judge_exile', fonts['normal'], True, '区域：处置按钮 放逐灰狼')
    draw_center_text(surface, '推荐：选择 1，完成“灰狼不再伤人”的主线处置。', fonts['normal'], C_YELLOW, VH - 90)


def draw_ending_panel(surface, game_state, fonts):
    """绘制结局界面。

    :param surface: 目标画布。
    :param game_state: 游戏状态字典。
    :param fonts: 字体字典。
    """
    flags = game_state['flags']
    surface.fill((20, 24, 32))
    register_ui_area(game_state, (0, 0, VW, VH), '区域：结局 CG', 'draw_ending_panel / ending_name / ending_lines')
    pygame.draw.rect(surface, (237, 188, 118), (0, 0, VW, 180))
    pygame.draw.rect(surface, (97, 154, 99), (0, 180, VW, VH - 180))
    for tree_x in range(0, VW, 40):
        tree_top = 120 + (tree_x % 60)
        pygame.draw.polygon(surface, (38, 95, 60), [(tree_x, 260), (tree_x + 20, tree_top), (tree_x + 40, 260)])
        pygame.draw.rect(surface, (78, 55, 34), (tree_x + 18, 220, 6, 90))
    pygame.draw.rect(surface, (126, 79, 47), (VW - 300, 270, 128, 100))
    pygame.draw.polygon(surface, (147, 56, 49), [(VW - 312, 270), (VW - 236, 196), (VW - 160, 270)])
    hero_key = game_state['hero_key']
    draw_sprite_hero(surface, 250, 390, True, hero_key)
    draw_sprite_npc_by_role(surface, 320, 390, 'hunter')
    draw_sprite_npc_by_role(surface, 390, 390, 'blond_friend')
    draw_sprite_npc_by_role(surface, 460, 390, 'chief')
    draw_sprite_npc_by_role(surface, 530, 390, 'king')
    draw_sprite_npc_by_role(surface, 600, 390, 'spy')
    if flags['wolf_caged']:
        pygame.draw.rect(surface, C_DARK_GRAY, (660, 372, 96, 72))
        for bar_x in (672, 694, 716, 738):
            pygame.draw.rect(surface, C_SILVER, (bar_x, 374, 4, 68))
        draw_sprite_wolf(surface, 696, 398)
    if flags['aileen_found_dead']:
        pygame.draw.circle(surface, (90, 170, 255), (805, 410), 18)
        pygame.draw.rect(surface, (25, 30, 40), (797, 410, 16, 46))
        for match_x in (881, 891, 901, 911):
            pygame.draw.rect(surface, C_DARK_BROWN, (match_x, 434, 14, 3))
            pygame.draw.circle(surface, (90, 170, 255), (match_x + 15, 435), 3)
    pygame.draw.rect(surface, (16, 14, 20), (64, 36, VW - 128, 230))
    pygame.draw.rect(surface, C_CREAM, (64, 36, VW - 128, 230), 2)
    ending_title = ending_name(game_state)
    draw_center_text(surface, ending_title, fonts['big'], C_CREAM, 66)
    lines = ending_lines(game_state)
    line_y = 116
    for line in lines:
        draw_center_text(surface, line, fonts['normal'], C_WHITE, line_y)
        line_y += 34
    stats = f'蜂蜜 {flags["honeys"]}/3｜线索 {flags["truth_clues"]}/2｜火柴证据 {flags["match_clues"]}/2｜火柴盒救援 {"完成" if flags["prisoners_released"] else "未完成"}｜成就 {len(game_state["badges"])}'
    draw_center_text(surface, stats, fonts['small'], C_YELLOW, 234)
    roam_rect = (VW // 2 - 180, VH - 72, 160, 34)
    restart_rect = (VW // 2 + 30, VH - 72, 160, 34)
    draw_button(surface, game_state, roam_rect, '继续闲逛', 'ending_roam', fonts['normal'], True, '区域：结局按钮 继续闲逛')
    draw_button(surface, game_state, restart_rect, '重新开始', 'restart', fonts['normal'], True, '区域：结局按钮 重新开始')


def draw_frame(app_state):
    """绘制当前帧。

    :param app_state: 应用状态字典。
    """
    game_state = app_state['game_state']
    fonts = app_state['fonts']
    canvas = app_state['canvas']
    screen = app_state['screen']
    game_state['buttons'] = []
    game_state['ui_areas'] = []
    ui_state = game_state['ui_state']
    if ui_state == 'title':
        draw_title(canvas, app_state)
    elif ui_state == 'battle':
        draw_battle_panel(canvas, game_state, fonts)
    elif ui_state == 'judgement':
        draw_world(canvas, app_state)
        draw_judgement_panel(canvas, game_state, fonts)
    elif ui_state == 'ending':
        draw_ending_panel(canvas, game_state, fonts)
    elif ui_state == 'journal':
        draw_world(canvas, app_state)
        draw_journal_panel(canvas, game_state, fonts)
    elif ui_state == 'inventory':
        draw_world(canvas, app_state)
        draw_inventory_panel(canvas, game_state, fonts)
    elif ui_state == 'map':
        draw_world(canvas, app_state)
        draw_world_map_panel(canvas, game_state, fonts)
    elif ui_state == 'codex':
        draw_world(canvas, app_state)
        draw_codex_panel(canvas, game_state, fonts)
    elif ui_state == 'shop':
        draw_world(canvas, app_state)
        draw_shop_panel(canvas, game_state, fonts)
    elif ui_state == 'pause':
        draw_world(canvas, app_state)
        draw_pause_panel(canvas, game_state, fonts)
    else:
        draw_world(canvas, app_state)
        dialogue = game_state['dialogue']
        if ui_state == 'dialogue' and dialogue is not None:
            draw_portrait_dialogue(canvas, game_state, fonts)
            draw_dialogue(canvas, game_state, fonts)
    draw_tooltip(canvas, game_state, fonts)
    screen.blit(canvas, (0, 0))
    pygame.display.flip()


def restart_game(app_state):
    """重新开始游戏。

    :param app_state: 应用状态字典。
    """
    logger.info('玩家选择重新开始游戏。')
    app_state['game_state'] = create_game_state()


def close_current_panel(game_state):
    """关闭当前面板回到上一状态。

    :param game_state: 游戏状态字典。
    """
    previous_ui_state = game_state['previous_ui_state']
    game_state['ui_state'] = previous_ui_state
    show_message(game_state, '面板已关闭。')


def open_panel(game_state, ui_state):
    """打开指定面板。

    :param game_state: 游戏状态字典。
    :param ui_state: 面板状态。
    """
    current_ui_state = game_state['ui_state']
    if current_ui_state in ('explore', 'pause'):
        game_state['previous_ui_state'] = current_ui_state
        game_state['ui_state'] = ui_state
        show_message(game_state, '打开面板。')


def handle_button_action(app_state, action):
    """处理鼠标按钮动作。

    :param app_state: 应用状态字典。
    :param action: 按钮动作编号。
    """
    game_state = app_state['game_state']
    if action == 'start_title':
        start_game_from_title(game_state)
    elif action == 'hero_prev':
        select_previous_hero(game_state)
    elif action == 'hero_next':
        select_next_hero(game_state)
    elif action == 'title_act_prev':
        select_title_start_act(game_state, -1)
    elif action == 'title_act_next':
        select_title_start_act(game_state, 1)
    elif action == 'dialogue_next':
        advance_dialogue(game_state)
    elif action == 'open_journal':
        open_panel(game_state, 'journal')
    elif action == 'open_inventory':
        open_panel(game_state, 'inventory')
    elif action == 'open_map':
        open_panel(game_state, 'map')
    elif action == 'open_codex':
        open_panel(game_state, 'codex')
    elif action == 'open_pause':
        open_panel(game_state, 'pause')
    elif action == 'toggle_auto':
        if game_state['ui_state'] == 'judgement':
            apply_wolf_judgement(game_state, 'cage')
        else:
            toggle_auto_play(game_state)
    elif action == 'toggle_tooltip':
        toggle_tooltip(game_state)
    elif action == 'save':
        save_game_state(game_state)
    elif action == 'close_panel':
        close_current_panel(game_state)
    elif action == 'buy_1':
        shop_entry = SHOP_BUY_CATALOG[0]
        buy_shop_entry(game_state, shop_entry)
    elif action == 'buy_2':
        shop_entry = SHOP_BUY_CATALOG[1]
        buy_shop_entry(game_state, shop_entry)
    elif action == 'buy_3':
        shop_entry = SHOP_BUY_CATALOG[2]
        buy_shop_entry(game_state, shop_entry)
    elif action == 'buy_4':
        shop_entry = SHOP_BUY_CATALOG[3]
        buy_shop_entry(game_state, shop_entry)
    elif action == 'buy_5':
        shop_entry = SHOP_BUY_CATALOG[4]
        buy_shop_entry(game_state, shop_entry)
    elif action == 'sell_7':
        shop_entry = SHOP_SELL_CATALOG[0]
        sell_shop_entry(game_state, shop_entry)
    elif action == 'sell_8':
        shop_entry = SHOP_SELL_CATALOG[1]
        sell_shop_entry(game_state, shop_entry)
    elif action == 'sell_9':
        shop_entry = SHOP_SELL_CATALOG[2]
        sell_shop_entry(game_state, shop_entry)
    elif action == 'battle_attack':
        battle_player_attack(game_state)
    elif action == 'battle_heal':
        battle_player_heal(game_state)
    elif action == 'battle_defend':
        battle_player_defend(game_state)
    elif action == 'battle_bell':
        battle_player_bell(game_state)
    elif action == 'battle_question':
        battle_player_question(game_state)
    elif action == 'battle_lamp':
        battle_player_lamp(game_state)
    elif action == 'battle_card':
        battle_player_card(game_state)
    elif action == 'battle_cloth':
        battle_player_cloth(game_state)
    elif action == 'battle_whistle':
        battle_player_whistle(game_state)
    elif action == 'judge_cage':
        apply_wolf_judgement(game_state, 'cage')
    elif action == 'judge_exile':
        apply_wolf_judgement(game_state, 'exile')
    elif action == 'ending_roam':
        game_state['ui_state'] = 'explore'
        game_state['scene'] = 'village'
        set_time_of_day(game_state, 'morning')
        set_view_actor(game_state, 'red')
        player = game_state['player']
        set_player_tile(player, 10, 7)
        show_message(game_state, '结局 CG 已看完。你可以继续在地图里闲逛。')
    elif action == 'restart':
        restart_game(app_state)


def handle_mouse_click(app_state, pos):
    """处理鼠标点击。

    :param app_state: 应用状态字典。
    :param pos: 鼠标坐标。
    """
    game_state = app_state['game_state']
    click_x, click_y = pos
    clicked_action = None
    for button in game_state['buttons']:
        rect = button['rect']
        rect_obj = pygame.Rect(rect)
        if clicked_action is None and rect_obj.collidepoint(click_x, click_y):
            clicked_action = button['action']
    if clicked_action is not None:
        handle_button_action(app_state, clicked_action)


def handle_mouse_move(game_state, pos):
    """处理鼠标移动。

    鼠标位置会影响按钮 hover 效果和 tooltip 命中测试。
    这里只保存位置，不立即绘制，因为 Pygame UI 通常在下一帧统一重绘。

    :param game_state: 游戏状态字典。
    :param pos: 鼠标坐标。
    """
    game_state['mouse_pos'] = pos


def handle_scroll(game_state, amount):
    """处理滚动面板偏移。

    :param game_state: 游戏状态字典。
    :param amount: 滚动变化量。
    """
    ui_state = game_state['ui_state']
    if ui_state in game_state['scroll_offsets']:
        scroll_offsets = game_state['scroll_offsets']
        scroll_offsets[ui_state] += amount
        if scroll_offsets[ui_state] < 0:
            scroll_offsets[ui_state] = 0


def handle_shop_key(game_state, key):
    """处理市场商店按键。

    :param game_state: 游戏状态字典。
    :param key: Pygame 键值。
    """
    if key in KEYS_SHOP_CLOSE:
        game_state['ui_state'] = 'explore'
        show_message(game_state, '离开村口市场。')
    elif key in SHOP_BUY_INDEX_BY_KEY:
        shop_entry_index = SHOP_BUY_INDEX_BY_KEY[key]
        shop_entry = SHOP_BUY_CATALOG[shop_entry_index]
        buy_shop_entry(game_state, shop_entry)
    elif key in SHOP_SELL_INDEX_BY_KEY:
        shop_entry_index = SHOP_SELL_INDEX_BY_KEY[key]
        shop_entry = SHOP_SELL_CATALOG[shop_entry_index]
        sell_shop_entry(game_state, shop_entry)


def handle_battle_key(game_state, key):
    """处理战斗按键。

    :param game_state: 游戏状态字典。
    :param key: Pygame 键值。
    """
    battle = game_state['battle']
    if battle is not None and key in BATTLE_ACTION_BY_KEY:
        battle_action = BATTLE_ACTION_BY_KEY[key]
        if battle_action == 'attack':
            battle_player_attack(game_state)
        elif battle_action == 'heal':
            battle_player_heal(game_state)
        elif battle_action == 'defend':
            battle_player_defend(game_state)
        elif battle_action == 'bell':
            battle_player_bell(game_state)
        elif battle_action == 'question':
            battle_player_question(game_state)
        elif battle_action == 'lamp':
            battle_player_lamp(game_state)
        elif battle_action == 'card':
            battle_player_card(game_state)
        elif battle_action == 'cloth':
            battle_player_cloth(game_state)
        elif battle_action == 'whistle':
            battle_player_whistle(game_state)


def handle_judgement_key(game_state, key):
    """处理灰狼处置按键。

    :param game_state: 游戏状态字典。
    :param key: Pygame 键值。
    """
    if key in JUDGEMENT_CHOICE_BY_KEY:
        choice = JUDGEMENT_CHOICE_BY_KEY[key]
        apply_wolf_judgement(game_state, choice)
    elif key == KEY_ESCAPE:
        show_message(game_state, '请先处置灰狼。囚禁可以防止它继续伤害村民。')


def handle_explore_key(game_state, key):
    """处理探索状态按键。

    :param game_state: 游戏状态字典。
    :param key: Pygame 键值。
    """
    if key in KEYS_CONFIRM:
        try_interact(game_state)
    elif key == KEY_OPEN_JOURNAL:
        open_panel(game_state, 'journal')
    elif key == KEY_OPEN_INVENTORY:
        open_panel(game_state, 'inventory')
    elif key == KEY_OPEN_WORLD_MAP:
        open_panel(game_state, 'map')
    elif key == KEY_OPEN_CODEX:
        open_panel(game_state, 'codex')
    elif key == KEY_OPEN_PAUSE:
        open_panel(game_state, 'pause')
        show_message(game_state, '游戏已暂停。暂停后仍可打开札记、背包、地图和图鉴。')
    elif key == KEY_TOGGLE_HERO:
        select_next_hero(game_state)
        hero_name = current_hero_name(game_state)
        show_message(game_state, f'主角形象切换为：{hero_name}。')
    elif key == KEY_TOGGLE_AUTO_PICKUP:
        toggle_auto_pickup_reachable(game_state)
    elif key == KEY_TOGGLE_PATH_HINT:
        toggle_path_hint(game_state)
    elif key == KEY_ESCAPE:
        open_panel(game_state, 'pause')


def handle_pause_key(game_state, key):
    """处理暂停菜单按键。

    :param game_state: 游戏状态字典。
    :param key: Pygame 键值。
    """
    if key in KEYS_PAUSE_CLOSE:
        game_state['ui_state'] = 'explore'
        show_message(game_state, '继续探索。')
    elif key == KEY_OPEN_JOURNAL:
        open_panel(game_state, 'journal')
    elif key == KEY_OPEN_INVENTORY:
        open_panel(game_state, 'inventory')
    elif key == KEY_OPEN_WORLD_MAP:
        open_panel(game_state, 'map')
    elif key == KEY_OPEN_CODEX:
        open_panel(game_state, 'codex')
    elif key == KEY_TOGGLE_AUTO_PICKUP:
        toggle_auto_pickup_reachable(game_state)
    elif key == KEY_TOGGLE_PATH_HINT:
        toggle_path_hint(game_state)


def handle_key(app_state, key):
    """处理键盘按键事件。

    :param app_state: 应用状态字典。
    :param key: Pygame 键值。
    """
    game_state = app_state['game_state']
    ui_state = game_state['ui_state']
    if key == KEY_SAVE:
        save_game_state(game_state)
    elif key == KEY_LOAD:
        app_state['game_state'] = load_game_state()
    elif key == KEY_SCROLL_UP:
        handle_scroll(game_state, -SCROLL_STEP)
    elif key == KEY_SCROLL_DOWN:
        handle_scroll(game_state, SCROLL_STEP)
    elif ui_state == 'shop':
        handle_shop_key(game_state, key)
    elif key == KEY_TOGGLE_VOICE:
        toggle_voice(game_state)
    elif key == KEY_TOGGLE_SOUND:
        toggle_sound(game_state)
    elif key == KEY_TOGGLE_AUTO_PLAY:
        if ui_state == 'judgement':
            apply_wolf_judgement(game_state, 'cage')
        else:
            toggle_auto_play(game_state)
    elif key in AUTO_SPEED_INDEX_BY_KEY and ui_state != 'judgement':
        auto_speed_index = AUTO_SPEED_INDEX_BY_KEY[key]
        set_auto_speed(game_state, auto_speed_index)
    elif ui_state == 'title':
        if key in KEYS_MOVE_LEFT:
            select_previous_hero(game_state)
        elif key in KEYS_MOVE_RIGHT:
            select_next_hero(game_state)
        elif key == pygame.K_PAGEUP:
            select_title_start_act(game_state, -1)
        elif key == pygame.K_PAGEDOWN:
            select_title_start_act(game_state, 1)
        elif key in KEYS_TITLE_START:
            start_game_from_title(game_state)
        elif key == KEY_ESCAPE:
            app_state['running'] = False
    elif ui_state == 'dialogue':
        if key in KEYS_DIALOGUE_ADVANCE:
            advance_dialogue(game_state)
    elif ui_state == 'battle':
        handle_battle_key(game_state, key)
    elif ui_state == 'judgement':
        handle_judgement_key(game_state, key)
    elif ui_state == 'ending':
        if key in KEYS_CONFIRM or key == KEY_RESTART:
            restart_game(app_state)
        elif key == KEY_ESCAPE:
            game_state['ui_state'] = 'explore'
    elif ui_state == 'pause':
        handle_pause_key(game_state, key)
    elif ui_state == 'journal':
        if key in KEYS_PANEL_CLOSE or key == KEY_OPEN_JOURNAL:
            close_current_panel(game_state)
    elif ui_state == 'inventory':
        if key in KEYS_PANEL_CLOSE or key == KEY_OPEN_INVENTORY:
            close_current_panel(game_state)
    elif ui_state == 'map':
        if key in KEYS_PANEL_CLOSE or key == KEY_OPEN_WORLD_MAP:
            close_current_panel(game_state)
    elif ui_state == 'codex':
        if key in KEYS_PANEL_CLOSE or key == KEY_OPEN_CODEX:
            close_current_panel(game_state)
    elif ui_state == 'explore':
        handle_explore_key(game_state, key)


def update_manual_movement(game_state):
    """更新手动移动。

    :param game_state: 游戏状态字典。
    """
    player = game_state['player']
    if not player['moving']:
        pressed_keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        if pressed_any_key(pressed_keys, KEYS_MOVE_LEFT):
            dx = -1
        elif pressed_any_key(pressed_keys, KEYS_MOVE_RIGHT):
            dx = 1
        elif pressed_any_key(pressed_keys, KEYS_MOVE_UP):
            dy = -1
        elif pressed_any_key(pressed_keys, KEYS_MOVE_DOWN):
            dy = 1
        if dx or dy:
            player['dir'] = (dx, dy)
            next_x = player['x'] + dx
            next_y = player['y'] + dy
            if can_walk(game_state, next_x, next_y):
                start_player_move(player, dx, dy)
            else:
                bump(game_state, next_x, next_y)


def auto_battle_action(game_state):
    """自动战斗行动。

    :param game_state: 游戏状态字典。
    """
    battle = game_state['battle']
    flags = game_state['flags']
    inventory = game_state['inventory']
    player = game_state['player']
    clue_total = flags['truth_clues'] + flags['match_clues']
    if battle is not None:
        if player['hp'] <= 18 and battle['heals'] > 0:
            battle_player_heal(game_state)
        elif battle['battle_key'] in ('gray_wolf', 'aileen') and battle['stage'] in ('disadvantage', 'smoke_dream') and not battle['question_used'] and clue_total >= 2:
            battle_player_question(game_state)
        elif battle['battle_key'] in ('gray_wolf', 'aileen') and battle['stage'] in ('disadvantage', 'smoke_dream') and not battle['bell_used'] and flags['met_hunter']:
            battle_player_bell(game_state)
        elif not battle['question_used'] and clue_total >= 2:
            battle_player_question(game_state)
        elif not battle['bell_used'] and flags['met_hunter']:
            battle_player_bell(game_state)
        elif not battle['lamp_used'] and inventory['油灯'] > 0:
            battle_player_lamp(game_state)
        elif not battle['card_used'] and inventory['清醒卡片'] > 0:
            battle_player_card(game_state)
        elif not battle['cloth_used'] and inventory['防烟布'] > 0:
            battle_player_cloth(game_state)
        elif not battle['whistle_used'] and inventory['木哨'] > 0:
            battle_player_whistle(game_state)
        elif player['hp'] <= 12:
            battle_player_defend(game_state)
        else:
            battle_player_attack(game_state)


def update_auto_play(game_state):
    """更新自动游玩。

    自动游玩是确定性规则 + 最短路径 + 状态机，不是神经网络。
    面试考点：感知当前状态、选择目标、规划路径、执行动作，是可解释的 AI 控制器。

    :param game_state: 游戏状态字典。
    """
    ui_state = game_state['ui_state']
    if ui_state == 'title':
        if game_state['auto_timer'] <= 0:
            skip_acts = game_state['title_skip_acts']
            if skip_acts == 0:
                start_intro_dialogue(game_state)
            else:
                apply_start_skip_to_game_state(game_state, skip_acts, '自动模式')
            game_state['auto_timer'] = 60
    elif ui_state == 'dialogue':
        dialogue = game_state['dialogue']
        if dialogue is not None:
            if dialogue['auto_timer'] <= 0:
                entries = dialogue['entries']
                dialogue_index = dialogue['index']
                entry = entries[dialogue_index]
                text = entry[1]
                text_frames = len(text) * DIALOGUE_CHAR_FRAMES
                base_frames = DIALOGUE_BASE_FRAMES + text_frames
                auto_speed = current_auto_speed(game_state)
                dialogue['auto_timer'] = max(18, base_frames // auto_speed)
            else:
                dialogue['auto_timer'] -= 1
                if dialogue['auto_timer'] <= 0:
                    advance_dialogue(game_state)
    elif ui_state == 'battle':
        if game_state['battle'] is not None and game_state['battle_auto_timer'] <= 0:
            auto_battle_action(game_state)
            game_state['battle_auto_timer'] = BATTLE_AUTO_FRAMES
    elif ui_state == 'judgement':
        if game_state['auto_timer'] <= 0:
            apply_wolf_judgement(game_state, 'cage')
            game_state['auto_timer'] = 40
    elif ui_state == 'explore':
        player = game_state['player']
        if not player['moving'] and game_state['auto_timer'] <= 0:
            auto_explore_action(game_state)
            game_state['auto_timer'] = 10
    elif ui_state in ('journal', 'inventory', 'map', 'codex', 'pause', 'shop'):
        game_state['auto_paused_by_user'] = True
    elif ui_state == 'ending':
        game_state['auto_play'] = False


def after_player_arrival(game_state):
    """玩家抵达目标格后的检查。

    :param game_state: 游戏状态字典。
    """
    check_item_pickup(game_state)
    check_portal(game_state)


def update_app(app_state, dt):
    """更新游戏状态。

    :param app_state: 应用状态字典。
    :param dt: 上一帧到当前帧的毫秒数。
    """
    game_state = app_state['game_state']
    if game_state['message_timer'] > 0:
        game_state['message_timer'] -= 1
    if game_state['auto_timer'] > 0:
        game_state['auto_timer'] -= 1
    if game_state['battle_auto_timer'] > 0:
        game_state['battle_auto_timer'] -= 1
    dialogue = game_state['dialogue']
    voice_enabled = game_state['voice_enabled']
    tts_engine = app_state['tts_engine']
    speak_dialogue_entry(voice_enabled, dialogue, tts_engine)
    if game_state['auto_play']:
        update_auto_play(game_state)
    if game_state['ui_state'] == 'explore':
        if not game_state['auto_play']:
            update_manual_movement(game_state)
        player = game_state['player']
        arrived = update_player_move(player)
        if arrived:
            flags = game_state['flags']
            flags['steps_taken'] += 1
            after_player_arrival(game_state)


def create_publish_images():
    """生成上架页面需要上传的图标与封面。

    Pillow 是 Python Imaging Library 的现代分支，适合在没有外部资源文件的情况下用几何图形生成发布占位图。
    本版封面文字显式使用 yahei_regular_font，通过 ImageFont.truetype 加载，满足“封面应该使用 yahei_regular_font”的需求。
    面试考点：Pillow 负责静态图像生成，Pygame 负责实时窗口渲染，两者职责不同。
    humanize.naturalsize 用于把输出文件大小展示为可读文本，不改变文件本身。
    推荐书：英文 Python Data Science Handbook；中文可参考《Python 自动化办公与实战》。
    """
    icon = Image.new('RGB', (512, 512), (20, 18, 28))
    icon_draw = ImageDraw.Draw(icon)
    icon_draw.rectangle((0, 360, 512, 512), fill=(45, 92, 55))
    icon_draw.polygon([(256, 80), (150, 380), (362, 380)], fill=(196, 38, 48))
    icon_draw.ellipse((204, 150, 308, 254), fill=(238, 183, 137))
    icon_draw.rectangle((215, 185, 232, 200), fill=(15, 13, 18))
    icon_draw.rectangle((280, 185, 297, 200), fill=(15, 13, 18))
    icon_draw.rectangle((238, 235, 274, 246), fill=(240, 240, 228))
    icon_draw.rectangle((348, 260, 408, 330), fill=(222, 181, 82))
    icon_draw.ellipse((64, 70, 150, 156), fill=(90, 170, 255))
    icon.save(PUBLISH_ICON_PATH)

    cover_font_title = ImageFont.truetype(yahei_regular_font, 42)
    cover_font_subtitle = ImageFont.truetype(yahei_regular_font, 28)
    cover_font_small = ImageFont.truetype(yahei_regular_font, 24)
    cover = Image.new('RGB', (1280, 720), (18, 20, 35))
    cover_draw = ImageDraw.Draw(cover)
    cover_draw.rectangle((0, 490, 1280, 720), fill=(44, 94, 62))
    cover_draw.rectangle((720, 220, 1110, 520), fill=(42, 38, 54))
    cover_draw.rectangle((748, 250, 1080, 490), outline=(222, 181, 82), width=6)
    for bar_x in (790, 860, 930, 1000):
        cover_draw.rectangle((bar_x, 260, bar_x + 14, 480), fill=(190, 200, 210))
    for offset_index in range(4):
        offset = offset_index * 26
        cover_draw.rectangle((758 + offset, 502 - offset, 1088 + offset, 520 - offset), outline=(90, 170, 255), width=2)
    cover_draw.rectangle((780, 340, 1020, 440), fill=(18, 16, 28), outline=(222, 181, 82), width=5)
    cover_draw.line((780, 455, 1020, 455), fill=(90, 170, 255), width=5)
    cover_draw.polygon([(280, 160), (150, 520), (410, 520)], fill=(196, 38, 48))
    cover_draw.ellipse((222, 240, 318, 336), fill=(238, 183, 137))
    cover_draw.rectangle((225, 275, 240, 292), fill=(15, 13, 18))
    cover_draw.rectangle((288, 275, 303, 292), fill=(15, 13, 18))
    cover_draw.rectangle((510, 340, 610, 520), fill=(58, 52, 82))
    cover_draw.ellipse((512, 250, 608, 346), fill=(238, 183, 137))
    cover_draw.rectangle((500, 232, 620, 272), fill=(235, 218, 160))
    cover_draw.ellipse((1030, 130, 1140, 240), fill=(90, 170, 255))
    cover_draw.text((80, 60), 'Little Red Riding Hood RPG', fill=(249, 229, 184), font=cover_font_title)
    cover_draw.text((80, 116), 'Hotel Conspiracy / Matchbox Prison', fill=(240, 240, 228), font=cover_font_subtitle)
    cover_draw.text((80, 160), '小红帽RPG', fill=(240, 240, 228), font=cover_font_subtitle)
    cover.save(PUBLISH_COVER_PATH)

    icon_size = PUBLISH_ICON_PATH.stat().st_size
    cover_size = PUBLISH_COVER_PATH.stat().st_size
    icon_size_text = naturalsize(icon_size)
    cover_size_text = naturalsize(cover_size)
    logger.info(f'上架图标已生成：{PUBLISH_ICON_PATH}｜大小：{icon_size_text}')
    logger.info(f'上架封面已生成：{PUBLISH_COVER_PATH}｜大小：{cover_size_text}')


PORTALS = build_portals(PORTAL_BLUEPRINTS)
SCENE_GRAPH = build_scene_graph(PORTAL_BLUEPRINTS)

RUN_MODE = 'normal'

if __name__ == '__main__':
    DEBUG_MODE = True


    if RUN_MODE == 'storyline':
        storyline_text = build_storyline_text()
        output_storyline_text(storyline_text)
        sys.exit()
    elif RUN_MODE == 'original_story':
        original_story_text = build_original_story_text()
        output_original_story_text(original_story_text)
        sys.exit()
    elif RUN_MODE == 'fountain':
        fountain_text = build_fountain_text()
        output_fountain_text(fountain_text)
        sys.exit()
    elif RUN_MODE == 'publish_info':
        create_publish_images()
        publish_table = PrettyTable()
        publish_table.field_names = ['序号', '字段', '控件类型', '表单name', '建议填写值', '候选项 / 说明']
        publish_rows = [
            [1, '游戏名称', '单行文本框', 'title', '小红帽RPG', '字数不超过30个字符。'],
            [2, '一句话介绍', '单行文本框', 'introduction', '多视角童话阴谋RPG', '不超过30个汉字，突出“童话、阴谋、多视角、RPG”。'],
            [3, '项目类型', '下拉框', 'project-type', '游戏', '提交值：type:game。'],
            [4, '游戏图标', '图片上传控件', '', str(PUBLISH_ICON_PATH), '脚本已生成 512×512 PNG；发布页上传即可。'],
            [5, '简介', '多行文本框', 'description', '一款单文件 Pygame 童话 RPG。玩家操控露比穿过森林、识破灰狼伪装，随后追查艾琳的蓝火柴阴谋；游戏包含密语酒店多人密会、多视角切换、火柴盒监狱抽屉囚室救援、回合战斗、自动游玩、录制和剧本导出。', '不超过300字；突出玩法、类型和特色。'],
            [6, '封面', '图片上传控件', '', str(PUBLISH_COVER_PATH), '脚本已生成 1280×720 PNG，封面文字使用 yahei_regular_font；发布页上传即可。'],
            [7, '运行平台', '多选下拉框', 'platform', 'Windows；macOS；Linux', 'Pygame 桌面脚本，PyInstaller 可打包单文件。'],
            [8, '游戏类型', '多选下拉框', 'genre', '角色扮演；冒险；文字；单人；回合制', '可按页面标签取交集。'],
            [9, '风格/题材', '多选下拉框', 'style', '童话；像素；奇幻；黑暗；推理', '本作是小红帽改写，核心卖点是童话黑暗化与阴谋反转。'],
            [10, 'BOOOMJAM参赛选项', '下拉框', 'event-name', '不参赛', '如实际参赛，由用户改成对应赛事。'],
            [11, '项目目标', '下拉框', 'target', '仅试玩展示', '若继续完善美术与音频，可改为“上架销售”。'],
            [12, '游戏状态', '多选下拉框', 'development-status', '持续更新；招募成员', '如果已有发行计划，可补充预计上架平台。'],
        ]
        for publish_row in publish_rows:
            publish_table.add_row(publish_row)
        publish_table_text = f'\n{publish_table}'
        logger.info('目标页面必填字段清单如下：')
        logger.info(publish_table_text)
        packaging_lines = [
            '单文件 Pygame 打包说明：',
            '1、确认当前脚本可以用 python momogame_little_red_hood_dev.py 正常运行。',
            '2、安装打包工具：python -m pip install pyinstaller',
            '3、Windows 图形窗口打包：python -m PyInstaller --onefile --windowed --name momogame_little_red_hood_dev momogame_little_red_hood_dev.py',
            '4、如果需要保留控制台日志，把 --windowed 删除。',
            '5、如录制模式使用 ImageIO 写 MP4，打包时可追加 --collect-all imageio_ffmpeg，确保视频编码器一起进入可执行文件。',
            '6、如果 momo 系列库来自本地源码文件，请把这些库与脚本放在同一项目目录，PyInstaller 会根据 import 分析收集；若是 pip 安装包则无需额外处理。',
            '7、本脚本不读取外部图片、音乐或地图文件，图标和封面由 publish_info 模式本地生成，发布页上传即可。',
            '8、打包产物位于 dist 目录，运行其中的可执行文件即可启动游戏。',
        ]
        packaging_text = '\n'.join(packaging_lines)
        logger.info(packaging_text)
        sys.exit()
    elif RUN_MODE == 'normal' or RUN_MODE == 'record':
        controls_table = PrettyTable()
        controls_table.field_names = ['按键', '功能']
        for control_row in CONTROL_TABLE_ROWS:
            controls_table.add_row(control_row)
        controls_table_text = f'\n{controls_table}'
        logger.info(controls_table_text)

        app_state = create_app_state()
        record_writer = None
        record_ending_frames = 0

        if RUN_MODE == 'record':
            prepare_record_mode(app_state)
            record_writer = imageio.get_writer(RECORD_PATH, fps=FPS)

        while app_state['running']:
            game_state = app_state['game_state']
            game_state['tick'] += 1
            clock = app_state['clock']
            dt = clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    app_state['running'] = False
                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    handle_key(app_state, key)
                elif event.type == pygame.MOUSEMOTION:
                    pos = event.pos
                    handle_mouse_move(game_state, pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        pos = event.pos
                        handle_mouse_move(game_state, pos)
                        handle_mouse_click(app_state, pos)
                elif event.type == pygame.MOUSEWHEEL:
                    wheel_y = event.y
                    handle_scroll(game_state, -wheel_y * SCROLL_STEP)

            update_app(app_state, dt)
            draw_frame(app_state)

            if record_writer is not None:
                canvas = app_state['canvas']
                write_recording_frame(record_writer, canvas)
                game_state = app_state['game_state']
                flags = game_state['flags']
                if game_state['ui_state'] == 'ending':
                    record_ending_frames += 1
                    if record_ending_frames >= RECORD_ENDING_HOLD_FRAMES:
                        app_state['running'] = False
                elif RECORD_STOP_WHEN_AUTO_PLAY_FINISHED and flags['ending_ready'] and not game_state['auto_play']:
                    record_ending_frames += 1
                    if record_ending_frames >= RECORD_ENDING_HOLD_FRAMES:
                        logger.info('录制模式检测到自动游玩已完成，正在结束录制。')
                        app_state['running'] = False
                else:
                    record_ending_frames = 0

            sounds = app_state['sounds']
            game_state = app_state['game_state']
            play_queued_sounds(sounds, game_state)

        if record_writer is not None:
            record_writer.close()
            logger.info(f'录制完成：{RECORD_PATH}')

        logger.info('收到退出请求，正在关闭 Pygame。')
        pygame.quit()
        sys.exit()
    else:
        raise ValueError(f'未知 RUN_MODE：{RUN_MODE}')
