"""
FRACKTAL: Fractal Recursive Symbolic Ontology Engine

Advanced semantic compression through recursive symbolic pattern recognition
with perfect reconstruction capabilities.
"""

from .core import FRSOE, SymbolicEngine
from .models import CodexMap, SymbolicTree, FractalHash

# Optional imports for visualization and analysis
try:
    from .utils import entropy_analysis, visualize_tree, generate_codex
    _has_utils = True
except ImportError:
    _has_utils = False

__version__ = "1.0.0"
__author__ = "Gregory Betti - Betti Labs"
__email__ = "gorygrey@protonmail.com"

__all__ = [
    "FRSOE",
    "SymbolicEngine", 
    "CodexMap",
    "SymbolicTree",
    "FractalHash"
]

# Add utils functions if available
if _has_utils:
    __all__.extend(["entropy_analysis", "visualize_tree", "generate_codex"])

# Add recursive compression if available
try:
    from .recursive_compression import RecursiveFRSOE, RecursiveCompressor
    __all__.extend(["RecursiveFRSOE", "RecursiveCompressor"])
except ImportError:
    pass 