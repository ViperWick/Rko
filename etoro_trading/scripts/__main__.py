# -*- coding: utf-8 -*-
"""允許：python -m etoro_trading.scripts <子命令>"""
from __future__ import annotations

import sys

from etoro_trading.scripts.etoro_tools import main

if __name__ == "__main__":
    sys.exit(main())
