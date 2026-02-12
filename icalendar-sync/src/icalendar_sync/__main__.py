#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCalendar Sync - Module entry point
Allows execution via: python -m icalendar_sync

@author: Black_Temple
@version: 2.2.11
"""

import sys
import warnings

# Suppress RuntimeWarning about __main__ in sys.modules
warnings.filterwarnings('ignore', category=RuntimeWarning,
                       message='.*__main__.*sys.modules.*')

from .calendar import main

if __name__ == '__main__':
    main()
