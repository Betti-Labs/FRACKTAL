#!/usr/bin/env python3
"""
FRSOE Unit Tests

Comprehensive test suite for the Fractal Recursive Symbolic Ontology Engine.
"""

import sys
import os
import unittest
import json
import tempfile
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frsoe import FRSOE, SymbolicEngine, CodexMap, SymbolicTree, FractalHash
from frsoe.utils import entropy_analysis, visualize_tree, generate_codex


class TestSymbolicEngine(unittest.TestCase):
    """Test the core SymbolicEngine functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = SymbolicEngine(hash_depth=4, symbol_range=1000)
        
    def test_extract_symbols(self):
        """Test symbolic extraction from data."""
        data = "Hello, World!"
        symbols = self.engine.extract_symbols(data)
        
        # Should have n-1 symbols for n-character string
        self.assertEqual(len(symbols), len(data) - 1)
        
        # All symbols should be strings starting with "S_"
        for symbol in symbols:
            self.assertTrue(symbol.startswith("S_"))
            self.assertTrue(symbol[2:].isdigit())
            
    def test_build_rso_tree(self):
        """Test RSO tree construction."""
        symbols = ["S_001", "S_002", "S_003", "S_004"]
        tree = self.engine.build_rso_tree(symbols)
        
        # Should have all symbols as nodes
        self.assertEqual(len(tree.nodes), 4)
        
        # First symbol should be root (no parent)
        self.assertIsNone(tree.nodes["S_001"]["link"])
        
        # Other symbols should have parents
        self.assertEqual(tree.nodes["S_002"]["link"], "S_001")
        self.assertEqual(tree.nodes["S_003"]["link"], "S_002")
        self.assertEqual(tree.nodes["S_004"]["link"], "S_003")
        
    def test_hash_symbol(self):
        """Test recursive symbol hashing."""
        symbol = "S_001"
        hash_result = self.engine.hash_symbol(symbol)
        
        # Should be a valid SHA-256 hash
        self.assertEqual(len(hash_result), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_result))
        
        # Different depths should produce different hashes
        hash_1 = self.engine.hash_symbol(symbol, depth=1)
        hash_4 = self.engine.hash_symbol(symbol, depth=4)
        self.assertNotEqual(hash_1, hash_4)
        
    def test_collapse_tree(self):
        """Test tree collapse into fractal space."""
        symbols = ["S_001", "S_002", "S_003"]
        tree = self.engine.build_rso_tree(symbols)
        collapsed = self.engine.collapse_tree(tree)
        
        # Should have hash for each symbol
        self.assertEqual(len(collapsed), 3)
        
        # All hashes should be valid
        for symbol, hash_val in collapsed.items():
            self.assertEqual(len(hash_val), 64)
            
    def test_compute_codex_fingerprint(self):
        """Test codex fingerprint generation."""
        import pandas as pd
        
        # Create test codex DataFrame
        codex_data = [
            {"Symbol ID": "S_001", "Fractal Hash": "a" * 64},
            {"Symbol ID": "S_002", "Fractal Hash": "b" * 64}
        ]
        codex_df = pd.DataFrame(codex_data)
        
        fingerprint = self.engine.compute_codex_fingerprint(codex_df)
        
        # Should be valid SHA-256 hash
        self.assertEqual(len(fingerprint), 64)
        
    def test_reconstruct_from_codex(self):
        """Test data reconstruction from codex."""
        import pandas as pd
        
        # Create test codex with overlapping chunks
        codex_data = [
            {"Original Chunk": "He"},
            {"Original Chunk": "el"},
            {"Original Chunk": "ll"},
            {"Original Chunk": "lo"}
        ]
        codex_df = pd.DataFrame(codex_data)
        
        reconstructed = self.engine.reconstruct_from_codex(codex_df)
        self.assertEqual(reconstructed, "Hello")


class TestFRSOE(unittest.TestCase):
    """Test the main FRSOE engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.frsoe = FRSOE(hash_depth=4, symbol_range=1000)
        
    def test_compress_and_reconstruct(self):
        """Test complete compression and reconstruction cycle."""
        test_data = "Hello, World! This is a test of FRSOE compression."
        
        # Compress
        codex_map = self.frsoe.compress(test_data)
        
        # Verify codex structure
        self.assertIsInstance(codex_map, CodexMap)
        self.assertEqual(codex_map.original_data, test_data)
        self.assertGreater(len(codex_map.codex_df), 0)
        
        # Reconstruct
        reconstructed = self.frsoe.reconstruct(codex_map)
        
        # Should be perfect reconstruction
        self.assertEqual(reconstructed, test_data)
        
    def test_verify_reconstruction(self):
        """Test reconstruction verification."""
        test_data = "Test data for verification"
        codex_map = self.frsoe.compress(test_data)
        
        # Should verify as perfect
        self.assertTrue(self.frsoe.verify_reconstruction(codex_map))
        
    def test_analyze_entropy(self):
        """Test entropy analysis."""
        test_data = "Hello, World!"
        codex_map = self.frsoe.compress(test_data)
        
        entropy = self.frsoe.analyze_entropy(codex_map)
        
        # Should have all required keys
        required_keys = ["original_entropy", "symbolic_entropy", "fractal_entropy", "entropy_preservation"]
        for key in required_keys:
            self.assertIn(key, entropy)
            
        # Entropy values should be non-negative
        for key in required_keys:
            self.assertGreaterEqual(entropy[key], 0)
            
    def test_get_compression_stats(self):
        """Test compression statistics."""
        test_data = "Test data for statistics"
        codex_map = self.frsoe.compress(test_data)
        
        stats = self.frsoe.get_compression_stats(codex_map)
        
        # Should have all required keys
        required_keys = ["original_size", "codex_size", "compression_ratio", "space_saved", 
                        "compression_percentage", "symbol_count", "unique_symbols", "tree_depth", "fingerprint"]
        for key in required_keys:
            self.assertIn(key, stats)
            
        # Compression ratio should be positive
        self.assertGreater(stats["compression_ratio"], 0)
        
    def test_batch_compress(self):
        """Test batch compression."""
        test_data_list = ["Hello", "World", "Test"]
        codex_maps = self.frsoe.batch_compress(test_data_list)
        
        # Should return list of CodexMaps
        self.assertEqual(len(codex_maps), 3)
        for codex_map in codex_maps:
            self.assertIsInstance(codex_map, CodexMap)
            
        # Each should reconstruct perfectly
        for i, codex_map in enumerate(codex_maps):
            reconstructed = self.frsoe.reconstruct(codex_map)
            self.assertEqual(reconstructed, test_data_list[i])


class TestCodexMap(unittest.TestCase):
    """Test CodexMap functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.frsoe = FRSOE()
        self.test_data = "Hello, World!"
        self.codex_map = self.frsoe.compress(self.test_data)
        
    def test_codex_map_creation(self):
        """Test CodexMap creation and validation."""
        # Should have all required properties
        self.assertEqual(self.codex_map.original_data, self.test_data)
        self.assertGreater(len(self.codex_map.codex_df), 0)
        self.assertIsInstance(self.codex_map.symbolic_tree, SymbolicTree)
        self.assertIsInstance(self.codex_map.fractal_hashes, dict)
        self.assertEqual(len(self.codex_map.fingerprint), 64)
        self.assertGreater(self.codex_map.compression_ratio, 0)
        
    def test_symbol_sequence(self):
        """Test symbol sequence extraction."""
        sequence = self.codex_map.get_symbol_sequence()
        self.assertEqual(len(sequence), len(self.codex_map.codex_df))
        
        # All should be valid symbols
        for symbol in sequence:
            self.assertTrue(symbol.startswith("S_"))
            
    def test_hash_sequence(self):
        """Test hash sequence extraction."""
        sequence = self.codex_map.get_hash_sequence()
        self.assertEqual(len(sequence), len(self.codex_map.codex_df))
        
        # All should be valid hashes
        for hash_val in sequence:
            self.assertEqual(len(hash_val), 64)
            
    def test_symbol_frequency(self):
        """Test symbol frequency analysis."""
        freq = self.codex_map.get_symbol_frequency()
        self.assertIsInstance(freq, dict)
        
        # Frequencies should be positive
        for count in freq.values():
            self.assertGreater(count, 0)
            
    def test_save_and_load(self):
        """Test saving and loading CodexMap."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            
        try:
            # Save
            self.codex_map.save_to_file(temp_path)
            
            # Load
            loaded_codex = CodexMap.load_from_file(temp_path)
            
            # Should be equivalent
            self.assertEqual(loaded_codex.original_data, self.codex_map.original_data)
            self.assertEqual(loaded_codex.fingerprint, self.codex_map.fingerprint)
            self.assertEqual(loaded_codex.compression_ratio, self.codex_map.compression_ratio)
            
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    def test_get_summary(self):
        """Test codex summary generation."""
        summary = self.codex_map.get_summary()
        
        # Should have all required keys
        required_keys = ["original_length", "symbol_count", "unique_symbols", 
                        "tree_depth", "compression_ratio", "fingerprint"]
        for key in required_keys:
            self.assertIn(key, summary)


class TestSymbolicTree(unittest.TestCase):
    """Test SymbolicTree functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.frsoe = FRSOE()
        self.test_data = "Hello, World!"
        self.codex_map = self.frsoe.compress(self.test_data)
        self.tree = self.codex_map.symbolic_tree
        
    def test_tree_properties(self):
        """Test tree property calculations."""
        self.assertGreaterEqual(self.tree.max_depth, 0)
        self.assertGreater(self.tree.node_count, 0)
        self.assertIsInstance(self.tree.root_nodes, list)
        
    def test_get_children(self):
        """Test getting children of nodes."""
        for symbol in self.tree.nodes:
            children = self.tree.get_children(symbol)
            self.assertIsInstance(children, list)
            
    def test_get_parent(self):
        """Test getting parent of nodes."""
        for symbol in self.tree.nodes:
            parent = self.tree.get_parent(symbol)
            if parent is not None:
                self.assertIn(parent, self.tree.nodes)
                
    def test_get_depth(self):
        """Test getting depth of nodes."""
        for symbol in self.tree.nodes:
            depth = self.tree.get_depth(symbol)
            self.assertGreaterEqual(depth, 0)
            
    def test_get_path_to_root(self):
        """Test getting path to root."""
        for symbol in self.tree.nodes:
            path = self.tree.get_path_to_root(symbol)
            self.assertIsInstance(path, list)
            self.assertGreater(len(path), 0)
            
    def test_to_dict_and_json(self):
        """Test tree serialization."""
        tree_dict = self.tree.to_dict()
        self.assertIn("nodes", tree_dict)
        self.assertIn("max_depth", tree_dict)
        self.assertIn("node_count", tree_dict)
        self.assertIn("root_nodes", tree_dict)
        
        tree_json = self.tree.to_json()
        self.assertIsInstance(tree_json, str)
        
        # Should be valid JSON
        parsed = json.loads(tree_json)
        self.assertEqual(parsed["max_depth"], self.tree.max_depth)


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.frsoe = FRSOE()
        self.test_data = "Hello, World!"
        self.codex_map = self.frsoe.compress(self.test_data)
        
    def test_entropy_analysis(self):
        """Test entropy analysis utility."""
        analysis = entropy_analysis(self.codex_map)
        
        # Should have all required keys
        required_keys = ["original_entropy", "symbolic_entropy", "hash_depths", 
                        "fractal_entropies", "entropy_preservation"]
        for key in required_keys:
            self.assertIn(key, analysis)
            
        # Should have results for each hash depth
        self.assertEqual(len(analysis["fractal_entropies"]), len(analysis["hash_depths"]))
        
    def test_visualize_tree(self):
        """Test tree visualization."""
        fig = visualize_tree(self.codex_map.symbolic_tree)
        
        # Should return a plotly figure
        self.assertIsInstance(fig, type(go.Figure()))
        
    def test_generate_codex(self):
        """Test codex report generation."""
        report = generate_codex(self.codex_map)
        
        # Should have all required sections
        required_sections = ["metadata", "symbol_analysis", "hash_analysis", 
                           "entropy_analysis", "tree_structure"]
        for section in required_sections:
            self.assertIn(section, report)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.frsoe = FRSOE()
        
    def test_empty_string(self):
        """Test handling of empty strings."""
        codex_map = self.frsoe.compress("")
        reconstructed = self.frsoe.reconstruct(codex_map)
        self.assertEqual(reconstructed, "")
        
    def test_single_character(self):
        """Test handling of single character strings."""
        codex_map = self.frsoe.compress("A")
        reconstructed = self.frsoe.reconstruct(codex_map)
        self.assertEqual(reconstructed, "A")
        
    def test_unicode_characters(self):
        """Test handling of Unicode characters."""
        test_data = "Hello, 世界! 🌍"
        codex_map = self.frsoe.compress(test_data)
        reconstructed = self.frsoe.reconstruct(codex_map)
        self.assertEqual(reconstructed, test_data)
        
    def test_large_data(self):
        """Test handling of large data."""
        test_data = "A" * 1000
        codex_map = self.frsoe.compress(test_data)
        reconstructed = self.frsoe.reconstruct(codex_map)
        self.assertEqual(reconstructed, test_data)
        
    def test_special_characters(self):
        """Test handling of special characters."""
        test_data = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        codex_map = self.frsoe.compress(test_data)
        reconstructed = self.frsoe.reconstruct(codex_map)
        self.assertEqual(reconstructed, test_data)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2) 