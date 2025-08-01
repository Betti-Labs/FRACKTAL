"""
Recursive Symbolic Compression for FRSOE

This module adds actual compression to FRSOE by detecting recursive patterns
in symbolic sequences and creating reversible mappings for perfect reconstruction.
Inspired by the Flat Loop Universe's recursive topology concepts.
"""

import hashlib
import json
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import time


class RecursiveCompressor:
    """
    Recursive symbolic compressor that finds patterns in FRSOE symbols
    and creates reversible mappings for actual compression.
    """
    
    def __init__(self, min_pattern_length: int = 4, min_occurrences: int = 3):
        self.min_pattern_length = min_pattern_length
        self.min_occurrences = min_occurrences
        self.pattern_dict = {}
        self.pattern_counter = 0
        
    def find_patterns(self, symbols: List[str]) -> Dict[str, List[str]]:
        """
        Find repeating patterns in symbolic sequence.
        Only keep patterns that actually save significant space.
        
        Args:
            symbols: List of symbolic IDs
            
        Returns:
            Dictionary mapping pattern IDs to pattern sequences
        """
        if len(symbols) < self.min_pattern_length * 2:
            return {}  # Too short to compress
            
        patterns = {}
        
        # Only look for patterns of reasonable length
        max_pattern_length = min(len(symbols) // 3, 20)  # Cap at 20 symbols
        
        for length in range(self.min_pattern_length, max_pattern_length + 1):
            # Use sliding window to find patterns
            pattern_counts = defaultdict(int)
            
            # Count occurrences of each pattern
            for i in range(len(symbols) - length + 1):
                pattern = tuple(symbols[i:i+length])
                pattern_counts[pattern] += 1
            
            # Only keep patterns that appear multiple times AND save space
            for pattern, count in pattern_counts.items():
                if count >= self.min_occurrences:
                    pattern_sequence = list(pattern)
                    pattern_length = len(pattern_sequence)
                    
                    # Calculate space savings
                    original_space = pattern_length * count
                    compressed_space = count + pattern_length  # 1 ref per occurrence + dict entry
                    space_saved = original_space - compressed_space
                    
                    # Only use pattern if it saves significant space (at least 5 symbols)
                    if space_saved >= 5:
                        pattern_id = f"P_{self.pattern_counter:03d}"
                        patterns[pattern_id] = pattern_sequence
                        self.pattern_counter += 1
                        
                        # Limit total patterns to avoid overhead
                        if len(patterns) >= 10:
                            break
            
            if len(patterns) >= 10:
                break
        
        return patterns
    
    def compress_with_patterns(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Compress symbolic sequence using pattern detection.
        
        Args:
            symbols: List of symbolic IDs
            
        Returns:
            Dictionary containing compressed representation
        """
        start_time = time.time()
        
        # Find patterns
        patterns = self.find_patterns(symbols)
        
        # If no good patterns found, return original
        if not patterns:
            return {
                'original_symbols': symbols,
                'compressed_sequence': symbols,
                'patterns': {},
                'compression_stats': {
                    'original_size': len(symbols),
                    'compressed_size': len(symbols),
                    'compression_ratio': 1.0,
                    'space_saved': 0,
                    'compression_percentage': 0.0,
                    'pattern_count': 0,
                    'compression_time': time.time() - start_time
                }
            }
        
        # Create compressed sequence by replacing patterns with references
        compressed_sequence = self._replace_patterns(symbols, patterns)
        
        # Calculate compression stats
        original_size = len(symbols)
        compressed_size = len(compressed_sequence)
        pattern_dict_size = sum(len(pattern) for pattern in patterns.values())
        total_compressed_size = compressed_size + pattern_dict_size
        
        compression_time = time.time() - start_time
        
        return {
            'original_symbols': symbols,
            'compressed_sequence': compressed_sequence,
            'patterns': patterns,
            'compression_stats': {
                'original_size': original_size,
                'compressed_size': total_compressed_size,
                'compression_ratio': original_size / total_compressed_size if total_compressed_size > 0 else 1.0,
                'space_saved': original_size - total_compressed_size,
                'compression_percentage': ((original_size - total_compressed_size) / original_size) * 100 if original_size > 0 else 0,
                'pattern_count': len(patterns),
                'compression_time': compression_time
            }
        }
    
    def _replace_patterns(self, symbols: List[str], patterns: Dict[str, List[str]]) -> List[str]:
        """
        Replace pattern occurrences with pattern references.
        
        Args:
            symbols: Original symbolic sequence
            patterns: Dictionary of patterns to replace
            
        Returns:
            Compressed sequence with pattern references
        """
        if not patterns:
            return symbols
        
        # Sort patterns by length (longest first) to prioritize longer patterns
        sorted_patterns = sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True)
        
        compressed = symbols.copy()
        
        for pattern_id, pattern_sequence in sorted_patterns:
            # Find all occurrences of this pattern
            i = 0
            while i < len(compressed) - len(pattern_sequence) + 1:
                # Check if pattern matches at current position
                if compressed[i:i+len(pattern_sequence)] == pattern_sequence:
                    # Replace pattern with reference
                    compressed[i:i+len(pattern_sequence)] = [pattern_id]
                    i += 1  # Move past the replacement
                else:
                    i += 1
        
        return compressed
    
    def reconstruct_from_patterns(self, compressed_data: Dict[str, Any]) -> List[str]:
        """
        Reconstruct original symbolic sequence from compressed representation.
        
        Args:
            compressed_data: Compressed data dictionary
            
        Returns:
            Reconstructed symbolic sequence
        """
        start_time = time.time()
        
        compressed_sequence = compressed_data['compressed_sequence']
        patterns = compressed_data['patterns']
        
        # Expand all pattern references
        expanded = self._expand_patterns(compressed_sequence, patterns)
        
        reconstruction_time = time.time() - start_time
        
        # Verify reconstruction
        original = compressed_data['original_symbols']
        is_perfect = expanded == original
        
        return {
            'reconstructed_symbols': expanded,
            'is_perfect': is_perfect,
            'reconstruction_time': reconstruction_time
        }
    
    def _expand_patterns(self, compressed_sequence: List[str], patterns: Dict[str, List[str]]) -> List[str]:
        """
        Expand pattern references back to original sequences.
        
        Args:
            compressed_sequence: Sequence with pattern references
            patterns: Dictionary of patterns
            
        Returns:
            Expanded symbolic sequence
        """
        expanded = []
        
        for item in compressed_sequence:
            if item in patterns:
                # Expand pattern reference
                expanded.extend(patterns[item])
            else:
                # Keep original symbol
                expanded.append(item)
        
        return expanded
    
    def analyze_patterns(self, compressed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the patterns found in the compression.
        
        Args:
            compressed_data: Compressed data dictionary
            
        Returns:
            Pattern analysis results
        """
        patterns = compressed_data['patterns']
        original_symbols = compressed_data['original_symbols']
        
        analysis = {
            'total_patterns': len(patterns),
            'pattern_details': {},
            'pattern_efficiency': {},
            'symbolic_coverage': {}
        }
        
        # Analyze each pattern
        for pattern_id, pattern_sequence in patterns.items():
            pattern_length = len(pattern_sequence)
            
            # Count actual occurrences in original sequence
            occurrences = 0
            for i in range(len(original_symbols) - pattern_length + 1):
                if original_symbols[i:i+pattern_length] == pattern_sequence:
                    occurrences += 1
            
            # Calculate pattern efficiency
            original_space = pattern_length * occurrences
            compressed_space = occurrences + pattern_length  # 1 ref per occurrence + dict entry
            space_saved = original_space - compressed_space
            
            analysis['pattern_details'][pattern_id] = {
                'length': pattern_length,
                'sequence': pattern_sequence,
                'occurrences': occurrences,
                'space_saved': space_saved
            }
            
            analysis['pattern_efficiency'][pattern_id] = {
                'compression_ratio': pattern_length,  # How much we save per occurrence
                'space_efficiency': space_saved / original_space if original_space > 0 else 0
            }
        
        return analysis


class RecursiveFRSOE:
    """
    Enhanced FRSOE with recursive pattern compression.
    Combines FRSOE's symbolic extraction with recursive compression.
    """
    
    def __init__(self, hash_depth: int = 4, symbol_range: int = 10000, 
                 min_pattern_length: int = 4, min_occurrences: int = 3):
        """
        Initialize RecursiveFRSOE.
        
        Args:
            hash_depth: FRSOE hash depth
            symbol_range: FRSOE symbol range
            min_pattern_length: Minimum pattern length for compression
            min_occurrences: Minimum occurrences for pattern detection
        """
        from .core import FRSOE
        self.frsoe = FRSOE(hash_depth, symbol_range)
        self.compressor = RecursiveCompressor(min_pattern_length, min_occurrences)
        
    def compress(self, data: str) -> Dict[str, Any]:
        """
        Compress data using FRSOE + recursive pattern compression.
        
        Args:
            data: Input data to compress
            
        Returns:
            Complete compressed representation
        """
        # Phase 1: FRSOE symbolic extraction
        codex_map = self.frsoe.compress(data)
        symbols = codex_map.get_symbol_sequence()
        
        # Phase 2: Recursive pattern compression
        compressed_data = self.compressor.compress_with_patterns(symbols)
        
        # Combine results
        result = {
            'original_data': data,
            'frsoe_codex': codex_map,
            'recursive_compression': compressed_data,
            'combined_stats': self._combine_stats(codex_map, compressed_data)
        }
        
        return result
    
    def reconstruct(self, compressed_result: Dict[str, Any]) -> str:
        """
        Reconstruct original data from compressed representation.
        
        Args:
            compressed_result: Complete compressed result
            
        Returns:
            Reconstructed original data
        """
        # Phase 1: Reconstruct symbols from recursive compression
        recursive_result = self.compressor.reconstruct_from_patterns(
            compressed_result['recursive_compression']
        )
        
        # Phase 2: Reconstruct original data from symbols
        reconstructed_symbols = recursive_result['reconstructed_symbols']
        
        # Create temporary codex with reconstructed symbols
        temp_codex = compressed_result['frsoe_codex']
        temp_codex.codex_df['Symbol ID'] = reconstructed_symbols
        
        # Reconstruct original data
        reconstructed_data = self.frsoe.reconstruct(temp_codex)
        
        return reconstructed_data
    
    def _combine_stats(self, codex_map, compressed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine FRSOE and recursive compression statistics."""
        frsoe_stats = self.frsoe.get_compression_stats(codex_map)
        recursive_stats = compressed_data['compression_stats']
        
        return {
            'frsoe_stats': frsoe_stats,
            'recursive_stats': recursive_stats,
            'overall_compression_ratio': recursive_stats['compression_ratio'],
            'total_space_saved': recursive_stats['space_saved'],
            'pattern_count': recursive_stats['pattern_count']
        }
    
    def verify_reconstruction(self, compressed_result: Dict[str, Any]) -> bool:
        """Verify perfect reconstruction."""
        reconstructed = self.reconstruct(compressed_result)
        return reconstructed == compressed_result['original_data']
    
    def get_detailed_analysis(self, compressed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed analysis of the compression."""
        pattern_analysis = self.compressor.analyze_patterns(
            compressed_result['recursive_compression']
        )
        
        return {
            'pattern_analysis': pattern_analysis,
            'frsoe_analysis': self.frsoe.analyze_entropy(compressed_result['frsoe_codex']),
            'combined_stats': compressed_result['combined_stats']
        } 