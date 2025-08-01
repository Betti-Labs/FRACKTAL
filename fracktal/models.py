"""
FRSOE Data Models

This module contains the core data structures used by the FRSOE system.
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json


@dataclass
class SymbolicTree:
    """
    Represents the Recursive Symbolic Ontology tree structure.
    
    This tree links each symbol to its predecessor recursively, creating
    a hierarchical representation of symbolic relationships.
    """
    
    nodes: Dict[str, Dict[str, Any]]
    
    def __post_init__(self):
        """Calculate additional properties after initialization."""
        self.max_depth = max(
            (node.get("depth", 0) for node in self.nodes.values()),
            default=0
        )
        self.node_count = len(self.nodes)
        self.root_nodes = [
            symbol for symbol, data in self.nodes.items()
            if data.get("link") is None
        ]
    
    def get_children(self, symbol: str) -> List[str]:
        """Get all children of a given symbol."""
        return self.nodes.get(symbol, {}).get("children", [])
    
    def get_parent(self, symbol: str) -> Optional[str]:
        """Get the parent of a given symbol."""
        return self.nodes.get(symbol, {}).get("link")
    
    def get_depth(self, symbol: str) -> int:
        """Get the depth of a given symbol in the tree."""
        return self.nodes.get(symbol, {}).get("depth", 0)
    
    def get_path_to_root(self, symbol: str) -> List[str]:
        """Get the path from a symbol to the root."""
        path = [symbol]
        current = symbol
        
        while current in self.nodes and self.nodes[current].get("link"):
            parent = self.nodes[current]["link"]
            path.append(parent)
            current = parent
            
        return path[::-1]  # Reverse to get root->leaf order
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tree to dictionary representation."""
        return {
            "nodes": self.nodes,
            "max_depth": self.max_depth,
            "node_count": self.node_count,
            "root_nodes": self.root_nodes
        }
    
    def to_json(self) -> str:
        """Convert tree to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class FractalHash:
    """
    Represents a fractal hash with metadata.
    
    Fractal hashes are created by recursively hashing symbols
    to collapse them into fractal attractor space.
    """
    
    symbol: str
    hash_value: str
    depth: int
    original_data: str
    
    def __post_init__(self):
        """Validate hash after initialization."""
        if not self.hash_value or len(self.hash_value) != 64:
            raise ValueError("Fractal hash must be a valid SHA-256 hash (64 characters)")
    
    def get_short_hash(self, length: int = 8) -> str:
        """Get a shortened version of the hash."""
        return self.hash_value[:length]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "symbol": self.symbol,
            "hash_value": self.hash_value,
            "depth": self.depth,
            "original_data": self.original_data
        }


@dataclass
class CodexMap:
    """
    Complete codex mapping containing all FRSOE encoding information.
    
    The CodexMap is the central data structure that contains the original data,
    symbolic representations, fractal hashes, and metadata needed for
    perfect reconstruction.
    """
    
    original_data: str
    codex_df: pd.DataFrame
    symbolic_tree: SymbolicTree
    fractal_hashes: Dict[str, str]
    fingerprint: str
    compression_ratio: float
    
    # Optional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Validate and process codex after initialization."""
        # Validate required columns
        required_columns = ["Index", "Original Chunk", "Symbol ID", "Fractal Hash"]
        missing_columns = [col for col in required_columns if col not in self.codex_df.columns]
        if missing_columns:
            raise ValueError(f"Codex DataFrame missing required columns: {missing_columns}")
        
        # Validate fingerprint
        if not self.fingerprint or len(self.fingerprint) != 64:
            raise ValueError("Fingerprint must be a valid SHA-256 hash (64 characters)")
        
        # Calculate additional properties
        self.symbol_count = len(self.codex_df)
        self.unique_symbols = self.codex_df["Symbol ID"].nunique()
        self.tree_depth = self.symbolic_tree.max_depth
        
    def get_symbol_sequence(self) -> List[str]:
        """Get the sequence of symbols in order."""
        return self.codex_df["Symbol ID"].tolist()
    
    def get_hash_sequence(self) -> List[str]:
        """Get the sequence of fractal hashes in order."""
        return self.codex_df["Fractal Hash"].tolist()
    
    def get_chunk_sequence(self) -> List[str]:
        """Get the sequence of original chunks in order."""
        return self.codex_df["Original Chunk"].tolist()
    
    def get_symbol_frequency(self) -> Dict[str, int]:
        """Get frequency count of each symbol."""
        return self.codex_df["Symbol ID"].value_counts().to_dict()
    
    def get_hash_frequency(self) -> Dict[str, int]:
        """Get frequency count of each fractal hash."""
        return self.codex_df["Fractal Hash"].value_counts().to_dict()
    
    def get_symbol_at_index(self, index: int) -> Optional[str]:
        """Get symbol at specific index."""
        if 0 <= index < len(self.codex_df):
            return self.codex_df.iloc[index]["Symbol ID"]
        return None
    
    def get_hash_at_index(self, index: int) -> Optional[str]:
        """Get fractal hash at specific index."""
        if 0 <= index < len(self.codex_df):
            return self.codex_df.iloc[index]["Fractal Hash"]
        return None
    
    def get_chunk_at_index(self, index: int) -> Optional[str]:
        """Get original chunk at specific index."""
        if 0 <= index < len(self.codex_df):
            return self.codex_df.iloc[index]["Original Chunk"]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert codex to dictionary representation."""
        return {
            "original_data": self.original_data,
            "codex_df": self.codex_df.to_dict("records"),
            "symbolic_tree": self.symbolic_tree.to_dict(),
            "fractal_hashes": self.fractal_hashes,
            "fingerprint": self.fingerprint,
            "compression_ratio": self.compression_ratio,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "symbol_count": self.symbol_count,
            "unique_symbols": self.unique_symbols,
            "tree_depth": self.tree_depth
        }
    
    def to_json(self) -> str:
        """Convert codex to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def save_to_file(self, filepath: str) -> None:
        """Save codex to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'CodexMap':
        """Load codex from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct objects
        codex_df = pd.DataFrame(data["codex_df"])
        symbolic_tree = SymbolicTree(data["symbolic_tree"]["nodes"])
        
        return cls(
            original_data=data["original_data"],
            codex_df=codex_df,
            symbolic_tree=symbolic_tree,
            fractal_hashes=data["fractal_hashes"],
            fingerprint=data["fingerprint"],
            compression_ratio=data["compression_ratio"],
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp")
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the codex."""
        return {
            "original_length": len(self.original_data),
            "symbol_count": self.symbol_count,
            "unique_symbols": self.unique_symbols,
            "tree_depth": self.tree_depth,
            "compression_ratio": self.compression_ratio,
            "fingerprint": self.fingerprint[:16] + "...",
            "most_common_symbol": max(self.get_symbol_frequency().items(), key=lambda x: x[1])[0] if self.get_symbol_frequency() else None,
            "most_common_hash": max(self.get_hash_frequency().items(), key=lambda x: x[1])[0][:16] + "..." if self.get_hash_frequency() else None
        } 