# -*- coding: utf-8 -*-
"""
Quick Test: Real Data Training
================================
Test the real data training pipeline with a small sample.
"""

import os
import sys

# Set small target for testing
os.environ['TARGET_MATCHES'] = '50'

# Import and run
from train_with_real_data import *

if __name__ == "__main__":
    print("="*80)
    print("QUICK TEST: Real Data Training (50 matches)")
    print("="*80)
    
    # Override configuration for quick test
    TARGET_MATCHES = 50
    MAJOR_LEAGUES = {
        39: "Premier League",  # Only PL for quick test
        203: "Süper Lig"       # And Süper Lig
    }
    
    main()
