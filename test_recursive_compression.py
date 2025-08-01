#!/usr/bin/env python3
"""
Test Recursive Compression - Does it actually compress?

Test the new recursive pattern compression to see if we get actual compression
while maintaining perfect reconstruction.
"""

import sys
import os
import json
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fracktal.recursive_compression import RecursiveFRSOE, RecursiveCompressor

def test_recursive_compression():
    """Test if recursive compression actually compresses."""
    
    print("🔥 TESTING RECURSIVE COMPRESSION")
    print("=" * 50)
    print("Does it actually compress? Let's find out!")
    print("=" * 50)
    
    # Initialize both regular FRSOE and recursive FRSOE
    from fracktal.core import FRSOE
    regular_frsoe = FRSOE()
    recursive_frsoe = RecursiveFRSOE(min_pattern_length=3, min_occurrences=2)
    
    # Test data with obvious patterns
    test_cases = {
        "repetitive_pattern": "ABABABABABABABABABABABABABABABABABABABAB",
        "repetitive_phrase": "Hello World! Hello World! Hello World! Hello World! Hello World!",
        "json_with_patterns": json.dumps({
            "users": [
                {"id": i, "name": f"User{i}", "email": f"user{i}@example.com"}
                for i in range(10)
            ] * 5  # Repeat the same structure 5 times
        }, indent=2),
        "code_with_patterns": '''
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

def process_data_again(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

def process_data_final(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
        '''.strip()
    }
    
    for name, data in test_cases.items():
        print(f"\n💀 TESTING: {name}")
        print(f"Data size: {len(data):,} characters")
        print("-" * 40)
        
        # Test regular FRSOE
        print("📊 Regular FRSOE:")
        start_time = time.time()
        regular_codex = regular_frsoe.compress(data)
        regular_time = time.time() - start_time
        
        regular_stats = regular_frsoe.get_compression_stats(regular_codex)
        print(f"   Compression ratio: {regular_stats['compression_ratio']:.2f}x")
        print(f"   Compression time: {regular_time:.3f}s")
        
        # Test recursive FRSOE
        print("🚀 Recursive FRSOE:")
        start_time = time.time()
        recursive_result = recursive_frsoe.compress(data)
        recursive_time = time.time() - start_time
        
        combined_stats = recursive_result['combined_stats']
        print(f"   Overall compression ratio: {combined_stats['overall_compression_ratio']:.2f}x")
        print(f"   Pattern count: {combined_stats['pattern_count']}")
        print(f"   Space saved: {combined_stats['total_space_saved']} symbols")
        print(f"   Compression time: {recursive_time:.3f}s")
        
        # Show pattern details
        recursive_data = recursive_result['recursive_compression']
        patterns = recursive_data['patterns']
        if patterns:
            print(f"   Patterns found:")
            for pattern_id, pattern_sequence in list(patterns.items())[:3]:  # Show first 3
                print(f"     {pattern_id}: {pattern_sequence[:5]}{'...' if len(pattern_sequence) > 5 else ''}")
            if len(patterns) > 3:
                print(f"     ... and {len(patterns) - 3} more patterns")
        
        # Test reconstruction
        print("🔍 Testing reconstruction:")
        start_time = time.time()
        reconstructed = recursive_frsoe.reconstruct(recursive_result)
        reconstruction_time = time.time() - start_time
        
        is_perfect = data == reconstructed
        print(f"   Perfect reconstruction: {'✅' if is_perfect else '❌'}")
        print(f"   Reconstruction time: {reconstruction_time:.3f}s")
        
        # Compare compression ratios
        improvement = combined_stats['overall_compression_ratio'] / regular_stats['compression_ratio']
        print(f"   Improvement: {improvement:.2f}x better than regular FRSOE")
        
        if not is_perfect:
            print(f"   ❌ RECONSTRUCTION FAILED!")
            print(f"   Original: '{data[:50]}...'")
            print(f"   Reconstructed: '{reconstructed[:50]}...'")

def test_pattern_detection():
    """Test pattern detection specifically."""
    
    print("\n" + "=" * 50)
    print("🔍 TESTING PATTERN DETECTION")
    print("=" * 50)
    
    compressor = RecursiveCompressor(min_pattern_length=3, min_occurrences=2)
    
    # Test with obvious patterns
    test_symbols = ["S_001", "S_002", "S_003", "S_001", "S_002", "S_003", "S_004", "S_005"]
    
    print(f"Test symbols: {test_symbols}")
    
    # Find patterns
    patterns = compressor.find_patterns(test_symbols)
    print(f"Patterns found: {len(patterns)}")
    
    for pattern_id, pattern_sequence in patterns.items():
        print(f"  {pattern_id}: {pattern_sequence}")
    
    # Test compression
    compressed_data = compressor.compress_with_patterns(test_symbols)
    print(f"\nCompressed sequence: {compressed_data['compressed_sequence']}")
    print(f"Compression ratio: {compressed_data['compression_stats']['compression_ratio']:.2f}x")
    
    # Test reconstruction
    reconstruction_result = compressor.reconstruct_from_patterns(compressed_data)
    print(f"Reconstructed: {reconstruction_result['reconstructed_symbols']}")
    print(f"Perfect reconstruction: {reconstruction_result['is_perfect']}")

def analyze_compression_effectiveness():
    """Analyze when recursive compression is most effective."""
    
    print("\n" + "=" * 50)
    print("📊 COMPRESSION EFFECTIVENESS ANALYSIS")
    print("=" * 50)
    
    recursive_frsoe = RecursiveFRSOE(min_pattern_length=3, min_occurrences=2)
    
    # Test different types of data
    test_data = {
        "highly_repetitive": "A" * 1000,  # Should compress well
        "moderately_repetitive": "Hello World! " * 100,  # Should compress moderately
        "low_repetition": "The quick brown fox jumps over the lazy dog. " * 20,  # Should compress poorly
        "no_repetition": "".join([f"Unique{i}" for i in range(100)])  # Should not compress
    }
    
    results = {}
    
    for name, data in test_data.items():
        print(f"\n📝 {name}:")
        print(f"   Data size: {len(data):,} characters")
        
        # Compress
        result = recursive_frsoe.compress(data)
        stats = result['combined_stats']
        
        compression_ratio = stats['overall_compression_ratio']
        pattern_count = stats['pattern_count']
        space_saved = stats['total_space_saved']
        
        print(f"   Compression ratio: {compression_ratio:.2f}x")
        print(f"   Patterns found: {pattern_count}")
        print(f"   Space saved: {space_saved} symbols")
        
        # Effectiveness rating
        if compression_ratio > 1.5:
            effectiveness = "Excellent"
        elif compression_ratio > 1.2:
            effectiveness = "Good"
        elif compression_ratio > 1.05:
            effectiveness = "Moderate"
        else:
            effectiveness = "Poor"
        
        print(f"   Effectiveness: {effectiveness}")
        
        results[name] = {
            'compression_ratio': compression_ratio,
            'pattern_count': pattern_count,
            'effectiveness': effectiveness
        }
    
    # Summary
    print(f"\n🎯 SUMMARY:")
    print(f"   Best compression: {max(results.items(), key=lambda x: x[1]['compression_ratio'])[0]}")
    print(f"   Worst compression: {min(results.items(), key=lambda x: x[1]['compression_ratio'])[0]}")
    print(f"   Average compression ratio: {sum(r['compression_ratio'] for r in results.values()) / len(results):.2f}x")

def main():
    """Run all tests."""
    
    test_recursive_compression()
    test_pattern_detection()
    analyze_compression_effectiveness()
    
    print(f"\n🏁 Testing completed!")
    print("The truth about recursive compression is revealed!")

if __name__ == "__main__":
    main() 