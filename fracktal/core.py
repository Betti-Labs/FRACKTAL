"""
Core FRSOE Implementation

This module contains the main FRSOE engine and symbolic processing algorithms
as described in the research paper.
"""

import hashlib
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from .models import CodexMap, SymbolicTree, FractalHash


class SymbolicEngine:
    """Core symbolic processing engine for FRSOE."""
    
    def __init__(self, hash_depth: int = 4, symbol_range: int = 10000):
        self.hash_depth = hash_depth
        self.symbol_range = symbol_range
        
    def extract_symbols(self, data: str) -> List[str]:
        """
        Extract symbolic representations from overlapping 2-character chunks.
        
        Args:
            data: Input string to process
            
        Returns:
            List of symbolic IDs for each chunk
        """
        symbols = []
        for i in range(len(data) - 1):
            chunk = data[i:i+2]
            # Create symbolic ID from hash
            symbol_id = f"S_{hash(chunk) % self.symbol_range:04d}"
            symbols.append(symbol_id)
        return symbols
    
    def build_rso_tree(self, symbols: List[str]) -> SymbolicTree:
        """
        Build Recursive Symbolic Ontology tree linking each symbol to its predecessor.
        
        Args:
            symbols: List of symbolic IDs
            
        Returns:
            SymbolicTree object containing the recursive structure
        """
        tree = {}
        for i, symbol in enumerate(symbols):
            tree[symbol] = {
                "index": i,
                "link": symbols[i-1] if i > 0 else None,
                "depth": 0,
                "children": []
            }
            
        # Build recursive links
        for symbol in tree:
            if tree[symbol]["link"]:
                parent = tree[symbol]["link"]
                tree[parent]["children"].append(symbol)
                tree[symbol]["depth"] = tree[parent]["depth"] + 1
                
        return SymbolicTree(tree)
    
    def hash_symbol(self, symbol: str, depth: Optional[int] = None) -> str:
        """
        Recursively hash a symbol to collapse into fractal attractor space.
        
        Args:
            symbol: Symbolic ID to hash
            depth: Number of recursive hash iterations (defaults to self.hash_depth)
            
        Returns:
            Fractal hash string
        """
        if depth is None:
            depth = self.hash_depth
            
        h = symbol
        for _ in range(depth):
            h = hashlib.sha256(h.encode()).hexdigest()
        return h
    
    def collapse_tree(self, tree: SymbolicTree) -> Dict[str, str]:
        """
        Collapse the symbolic tree into fractal attractor space.
        
        Args:
            tree: SymbolicTree object
            
        Returns:
            Dictionary mapping symbols to their fractal hashes
        """
        return {key: self.hash_symbol(key) for key in tree.nodes}
    
    def compute_codex_fingerprint(self, codex_df: pd.DataFrame) -> str:
        """
        Generate unique fingerprint for encoded input.
        
        Args:
            codex_df: Codex DataFrame with symbols and hashes
            
        Returns:
            Unique fingerprint string
        """
        combined = "".join(codex_df["Symbol ID"].tolist()) + "".join(codex_df["Fractal Hash"].tolist())
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def reconstruct_from_codex(self, codex_df: pd.DataFrame) -> str:
        """
        Reconstruct original input from overlapping chunks in codex.
        
        Args:
            codex_df: Codex DataFrame with original chunks
            
        Returns:
            Reconstructed original string
        """
        chunks = codex_df["Original Chunk"].tolist()
        if not chunks:
            return ""
            
        reconstructed = chunks[0]
        for i in range(1, len(chunks)):
            reconstructed += chunks[i][-1]
        return reconstructed


class FRSOE:
    """
    Main FRSOE engine for compression and reconstruction.
    
    This class implements the complete Fractal Recursive Symbolic Ontology Engine
    as described in the research paper.
    """
    
    def __init__(self, hash_depth: int = 4, symbol_range: int = 10000):
        """
        Initialize FRSOE engine.
        
        Args:
            hash_depth: Number of recursive hash iterations
            symbol_range: Range for symbolic ID generation
        """
        self.engine = SymbolicEngine(hash_depth, symbol_range)
        self.codex_history = []
        
    def compress(self, data: str) -> CodexMap:
        """
        Compress input data using FRSOE symbolic encoding.
        
        Args:
            data: Input string to compress
            
        Returns:
            CodexMap object containing the complete encoding
        """
        # Extract symbolic representations
        symbols = self.engine.extract_symbols(data)
        
        # Build RSO tree
        tree = self.engine.build_rso_tree(symbols)
        
        # Generate original chunks for reconstruction
        chunks = []
        for i in range(len(data) - 1):
            chunks.append(data[i:i+2])
        
        # Create codex DataFrame
        codex_data = []
        for i, (chunk, symbol) in enumerate(zip(chunks, symbols)):
            fractal_hash = self.engine.hash_symbol(symbol)
            codex_data.append({
                "Index": i,
                "Original Chunk": chunk,
                "Symbol ID": symbol,
                "Fractal Hash": fractal_hash,
                "Tree Depth": tree.nodes[symbol]["depth"]
            })
        
        codex_df = pd.DataFrame(codex_data)
        
        # Generate fingerprint
        fingerprint = self.engine.compute_codex_fingerprint(codex_df)
        
        # Create CodexMap
        codex_map = CodexMap(
            original_data=data,
            codex_df=codex_df,
            symbolic_tree=tree,
            fractal_hashes=self.engine.collapse_tree(tree),
            fingerprint=fingerprint,
            compression_ratio=len(data) / len(codex_df)
        )
        
        # Store in history
        self.codex_history.append(codex_map)
        
        return codex_map
    
    def reconstruct(self, codex_map: CodexMap) -> str:
        """
        Reconstruct original data from CodexMap.
        
        Args:
            codex_map: CodexMap object containing the encoding
            
        Returns:
            Reconstructed original string
        """
        return self.engine.reconstruct_from_codex(codex_map.codex_df)
    
    def analyze_entropy(self, codex_map: CodexMap) -> Dict[str, float]:
        """
        Analyze entropy preservation in the encoding.
        
        Args:
            codex_map: CodexMap object to analyze
            
        Returns:
            Dictionary with entropy metrics
        """
        # Calculate original entropy
        original_entropy = self._calculate_entropy(codex_map.original_data)
        
        # Calculate symbolic entropy
        symbols = codex_map.codex_df["Symbol ID"].tolist()
        symbolic_entropy = self._calculate_entropy("".join(symbols))
        
        # Calculate fractal entropy
        hashes = codex_map.codex_df["Fractal Hash"].tolist()
        fractal_entropy = self._calculate_entropy("".join(hashes))
        
        return {
            "original_entropy": original_entropy,
            "symbolic_entropy": symbolic_entropy,
            "fractal_entropy": fractal_entropy,
            "entropy_preservation": symbolic_entropy / original_entropy if original_entropy > 0 else 1.0
        }
    
    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not data:
            return 0.0
            
        # Count character frequencies
        freq = {}
        for char in data:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        length = len(data)
        for count in freq.values():
            p = count / length
            if p > 0:
                entropy -= p * np.log2(p)
                
        return entropy
    
    def get_compression_stats(self, codex_map: CodexMap) -> Dict[str, Any]:
        """
        Get comprehensive compression statistics.
        
        Args:
            codex_map: CodexMap object to analyze
            
        Returns:
            Dictionary with compression statistics
        """
        original_size = len(codex_map.original_data)
        codex_size = len(codex_map.codex_df)
        
        return {
            "original_size": original_size,
            "codex_size": codex_size,
            "compression_ratio": codex_map.compression_ratio,
            "space_saved": original_size - codex_size,
            "compression_percentage": ((original_size - codex_size) / original_size) * 100,
            "symbol_count": len(codex_map.codex_df),
            "unique_symbols": codex_map.codex_df["Symbol ID"].nunique(),
            "tree_depth": codex_map.symbolic_tree.max_depth,
            "fingerprint": codex_map.fingerprint
        }
    
    def batch_compress(self, data_list: List[str]) -> List[CodexMap]:
        """
        Compress multiple inputs in batch.
        
        Args:
            data_list: List of input strings
            
        Returns:
            List of CodexMap objects
        """
        return [self.compress(data) for data in data_list]
    
    def verify_reconstruction(self, codex_map: CodexMap) -> bool:
        """
        Verify that reconstruction is perfect.
        
        Args:
            codex_map: CodexMap object to verify
            
        Returns:
            True if reconstruction is perfect, False otherwise
        """
        reconstructed = self.reconstruct(codex_map)
        return reconstructed == codex_map.original_data 