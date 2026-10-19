"""
MedGraph AI — RAG Subsystem Configuration
==========================================
Re-exports settings from rag_config.py for backward compatibility.
"""

import os
import sys

_RAG_DIR = os.path.dirname(os.path.abspath(__file__))
if _RAG_DIR not in sys.path:
    sys.path.insert(0, _RAG_DIR)

try:
    from rag_config import *
except ImportError:
    from backend.rag.rag_config import *
