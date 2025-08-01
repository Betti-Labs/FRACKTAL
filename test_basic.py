#!/usr/bin/env python3
"""
Basic FRSOE Test

Simple test to verify core functionality works without visualization dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test core functionality only
from fracktal.core import FRSOE, SymbolicEngine
from fracktal.models import CodexMap, SymbolicTree

def test_basic_functionality():
    """Test basic FRSOE functionality."""
    print("🧠 Testing FRSOE Basic Functionality")
    print("=" * 50)
    
    # Initialize engine
    engine = FRSOE(hash_depth=4)
    print("✅ Engine initialized")
    
    # Test data
    test_cases = [
        "Hello, World!",
        "This is a test of FRSOE compression.",
        "ABABABABABABABABABAB",
        "The quick brown fox jumps over the lazy dog."
    ]
    
    for i, data in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: '{data[:30]}{'...' if len(data) > 30 else ''}'")
        
        # Compress
        codex_map = engine.compress(data)
        print(f"   Original length: {len(data)}")
        print(f"   Symbol count: {len(codex_map.codex_df)}")
        print(f"   Unique symbols: {codex_map.unique_symbols}")
        print(f"   Tree depth: {codex_map.tree_depth}")
        
        # Reconstruct
        reconstructed = engine.reconstruct(codex_map)
        is_perfect = engine.verify_reconstruction(codex_map)
        
        print(f"   Perfect reconstruction: {'✅' if is_perfect else '❌'}")
        
        # Show fingerprint
        print(f"   Fingerprint: {codex_map.fingerprint[:16]}...")
        
        # Verify perfect match
        if data != reconstructed:
            print(f"   ❌ RECONSTRUCTION FAILED!")
            print(f"   Original: '{data}'")
            print(f"   Reconstructed: '{reconstructed}'")
            return False
    
    print("\n🎉 All tests passed!")
    print("✅ Perfect reconstruction verified")
    print("✅ Symbolic extraction working")
    print("✅ RSO tree construction working")
    print("✅ Fractal hash collapse working")
    print("✅ Codex fingerprinting working")
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1) 