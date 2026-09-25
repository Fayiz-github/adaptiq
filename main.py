"""
main.py
-------
Quick entry point to start the Adaptiq quiz platform.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

from app import main

if __name__ == "__main__":
    main()
