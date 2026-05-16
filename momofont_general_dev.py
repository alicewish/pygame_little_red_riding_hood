import csv
import os
import sys
from datetime import timedelta
from functools import lru_cache
from getpass import getuser
from locale import getlocale
from os.path import abspath, dirname, expanduser
from pathlib import Path
from platform import machine, processor, python_version, system, uname
from re import findall
from re import search
from shutil import copy2
from time import time
from uuid import getnode

import pandas as pd
from fontTools.ttLib import TTCollection, TTFont, TTLibError
from humanize import intcomma, naturalsize, precisedelta
from loguru import logger
from matplotlib import colormaps
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from pathvalidate import sanitize_filename
from platformdirs import user_downloads_dir, user_documents_dir, user_videos_dir
from prettytable import PrettyTable
from psutil import virtual_memory

PY_PATH = Path(__file__).resolve()
IS_DEV = PY_PATH.stem.endswith('_dev')
IS_DUP = PY_PATH.stem.endswith('_dup')

DEBUG_MODE = False

# =============================================================================
# 脚本元信息（供自动化脚本读取，不要在此处写发布日期/许可证）
# =============================================================================

SCRIPT_FILE_NAME = 'momo_font_metadata_scanner.py'
SCRIPT_VERSION = '1.0.5'
SCRIPT_TITLE_EN = 'Momo Font Metadata Scanner'
SCRIPT_TITLE_CN = 'Momo 字体元数据扫描与选择脚本'

GITHUB_REPO_NAME = 'momo-font-metadata-scanner'

# 颜色映射（matplotlib）
COLORMAP_TAB20 = colormaps['tab20']

# 当前运行平台的大致类型，用于在日志中给出一些人类友好的提示
SYSTEM = ''
PLATFORM_SYSTEM = system()
platform_uname = uname()
OS_KERNEL_ARCH = platform_uname.machine

sys_platform_lower = sys.platform.lower()

is_android_by_platform = False
if 'android' in sys_platform_lower or 'pydroid' in sys_platform_lower:
    is_android_by_platform = True

android_root_env = os.environ.get('ANDROID_ROOT', '')
android_data_env = os.environ.get('ANDROID_DATA', '')
android_storage_env = os.environ.get('ANDROID_STORAGE', '')
termux_version_env = os.environ.get('TERMUX_VERSION', '')

is_android_by_env = False
if termux_version_env:
    is_android_by_env = True
elif android_root_env and Path(android_root_env).exists():
    is_android_by_env = True
elif android_data_env and Path(android_data_env).exists():
    is_android_by_env = True
elif android_storage_env and Path(android_storage_env).exists():
    is_android_by_env = True

is_android_by_fs = False
system_fonts_dir = Path('/system/fonts')
system_build_prop = Path('/system/build.prop')
if system_fonts_dir.exists() or system_build_prop.exists():
    is_android_by_fs = True

IS_ANDROID = False
if is_android_by_platform:
    IS_ANDROID = True
elif is_android_by_env:
    IS_ANDROID = True
elif is_android_by_fs:
    IS_ANDROID = True

ANDROID_PUBLIC_DOWNLOADS = None
if IS_ANDROID:
    candidate_directory_list = []

    storage_emulated_download = Path('/storage/emulated/0/Download')
    candidate_directory_list.append(storage_emulated_download)

    storage_emulated_downloads = Path('/storage/emulated/0/Downloads')
    candidate_directory_list.append(storage_emulated_downloads)

    sdcard_download = Path('/sdcard/Download')
    candidate_directory_list.append(sdcard_download)

    storage_self_primary_download = Path('/storage/self/primary/Download')
    candidate_directory_list.append(storage_self_primary_download)

    termux_home_path = Path.home()
    termux_downloads = termux_home_path / 'storage/downloads'
    candidate_directory_list.append(termux_downloads)

    for candidate_directory_path in candidate_directory_list:
        candidate_exists = candidate_directory_path.exists()
        candidate_is_dir = False
        if candidate_exists:
            candidate_is_dir = candidate_directory_path.is_dir()

        if candidate_exists and candidate_is_dir:
            ANDROID_PUBLIC_DOWNLOADS = candidate_directory_path
            break

# 根据架构与平台粗略判断当前系统类型
if IS_ANDROID:
    SYSTEM = 'ANDROID'
else:
    if OS_KERNEL_ARCH in ['x86_64', 'AMD64']:
        if PLATFORM_SYSTEM == 'Windows':
            SYSTEM = 'WINDOWS'
        elif PLATFORM_SYSTEM == 'Linux':
            SYSTEM = 'LINUX'
        else:
            SYSTEM = 'MAC'
    else:
        if PLATFORM_SYSTEM == 'Windows':
            SYSTEM = 'WINDOWS'
        elif PLATFORM_SYSTEM == 'Darwin':
            SYSTEM = 'M1'
        else:
            SYSTEM = 'PI'

# OS 家族归一（mac/win/linux），用于策略分流
if SYSTEM in ['MAC', 'M1']:
    OS_FAMILY = 'mac'
elif SYSTEM == 'WINDOWS':
    OS_FAMILY = 'win'
else:
    OS_FAMILY = 'linux'

# 系统默认语言（用于提示信息的本地化）
locale_tup = getlocale()
if locale_tup and locale_tup[0]:
    lang_code = locale_tup[0]
else:
    lang_code = 'zh_CN'

# 用户名与家目录
username = getuser()
homedir = expanduser('~')
homedir = Path(homedir)
DOWNLOADS = homedir / 'Downloads'
DOCUMENTS = homedir / 'Documents'
MOVIES = homedir / 'Movies'
Data = homedir / 'Data'

detected_downloads = user_downloads_dir()
DOWNLOADS = Path(detected_downloads)
detected_documents = user_documents_dir()
DOCUMENTS = Path(detected_documents)
detected_videos = user_videos_dir()
VIDEOS = Path(detected_videos)

# 硬件与节点信息
mac_address = ':'.join(findall('..', '%012x' % getnode()))
node_name = platform_uname.node

# 当前脚本目录（绝对路径）
current_dir = dirname(abspath(__file__))
current_dir = Path(current_dir)

# 工作目录与用户数据目录（以当前工作路径为程序根目录）
dirpath = os.getcwd()
ProgramFolder = Path(dirpath)
UserDataFolder = ProgramFolder / 'MomoHanhuaUserData'

# Python 版本与处理器信息
python_ver = python_version()
python_vs = f'{sys.version_info.major}.{sys.version_info.minor}'

# 不同系统下的编码、换行、快捷键提示
if SYSTEM == 'WINDOWS':
    encoding = 'gbk'
    line_feed = '\n'
    cmct = 'ctrl'
else:
    encoding = 'utf-8'
    line_feed = '\n'
    cmct = 'command'

if SYSTEM in ['MAC', 'M1']:
    processor_name = processor()
else:
    processor_name = machine()

line_feeds = line_feed * 2
lf = line_feed
lfs = line_feeds

# 设备信息（内存容量，单位 GB）
ram = str(round(virtual_memory().total / (1024.0 ** 3)))
computer_marker = f'{processor_name}_{ram}GB'

# 预设 Anaconda 版本信息（仅用于提示，不参与逻辑判断之外的操作）
anaconda311 = '3.11.8'
anaconda312 = '3.12.7'
anaconda313 = '3.13.5'
anaconda313_arm = '3.13.9'

py_312 = '3.12.10'

anaconda_vers = [anaconda311, anaconda312, anaconda313, anaconda313_arm]
anaconda_normal_vers = [anaconda311, anaconda312, anaconda313, anaconda313_arm, py_312]

DATE_FORMATTER = '%Y-%m-%d %H:%M:%S'

# 需要忽略的临时文件或系统文件模式
ignores = ('*~', '._*')

IGNORE_SPEC_PATTERNS = [
    '*~',
    '._*',
    '.DS_Store',
    '__MACOSX/',
    '__pycache__/',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.git/',
    '.svn/',
    '.hg/',
    '.idea/',
    '.vscode/',
    'Thumbs.db',
    'ehthumbs.db',
]

MomoAutomateUserData = ProgramFolder / 'MomoAutomateUserData'
MomoHanhuaUserData = ProgramFolder / 'MomoHanhuaUserData'
MomoAIUserData = ProgramFolder / 'MomoAIUserData'
# =============================================================================
# 用户可调全局常量区（必须在 DEBUG_MODE = False 之后）
# =============================================================================

# 是否导出“全量字体元数据报表”（与缓存 CSV 不同：报表放在更容易找到的位置）
EXPORT_ALL_FONTS_REPORT = True

# 是否导出“按 kind 选择的字体报表”（Light/Regular/Bold）
EXPORT_SELECTED_FONTS_REPORT = True

# 是否导出“中英日韩俄拉丁”多语种字体列表
EXPORT_MULTILINGUAL_FONTS_REPORT = True

# Android：如果能定位到公共 Downloads，则把报表复制一份到 Downloads 下，方便用户在文件管理器里直接打开
COPY_REPORTS_TO_ANDROID_DOWNLOADS = True

# Android：复制报表时放到 Downloads 的子目录名
ANDROID_REPORT_FOLDER_NAME = 'MomoHanhuaReports'

# 允许用户手工补充额外字体目录（禁止读取环境变量，因此这里提供常量入口）
# 用法示例：
# CUSTOM_FONT_DIRS = [
#     '/sdcard/MyFonts',
#     'D:/MyFontLibrary',
# ]
CUSTOM_FONT_DIRS = []

# 常见临时/资源叉文件前缀（macOS/Windows 拖拽复制后常见）
IGNORED_FILE_PREFIXES = ('~$', '._')

# =============================================================================
# 通用常量（编码、CSV、扫描节奏等）
# =============================================================================

CSV_ENCODING = 'utf-8'
CSV_QUOTING_MODE = csv.QUOTE_MINIMAL
CSV_ESCAPE_CHAR = '\\'

# 解析/进度日志节奏（避免高频刷屏）
FONT_PARSE_PROGRESS_INTERVAL = 200

# 支持的字体后缀集合（目录扫描阶段使用）
SUPPORTED_FONT_SUFFIX_SET = {'.ttf', '.otf', '.ttc', '.otc'}

# cmap 轻量探测中日韩覆盖时，用少量高频汉字码点即可，避免全量统计造成极高成本
CJK_PROBE_CHARACTERS = ['你', '好', '中', '文', '漢', '字']
CJK_PROBE_CODEPOINT_LIST = [ord(character) for character in CJK_PROBE_CHARACTERS]

# =============================================================================
# 路径与缓存文件
# =============================================================================


# 统一放在当前 ProgramFolder 下，便于 PyCharm 一键运行时就近读写
UserDataFolder = ProgramFolder / 'MomoHanhuaUserData'
font_csv = UserDataFolder / f'font_metadata_{computer_marker}.csv'

# Android：用户可见的报表输出目录（尽量放到公共 Downloads）
ANDROID_PUBLIC_REPORT_FOLDER = None
if IS_ANDROID and ANDROID_PUBLIC_DOWNLOADS is not None:
    ANDROID_PUBLIC_REPORT_FOLDER = ANDROID_PUBLIC_DOWNLOADS / ANDROID_REPORT_FOLDER_NAME

# =============================================================================
# 字体元数据字段模板（稳定 schema：统一用方括号访问）
# =============================================================================

FONT_METADATA_DEFAULTS = {
    'file_path': '',
    'file_name': '',
    'suffix': '',
    'collection_index': 0,
    'is_collection': False,
    'family_name': 'Unknown',
    'subfamily_name': 'Regular',
    'full_name': 'Unknown',
    'postscript_name': 'Undefined',
    'weight_class': 400,
    'width_class': 5,
    'size_bytes': 0,
    'file_mtime_ns': 0,
    'weight_type': 'Regular',
    'is_valid': True,
    'is_variable': False,
    'variable_weight_default': None,
    'os2_regular_flag': False,
    'os2_bold_flag': False,
    'italic_flag': False,
    'support_gbk': False,
    'codepage_range1': 0,
    'codepage_range2': 0,
    'language_count': 0,
    'language_list': '',
}

FONT_METADATA_COLUMN_LIST = list(FONT_METADATA_DEFAULTS.keys())
FONT_METADATA_COLUMN_SET = set(FONT_METADATA_COLUMN_LIST)


# =============================================================================
# 基础工具函数
# =============================================================================


def sanitize_text_for_filename(text_value):
    """
    将任意文本转换为更适合做文件名的一段字符串。

    说明：
        - 仅在把“不可信文本”用于文件名时才需要安全化
        - 这里使用第三方库 pathvalidate.sanitize_filename，避免自研不完整规则
    """
    safe_text = ''
    if text_value:
        unsafe_text = str(text_value)
        safe_text = sanitize_filename(unsafe_text)

    return safe_text


def ensure_directory_exists(directory_path):
    """
    确保目录存在，不存在则创建。

    说明：
        - 目录创建属于低频操作，DEBUG_MODE 下输出锚点，避免模块被引用时刷屏
        - 目录已存在时不额外刷屏（除 DEBUG_MODE）
    """
    directory_exists = directory_path.exists()
    if not directory_exists:
        directory_path.mkdir(parents=True, exist_ok=True)
        if DEBUG_MODE:
            logger.success(f'已创建目录: {directory_path}')

    if DEBUG_MODE:
        logger.debug(f'确认目录存在: {directory_path}')

    return


def format_duration_for_display(duration_seconds):
    """
    将耗时秒数格式化为更易读的文本（使用 precisedelta）。

    说明：
        - 用于关键流程的耗时锚点
        - 不做微基准，避免 perf_counter 风格的噪声
        - 为兼容不同 humanize 版本，这里统一先把秒数转为 timedelta 再交给 precisedelta
    """
    duration_text = 'Unknown'

    if duration_seconds is not None:
        normalized_seconds = float(duration_seconds)
        if normalized_seconds >= 0:
            duration_timedelta = timedelta(seconds=normalized_seconds)
            duration_text = precisedelta(duration_timedelta)

    return duration_text


def is_readable_file_path(file_path_text):
    """
    判断文件是否存在且可读。

    为什么要做这个判断：
        - Android 某些系统目录存在，但文件可能无读权限（TTFont 打开会失败）
        - 提前过滤不可读文件，可显著提升“脚本在 Android 上不崩”的概率
    """
    file_path_obj = Path(str(file_path_text))
    file_exists = file_path_obj.exists()

    file_readable = False
    if file_exists:
        file_readable = os.access(str(file_path_obj), os.R_OK)

    is_readable = False
    if file_exists and file_readable:
        is_readable = True

    return is_readable


def copy_report_to_directory(source_file_path, target_directory_path):
    """
    将报表文件复制到指定目录（保留元数据），用于 Android 报表输出到公共 Downloads。

    说明：
        - 不做自动重试
        - 若目录不可写，会 warning 并跳过（不影响字体扫描主流程）
        - 复制成功属于信息型事件，默认只在 DEBUG_MODE 下输出
    """
    source_path = Path(str(source_file_path))
    target_dir = Path(str(target_directory_path))

    source_exists = source_path.exists()
    if not source_exists:
        raise ValueError(f'报表文件不存在，无法复制: {source_path}')

    ensure_directory_exists(target_dir)

    target_writable = os.access(str(target_dir), os.W_OK)
    if target_writable:
        target_file_path = target_dir / source_path.name
        copy2(str(source_path), str(target_file_path))

        source_size_bytes = int(os.stat(str(source_path)).st_size)
        source_size_text = format_size_for_display(source_size_bytes)
        if DEBUG_MODE:
            logger.success(f'已复制报表到: {target_file_path} (大小: {source_size_text})')
    else:
        logger.warning(f'目标目录不可写，跳过复制: {target_dir}')

    return


def create_metadata_template():
    """
    创建一个新的元数据 dict（稳定字段集合）。
    """
    metadata_template = FONT_METADATA_DEFAULTS.copy()
    return metadata_template


def format_size_for_display(size_bytes):
    """
    将字节数格式化为更易读的字符串（使用 naturalsize）。
    """
    friendly_size_text = 'Unknown'
    if size_bytes and int(size_bytes) > 0:
        friendly_size_text = naturalsize(int(size_bytes), binary=True)

    return friendly_size_text


def normalize_bool_value(raw_value):
    """
    将 CSV 读取出来的各种 bool 表示统一转为 bool。

    支持常见形态：
        - True/False
        - 1/0
        - 'True'/'False'
        - 'Y'/'N'
        - NaN/None
    """
    normalized_value = False

    if pd.isna(raw_value):
        normalized_value = False
    else:
        raw_text = str(raw_value).strip().lower()
        true_set = {'1', 'true', 't', 'y', 'yes'}
        false_set = {'0', 'false', 'f', 'n', 'no', ''}

        if raw_text in true_set:
            normalized_value = True
        elif raw_text in false_set:
            normalized_value = False
        else:
            normalized_value = False

    return normalized_value


# =============================================================================
# 字体文件状态（size + mtime）用于增量缓存判断
# =============================================================================


def get_font_file_stat(font_path):
    """
    获取字体文件的两个关键指纹：
        - 文件大小（bytes）
        - 最后修改时间（mtime_ns）

    用途：
        - 缓存表格增量更新（判断文件是否变化）
    """
    file_stat = os.stat(str(font_path))
    size_bytes = int(file_stat.st_size)
    file_mtime_ns = int(file_stat.st_mtime_ns)

    if DEBUG_MODE:
        logger.debug(f'文件指纹: size={size_bytes} mtime_ns={file_mtime_ns} path={font_path}')

    return size_bytes, file_mtime_ns


def get_font_file_size_bytes(font_path):
    """
    获取字体文件大小（字节）。
    """
    size_bytes, file_mtime_ns = get_font_file_stat(font_path)
    file_size_bytes = int(size_bytes)

    return file_size_bytes


# =============================================================================
# 字体匹配规则与常量定义（文件名 + 关键字）
# =============================================================================

MICROSOFT_YAHEI_FILENAMES = {
    'msyh.ttf',
    'msyh.ttc',
    'msyhbd.ttf',
    'msyhbd.ttc',
    'msyhl.ttf',
    'msyhl.ttc',
    'microsoftyahei.ttf',
    'microsoftyahei.ttc',
    'microsoftyaheibd.ttc',
}

MICROSOFT_YAHEI_KEYWORDS = [
    'microsoft yahei',
    'microsoftyahei',
    '微软雅黑',
    'msyh',
]

SOURCE_HAN_SANS_FAMILY_BASES = [
    'source han sans',
    'sourcehansans',
    'source han sans sc',
    'source han sans tc',
    'source han sans cn',
    'source han sans tw',
    'source han sans hk',
    'source han sans jp',
    'source han sans kr',
    'sourcehansanssc',
    'sourcehansanstc',
    'sourcehansanscn',
    'sourcehansanstw',
    'sourcehansanshk',
    'sourcehansansjp',
    'sourcehansanskr',
    'noto sans cjk',
    'notosanscjk',
    'noto sans cjk sc',
    'noto sans cjk tc',
    'noto sans cjk jp',
    'noto sans cjk kr',
    'noto sans s chinese',
    'notosanshans',
    'noto sans sc',
    'noto sans tc',
    'noto sans jp',
    'noto sans kr',
    'notosanssc',
    'notosanstc',
    'notosansjp',
    'notosanskr',
    '思源黑体',
    '源ノ角ゴシック',
    '本ゴシック',
    '本黑',
    '본고딕',
]

SOURCE_HAN_SANS_FILENAMES = {
    'sourcehansanssc-vf.otf',
    'sourcehansanssc-regular.otf',
    'sourcehansanssc-light.otf',
    'sourcehansanssc-bold.otf',
    'sourcehansanssc-extralight.otf',
    'sourcehansanssc-medium.otf',
    'sourcehansanssc-semibold.otf',
    'sourcehansanscn-regular.otf',
    'sourcehansanscn-medium.otf',
    'sourcehansanscn-bold.otf',
    'sourcehansanstc-regular.otf',
    'sourcehansanstc-bold.otf',
    'noto sans cjk sc regular.otf',
    'noto sans cjk sc bold.otf',
    'notosanshans-light.otf',
    'notosanshans-regular.otf',
    'notosanshans-bold.otf',
    'notosanshans-black.otf',
}

PINGFANG_FILENAMES = {
    'pingfang.ttc',
    'pingfangsc.ttc',
    'pingfangtc.ttc',
    'pingfanghk.ttc',
}

PINGFANG_KEYWORDS = [
    'pingfang',
    'pingfang sc',
    'pingfang tc',
    'pingfang hk',
    '苹方',
    '苹方-简',
    '苹方-繁',
]

FZ_LANTING_HEI_KEYWORDS = [
    'fzlantinghei',
    'fzlth',
    '方正兰亭黑',
    '兰亭黑',
]

FZ_LANTING_HEI_FILENAMES = {
    '方正兰亭黑_gbk.ttf',
    '方正兰亭黑扁_gbk.ttf',
    '方正兰亭黑扁简体.ttf',
    '方正兰亭黑简体.ttf',
    '方正兰亭黑长_gbk.ttf',
    '方正兰亭黑长简体.ttf',
}

FZ_CUSONG_KEYWORDS = [
    'fzcusong',
    '方正粗宋',
]

FZ_ZHENGZHONGHEI_KEYWORDS = [
    'fzzhenghei',
    'fzzhengzhonghei',
    '方正正中黑',
    '方正正黑',
    'fzzzh',
]

FZ_ZHUNYUAN_KEYWORDS = [
    'fzzhunyuan',
    '方正准圆',
    'fzzy',
]

FZ_QINGFANGSONG_KEYWORDS = [
    'fzqingfs',
    '方正清仿宋',
    '清仿宋',
]

NEW_SIMSUN_FILENAMES = {
    'simsun.ttc',
    'nsimsun.ttf',
}

NEW_SIMSUN_KEYWORDS = [
    'nsimsun',
    '新宋体',
    '新宋',
    'simsun',
    '宋体',
]

DENGXIAN_FILENAMES = {
    'deng.ttf',
    'dengb.ttf',
    'dengl.ttf',
}

DENGXIAN_KEYWORDS = [
    'dengxian',
    '等线',
]

FANGSONG_FILENAMES = {
    'simfang.ttf',
}

FANGSONG_KEYWORDS = [
    'fangsong',
    '仿宋',
    'simfang',
]

SMILEY_SANS_KEYWORDS = [
    'smileysans',
    'smiley sans',
    '得意黑',
]

HARMONYOS_SANS_KEYWORDS = [
    'harmonyos sans',
    'harmonyossans',
    '鸿蒙',
    '鸿蒙字体',
    '鸿蒙黑体',
]

ALI_PUHUITI_KEYWORDS = [
    'alibaba puhuiti',
    'alibabapuhuiti',
    '阿里巴巴普惠体',
    '普惠体',
]

SHOUZHA_FONT_KEYWORDS = [
    'shouzha',
    'shouzhati',
    '手札体',
    '手札',
]

SHOUZHA_FONT_FILENAMES = {
    'hannotate.ttc',
}

SHUIDI_FONT_KEYWORDS = [
    'shuidi',
    'shuiditi',
    '水滴体',
    '水滴',
]

ZHUJIE_FONT_KEYWORDS = [
    'zhujie',
    'zhujieti',
    '竹节体',
    '竹节',
]

PIXEL_FONT_KEYWORDS = [
    'pixel',
    'pixel font',
    '像素体',
    '像素字体',
    '像素',
]

XINGKAI_FONT_KEYWORDS = [
    'xingkai',
    'stxingkai',
    'fzxingkai',
    '华文行楷',
    '行楷',
]

YUANTI_FONT_KEYWORDS = [
    'yuanti',
    'youyuan',
    '圆体',
    '圆字体',
    '幼圆',
]

MINCHO_FONT_KEYWORDS = [
    'mincho',
    'ms mincho',
    'hira mincho',
    'hiraminpro',
    '明朝体',
    '明朝',
    '宋體',
]

HUAKANG_LIZHONGHEI_FONT_KEYWORDS = [
    '華康儷中黑',
    '華康丽中黑',
    'hklihei',
    'dflihei',
    'lihei',
]

GUYINSONG_FONT_KEYWORDS = [
    '古印宋',
    'guyinsong',
    'guyin song',
]

# Android 常见字体
ROBOTO_KEYWORDS = [
    'roboto',
]

DROID_SANS_FALLBACK_KEYWORDS = [
    'droidsansfallback',
    'droid sans fallback',
    'droid sans',
]

# 说明：
#   - 这里用 dict 保存匹配规则，是因为调用方需要按 key 读取 filenames/keywords
#   - key 语义：
#       - filenames: set[str]，用于“文件名精确命中”
#       - keywords: list[str]，用于“名称字段包含关键字”
FONT_IDENTIFIERS = {
    'roboto': {
        'filenames': set(),
        'keywords': ROBOTO_KEYWORDS,
    },
    'droid_sans_fallback': {
        'filenames': set(),
        'keywords': DROID_SANS_FALLBACK_KEYWORDS,
    },
    'microsoft_yahei': {
        'filenames': MICROSOFT_YAHEI_FILENAMES,
        'keywords': MICROSOFT_YAHEI_KEYWORDS,
    },
    'source_han_sans': {
        'filenames': SOURCE_HAN_SANS_FILENAMES,
        'keywords': SOURCE_HAN_SANS_FAMILY_BASES,
    },
    'pingfang': {
        'filenames': PINGFANG_FILENAMES,
        'keywords': PINGFANG_KEYWORDS,
    },
    'fz_lanting_hei': {
        'filenames': FZ_LANTING_HEI_FILENAMES,
        'keywords': FZ_LANTING_HEI_KEYWORDS,
    },
    'lanting': {
        'filenames': FZ_LANTING_HEI_FILENAMES,
        'keywords': FZ_LANTING_HEI_KEYWORDS,
    },
    'fz_cusong': {
        'filenames': set(),
        'keywords': FZ_CUSONG_KEYWORDS,
    },
    'fz_zhengzhonghei': {
        'filenames': set(),
        'keywords': FZ_ZHENGZHONGHEI_KEYWORDS,
    },
    'fz_zhunyuan': {
        'filenames': set(),
        'keywords': FZ_ZHUNYUAN_KEYWORDS,
    },
    'fz_qingfangsong': {
        'filenames': set(),
        'keywords': FZ_QINGFANGSONG_KEYWORDS,
    },
    'new_simsun': {
        'filenames': NEW_SIMSUN_FILENAMES,
        'keywords': NEW_SIMSUN_KEYWORDS,
    },
    'dengxian': {
        'filenames': DENGXIAN_FILENAMES,
        'keywords': DENGXIAN_KEYWORDS,
    },
    'fangsong': {
        'filenames': FANGSONG_FILENAMES,
        'keywords': FANGSONG_KEYWORDS,
    },
    'smiley_sans': {
        'filenames': set(),
        'keywords': SMILEY_SANS_KEYWORDS,
    },
    'harmonyos_sans': {
        'filenames': set(),
        'keywords': HARMONYOS_SANS_KEYWORDS,
    },
    'ali_puhuiti': {
        'filenames': set(),
        'keywords': ALI_PUHUITI_KEYWORDS,
    },
    'shouzha': {
        'filenames': SHOUZHA_FONT_FILENAMES,
        'keywords': SHOUZHA_FONT_KEYWORDS,
    },
    'shuidi': {
        'filenames': set(),
        'keywords': SHUIDI_FONT_KEYWORDS,
    },
    'zhujie': {
        'filenames': set(),
        'keywords': ZHUJIE_FONT_KEYWORDS,
    },
    'pixel': {
        'filenames': set(),
        'keywords': PIXEL_FONT_KEYWORDS,
    },
    'xingkai': {
        'filenames': set(),
        'keywords': XINGKAI_FONT_KEYWORDS,
    },
    'yuanti': {
        'filenames': set(),
        'keywords': YUANTI_FONT_KEYWORDS,
    },
    'mincho': {
        'filenames': set(),
        'keywords': MINCHO_FONT_KEYWORDS,
    },
    'huakang_lizhonghei': {
        'filenames': set(),
        'keywords': HUAKANG_LIZHONGHEI_FONT_KEYWORDS,
    },
    'guyinsong': {
        'filenames': set(),
        'keywords': GUYINSONG_FONT_KEYWORDS,
    },
}

# =============================================================================
# 代码页 bit -> 语言/区域 描述映射（来自 OS/2 ulCodePageRange 规范）
# =============================================================================

CODEPAGE_BIT_LANGUAGE_MAP = {
    0: '西欧语言 (Latin-1, 1252)',
    1: '东欧语言 (Latin-2, 1250)',
    2: '西里尔字母语言 (1251)',
    3: '希腊语 (1253)',
    4: '土耳其语 (1254)',
    5: '希伯来语 (1255)',
    6: '阿拉伯语 (1256)',
    7: '波罗的语族 (1257)',
    8: '越南语 (1258)',
    16: '泰语 (874)',
    17: '日语 (Shift-JIS, 932)',
    18: '简体中文 (936, PRC / 新加坡)',
    19: '韩文 (Wansung, 949)',
    20: '繁体中文 (950, 台湾 / 香港)',
    21: '韩文 (Johab, 1361)',
    29: 'Mac Roman (Macintosh US Roman)',
    30: 'OEM 字符集 (系统 OEM)',
    31: '符号字符集 (Symbol)',
    48: 'IBM 希腊文 (869)',
    49: 'MS-DOS 俄文 (866)',
    50: 'MS-DOS 北欧 (865)',
    51: 'MS-DOS 阿拉伯文 (864)',
    52: 'MS-DOS 加拿大法语 (863)',
    53: 'MS-DOS 希伯来文 (862)',
    54: 'MS-DOS 冰岛文 (861)',
    55: 'MS-DOS 葡萄牙文 (860)',
    56: 'IBM 土耳其文 (857)',
    57: 'IBM 西里尔文 (855)',
    58: 'IBM Latin-2 (852)',
    59: 'MS-DOS 波罗的语族 (775)',
    60: '希腊文 (737)',
    61: '阿拉伯文 (708, ASMO 708)',
    62: '西欧语言 (850, WE/Latin-1)',
    63: 'MS-DOS 美国 (437)',
}


# =============================================================================
# 系统字体目录收集（桌面 + Android）
# =============================================================================


def get_font_dirs():
    """
    收集系统字体目录：

    目录来源（不读取环境变量）：
        1) CUSTOM_FONT_DIRS（用户手工配置）
        2) Windows/macOS/Linux/Android 常见字体目录
        3) matplotlib 已知字体路径反推目录

    返回：
        list[Path]：存在且可读的字体目录（去重）
    """
    started_timestamp = time()

    if DEBUG_MODE:
        logger.info('开始收集系统字体目录')

    potential_font_directories = []
    home_dir_path = Path.home()

    if CUSTOM_FONT_DIRS:
        if DEBUG_MODE:
            logger.info(f'检测到 CUSTOM_FONT_DIRS 数量: {intcomma(len(CUSTOM_FONT_DIRS))}')
        for custom_dir_value in CUSTOM_FONT_DIRS:
            custom_dir_text = str(custom_dir_value).strip()
            if custom_dir_text:
                custom_dir_path = Path(custom_dir_text)
                potential_font_directories.append(custom_dir_path)
                if DEBUG_MODE:
                    logger.debug(f'加入自定义字体目录: {custom_dir_path}')

    if IS_ANDROID:
        if DEBUG_MODE:
            logger.info('按 Android 规则收集字体目录')

        android_dir_list = [
            Path('/system/fonts'),
            Path('/system/font'),
            Path('/vendor/fonts'),
            Path('/product/fonts'),
            Path('/system_ext/fonts'),
            Path('/apex/com.android.runtime/fonts'),
            Path('/apex/com.android.art/fonts'),
            Path('/apex/com.android.i18n/fonts'),
            Path('/data/fonts'),
            Path('/data/local/fonts'),
            Path('/data/system/theme/fonts'),
            Path('/sdcard/fonts'),
            Path('/storage/emulated/0/fonts'),
            Path('/data/data/ru.iiec.pydroid3/files/usr/share/fonts'),
            Path('/data/data/ru.iiec.pydroid3/files/usr/share/fonts/truetype'),
            Path('/data/data/com.termux/files/usr/share/fonts'),
            Path('/data/data/com.termux/files/usr/share/fonts/truetype'),
        ]

        if ANDROID_PUBLIC_DOWNLOADS is not None:
            android_dir_list.append(ANDROID_PUBLIC_DOWNLOADS / 'fonts')

        for android_font_dir in android_dir_list:
            potential_font_directories.append(android_font_dir)

    elif PLATFORM_SYSTEM == 'Windows':
        if DEBUG_MODE:
            logger.info('按 Windows 规则收集字体目录')

        windows_root_path = Path('C:/Windows')
        windows_fonts_dir = windows_root_path / 'Fonts'
        potential_font_directories.append(windows_fonts_dir)

        potential_font_directories.append(home_dir_path / 'AppData/Local/Microsoft/Windows/Fonts')
        potential_font_directories.append(home_dir_path / 'AppData/Roaming/Microsoft/Windows/Fonts')

        potential_font_directories.append(Path('C:/ProgramData/Microsoft/Windows/Fonts'))
        potential_font_directories.append(Path('C:/Users/Public/Documents/Fonts'))
        potential_font_directories.append(Path('C:/Program Files/Common Files/Adobe/Fonts'))
        potential_font_directories.append(Path('C:/Program Files (x86)/Common Files/Adobe/Fonts'))

        if DEBUG_MODE:
            logger.debug(f'Windows 系统字体目录候选: {windows_fonts_dir}')

    elif PLATFORM_SYSTEM == 'Darwin':
        if DEBUG_MODE:
            logger.info('按 macOS 规则收集字体目录')

        mac_dir_list = [
            Path('/System/Library/Fonts'),
            Path('/System/Library/Fonts/Supplemental'),
            Path('/System/Library/Fonts/LanguageSupport'),
            Path('/Library/Fonts'),
            Path('/Library/Fonts/Microsoft'),
            home_dir_path / 'Library/Fonts',
            home_dir_path / 'Library/Fonts/Microsoft',
            Path('/Network/Library/Fonts'),
            Path('/System/Library/AssetsV2/com_apple_MobileAsset_Font6'),
            Path('/System/Library/AssetsV2/com_apple_MobileAsset_Font7'),
        ]
        for mac_font_dir in mac_dir_list:
            potential_font_directories.append(mac_font_dir)

    elif PLATFORM_SYSTEM == 'Linux':
        if DEBUG_MODE:
            logger.info('按 Linux 规则收集字体目录')

        linux_dir_list = [
            Path('/usr/share/fonts'),
            Path('/usr/local/share/fonts'),
            Path('/usr/share/fonts/truetype'),
            Path('/usr/share/fonts/opentype'),
            Path('/usr/share/fonts/X11'),
            Path('/usr/share/fonts/truetype/dejavu'),
            Path('/usr/share/fonts/truetype/msttcorefonts'),
            Path('/usr/share/fonts/truetype/noto'),
            home_dir_path / '.local/share/fonts',
            home_dir_path / '.fonts',
            Path('/var/lib/snapd/desktop/fonts'),
            home_dir_path / '.var/app/fonts',
        ]
        for linux_font_dir in linux_dir_list:
            potential_font_directories.append(linux_font_dir)

    if DEBUG_MODE:
        logger.info('尝试从 matplotlib.font_manager 反查字体目录')

    matplotlib_entries = font_manager.fontManager.ttflist
    for font_entry in matplotlib_entries:
        font_entry_path = Path(str(font_entry.fname))
        potential_font_directories.append(font_entry_path.parent)

    valid_font_directories = []
    visited_directory_string_set = set()

    for directory_path in potential_font_directories:
        directory_exists = directory_path.exists()

        directory_is_dir = False
        if directory_exists:
            directory_is_dir = directory_path.is_dir()

        directory_readable = os.access(str(directory_path), os.R_OK)
        directory_traversable = os.access(str(directory_path), os.X_OK)

        if directory_exists and directory_is_dir and directory_readable and directory_traversable:
            resolved_directory_path = directory_path.resolve()
            directory_string = str(resolved_directory_path)

            already_seen = directory_string in visited_directory_string_set
            if not already_seen:
                visited_directory_string_set.add(directory_string)
                valid_font_directories.append(resolved_directory_path)

                if DEBUG_MODE:
                    logger.debug(f'确认存在字体目录: {resolved_directory_path}')

    elapsed_seconds = time() - started_timestamp
    elapsed_text = format_duration_for_display(elapsed_seconds)
    if DEBUG_MODE:
        logger.success(
            f'最终收集到有效字体目录数量: {intcomma(len(valid_font_directories))} (耗时: {elapsed_text})'
        )

    return valid_font_directories


# =============================================================================
# 字重识别与标准化
# =============================================================================


def get_weight_info_from_name(name_text):
    """
    从字体名称（家族名/子族名/PostScript 名等）中分析字重信息。

    返回:
        weight_value, weight_type_label
        - weight_value: 100~900
        - weight_type_label: Light / Regular / Bold
    """
    detected_weight_value = None
    detected_weight_type = None

    if name_text:
        name_lower = str(name_text).lower()
        name_no_space = name_lower.replace(' ', '')

        if DEBUG_MODE:
            logger.debug(f'根据名称分析字重: {name_lower}')

        weight_match = search(r'w([1-9])', name_lower)
        if weight_match:
            w_number_text = weight_match.group(1)
            w_number = int(w_number_text)

            detected_weight_value = w_number * 100
            if w_number <= 3:
                detected_weight_type = 'Light'
            elif w_number <= 6:
                detected_weight_type = 'Regular'
            else:
                detected_weight_type = 'Bold'

            if DEBUG_MODE:
                logger.debug(f'识别到 W{w_number} 字重标记')
        else:
            is_light_by_name = False
            is_bold_by_name = False
            is_regular_by_name = False

            if (
                    'extra light' in name_lower
                    or 'extralight' in name_lower
                    or 'ultralight' in name_lower
                    or 'ultra light' in name_lower
                    or 'thin' in name_lower
                    or 'hairline' in name_lower
            ):
                is_light_by_name = True

            if ' light' in name_lower or name_lower.endswith('light'):
                is_light_by_name = True

            if (
                    'extra bold' in name_lower
                    or 'extrabold' in name_lower
                    or 'heavy' in name_lower
                    or 'black' in name_lower
                    or 'demibold' in name_lower
                    or 'semi bold' in name_lower
                    or 'semibold' in name_lower
            ):
                is_bold_by_name = True

            if ' bold' in name_lower or name_lower.endswith('bold'):
                is_bold_by_name = True

            if (
                    'medium' in name_lower
                    or 'regular' in name_lower
                    or 'normal' in name_lower
                    or 'book' in name_lower
                    or 'roman' in name_lower
            ):
                is_regular_by_name = True

            if (
                    '特细' in name_no_space
                    or '极细' in name_no_space
                    or '超细' in name_no_space
                    or '纤细' in name_no_space
                    or '纤' in name_no_space
                    or '细体' in name_no_space
                    or '细字' in name_no_space
                    or '轻' in name_no_space
            ):
                is_light_by_name = True

            if (
                    '粗体' in name_no_space
                    or '中黑' in name_no_space
                    or '粗黑' in name_no_space
                    or '特黑' in name_no_space
                    or '准黑' in name_no_space
                    or '黑体' in name_no_space
            ):
                is_bold_by_name = True

            if (
                    '常规' in name_no_space
                    or '标准' in name_no_space
                    or '標準' in name_no_space
                    or '普通' in name_no_space
                    or '中等' in name_no_space
            ):
                is_regular_by_name = True

            if is_bold_by_name:
                detected_weight_type = 'Bold'
            elif is_light_by_name:
                detected_weight_type = 'Light'
            elif is_regular_by_name:
                detected_weight_type = 'Regular'

            if detected_weight_type == 'Light':
                detected_weight_value = 300
            elif detected_weight_type == 'Bold':
                detected_weight_value = 700
            elif detected_weight_type == 'Regular':
                detected_weight_value = 400

    if DEBUG_MODE:
        logger.debug(f'名称分析字重结果: value={detected_weight_value} type={detected_weight_type}')

    return detected_weight_value, detected_weight_type


def normalize_font_weight_info(os2_weight_class, subfamily_name, postscript_name):
    """
    将 OS/2 字重信息与名称信息综合，统一出：
        - 数值字重（100-900）
        - 字重类型标签：Light / Regular / Bold
    """
    base_weight_value = 400
    if os2_weight_class:
        base_weight_value = int(os2_weight_class)

    name_parts_list = []
    if subfamily_name:
        name_parts_list.append(str(subfamily_name))
    if postscript_name:
        name_parts_list.append(str(postscript_name))

    combined_name_for_weight = ' '.join(name_parts_list)
    if DEBUG_MODE:
        logger.debug(f'开始标准化字重，OS/2={base_weight_value} 名称={combined_name_for_weight}')

    name_weight_value = None
    name_weight_type = None
    if combined_name_for_weight:
        name_weight_value, name_weight_type = get_weight_info_from_name(combined_name_for_weight)

    final_weight_value = base_weight_value
    final_weight_type = 'Regular'

    if name_weight_type is not None:
        final_weight_type = name_weight_type
        if name_weight_value is not None:
            final_weight_value = int(name_weight_value)
        else:
            if final_weight_type == 'Light':
                if final_weight_value > 500:
                    final_weight_value = 300
            elif final_weight_type == 'Bold':
                if final_weight_value < 600:
                    final_weight_value = 700
    else:
        if final_weight_value <= 350:
            final_weight_type = 'Light'
        elif final_weight_value >= 600:
            final_weight_type = 'Bold'
        else:
            final_weight_type = 'Regular'

    if final_weight_value < 100:
        final_weight_value = 100
    if final_weight_value > 900:
        final_weight_value = 900

    if DEBUG_MODE:
        logger.debug(f'标准化后字重: value={final_weight_value} type={final_weight_type}')

    return final_weight_value, final_weight_type


# =============================================================================
# 语言 / 代码页相关分析函数
# =============================================================================


@lru_cache(maxsize=1024)
def get_language_list_from_codepages_cached(codepage_range1_int, codepage_range2_int):
    """
    缓存版本：输入必须为 int，避免 NaN/None 等不可控值导致缓存失效。

    说明：
        - 该函数只做 bit 判断与映射，结果非常稳定，适合缓存
        - 上层函数负责把 raw 值规整到 int
    """
    lang_name_set = set()

    for global_bit_index in sorted(CODEPAGE_BIT_LANGUAGE_MAP.keys()):
        lang_name = CODEPAGE_BIT_LANGUAGE_MAP[global_bit_index]

        if global_bit_index < 32:
            bit_mask = 1 << global_bit_index
            if codepage_range1_int & bit_mask:
                lang_name_set.add(lang_name)
        else:
            local_bit_index = global_bit_index - 32
            bit_mask = 1 << local_bit_index
            if codepage_range2_int & bit_mask:
                lang_name_set.add(lang_name)

    lang_name_list = sorted(lang_name_set)

    return lang_name_list


def get_language_list_from_codepages(codepage_range1_value, codepage_range2_value):
    """
    根据 OS/2 表中的 ulCodePageRange1 / ulCodePageRange2 两个字段，
    推断出大致的语言组列表。
    """
    if pd.isna(codepage_range1_value):
        codepage_range1_int = 0
    else:
        codepage_range1_int = int(codepage_range1_value)

    if pd.isna(codepage_range2_value):
        codepage_range2_int = 0
    else:
        codepage_range2_int = int(codepage_range2_value)

    lang_name_list = get_language_list_from_codepages_cached(codepage_range1_int, codepage_range2_int)

    if DEBUG_MODE:
        logger.debug(
            f'根据代码页字段计算语言列表，CodePage1={codepage_range1_int} CodePage2={codepage_range2_int} '
            f'语言数量={intcomma(len(lang_name_list))}'
        )

    return lang_name_list


def get_language_count_from_codepages(codepage_range1_value, codepage_range2_value):
    """
    返回代码页对应的语言组数量，用于快速评估字体语言覆盖。
    """
    lang_name_list = get_language_list_from_codepages(codepage_range1_value, codepage_range2_value)
    language_count_value = len(lang_name_list)

    return language_count_value


def normalize_language_fields_in_metadata(metadata_dict):
    """
    统一修正 metadata_dict 中与语言相关的字段：
        - language_list 一律为字符串
        - language_count 一律为 int

    说明：
        - 为了兼容旧缓存，若缺少键则在此处补齐
    """
    if 'language_list' not in metadata_dict:
        metadata_dict['language_list'] = ''

    language_list_value = metadata_dict['language_list']
    normalized_language_list_text = ''
    if pd.isna(language_list_value):
        normalized_language_list_text = ''
    else:
        normalized_language_list_text = str(language_list_value)

    metadata_dict['language_list'] = normalized_language_list_text

    if 'language_count' not in metadata_dict:
        metadata_dict['language_count'] = 0

    language_count_value = metadata_dict['language_count']
    normalized_language_count_value = 0
    if pd.isna(language_count_value):
        normalized_language_count_value = 0
    else:
        normalized_language_count_value = int(language_count_value)

    metadata_dict['language_count'] = normalized_language_count_value

    if DEBUG_MODE:
        logger.debug(
            f'规范化语言字段: language_count={normalized_language_count_value} language_list={normalized_language_list_text}'
        )

    return metadata_dict


# =============================================================================
# name 表解码工具（关键修复点）
# =============================================================================


def decode_name_record_to_unicode(name_record):
    """
    安全地将 fontTools 的 NameRecord 转为 Unicode 字符串。

    关键点：
        - 一律使用 errors='replace' 避免某些系统字体 name 记录带有非 ASCII 字节导致崩溃
        - 不做“修正文本”的二次处理（不引入 ftfy / fix_text）
    """
    decoded_text = ''
    decoded_text_candidate = name_record.toUnicode(errors='replace')
    if decoded_text_candidate:
        decoded_text = decoded_text_candidate

    return decoded_text


def get_best_name_text_from_name_table(name_table, target_name_id):
    """
    从 name 表中选出更“靠谱”的 name 记录（避免随便取最后一条导致语言/平台混乱）。

    简单优先级策略（可读性优先，不做复杂黑魔法）：
        1) Windows Unicode (platformID=3) 优先
        2) Unicode (platformID=0) 次之
        3) Macintosh (platformID=1) 再次
        4) 同平台内优先 en-US (langID=0x0409)（如果存在）
    """
    candidate_record_list = []
    for name_record in name_table.names:
        is_target = name_record.nameID == int(target_name_id)
        if is_target:
            candidate_record_list.append(name_record)

    best_text = ''
    best_score_value = -10_000.0

    for name_record in candidate_record_list:
        score_value = 0.0

        if name_record.platformID == 3:
            score_value = score_value + 100.0
            if int(name_record.langID) == 0x0409:
                score_value = score_value + 50.0
        elif name_record.platformID == 0:
            score_value = score_value + 90.0
        elif name_record.platformID == 1:
            score_value = score_value + 80.0
        else:
            score_value = score_value + 10.0

        decoded_text = decode_name_record_to_unicode(name_record)
        if decoded_text:
            text_length = len(decoded_text)
            length_bonus = min(text_length, 50) * 0.1
            score_value = score_value + float(length_bonus)
        else:
            score_value = score_value - 1000.0

        if score_value > best_score_value:
            best_score_value = score_value
            best_text = decoded_text

    return best_text


# =============================================================================
# 字体元数据提取（fontTools）
# =============================================================================


def probe_cjk_support_by_cmap(ttfont_object, file_path_text, collection_index):
    """
    使用 cmap 做一个非常轻量的“中文覆盖探测”。

    说明：
        - CodePage bits 并不总是可靠（有的字体没填、或填的不完整）
        - 这里不做全量范围扫描，只检查少量高频汉字码点，成本较低
        - 若 fontTools 无法提供 cmap，则返回 False

    关键修复点：
        - 部分第三方字体的 cmap 子表存在结构性错误
        - fontTools 在 decompile 某些 format 4 cmap 时会抛出 AssertionError
        - 本函数属于“补充探测”，失败不应中断全量扫描流程
        - 因此这里捕获常见异常并记录 warning，然后返回 False

    返回:
        bool
    """
    supports_cjk = False

    best_cmap = None
    try:
        best_cmap = ttfont_object.getBestCmap()
    except (AssertionError, TTLibError, KeyError, IndexError, ValueError) as error:
        file_name_str = Path(str(file_path_text)).name
        logger.warning(
            f'cmap 解析失败，将跳过 CJK 探测: {file_name_str} index={int(collection_index)} error={error}'
        )
        best_cmap = None
    except Exception as error:
        file_name_str = Path(str(file_path_text)).name
        logger.warning(
            f'cmap 探测发生未知错误，将跳过 CJK 探测: {file_name_str} index={int(collection_index)} error={error}'
        )
        best_cmap = None

    if best_cmap:
        for codepoint_value in CJK_PROBE_CODEPOINT_LIST:
            has_glyph = codepoint_value in best_cmap
            if has_glyph:
                supports_cjk = True
                break

    return supports_cjk


def extract_metadata_from_ttfont(ttfont_object, file_path, collection_index):
    """
    使用 fontTools 从 TTFont 对象中提取详细元数据。

    返回：
        dict（调用方需要按 key 访问，且后续需要写 CSV，因此此处使用 dict）

    metadata key 语义（核心字段）：
        - file_path: 字体文件完整路径（字符串，便于落盘 CSV）
        - file_name: 字体文件名（含扩展名）
        - suffix: 扩展名（.ttf/.otf/.ttc/.otc）
        - collection_index: 集合字体索引（非集合则为 0）
        - is_collection: 是否为集合字体（TTC/OTC）
        - family_name/subfamily_name/full_name/postscript_name: name 表解析结果
        - weight_class/width_class: OS/2 表结果（字重/字宽）
        - weight_type: Light/Regular/Bold（综合 OS/2 + 名称推断）
        - is_variable: 是否可变字体（fvar）
        - italic_flag: 是否斜体（OS/2 + post）
        - support_gbk: 是否支持中日韩常用汉字（粗略判断：CodePage bits + cmap 探测）
        - codepage_range1/codepage_range2: OS/2 codepage bits
        - language_count/language_list: 基于 codepage bits 推断的语言组数量与列表
        - is_valid: 是否“可用”（当前用 PostScript 名是否存在做一个严格门槛）
    """
    file_path_text = str(file_path)
    file_path_obj = Path(file_path_text)

    file_name = file_path_obj.name
    suffix = file_path_obj.suffix.lower()

    size_bytes, file_mtime_ns = get_font_file_stat(file_path_obj)

    metadata = create_metadata_template()
    metadata['file_path'] = file_path_text
    metadata['file_name'] = file_name
    metadata['suffix'] = suffix
    metadata['collection_index'] = int(collection_index)
    metadata['size_bytes'] = int(size_bytes)
    metadata['file_mtime_ns'] = int(file_mtime_ns)

    if 'name' in ttfont_object:
        name_table = ttfont_object['name']

        family_name_text = get_best_name_text_from_name_table(name_table, 1)
        subfamily_name_text = get_best_name_text_from_name_table(name_table, 2)
        full_name_text = get_best_name_text_from_name_table(name_table, 4)
        postscript_name_text = get_best_name_text_from_name_table(name_table, 6)

        if family_name_text:
            metadata['family_name'] = family_name_text
        if subfamily_name_text:
            metadata['subfamily_name'] = subfamily_name_text
        if full_name_text:
            metadata['full_name'] = full_name_text
        if postscript_name_text:
            metadata['postscript_name'] = postscript_name_text

    if 'OS/2' in ttfont_object:
        os2_table = ttfont_object['OS/2']

        metadata['weight_class'] = int(os2_table.usWeightClass)
        metadata['width_class'] = int(os2_table.usWidthClass)

        fs_selection_value = int(os2_table.fsSelection)
        os2_regular_flag = bool(fs_selection_value & (1 << 6))
        os2_bold_flag = bool(fs_selection_value & (1 << 5))
        os2_italic_flag = bool(fs_selection_value & 1)

        metadata['os2_regular_flag'] = os2_regular_flag
        metadata['os2_bold_flag'] = os2_bold_flag
        metadata['italic_flag'] = os2_italic_flag

        if hasattr(os2_table, 'ulCodePageRange1'):
            codepage_range1_value = int(os2_table.ulCodePageRange1)
            metadata['codepage_range1'] = int(codepage_range1_value)

            simplified_cn_bit = 1 << 18
            traditional_cn_bit = 1 << 20
            support_simplified = bool(codepage_range1_value & simplified_cn_bit)
            support_traditional = bool(codepage_range1_value & traditional_cn_bit)

            if support_simplified or support_traditional:
                metadata['support_gbk'] = True

        if hasattr(os2_table, 'ulCodePageRange2'):
            codepage_range2_value = int(os2_table.ulCodePageRange2)
            metadata['codepage_range2'] = int(codepage_range2_value)

    if 'post' in ttfont_object:
        post_table = ttfont_object['post']
        if float(post_table.italicAngle) != 0:
            metadata['italic_flag'] = True

    if 'fvar' in ttfont_object:
        fvar_table = ttfont_object['fvar']
        metadata['is_variable'] = True

        default_weight_value = None
        for axis_record in fvar_table.axes:
            axis_tag_text = str(axis_record.axisTag).strip().lower()
            if axis_tag_text == 'wght':
                default_weight_value = axis_record.defaultValue

        metadata['variable_weight_default'] = default_weight_value

    # 字重标准化：综合 OS/2 + 名称推断
    weight_value, weight_type_label = normalize_font_weight_info(
        metadata['weight_class'],
        metadata['subfamily_name'],
        metadata['postscript_name'],
    )
    metadata['weight_class'] = int(weight_value)
    metadata['weight_type'] = weight_type_label

    # 语言覆盖（按 codepage bits 粗略估计）
    lang_name_list = get_language_list_from_codepages(metadata['codepage_range1'], metadata['codepage_range2'])
    metadata['language_count'] = int(len(lang_name_list))
    metadata['language_list'] = '|'.join(lang_name_list)

    # 额外：当 codepage bits 没标中日韩时，使用 cmap 做轻量探测，提升 Android/部分字体的准确率
    if not bool(metadata['support_gbk']):
        cmap_supports = probe_cjk_support_by_cmap(ttfont_object, file_path_text, collection_index)
        if cmap_supports:
            metadata['support_gbk'] = True

    # 严格门槛：PostScript 名缺失时标记为无效
    if (not metadata['postscript_name']) or metadata['postscript_name'] == 'Undefined':
        metadata['is_valid'] = False
        file_name_for_log = metadata['file_name']
        logger.warning(f'字体缺少有效 PostScript 名称，标记为无效: {file_name_for_log}')

    if DEBUG_MODE:
        logger.debug(
            f'提取字体元数据: file={metadata["file_name"]} family={metadata["family_name"]} '
            f'subfamily={metadata["subfamily_name"]} ps={metadata["postscript_name"]} '
            f'weight={metadata["weight_class"]} type={metadata["weight_type"]} '
            f'gbk={metadata["support_gbk"]} lang_cnt={metadata["language_count"]}'
        )

    return metadata


def get_font_file_metadata(file_path):
    """
    读取单个字体文件（支持 TTC/OTC 集合、TTF/OTF 单体），返回该文件中所有字体实例的元数据列表。

    说明：
        - 不捕获解析异常，让异常自然抛出（便于定位真实错误源）
        - 但会通过 try/finally 确保文件句柄正确关闭，避免资源泄漏
    """
    metadata_list = []

    file_path_text = str(file_path)
    file_path_obj = Path(file_path_text)
    suffix_lower = file_path_obj.suffix.lower()

    readable_flag = is_readable_file_path(file_path_text)
    if not readable_flag:
        logger.warning(f'字体文件不可读，将跳过解析: {file_path_text}')

    if readable_flag:
        if suffix_lower in ['.ttc', '.otc']:
            if DEBUG_MODE:
                logger.debug(f'按集合字体方式解析: {file_path_text}')

            ttc_object = TTCollection(file_path_text)
            font_index = 0

            try:
                for font_object in ttc_object:
                    font_metadata = extract_metadata_from_ttfont(font_object, file_path_text, font_index)
                    font_metadata['is_collection'] = True
                    metadata_list.append(normalize_language_fields_in_metadata(font_metadata))
                    font_index = font_index + 1
            finally:
                ttc_object.close()
        else:
            if DEBUG_MODE:
                logger.debug(f'按单字体方式解析: {file_path_text}')

            font_object = TTFont(file_path_text, fontNumber=0, lazy=True)
            try:
                font_metadata = extract_metadata_from_ttfont(font_object, file_path_text, 0)
                font_metadata['is_collection'] = False
                metadata_list.append(normalize_language_fields_in_metadata(font_metadata))
            finally:
                font_object.close()

    if DEBUG_MODE:
        logger.debug(f'从字体文件提取实例数量: {intcomma(len(metadata_list))} path={file_path_text}')

    return metadata_list


# =============================================================================
# DataFrame / 缓存读取
# =============================================================================


def convert_metadata_list_to_dataframe(all_fonts_metadata):
    """
    将字体元数据列表转换为 pandas.DataFrame，便于保存与展示。

    关键点：
        - 强制补齐缺失列，保证 CSV schema 稳定（兼容旧缓存/部分异常行）
        - 强制按 FONT_METADATA_COLUMN_LIST 排列列顺序，便于 diff 与排查
    """
    metadata_dataframe = pd.DataFrame(all_fonts_metadata)

    for column_name in FONT_METADATA_COLUMN_LIST:
        has_column = column_name in metadata_dataframe.columns
        if not has_column:
            metadata_dataframe[column_name] = FONT_METADATA_DEFAULTS[column_name]

    metadata_dataframe = metadata_dataframe[FONT_METADATA_COLUMN_LIST]

    if 'language_list' in metadata_dataframe.columns:
        metadata_dataframe['language_list'] = metadata_dataframe['language_list'].fillna('')

    if 'language_count' in metadata_dataframe.columns:
        metadata_dataframe['language_count'] = metadata_dataframe['language_count'].fillna(0).astype(int)

    if 'size_bytes' in metadata_dataframe.columns:
        metadata_dataframe['size_bytes'] = metadata_dataframe['size_bytes'].fillna(0).astype(int)

    if 'file_mtime_ns' in metadata_dataframe.columns:
        metadata_dataframe['file_mtime_ns'] = metadata_dataframe['file_mtime_ns'].fillna(0).astype(int)

    if 'collection_index' in metadata_dataframe.columns:
        metadata_dataframe['collection_index'] = metadata_dataframe['collection_index'].fillna(0).astype(int)

    if 'weight_class' in metadata_dataframe.columns:
        metadata_dataframe['weight_class'] = metadata_dataframe['weight_class'].fillna(0).astype(int)

    if 'width_class' in metadata_dataframe.columns:
        metadata_dataframe['width_class'] = metadata_dataframe['width_class'].fillna(0).astype(int)

    if 'codepage_range1' in metadata_dataframe.columns:
        metadata_dataframe['codepage_range1'] = metadata_dataframe['codepage_range1'].fillna(0).astype(int)

    if 'codepage_range2' in metadata_dataframe.columns:
        metadata_dataframe['codepage_range2'] = metadata_dataframe['codepage_range2'].fillna(0).astype(int)

    bool_column_list = [
        'is_collection',
        'is_valid',
        'is_variable',
        'os2_regular_flag',
        'os2_bold_flag',
        'italic_flag',
        'support_gbk',
    ]
    for column_name in bool_column_list:
        if column_name in metadata_dataframe.columns:
            metadata_dataframe[column_name] = metadata_dataframe[column_name].fillna(False).astype(bool)

    if DEBUG_MODE:
        logger.debug(f'已将 {intcomma(len(all_fonts_metadata))} 条字体元数据转换为 DataFrame')

    return metadata_dataframe


def load_font_metadata_from_cache(cache_path):
    """
    从缓存表格中读取字体元数据，恢复为“元数据 dict 列表”。

    兼容旧版本缓存：
        - 若缺少 language_count / language_list，则根据 codepage_range1/2 自动补齐
        - 若缺少 file_mtime_ns，则读取文件 stat 自动补齐
        - 若缺少 size_bytes，则读取文件 stat 自动补齐

    去重策略：
        - 按 (file_path, collection_index) 去重，避免缓存重复行导致结果重复

    关键修复点：
        - mtime_ns 是纳秒级整数，数值非常大（通常在 1e18 量级）
        - pandas 默认推断类型时，若列中出现缺失值或混杂类型，可能把该列推断为 float
        - float64 无法精确表示 1e18 级别的整数，会发生精度丢失，导致增量缓存对比误判“文件已变化”
        - 因此这里统一按字符串读取，再逐字段转换为 int/bool/text，确保指纹稳定可靠

    日志策略：
        - 加载缓存属于性能优化路径，默认只在 DEBUG_MODE 下输出 info/success
        - 缓存损坏属于硬错误，直接抛异常（让调用栈定位问题行）
    """
    all_metadata_list = []

    started_timestamp = time()

    cache_exists = cache_path.exists()
    if cache_exists:
        if DEBUG_MODE:
            logger.info(f'检测到字体元数据缓存表格: {cache_path}')
            logger.info('为避免超大整数列被 pandas 推断为 float 导致精度丢失，将按字符串读取缓存 CSV')

        metadata_dataframe = pd.read_csv(
            cache_path,
            encoding=CSV_ENCODING,
            quoting=CSV_QUOTING_MODE,
            escapechar=CSV_ESCAPE_CHAR,
            dtype=str,
        )
        has_rows = not metadata_dataframe.empty

        if has_rows:
            for column_name in FONT_METADATA_COLUMN_LIST:
                has_column = column_name in metadata_dataframe.columns
                if not has_column:
                    metadata_dataframe[column_name] = FONT_METADATA_DEFAULTS[column_name]

            row_count = int(metadata_dataframe.shape[0])
            col_count = int(metadata_dataframe.shape[1])
            if DEBUG_MODE:
                logger.info(f'缓存表格中共有 {intcomma(row_count)} 行, {intcomma(col_count)} 列')

            has_language_columns = (
                    'language_count' in metadata_dataframe.columns and 'language_list' in metadata_dataframe.columns
            )
            has_mtime_column = 'file_mtime_ns' in metadata_dataframe.columns
            has_size_column = 'size_bytes' in metadata_dataframe.columns

            if not has_language_columns:
                if DEBUG_MODE:
                    logger.info('检测到旧缓存：缺少 language 字段，将在加载时自动补齐')
            if not has_mtime_column:
                if DEBUG_MODE:
                    logger.info('检测到旧缓存：缺少 file_mtime_ns，将在加载时自动补齐')
            if not has_size_column:
                if DEBUG_MODE:
                    logger.info('检测到旧缓存：缺少 size_bytes，将在加载时自动补齐')

            if 'file_path' not in metadata_dataframe.columns:
                raise ValueError(f'缓存表格缺少 file_path 列，缓存已损坏: {cache_path}')

            if 'collection_index' not in metadata_dataframe.columns:
                metadata_dataframe['collection_index'] = 0

            metadata_dataframe = metadata_dataframe.drop_duplicates(subset=['file_path', 'collection_index'],
                                                                    keep='first')

            for row_index, cache_row in metadata_dataframe.iterrows():
                metadata_dict = create_metadata_template()

                for column_name in metadata_dataframe.columns:
                    if column_name in FONT_METADATA_COLUMN_SET:
                        metadata_dict[column_name] = cache_row[column_name]
                    else:
                        if DEBUG_MODE:
                            logger.debug(f'缓存出现未知列，将忽略: {column_name}')

                file_path_value = metadata_dict['file_path']
                if pd.isna(file_path_value) or not str(file_path_value).strip():
                    raise ValueError(f'缓存表格中出现空 file_path，缓存已损坏: {cache_path} 行号={row_index}')

                normalized_file_path = str(file_path_value)
                metadata_dict['file_path'] = normalized_file_path

                collection_index_value = metadata_dict['collection_index']
                if pd.isna(collection_index_value):
                    metadata_dict['collection_index'] = 0
                else:
                    metadata_dict['collection_index'] = int(collection_index_value)

                file_name_value = metadata_dict['file_name']
                if pd.isna(file_name_value) or not str(file_name_value).strip():
                    metadata_dict['file_name'] = Path(normalized_file_path).name
                else:
                    metadata_dict['file_name'] = str(file_name_value)

                suffix_value = metadata_dict['suffix']
                if pd.isna(suffix_value) or not str(suffix_value).strip():
                    metadata_dict['suffix'] = Path(normalized_file_path).suffix.lower()
                else:
                    metadata_dict['suffix'] = str(suffix_value).lower()

                text_field_list = ['family_name', 'subfamily_name', 'full_name', 'postscript_name', 'weight_type']
                for field_name in text_field_list:
                    field_value = metadata_dict[field_name]
                    if pd.isna(field_value):
                        metadata_dict[field_name] = str(FONT_METADATA_DEFAULTS[field_name])
                    else:
                        metadata_dict[field_name] = str(field_value)

                int_field_list = [
                    'weight_class',
                    'width_class',
                    'codepage_range1',
                    'codepage_range2',
                    'language_count',
                    'size_bytes',
                    'file_mtime_ns',
                ]
                for field_name in int_field_list:
                    field_value = metadata_dict[field_name]
                    if pd.isna(field_value):
                        metadata_dict[field_name] = int(FONT_METADATA_DEFAULTS[field_name])
                    else:
                        metadata_dict[field_name] = int(field_value)

                bool_field_list = [
                    'is_collection',
                    'is_valid',
                    'is_variable',
                    'os2_regular_flag',
                    'os2_bold_flag',
                    'italic_flag',
                    'support_gbk',
                ]
                for field_name in bool_field_list:
                    field_value = metadata_dict[field_name]
                    metadata_dict[field_name] = normalize_bool_value(field_value)

                variable_weight_value = metadata_dict['variable_weight_default']
                if pd.isna(variable_weight_value):
                    metadata_dict['variable_weight_default'] = None

                if not has_language_columns:
                    lang_name_list = get_language_list_from_codepages(
                        metadata_dict['codepage_range1'],
                        metadata_dict['codepage_range2'],
                    )
                    metadata_dict['language_count'] = int(len(lang_name_list))
                    metadata_dict['language_list'] = '|'.join(lang_name_list)

                font_path_obj = Path(normalized_file_path)
                font_file_exists = font_path_obj.exists()
                if font_file_exists:
                    current_size_bytes, current_mtime_ns = get_font_file_stat(font_path_obj)

                    if not has_size_column:
                        metadata_dict['size_bytes'] = int(current_size_bytes)
                    else:
                        metadata_dict['size_bytes'] = int(metadata_dict['size_bytes'])

                    if not has_mtime_column:
                        metadata_dict['file_mtime_ns'] = int(current_mtime_ns)
                    else:
                        metadata_dict['file_mtime_ns'] = int(metadata_dict['file_mtime_ns'])

                normalized_metadata = normalize_language_fields_in_metadata(metadata_dict)
                all_metadata_list.append(normalized_metadata)

            elapsed_seconds = time() - started_timestamp
            elapsed_text = format_duration_for_display(elapsed_seconds)
            if DEBUG_MODE:
                logger.success(
                    f'从缓存表格加载 {intcomma(len(all_metadata_list))} 条字体元数据（已去重）(耗时: {elapsed_text})'
                )
        else:
            if DEBUG_MODE:
                logger.info('缓存表格存在但无内容，将视为无缓存')
    else:
        if DEBUG_MODE:
            logger.info(f'未检测到字体元数据缓存表格: {cache_path}')

    return all_metadata_list


# =============================================================================
# 字体文件发现与全量扫描
# =============================================================================


def log_os_walk_error(os_error):
    """
    os.walk 的错误回调。

    说明：
        - 目录扫描阶段最常见问题是权限不足（Android/系统目录）
        - 用 onerror 回调可以在不写 try/except 的前提下记录问题并继续扫描
        - 不改变主流程语义：能读的继续读，不能读的明确 warning
    """
    logger.warning(f'递归扫描目录时发生错误，将忽略该分支: {os_error}')
    return


def discover_font_files(font_directory_list):
    """
    发现所有字体文件路径（TTF/OTF/TTC/OTC），返回去重后的有序列表。

    说明：
        - 优先使用 matplotlib.font_manager.findSystemFonts 获取 ttf/otf
        - 同时使用 os.walk 扫描 ttf/otf/ttc/otc，补齐 Android 等环境的遗漏
        - 会过滤不可读文件，提升 Android 兼容性（避免打开字体时报权限异常）
        - os.walk 使用 onerror 回调记录权限错误并继续

    日志策略：
        - 发现与统计属于信息型输出，默认只在 DEBUG_MODE 下打印
        - 不可读文件数量属于影响结果的重要信息，使用 warning 输出（默认可见）
    """
    started_timestamp = time()

    directory_string_list = []
    for directory_path in font_directory_list:
        directory_string_list.append(str(directory_path))

    if DEBUG_MODE:
        logger.info(f'开始扫描字体文件，目录数量: {intcomma(len(directory_string_list))}')

    ttf_file_list = font_manager.findSystemFonts(fontpaths=directory_string_list, fontext='ttf')
    otf_file_list = font_manager.findSystemFonts(fontpaths=directory_string_list, fontext='otf')

    if DEBUG_MODE:
        logger.info(
            f'matplotlib 发现 ttf 数量: {intcomma(len(ttf_file_list))}, otf 数量: {intcomma(len(otf_file_list))}')

    if DEBUG_MODE:
        font_type_table = PrettyTable()
        font_type_table.field_names = ['字体类型', '数量']
        font_type_table.align = 'l'
        font_type_table.add_row(['TTF', len(ttf_file_list)])
        font_type_table.add_row(['OTF', len(otf_file_list)])

        table_text = font_type_table.get_string()
        for table_line in table_text.split('\n'):
            logger.info(table_line)

    all_font_file_path_set = set()
    unreadable_count = 0

    for ttf_file_path in ttf_file_list:
        normalized_path = str(ttf_file_path)
        readable_flag = is_readable_file_path(normalized_path)
        if readable_flag:
            all_font_file_path_set.add(normalized_path)
        else:
            unreadable_count = unreadable_count + 1
            if DEBUG_MODE:
                logger.warning(f'发现不可读字体文件，将忽略: {normalized_path}')

    for otf_file_path in otf_file_list:
        normalized_path = str(otf_file_path)
        readable_flag = is_readable_file_path(normalized_path)
        if readable_flag:
            all_font_file_path_set.add(normalized_path)
        else:
            unreadable_count = unreadable_count + 1
            if DEBUG_MODE:
                logger.warning(f'发现不可读字体文件，将忽略: {normalized_path}')

    walk_discovered_count = 0

    for directory_path in font_directory_list:
        directory_exists = directory_path.exists()
        if directory_exists:
            if DEBUG_MODE:
                logger.debug(f'递归扫描目录: {directory_path}')

            for root_dir, sub_dir_list, file_name_list in os.walk(str(directory_path), onerror=log_os_walk_error):
                root_path = Path(str(root_dir))

                for file_name in file_name_list:
                    file_name_lower = str(file_name).lower()

                    is_ignored = False
                    for ignore_prefix in IGNORED_FILE_PREFIXES:
                        ignore_hit = file_name_lower.startswith(ignore_prefix)
                        if ignore_hit:
                            is_ignored = True

                    if not is_ignored:
                        file_path = root_path / str(file_name)
                        suffix_lower = file_path.suffix.lower()

                        is_supported = suffix_lower in SUPPORTED_FONT_SUFFIX_SET
                        if is_supported:
                            readable_flag = is_readable_file_path(str(file_path))
                            if readable_flag:
                                all_font_file_path_set.add(str(file_path))
                                walk_discovered_count = walk_discovered_count + 1
                            else:
                                unreadable_count = unreadable_count + 1
                                if DEBUG_MODE:
                                    logger.warning(f'发现不可读字体文件，将忽略: {file_path}')

    font_file_path_list = sorted(all_font_file_path_set)

    elapsed_seconds = time() - started_timestamp
    elapsed_text = format_duration_for_display(elapsed_seconds)

    if DEBUG_MODE:
        logger.success(f'共发现字体文件数量: {intcomma(len(font_file_path_list))} (耗时: {elapsed_text})')
    if unreadable_count > 0:
        logger.warning(f'扫描过程中发现不可读字体文件数量: {intcomma(unreadable_count)}（已忽略，避免解析崩溃）')
    if DEBUG_MODE:
        logger.debug(f'os.walk 补充发现字体文件次数（含重复前）: {intcomma(walk_discovered_count)}')

    return font_file_path_list


def scan_all_fonts_in_dirs(font_directory_list):
    """
    全量扫描多个目录下的所有字体文件，返回所有字体实例元数据列表。
    """
    started_timestamp = time()

    font_file_path_list = discover_font_files(font_directory_list)
    all_metadata_list = []

    total_count = len(font_file_path_list)
    parsed_count = 0

    if DEBUG_MODE:
        logger.info(f'开始深度解析字体文件，总文件数: {intcomma(total_count)}')

    for font_file_path in font_file_path_list:
        if DEBUG_MODE:
            logger.debug(f'解析字体文件: {font_file_path}')

        metadata_list_for_file = get_font_file_metadata(font_file_path)
        for font_metadata in metadata_list_for_file:
            normalized_metadata = normalize_language_fields_in_metadata(font_metadata)
            all_metadata_list.append(normalized_metadata)

        parsed_count = parsed_count + 1
        if parsed_count % FONT_PARSE_PROGRESS_INTERVAL == 0 or parsed_count == total_count:
            if DEBUG_MODE:
                logger.info(f'解析进度: {intcomma(parsed_count)} / {intcomma(total_count)}')

    elapsed_seconds = time() - started_timestamp
    elapsed_text = format_duration_for_display(elapsed_seconds)

    if DEBUG_MODE:
        logger.success(
            f'字体扫描完成，共获得字体实例元数据数量: {intcomma(len(all_metadata_list))} (耗时: {elapsed_text})')

    return all_metadata_list


# =============================================================================
# 缓存签名与增量更新加载
# =============================================================================


def get_font_directory_signature(font_directory_list):
    """
    根据字体目录列表生成稳定签名（tuple[str]），作为 LRU 缓存键。
    """
    directory_string_list = []

    for directory_path in font_directory_list:
        directory_exists = directory_path.exists()

        directory_is_dir = False
        if directory_exists:
            directory_is_dir = directory_path.is_dir()

        directory_readable = os.access(str(directory_path), os.R_OK)
        directory_traversable = os.access(str(directory_path), os.X_OK)

        if directory_exists and directory_is_dir and directory_readable and directory_traversable:
            resolved_directory_path = directory_path.resolve()
            directory_string_list.append(str(resolved_directory_path))
        else:
            if DEBUG_MODE:
                logger.debug(f'构建签名时忽略不可用目录: {directory_path}')

    directory_string_list.sort()
    signature_tuple = tuple(directory_string_list)

    if DEBUG_MODE:
        logger.debug(f'字体目录签名包含目录数量: {intcomma(len(signature_tuple))}')

    return signature_tuple


@lru_cache(maxsize=4)
def load_all_fonts_metadata_cached(font_directory_signature):
    """
    带 LRU 缓存的字体元数据加载逻辑。

    核心策略：
        - 首次：全量扫描并写入 CSV 缓存
        - 后续：从 CSV 读取；仅对“新增字体文件”或“文件已变化（size/mtime 变化）”做增量解析

    日志策略：
        - 性能路径与进度输出默认只在 DEBUG_MODE 下打印
        - 影响结果的异常/跳过使用 warning 输出（默认可见）
    """
    started_timestamp = time()

    if DEBUG_MODE:
        logger.info(f'进入字体元数据加载逻辑，目录数量: {intcomma(len(font_directory_signature))}')

    ensure_directory_exists(UserDataFolder)

    font_directory_list = []
    for directory_string in font_directory_signature:
        font_directory_list.append(Path(directory_string))

    font_file_path_list = discover_font_files(font_directory_list)

    system_font_file_set = set()
    for font_file_path in font_file_path_list:
        system_font_file_set.add(str(font_file_path))

    if DEBUG_MODE:
        logger.info(f'当前系统字体文件数量（TTF/OTF/TTC/OTC）: {intcomma(len(font_file_path_list))}')

    cached_metadata_list = load_font_metadata_from_cache(font_csv)

    cached_metadata_by_file_path = {}
    for cached_metadata in cached_metadata_list:
        cached_file_path = cached_metadata['file_path']
        if cached_file_path:
            if cached_file_path not in cached_metadata_by_file_path:
                cached_metadata_by_file_path[cached_file_path] = []
            cached_metadata_by_file_path[cached_file_path].append(cached_metadata)

    filtered_cached_metadata_list = []
    cached_up_to_date_file_path_set = set()

    cached_file_path_count = len(cached_metadata_by_file_path)
    changed_file_path_count = 0
    removed_file_path_count = 0

    if cached_metadata_by_file_path:
        if DEBUG_MODE:
            logger.success(f'检测到缓存数据，缓存文件数: {intcomma(cached_file_path_count)}，开始执行增量更新')

        for cached_file_path, cached_rows in cached_metadata_by_file_path.items():
            file_exists_in_system = cached_file_path in system_font_file_set and Path(cached_file_path).exists()

            if file_exists_in_system:
                current_size_bytes, current_mtime_ns = get_font_file_stat(cached_file_path)

                first_row = cached_rows[0]
                cached_size_value = first_row['size_bytes']
                cached_mtime_value = first_row['file_mtime_ns']

                cached_size_int = None
                cached_mtime_int = None

                if pd.isna(cached_size_value):
                    cached_size_int = None
                else:
                    cached_size_int = int(cached_size_value)

                if pd.isna(cached_mtime_value):
                    cached_mtime_int = None
                else:
                    cached_mtime_int = int(cached_mtime_value)

                file_is_up_to_date = False
                if cached_size_int is not None and cached_mtime_int is not None:
                    size_same = cached_size_int == int(current_size_bytes)
                    mtime_same = cached_mtime_int == int(current_mtime_ns)
                    if size_same and mtime_same:
                        file_is_up_to_date = True

                if file_is_up_to_date:
                    cached_up_to_date_file_path_set.add(cached_file_path)

                    for cached_row in cached_rows:
                        cached_row['size_bytes'] = int(current_size_bytes)
                        cached_row['file_mtime_ns'] = int(current_mtime_ns)
                        filtered_cached_metadata_list.append(normalize_language_fields_in_metadata(cached_row))
                else:
                    changed_file_path_count = changed_file_path_count + 1
                    if DEBUG_MODE:
                        logger.info(f'检测到字体文件已变化，将重新解析: {cached_file_path}')
            else:
                removed_file_path_count = removed_file_path_count + 1
                if DEBUG_MODE:
                    logger.debug(f'缓存中的字体文件在系统中不存在或不可读，将忽略: {cached_file_path}')

    if DEBUG_MODE:
        logger.info(
            f'缓存统计: cached_files={intcomma(cached_file_path_count)} '
            f'up_to_date={intcomma(len(cached_up_to_date_file_path_set))} '
            f'changed={intcomma(changed_file_path_count)} '
            f'removed={intcomma(removed_file_path_count)}'
        )

    missing_or_changed_font_file_list = []
    for font_file_path in font_file_path_list:
        is_cached_ok = font_file_path in cached_up_to_date_file_path_set
        if not is_cached_ok:
            missing_or_changed_font_file_list.append(font_file_path)

    if DEBUG_MODE:
        logger.info(f'需要解析的字体文件数量（新增或变化）: {intcomma(len(missing_or_changed_font_file_list))}')

    new_metadata_list = []
    if missing_or_changed_font_file_list:
        parse_started_timestamp = time()

        for font_file_path in missing_or_changed_font_file_list:
            if DEBUG_MODE:
                logger.debug(f'解析字体文件: {font_file_path}')

            metadata_list_for_file = get_font_file_metadata(font_file_path)
            for font_metadata in metadata_list_for_file:
                new_metadata_list.append(normalize_language_fields_in_metadata(font_metadata))

        parse_elapsed_seconds = time() - parse_started_timestamp
        parse_elapsed_text = format_duration_for_display(parse_elapsed_seconds)
        if DEBUG_MODE:
            logger.success(
                f'增量解析完成，新增/变化记录数: {intcomma(len(new_metadata_list))} (耗时: {parse_elapsed_text})')
    else:
        if DEBUG_MODE:
            logger.success('缓存已完全命中：无新增字体文件、无变化字体文件，无需解析')

    all_metadata_list = []
    for cached_metadata in filtered_cached_metadata_list:
        all_metadata_list.append(cached_metadata)
    for new_metadata in new_metadata_list:
        all_metadata_list.append(new_metadata)

    metadata_dataframe = convert_metadata_list_to_dataframe(all_metadata_list)

    write_started_timestamp = time()

    if DEBUG_MODE:
        logger.info(f'写入字体元数据缓存表格: {font_csv}，记录数: {intcomma(metadata_dataframe.shape[0])}')

    metadata_dataframe.to_csv(
        font_csv,
        index=False,
        encoding=CSV_ENCODING,
        quoting=CSV_QUOTING_MODE,
        escapechar=CSV_ESCAPE_CHAR,
    )

    write_elapsed_seconds = time() - write_started_timestamp
    write_elapsed_text = format_duration_for_display(write_elapsed_seconds)

    file_size_bytes = 0
    cache_exists = font_csv.exists()
    if cache_exists:
        file_size_bytes = int(os.stat(str(font_csv)).st_size)
    file_size_text = format_size_for_display(file_size_bytes)

    elapsed_seconds = time() - started_timestamp
    elapsed_text = format_duration_for_display(elapsed_seconds)

    if DEBUG_MODE:
        logger.success(
            f'字体元数据加载完成，总记录数: {intcomma(len(all_metadata_list))} '
            f'(写入耗时: {write_elapsed_text} 缓存大小: {file_size_text} 总耗时: {elapsed_text})'
        )

    return all_metadata_list


def load_all_fonts_metadata(font_directory_list):
    """
    懒加载全局字体元数据（统一对外入口）。
    """
    font_directory_signature = get_font_directory_signature(font_directory_list)
    all_metadata_list = load_all_fonts_metadata_cached(font_directory_signature)

    if DEBUG_MODE:
        logger.debug(f'从缓存加载函数中得到字体实例数量: {intcomma(len(all_metadata_list))}')

    return all_metadata_list


# =============================================================================
# 字体匹配与搜索相关函数
# =============================================================================


def get_target_identifiers(kind):
    """
    根据字体类型 kind 获取匹配规则（文件名集合与关键字列表）。

    返回：
        dict（调用方需要按 key 读取 filenames/keywords，因此这里返回 dict）
    """
    identifiers = {'filenames': set(), 'keywords': []}

    kind_exists = kind in FONT_IDENTIFIERS
    if kind_exists:
        identifiers = FONT_IDENTIFIERS[kind]
        if DEBUG_MODE:
            filenames_count = len(identifiers['filenames'])
            keywords_count = len(identifiers['keywords'])
            logger.debug(
                f'获取匹配规则 kind={kind} filenames={intcomma(filenames_count)} keywords={intcomma(keywords_count)}'
            )
    else:
        logger.warning(f'未知字体类型 kind={kind}，将返回空规则')

    return identifiers


def get_target_filenames(kind):
    """
    仅根据 kind 返回预设的“目标文件名集合”（统一转小写）。
    """
    identifiers = get_target_identifiers(kind)

    filename_set = set()
    for filename in identifiers['filenames']:
        filename_set.add(str(filename).lower())

    if DEBUG_MODE:
        logger.debug(f'kind={kind} 的目标文件名数量: {intcomma(len(filename_set))}')

    return filename_set


def normalize_name_for_precise_match(name_text):
    """
    将名称规整为便于精确匹配的形式（严格，不做模糊）：
        - 转小写
        - 去掉空格、下划线、连字符
    """
    normalized_text = ''
    if name_text:
        normalized_text_candidate = str(name_text).lower()
        normalized_text_candidate = normalized_text_candidate.replace(' ', '')
        normalized_text_candidate = normalized_text_candidate.replace('_', '')
        normalized_text_candidate = normalized_text_candidate.replace('-', '')
        normalized_text = normalized_text_candidate

    return normalized_text


def find_fonts_by_kind(all_fonts_metadata, kind):
    """
    从全量字体元数据中，筛选出符合 kind 要求的字体实例列表。

    筛选规则：
        1) 文件名命中预设 filenames
        2) 或者 PS/Family/Full/File 任意字段包含 keywords
    """
    identifiers = get_target_identifiers(kind)

    target_filenames = set()
    for filename in identifiers['filenames']:
        target_filenames.add(str(filename).lower())

    target_keywords = []
    for keyword in identifiers['keywords']:
        target_keywords.append(str(keyword))

    matched_fonts = []

    if DEBUG_MODE:
        logger.info(f'开始匹配字体 kind={kind}')

    for font_metadata in all_fonts_metadata:
        is_match = False

        is_valid_font = bool(font_metadata['is_valid'])
        if is_valid_font:
            file_name_lower = str(font_metadata['file_name']).lower()

            if target_filenames and file_name_lower in target_filenames:
                is_match = True
            else:
                if target_keywords:
                    combined_text = (
                        f'{font_metadata["postscript_name"]} '
                        f'{font_metadata["family_name"]} '
                        f'{font_metadata["full_name"]} '
                        f'{font_metadata["file_name"]}'
                    ).lower()

                    combined_text_clean = combined_text.replace(' ', '')

                    for keyword in target_keywords:
                        keyword_clean = str(keyword).replace(' ', '').lower()
                        if keyword_clean:
                            keyword_hit = keyword_clean in combined_text_clean
                            if keyword_hit:
                                is_match = True
                                break

        if is_match:
            matched_fonts.append(font_metadata)

    if DEBUG_MODE:
        logger.success(f'kind={kind} 匹配到字体实例数量: {intcomma(len(matched_fonts))}')

    return matched_fonts


def filter_fonts_by_precise_name(all_fonts_metadata, precise_name_text):
    """
    精确名称搜索：
        - 对比 PostScript / Family / FullName / 文件名 / 文件 stem（无扩展名）
        - 任一字段规范化后完全相等即命中
    """
    matched_font_list = []

    normalized_precise_text = normalize_name_for_precise_match(precise_name_text)

    if DEBUG_MODE:
        logger.info(f'开始精确名称搜索: {precise_name_text}')

    for font_metadata in all_fonts_metadata:
        file_name_str = str(font_metadata['file_name'])
        postscript_name_text = str(font_metadata['postscript_name'])
        family_name_text = str(font_metadata['family_name'])
        full_name_text = str(font_metadata['full_name'])

        normalized_postscript_name_text = normalize_name_for_precise_match(postscript_name_text)
        normalized_family_name_text = normalize_name_for_precise_match(family_name_text)
        normalized_full_name_text = normalize_name_for_precise_match(full_name_text)

        file_stem_text = Path(file_name_str).stem
        normalized_file_name_text = normalize_name_for_precise_match(file_name_str)
        normalized_file_stem_text = normalize_name_for_precise_match(file_stem_text)

        is_match = False
        if normalized_precise_text == normalized_postscript_name_text:
            is_match = True
        elif normalized_precise_text == normalized_family_name_text:
            is_match = True
        elif normalized_precise_text == normalized_full_name_text:
            is_match = True
        elif normalized_precise_text == normalized_file_stem_text:
            is_match = True
        elif normalized_precise_text == normalized_file_name_text:
            is_match = True

        if is_match:
            matched_font_list.append(font_metadata)

    if DEBUG_MODE:
        logger.success(f'精确名称搜索 [{precise_name_text}] 匹配到字体实例数量: {intcomma(len(matched_font_list))}')

    return matched_font_list


def kind2fontpaths(font_directory_list, target_filename_set):
    """
    基于“目标文件名集合”快速筛选字体元数据实例列表。
    """
    matched_metadata_list = []

    all_fonts_metadata = load_all_fonts_metadata(font_directory_list)

    for font_metadata in all_fonts_metadata:
        file_name_lower = str(font_metadata['file_name']).lower()
        is_target = file_name_lower in target_filename_set
        if is_target:
            matched_metadata_list.append(font_metadata)

    if DEBUG_MODE:
        logger.info(f'基于文件名集合筛选到字体实例数量: {intcomma(len(matched_metadata_list))}')

    return matched_metadata_list


def build_search_keyword_list(keyword_text):
    """
    根据用户输入构建搜索关键字序列（严格子串匹配，不做模糊）。

    规则：
        1) 原始关键字必加入
        2) 以“字体”结尾 -> 追加去掉“字体”的版本
        3) 以“体”结尾 -> 追加去掉“体”的版本
        4) 若输入与某个 kind 的关键字精确相等，则将该 kind 的全部关键字加入
    """
    search_keyword_list = []

    base_keyword = str(keyword_text)
    search_keyword_list.append(base_keyword)

    refined_keyword_list = []

    if keyword_text.endswith('字体'):
        if len(keyword_text) > 2:
            refined_keyword_list.append(keyword_text[:-2])
    elif keyword_text.endswith('体'):
        if len(keyword_text) > 1:
            refined_keyword_list.append(keyword_text[:-1])

    for refined_keyword in refined_keyword_list:
        already_exists = refined_keyword in search_keyword_list
        if not already_exists:
            search_keyword_list.append(refined_keyword)

    normalized_input_text = str(keyword_text).replace(' ', '').lower()

    for kind_name in FONT_IDENTIFIERS.keys():
        identifiers = FONT_IDENTIFIERS[kind_name]
        keyword_list_in_kind = identifiers['keywords']

        for defined_keyword in keyword_list_in_kind:
            defined_clean = str(defined_keyword).replace(' ', '').lower()
            if normalized_input_text == defined_clean:
                for related_keyword in keyword_list_in_kind:
                    already_in_list = related_keyword in search_keyword_list
                    if not already_in_list:
                        search_keyword_list.append(related_keyword)

    if DEBUG_MODE:
        keyword_display_text = ', '.join(search_keyword_list)
        logger.debug(f'关键字 [{keyword_text}] 最终搜索序列: {keyword_display_text}')

    return search_keyword_list


def search_fonts_by_keyword(all_fonts_metadata, keyword_text):
    """
    通用关键字搜索（严格子串匹配）。

    返回:
        matched_font_list, best_font_metadata
    """
    matched_font_list = []
    best_font_metadata = None

    search_keyword_list = build_search_keyword_list(keyword_text)

    normalized_search_keyword_list = []
    for raw_keyword in search_keyword_list:
        cleaned_keyword = str(raw_keyword).replace(' ', '').lower()
        normalized_search_keyword_list.append(cleaned_keyword)

    if DEBUG_MODE:
        logger.info(f'执行关键字搜索: {keyword_text} (关键字序列数量: {intcomma(len(normalized_search_keyword_list))})')

    for font_metadata in all_fonts_metadata:
        combined_text = (
            f'{font_metadata["postscript_name"]} '
            f'{font_metadata["family_name"]} '
            f'{font_metadata["full_name"]} '
            f'{font_metadata["file_name"]}'
        )

        combined_text_lower = combined_text.lower()
        combined_text_clean = combined_text_lower.replace(' ', '')

        is_match = False
        for normalized_keyword in normalized_search_keyword_list:
            if normalized_keyword:
                keyword_hit = normalized_keyword in combined_text_clean
                if keyword_hit:
                    is_match = True
                    break

        if is_match:
            matched_font_list.append(font_metadata)

    if matched_font_list:
        if DEBUG_MODE:
            search_table = PrettyTable()
            search_table.field_names = [
                'PS Name',
                'Family',
                'Subfamily',
                'Wt.',
                'Type',
                'GBK',
                'LangCnt',
                'Langs',
                'Size',
                'File',
            ]
            search_table.align = 'l'

            for font_metadata in matched_font_list:
                support_gbk_flag = bool(font_metadata['support_gbk'])
                gbk_flag_text = 'Y' if support_gbk_flag else 'N'

                size_bytes = int(font_metadata['size_bytes'])
                friendly_size_text = format_size_for_display(size_bytes)

                lang_name_list = get_language_list_from_codepages(
                    font_metadata['codepage_range1'],
                    font_metadata['codepage_range2'],
                )
                language_count_int = len(lang_name_list)

                short_language_list = lang_name_list
                if len(short_language_list) > 3:
                    truncated_list = short_language_list[:3]
                    truncated_list.append('...')
                    short_language_list = truncated_list

                language_desc_text = ','.join(short_language_list)

                search_table.add_row(
                    [
                        font_metadata['postscript_name'],
                        font_metadata['family_name'],
                        font_metadata['subfamily_name'],
                        font_metadata['weight_class'],
                        font_metadata['weight_type'],
                        gbk_flag_text,
                        language_count_int,
                        language_desc_text,
                        friendly_size_text,
                        font_metadata['file_name'],
                    ]
                )

            logger.info(f'--- 关键字搜索结果 (关键字: {keyword_text}) 共 {intcomma(len(matched_font_list))} 个实例 ---')
            search_table_text = search_table.get_string()
            for table_line in search_table_text.split('\n'):
                logger.info(table_line)

        best_font_metadata = choose_best_font(matched_font_list, 'Regular')
        if best_font_metadata is not None:
            if DEBUG_MODE:
                logger.success(f'关键字 [{keyword_text}] 选择到最佳 Regular 字体: {best_font_metadata["file_name"]}')
    else:
        logger.warning(f'关键字搜索未找到字体: {keyword_text}')

    return matched_font_list, best_font_metadata


def search_and_choose_font_by_keyword(all_fonts_metadata, keyword_text, target_weight_type):
    """
    先关键字搜索，再按目标字重选择得分最高的字体实例。
    """
    best_metadata = None

    matched_font_list, best_regular_font_metadata = search_fonts_by_keyword(all_fonts_metadata, keyword_text)

    if matched_font_list:
        if target_weight_type == 'Regular':
            if best_regular_font_metadata is not None:
                best_metadata = best_regular_font_metadata
            else:
                best_metadata = choose_best_font(matched_font_list, target_weight_type)
        elif target_weight_type == 'Bold':
            best_metadata = choose_best_font(matched_font_list, target_weight_type)
        elif target_weight_type == 'Light':
            best_metadata = choose_best_font(matched_font_list, target_weight_type)
        else:
            best_metadata = choose_best_font(matched_font_list, target_weight_type)

        if best_metadata is not None:
            if DEBUG_MODE:
                logger.success(
                    f'关键字 [{keyword_text}] 选择到最佳 {target_weight_type} 字重字体: {best_metadata["file_name"]}'
                )

    return best_metadata


# =============================================================================
# 字体评分与选择相关函数
# =============================================================================


def calculate_font_score(font_metadata, target_weight_type):
    """
    为字体实例打分，分数越高越符合目标字重，用于候选字体择优。
    """
    score_value = -1000.0

    if font_metadata:
        score_value = 0.0

        weight_class_value = font_metadata['weight_class']
        normalized_weight_value = 400
        if pd.isna(weight_class_value):
            normalized_weight_value = 400
        else:
            normalized_weight_value = int(weight_class_value)

        target_weight_value = 400
        if target_weight_type == 'Light':
            target_weight_value = 300
        elif target_weight_type == 'Bold':
            target_weight_value = 700
        else:
            target_weight_value = 400

        current_weight_type = font_metadata['weight_type']

        if current_weight_type == target_weight_type:
            score_value = score_value + 200.0
        else:
            if target_weight_type == 'Regular' and current_weight_type in ['Light', 'Bold']:
                score_value = score_value + 40.0
            elif target_weight_type in ['Light', 'Bold'] and current_weight_type == 'Regular':
                score_value = score_value - 40.0
            else:
                score_value = score_value - 80.0

        combined_name_text = (
            f'{font_metadata["postscript_name"]} '
            f'{font_metadata["family_name"]} '
            f'{font_metadata["full_name"]} '
            f'{font_metadata["file_name"]}'
        )
        combined_name_lower = combined_name_text.lower()
        combined_name_no_space = combined_name_lower.replace(' ', '')

        weight_match = search(r'w([1-9])', combined_name_lower)
        if weight_match:
            w_number_text = weight_match.group(1)
            w_number = int(w_number_text)

            if w_number <= 3 and target_weight_type == 'Light':
                score_value = score_value + 120.0
            elif 4 <= w_number <= 6 and target_weight_type == 'Regular':
                score_value = score_value + 120.0
            elif w_number >= 7 and target_weight_type == 'Bold':
                score_value = score_value + 160.0

            if w_number > 0:
                normalized_weight_value = w_number * 100

        if target_weight_type == 'Light':
            if (
                    'light' in combined_name_lower
                    or 'thin' in combined_name_lower
                    or 'ultra light' in combined_name_lower
                    or 'hairline' in combined_name_lower
                    or 'extra light' in combined_name_lower
            ):
                score_value = score_value + 80.0

            if (
                    '特细' in combined_name_no_space
                    or '极细' in combined_name_no_space
                    or '超细' in combined_name_no_space
                    or '纤细' in combined_name_no_space
                    or '细体' in combined_name_no_space
                    or '轻' in combined_name_no_space
            ):
                score_value = score_value + 80.0

        elif target_weight_type == 'Bold':
            if (
                    'bold' in combined_name_lower
                    or 'black' in combined_name_lower
                    or 'heavy' in combined_name_lower
                    or 'extrabold' in combined_name_lower
                    or 'extra bold' in combined_name_lower
                    or 'semibold' in combined_name_lower
                    or 'demibold' in combined_name_lower
            ):
                score_value = score_value + 80.0

            if (
                    '粗体' in combined_name_no_space
                    or '中黑' in combined_name_no_space
                    or '粗黑' in combined_name_no_space
                    or '特黑' in combined_name_no_space
                    or '准黑' in combined_name_no_space
                    or '黑体' in combined_name_no_space
            ):
                score_value = score_value + 80.0

        else:
            if (
                    'regular' in combined_name_lower
                    or 'normal' in combined_name_lower
                    or 'book' in combined_name_lower
                    or 'roman' in combined_name_lower
            ):
                score_value = score_value + 60.0

            if (
                    '常规' in combined_name_no_space
                    or '标准' in combined_name_no_space
                    or '中等' in combined_name_no_space
                    or '普通' in combined_name_no_space
            ):
                score_value = score_value + 60.0

        weight_difference = abs(normalized_weight_value - target_weight_value)
        score_value = score_value - weight_difference * 1.5

        size_bytes_value = font_metadata['size_bytes']
        size_bytes = 0
        if pd.isna(size_bytes_value):
            size_bytes = 0
        else:
            size_bytes = int(size_bytes_value)

        if size_bytes > 0:
            size_mebibytes = float(size_bytes) / (1024.0 * 1024.0)
            score_value = score_value + size_mebibytes * 3.0

        is_variable_font = bool(font_metadata['is_variable'])
        if is_variable_font:
            score_value = score_value - 30.0

        postscript_name_lower = str(font_metadata['postscript_name']).lower()
        family_name_lower = str(font_metadata['family_name']).lower()
        file_name_lower = str(font_metadata['file_name']).lower()

        if (
                'msyh' in file_name_lower
                or 'microsoft yahei' in postscript_name_lower
                or 'microsoft yahei' in family_name_lower
        ):
            if target_weight_type == 'Bold':
                if 'bd' in file_name_lower or 'bold' in postscript_name_lower:
                    score_value = score_value + 200.0
            elif target_weight_type == 'Light':
                if 'l' in file_name_lower or 'light' in postscript_name_lower:
                    score_value = score_value + 200.0
            else:
                score_value = score_value + 80.0

        if 'pingfang' in postscript_name_lower or 'pingfang' in family_name_lower or 'pingfang' in file_name_lower:
            if target_weight_type == 'Light':
                if 'light' in postscript_name_lower or 'ultralight' in postscript_name_lower:
                    score_value = score_value + 80.0
            elif target_weight_type == 'Bold':
                if 'semibold' in postscript_name_lower or 'bold' in postscript_name_lower:
                    score_value = score_value + 80.0
            else:
                score_value = score_value + 40.0

        support_gbk_flag = bool(font_metadata['support_gbk'])
        if support_gbk_flag:
            score_value = score_value + 200.0

        is_simplified_font = False
        is_traditional_font = False

        if '简' in combined_name_text:
            is_simplified_font = True
        if '繁' in combined_name_text:
            is_traditional_font = True

        if (
                ' sc' in combined_name_lower
                or '-sc' in combined_name_lower
                or 'sc-' in combined_name_lower
                or 'sc_' in combined_name_lower
        ):
            is_simplified_font = True
        if 'schinese' in combined_name_lower or 's chinese' in combined_name_lower:
            is_simplified_font = True

        if (
                ' tc' in combined_name_lower
                or '-tc' in combined_name_lower
                or 'tc-' in combined_name_lower
                or 'tc_' in combined_name_lower
        ):
            is_traditional_font = True
        if (
                'tw' in combined_name_lower
                or ' hk' in combined_name_lower
                or '-hk' in combined_name_lower
                or 'hk-' in combined_name_lower
        ):
            is_traditional_font = True
        if 'hkscs' in combined_name_lower:
            is_traditional_font = True
        if 't chinese' in combined_name_lower or 'chinese t' in combined_name_lower:
            is_traditional_font = True

        if support_gbk_flag:
            if is_simplified_font and not is_traditional_font:
                score_value = score_value + 40.0
            elif is_traditional_font and not is_simplified_font:
                score_value = score_value + 10.0
            elif is_simplified_font and is_traditional_font:
                score_value = score_value + 20.0

        family_name_length = len(str(font_metadata['family_name']))
        if family_name_length > 0:
            score_value = score_value - family_name_length * 0.5

        italic_flag = bool(font_metadata['italic_flag'])
        if italic_flag:
            score_value = score_value - 20.0

    if DEBUG_MODE:
        file_name_for_log = ''
        if font_metadata:
            file_name_for_log = font_metadata['file_name']
        logger.debug(f'评分 target={target_weight_type} score={score_value:.2f} file={file_name_for_log}')

    return score_value


def choose_best_font(font_metadata_list, target_weight_type):
    """
    根据目标字重在候选列表中选择得分最高的字体实例。
    """
    best_font_metadata = None

    scored_font_list = []
    for font_metadata in font_metadata_list:
        score_value = calculate_font_score(font_metadata, target_weight_type)
        scored_font_list.append((score_value, font_metadata))

    scored_font_list.sort(key=lambda item: item[0], reverse=True)

    if scored_font_list:
        best_font_metadata = scored_font_list[0][1]

        if DEBUG_MODE:
            score_table = PrettyTable()
            score_table.field_names = [
                'Score',
                'WeightClass',
                'WeightType',
                'GBK',
                'LangCnt',
                'Size',
                'Family',
                'Subfamily',
                'PS Name',
                'File',
            ]
            score_table.align = 'l'

            for score_value, font_metadata in scored_font_list:
                support_gbk_flag = bool(font_metadata['support_gbk'])
                gbk_flag_text = 'Y' if support_gbk_flag else 'N'

                size_bytes = int(font_metadata['size_bytes'])
                friendly_size_text = format_size_for_display(size_bytes)

                language_count_value = int(font_metadata['language_count'])

                var_text = 'Y' if bool(font_metadata['is_variable']) else 'N'

                score_table.add_row(
                    [
                        f'{score_value:.2f}',
                        font_metadata['weight_class'],
                        font_metadata['weight_type'],
                        gbk_flag_text,
                        language_count_value,
                        friendly_size_text,
                        font_metadata['family_name'],
                        font_metadata['subfamily_name'],
                        font_metadata['postscript_name'],
                        font_metadata['file_name'],
                    ]
                )

            logger.info(f'候选字体得分列表（目标字重: {target_weight_type}，按分数从高到低）')
            score_table_text = score_table.get_string()
            for table_line in score_table_text.split('\n'):
                logger.info(table_line)

            best_score_value = scored_font_list[0][0]
            logger.success(
                f'为字重 {target_weight_type} 选出的最高分字体: {best_font_metadata["file_name"]}，score={best_score_value:.2f}'
            )

    return best_font_metadata


def choose_regular_font(font_metadata_list):
    """
    选择最佳 Regular 字重字体，返回字体文件路径字符串。
    """
    best_font_path = None

    best_font_metadata = choose_best_font(font_metadata_list, 'Regular')
    if best_font_metadata is not None:
        best_font_path = best_font_metadata['file_path']

    if DEBUG_MODE and best_font_metadata is not None:
        logger.success(f'选择到 Regular 字体: {best_font_metadata["file_name"]}')

    return best_font_path


def choose_bold_font(font_metadata_list):
    """
    选择最佳 Bold 字重字体，返回字体文件路径字符串。
    """
    best_font_path = None

    best_font_metadata = choose_best_font(font_metadata_list, 'Bold')
    if best_font_metadata is not None:
        best_font_path = best_font_metadata['file_path']

    if DEBUG_MODE and best_font_metadata is not None:
        logger.success(f'选择到 Bold 字体: {best_font_metadata["file_name"]}')

    return best_font_path


def choose_light_font(font_metadata_list):
    """
    选择最佳 Light 字重字体，返回字体文件路径字符串。
    """
    best_font_path = None

    best_font_metadata = choose_best_font(font_metadata_list, 'Light')
    if best_font_metadata is not None:
        best_font_path = best_font_metadata['file_path']

    if DEBUG_MODE and best_font_metadata is not None:
        logger.success(f'选择到 Light 字体: {best_font_metadata["file_name"]}')

    return best_font_path


# =============================================================================
# 语言覆盖分析相关函数
# =============================================================================


def split_language_list_text(language_list_text):
    """
    将元数据中的 language_list 字符串拆分为语言名称列表。
    """
    lang_name_list = []

    if pd.isna(language_list_text):
        lang_name_list = []
    else:
        language_list_string = str(language_list_text)
        raw_language_list = language_list_string.split('|')

        for language_text in raw_language_list:
            stripped_language_text = str(language_text).strip()
            if stripped_language_text:
                lang_name_list.append(stripped_language_text)

    return lang_name_list


def get_fonts_with_most_languages(all_fonts_metadata, minimum_language_count, maximum_font_count):
    """
    找出支持语言数量最多的一批字体（按代码页数量粗略估计）。
    """
    language_and_font_list = []

    for font_metadata in all_fonts_metadata:
        language_count_value = font_metadata['language_count']
        language_count_int = 0
        if pd.isna(language_count_value):
            language_count_int = 0
        else:
            language_count_int = int(language_count_value)

        meets_minimum = language_count_int >= int(minimum_language_count)
        if meets_minimum:
            language_and_font_list.append((language_count_int, font_metadata))

    language_and_font_list.sort(key=lambda pair_item: pair_item[0], reverse=True)

    top_font_list = []
    for index_value, language_and_font_pair in enumerate(language_and_font_list):
        within_limit = index_value < int(maximum_font_count)
        if within_limit:
            top_font_list.append(language_and_font_pair[1])

    if DEBUG_MODE:
        logger.info(
            f'语言覆盖筛选: >= {minimum_language_count} 的候选数 {intcomma(len(language_and_font_list))}，'
            f'返回前 {intcomma(len(top_font_list))} 个'
        )

    return top_font_list


def find_multilingual_fonts(all_fonts_metadata):
    """
    查找同时支持「中 / 英 / 日 / 韩 / 俄 / 拉丁」字符集的字体（按代码页粗略估计）。
    """
    multilingual_font_list = []

    chinese_language_group_list = [
        '简体中文 (936, PRC / 新加坡)',
        '繁体中文 (950, 台湾 / 香港)',
    ]
    english_latin_language_group_list = [
        '西欧语言 (Latin-1, 1252)',
    ]
    japanese_language_group_list = [
        '日语 (Shift-JIS, 932)',
    ]
    korean_language_group_list = [
        '韩文 (Wansung, 949)',
        '韩文 (Johab, 1361)',
    ]
    russian_language_group_list = [
        '西里尔字母语言 (1251)',
        'MS-DOS 俄文 (866)',
    ]

    required_language_group_list = [
        chinese_language_group_list,
        english_latin_language_group_list,
        japanese_language_group_list,
        korean_language_group_list,
        russian_language_group_list,
    ]

    if DEBUG_MODE:
        logger.info('开始查找同时支持中英日韩俄拉丁的字体')

    for font_metadata in all_fonts_metadata:
        font_lang_name_list = split_language_list_text(font_metadata['language_list'])

        supports_all_required_groups = True
        for language_group_list in required_language_group_list:
            group_supported = False
            for required_lang_name in language_group_list:
                is_supported = required_lang_name in font_lang_name_list
                if is_supported:
                    group_supported = True

            if not group_supported:
                supports_all_required_groups = False

        if supports_all_required_groups:
            multilingual_font_list.append(font_metadata)

    multilingual_font_list_sorted = sorted(
        multilingual_font_list,
        key=lambda item: int(item['language_count']),
        reverse=True,
    )

    if DEBUG_MODE:
        logger.success(f'查找到满足中英日韩俄拉丁条件的字体数量: {intcomma(len(multilingual_font_list_sorted))}')

    return multilingual_font_list_sorted


def print_top_language_fonts(font_metadata_list, title_name):
    """
    使用 PrettyTable 打印“语言覆盖最广”的一批字体信息。
    """
    if DEBUG_MODE:
        language_table = PrettyTable()
        language_table.field_names = [
            'LangCnt',
            'Family',
            'Subfamily',
            'PS Name',
            'Size',
            'File',
            'Languages',
        ]
        language_table.align = 'l'

        for font_metadata in font_metadata_list:
            size_bytes = int(font_metadata['size_bytes'])
            friendly_size_text = format_size_for_display(size_bytes)

            lang_name_list = get_language_list_from_codepages(
                font_metadata['codepage_range1'],
                font_metadata['codepage_range2'],
            )
            language_count_int = len(lang_name_list)
            language_list_text = ','.join(lang_name_list)

            language_table.add_row(
                [
                    language_count_int,
                    font_metadata['family_name'],
                    font_metadata['subfamily_name'],
                    font_metadata['postscript_name'],
                    friendly_size_text,
                    font_metadata['file_name'],
                    language_list_text,
                ]
            )

        logger.info(f'--- 语言覆盖统计: {title_name} ---')
        table_text = language_table.get_string()
        for table_line in table_text.split('\n'):
            logger.info(table_line)

    return


def print_language_support_for_keyword(keyword_text, matched_font_list, best_font_metadata):
    """
    针对某个关键字（例如 Arial），统计并展示该关键字下所有匹配字体的语言覆盖情况。
    """
    if DEBUG_MODE:
        table = PrettyTable()
        table.field_names = [
            'LangCnt',
            'Family',
            'Subfamily',
            'PS Name',
            'Size',
            'File',
            'Languages',
        ]
        table.align = 'l'

        for font_metadata in matched_font_list:
            size_bytes = int(font_metadata['size_bytes'])
            friendly_size_text = format_size_for_display(size_bytes)

            lang_name_list = get_language_list_from_codepages(
                font_metadata['codepage_range1'],
                font_metadata['codepage_range2'],
            )
            language_count_int = len(lang_name_list)
            language_list_text = '|'.join(lang_name_list)

            table.add_row(
                [
                    language_count_int,
                    font_metadata['family_name'],
                    font_metadata['subfamily_name'],
                    font_metadata['postscript_name'],
                    friendly_size_text,
                    font_metadata['file_name'],
                    language_list_text,
                ]
            )

        logger.info(f'--- 关键字 [{keyword_text}] 的语言覆盖统计，共 {intcomma(len(matched_font_list))} 个实例 ---')
        table_text = table.get_string()
        for table_line in table_text.split('\n'):
            logger.info(table_line)

        if best_font_metadata is not None:
            logger.info(
                f'关键字 [{keyword_text}] 用作 Regular 示例的最佳字体: {best_font_metadata["file_name"]} '
                f'(语言组数量≈{best_font_metadata["language_count"]})'
            )

    return


# =============================================================================
# FontProperties 构建与结果打印相关函数
# =============================================================================


def build_font_properties_from_metadata(font_metadata):
    """
    根据字体元数据构建 matplotlib 的 FontProperties 对象。
    """
    font_file_path_text = str(font_metadata['file_path'])
    font_file_path = Path(font_file_path_text)

    file_exists = font_file_path.exists()
    if not file_exists:
        raise ValueError(f'字体文件不存在，无法构建 FontProperties: {font_file_path}')

    font_properties = FontProperties(fname=str(font_file_path))

    if DEBUG_MODE:
        logger.debug(f'已构建 FontProperties: {font_metadata["file_name"]}')

    return font_properties


def print_font_selection_result(kind, weight_type, font_metadata):
    """
    使用 PrettyTable 打印最终选择结果，并验证可构建 FontProperties。

    日志策略：
        - 成功选择属于信息型输出，默认只在 DEBUG_MODE 下打印
        - 找不到目标字体属于需要关注的情况，用 warning 输出（默认可见）
    """
    if font_metadata is None:
        logger.warning(f'kind={kind} 未找到 {weight_type} 字重的合适字体')
    else:
        if DEBUG_MODE:
            logger.success(f'已为 kind={kind} 选择 {weight_type} 字重字体: {font_metadata["file_name"]}')

        if DEBUG_MODE:
            selection_table = PrettyTable()
            selection_table.field_names = [
                'File',
                'Family',
                'Subfamily',
                'Full Name',
                'PS Name',
                'WeightClass',
                'WeightType',
                'WidthClass',
                'GBK',
                'LangCnt',
                'Variable',
                'Italic',
                'CollectionIndex',
                'IsCollection',
                'Size',
            ]
            selection_table.align = 'l'

            support_gbk_flag = bool(font_metadata['support_gbk'])
            gbk_flag_text = 'Y' if support_gbk_flag else 'N'

            friendly_size_text = format_size_for_display(int(font_metadata['size_bytes']))
            language_count_int = int(font_metadata['language_count'])

            is_variable_text = 'Y' if bool(font_metadata['is_variable']) else 'N'
            italic_text = 'Y' if bool(font_metadata['italic_flag']) else 'N'
            is_collection_text = 'Y' if bool(font_metadata['is_collection']) else 'N'

            selection_table.add_row(
                [
                    font_metadata['file_name'],
                    font_metadata['family_name'],
                    font_metadata['subfamily_name'],
                    font_metadata['full_name'],
                    font_metadata['postscript_name'],
                    font_metadata['weight_class'],
                    font_metadata['weight_type'],
                    font_metadata['width_class'],
                    gbk_flag_text,
                    language_count_int,
                    is_variable_text,
                    italic_text,
                    font_metadata['collection_index'],
                    is_collection_text,
                    friendly_size_text,
                ]
            )

            table_text = selection_table.get_string()
            for table_line in table_text.split('\n'):
                logger.info(table_line)

        build_font_properties_from_metadata(font_metadata)

    return


def print_search_summary(kind, font_metadata_list):
    """
    打印某一类字体的搜索汇总表。
    """
    if DEBUG_MODE:
        table = PrettyTable()
        table.field_names = [
            'PS Name',
            'Family',
            'Subfamily',
            'Wt.',
            'Type',
            'GBK',
            'LangCnt',
            'Var',
            'Size',
            'File',
        ]
        table.align = 'l'

        sorted_list = sorted(
            font_metadata_list,
            key=lambda item: (int(item['weight_class']), str(item['family_name'])),
        )

        for font_metadata in sorted_list:
            support_gbk_flag = bool(font_metadata['support_gbk'])
            gbk_flag_text = 'Y' if support_gbk_flag else 'N'

            friendly_size_text = format_size_for_display(int(font_metadata['size_bytes']))
            language_count_int = int(font_metadata['language_count'])
            var_text = 'Y' if bool(font_metadata['is_variable']) else 'N'

            table.add_row(
                [
                    font_metadata['postscript_name'],
                    font_metadata['family_name'],
                    font_metadata['subfamily_name'],
                    font_metadata['weight_class'],
                    font_metadata['weight_type'],
                    gbk_flag_text,
                    language_count_int,
                    var_text,
                    friendly_size_text,
                    font_metadata['file_name'],
                ]
            )

        logger.info(f'--- 搜索结果: {kind} (共 {intcomma(len(font_metadata_list))} 个实例) ---')
        table_text = table.get_string()
        for table_line in table_text.split('\n'):
            logger.info(table_line)

    return


# =============================================================================
# 报表输出：把“每个 kind 的最佳字体路径”导出为 CSV
# =============================================================================


def build_selected_fonts_dataframe(all_fonts_metadata, kind_list):
    """
    为每个 kind 选择 Light/Regular/Bold 三种字重的最佳字体，输出为 DataFrame。

    输出列：
        kind, weight_type, file_path, file_name, family_name, subfamily_name, postscript_name,
        weight_class, width_class, support_gbk, language_count, is_variable, italic_flag,
        is_collection, collection_index
    """
    record_list = []

    for kind in kind_list:
        candidates = find_fonts_by_kind(all_fonts_metadata, kind)

        regular_metadata = choose_best_font(candidates, 'Regular')
        bold_metadata = choose_best_font(candidates, 'Bold')
        light_metadata = choose_best_font(candidates, 'Light')

        weight_task_list = [
            ('Regular', regular_metadata),
            ('Bold', bold_metadata),
            ('Light', light_metadata),
        ]

        for weight_type, font_metadata in weight_task_list:
            if font_metadata is not None:
                record_dict = {
                    'kind': kind,
                    'weight_type': weight_type,
                    'file_path': font_metadata['file_path'],
                    'file_name': font_metadata['file_name'],
                    'family_name': font_metadata['family_name'],
                    'subfamily_name': font_metadata['subfamily_name'],
                    'postscript_name': font_metadata['postscript_name'],
                    'weight_class': int(font_metadata['weight_class']),
                    'width_class': int(font_metadata['width_class']),
                    'support_gbk': bool(font_metadata['support_gbk']),
                    'language_count': int(font_metadata['language_count']),
                    'is_variable': bool(font_metadata['is_variable']),
                    'italic_flag': bool(font_metadata['italic_flag']),
                    'is_collection': bool(font_metadata['is_collection']),
                    'collection_index': int(font_metadata['collection_index']),
                }
                record_list.append(record_dict)

    selected_dataframe = pd.DataFrame(record_list)

    if not selected_dataframe.empty:
        selected_dataframe = selected_dataframe.sort_values(by=['kind', 'weight_type'], ascending=True).reset_index(
            drop=True
        )

    return selected_dataframe


def save_dataframe_to_csv(dataframe_object, output_csv):
    """
    将 DataFrame 保存为 UTF-8 CSV。
    """
    dataframe_object.to_csv(
        output_csv,
        index=False,
        encoding=CSV_ENCODING,
        quoting=CSV_QUOTING_MODE,
        escapechar=CSV_ESCAPE_CHAR,
    )

    return


def export_all_fonts_metadata_report(all_fonts_metadata, output_path):
    """
    导出全量字体元数据报表（便于用户直接打开查看）。

    说明：
        - 缓存 CSV 主要用于加速扫描，位置可能较深
        - 报表 CSV 放在 UserDataFolder 根目录，并可选复制到 Android 公共 Downloads

    日志策略：
        - 导出成功属于信息型输出，默认只在 DEBUG_MODE 下输出
        - 复制失败（目录不可写）使用 warning 输出（默认可见）
    """
    started_timestamp = time()

    metadata_dataframe = convert_metadata_list_to_dataframe(all_fonts_metadata)
    save_dataframe_to_csv(metadata_dataframe, output_path)

    elapsed_seconds = time() - started_timestamp
    elapsed_text = format_duration_for_display(elapsed_seconds)

    if DEBUG_MODE:
        logger.success(
            f'已导出全量字体元数据报表: {output_path} (记录数: {intcomma(metadata_dataframe.shape[0])} 耗时: {elapsed_text})'
        )

    if COPY_REPORTS_TO_ANDROID_DOWNLOADS and ANDROID_PUBLIC_REPORT_FOLDER is not None:
        copy_report_to_directory(output_path, ANDROID_PUBLIC_REPORT_FOLDER)

    return


def export_selected_fonts_report(all_fonts_metadata, kind_list, output_path):
    """
    导出每个 kind 的 Light/Regular/Bold 最佳字体选择结果。
    """
    started_timestamp = time()

    selected_dataframe = build_selected_fonts_dataframe(all_fonts_metadata, kind_list)
    save_dataframe_to_csv(selected_dataframe, output_path)

    elapsed_seconds = time() - started_timestamp
    elapsed_text = format_duration_for_display(elapsed_seconds)

    if DEBUG_MODE:
        logger.success(
            f'已导出字体选择报表: {output_path} (记录数: {intcomma(selected_dataframe.shape[0])} 耗时: {elapsed_text})'
        )

    if COPY_REPORTS_TO_ANDROID_DOWNLOADS and ANDROID_PUBLIC_REPORT_FOLDER is not None:
        copy_report_to_directory(output_path, ANDROID_PUBLIC_REPORT_FOLDER)

    return


def export_multilingual_fonts_report(all_fonts_metadata, output_path):
    """
    导出“中英日韩俄拉丁”多语种字体列表。
    """
    started_timestamp = time()

    multilingual_font_list = find_multilingual_fonts(all_fonts_metadata)
    multilingual_dataframe = convert_metadata_list_to_dataframe(multilingual_font_list)
    save_dataframe_to_csv(multilingual_dataframe, output_path)

    elapsed_seconds = time() - started_timestamp
    elapsed_text = format_duration_for_display(elapsed_seconds)

    if DEBUG_MODE:
        logger.success(
            f'已导出多语种字体列表: {output_path} (记录数: {intcomma(multilingual_dataframe.shape[0])} 耗时: {elapsed_text})'
        )

    if COPY_REPORTS_TO_ANDROID_DOWNLOADS and ANDROID_PUBLIC_REPORT_FOLDER is not None:
        copy_report_to_directory(output_path, ANDROID_PUBLIC_REPORT_FOLDER)

    return


if __name__ == '__main__':
    DEBUG_MODE = True

    script_started_timestamp = time()

    logger.info(f'脚本: {SCRIPT_TITLE_CN} | {SCRIPT_TITLE_EN} | v{SCRIPT_VERSION}')
    logger.info(f'运行平台: {PLATFORM_SYSTEM}  Android={IS_ANDROID}  开发标记: dev={IS_DEV} dup={IS_DUP}')

    if IS_ANDROID:
        logger.info('当前为 Android 运行环境')
        if ANDROID_PUBLIC_DOWNLOADS is not None:
            logger.info(f'Android 公共下载目录: {ANDROID_PUBLIC_DOWNLOADS}')
        else:
            logger.warning('未能定位 Android 公共下载目录（不影响字体扫描）')

        if ANDROID_PUBLIC_REPORT_FOLDER is not None:
            logger.info(f'Android 报表输出目录: {ANDROID_PUBLIC_REPORT_FOLDER}')

    font_dirs = get_font_dirs()
    logger.info(f'系统有效字体目录数量: {intcomma(len(font_dirs))}')

    for font_dir_path in font_dirs:
        logger.debug(f'字体目录: {font_dir_path}')

    all_fonts_metadata = load_all_fonts_metadata(font_dirs)
    logger.success(f'系统检测到字体实例数量: {intcomma(len(all_fonts_metadata))}')

    tasks = [
        'roboto',
        'droid_sans_fallback',
        'microsoft_yahei',
        'source_han_sans',
        'pingfang',
        'fz_lanting_hei',
        'fz_zhengzhonghei',
        'fz_zhunyuan',
        'dengxian',
        'fangsong',
        'fz_cusong',
        'fz_qingfangsong',
        'new_simsun',
        'smiley_sans',
        'harmonyos_sans',
        'ali_puhuiti',
        'shouzha',
        'shuidi',
        'zhujie',
        'pixel',
        'xingkai',
        'yuanti',
        'mincho',
        'huakang_lizhonghei',
        'guyinsong',
    ]

    for kind in tasks:
        logger.info(f'开始处理字体类型: {kind}')

        candidates = find_fonts_by_kind(all_fonts_metadata, kind)
        print_search_summary(kind, candidates)

        regular_metadata_for_log = choose_best_font(candidates, 'Regular')
        bold_metadata_for_log = choose_best_font(candidates, 'Bold')
        light_metadata_for_log = choose_best_font(candidates, 'Light')

        print_font_selection_result(kind, 'Regular', regular_metadata_for_log)
        print_font_selection_result(kind, 'Bold', bold_metadata_for_log)
        print_font_selection_result(kind, 'Light', light_metadata_for_log)

    ensure_directory_exists(UserDataFolder)

    if EXPORT_ALL_FONTS_REPORT:
        all_report_path = UserDataFolder / f'all_fonts_metadata_{computer_marker}.csv'
        export_all_fonts_metadata_report(all_fonts_metadata, all_report_path)

    if EXPORT_SELECTED_FONTS_REPORT:
        selected_report_path = UserDataFolder / f'selected_fonts_{computer_marker}.csv'
        export_selected_fonts_report(all_fonts_metadata, tasks, selected_report_path)

    if EXPORT_MULTILINGUAL_FONTS_REPORT:
        multilingual_report_path = UserDataFolder / f'multilingual_fonts_{computer_marker}.csv'
        export_multilingual_fonts_report(all_fonts_metadata, multilingual_report_path)

    logger.info('统计语言覆盖最广的字体（按 CodePage 数量近似）')
    top_language_fonts = get_fonts_with_most_languages(
        all_fonts_metadata,
        minimum_language_count=10,
        maximum_font_count=20,
    )
    print_top_language_fonts(top_language_fonts, '系统中语言覆盖最广的字体（按 CodePage 数量）')

    arial_keyword = 'Arial'
    arial_matched_list, arial_best_font_metadata = search_fonts_by_keyword(all_fonts_metadata, arial_keyword)
    print_language_support_for_keyword(arial_keyword, arial_matched_list, arial_best_font_metadata)

    precise_font_name_text = 'Arial Unicode MS'
    arial_unicode_font_list = filter_fonts_by_precise_name(all_fonts_metadata, precise_font_name_text)
    print_search_summary('precise_search_arial_unicode_ms', arial_unicode_font_list)

    arial_unicode_best_metadata = choose_best_font(arial_unicode_font_list, 'Regular')
    print_font_selection_result('Arial Unicode MS', 'Regular', arial_unicode_best_metadata)

    logger.success('脚本执行完毕')

    script_elapsed_seconds = time() - script_started_timestamp
    script_elapsed_text = format_duration_for_display(script_elapsed_seconds)
    logger.success(f'脚本总耗时: {script_elapsed_text}')
