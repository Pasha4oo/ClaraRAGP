import os

from dotenv import load_dotenv

load_dotenv()

DEBUG=True 
"""
If DEBUG is False

Large VOSK model instead of small (3.44gb vs 87mb, loads much longer and use more RAM, but higher recognition quality)
Compile CORRECTOR model (which can take few seconds and then execute much faster)
Not sends stickers that not in preset packs (ignores standart stickers)
"""

ERROR_TYPE = "ONLINE"
"""
ONLINE/OFFLINE

If there any options, tries to use ONLINE or OFFLINE analogs of functions
"""

CENSOR_WORDS = ["АНОН", "РУСС", "ПЕРЕВ", "РОСС", "АНГЛ", "США", "ДИСКОР", "ШТАТ", "НЕПОН", "ЯЗЫК", "ВЕРИД", "КРАТК", "25", "*", "24", "КОРОТК", " ЛОЛ", "РОФЛ", "…", "САМ ЗНАЕ", "ДАЛЬШЕ"]

"""
If censor module detects these parts in any generated text, the text will be regenerated until it does not contain any of them
"""

API_ID = os.getenv("API_ID", 0)
API_HASH = os.getenv("API_HASH", "")