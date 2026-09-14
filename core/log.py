# core/log.py
import logging, sys
from core.config import LOG_FILE

log = logging.getLogger("helion")
log.setLevel(logging.DEBUG)

_fmt = logging.Formatter("[%(asctime)s] %(levelname)s  %(message)s", "%H:%M:%S")

_sh = logging.StreamHandler(sys.stdout)
_sh.setFormatter(_fmt)
log.addHandler(_sh)

try:
    _fh = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
    _fh.setFormatter(_fmt)
    log.addHandler(_fh)
except Exception:
    pass
