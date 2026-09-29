"""TASK-152 console helper: force UTF-8 stdout so Chinese diagnostics from the
gates survive the Windows console code page instead of crashing a print().
Import (or exec) before running any gate output through Python.
"""

import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
