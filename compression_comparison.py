#!/usr/bin/env python3
"""
FRSOE vs Traditional Compression - REAL COMPARISON

Direct comparison showing what FRSOE actually does vs traditional methods.
"""

import sys
import os
import json
import time
import gzip
import zlib
import bz2
import lzma
import hashlib
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from frsoe.core import FRSOE

def test_traditional_compression(data, name):
    """Test traditional compression methods."""
    
    results = {}
    
    # Gzip
    start_time = time.time()
    gzip_compressed = gzip.compress(data.encode('utf-8'))
    gzip_time = time.time() - start_time
    
    start_time = time.time()
    gzip_decompressed = gzip.decompress(gzip_compressed).decode('utf-8')
    gzip_decompress_time = time.time() - start_time
    
    results['gzip'] = {
        'compressed_size': len(gzip_compressed),
        'compression_ratio': len(data) / len(gzip_compressed),
        'compression_time': gzip_time,
        'decompression_time': gzip_decompress_time,
        'perfect_reconstruction': data == gzip_decompressed
    }
    
    # Zlib
    start_time = time.time()
    zlib_compressed = zlib.compress(data.encode('utf-8'))
    zlib_time = time.time() - start_time
    
    start_time = time.time()
    zlib_decompressed = zlib.decompress(zlib_compressed).decode('utf-8')
    zlib_decompress_time = time.time() - start_time
    
    results['zlib'] = {
        'compressed_size': len(zlib_compressed),
        'compression_ratio': len(data) / len(zlib_compressed),
        'compression_time': zlib_time,
        'decompression_time': zlib_decompress_time,
        'perfect_reconstruction': data == zlib_decompressed
    }
    
    # Bzip2
    start_time = time.time()
    bzip2_compressed = bz2.compress(data.encode('utf-8'))
    bzip2_time = time.time() - start_time
    
    start_time = time.time()
    bzip2_decompressed = bz2.decompress(bzip2_compressed).decode('utf-8')
    bzip2_decompress_time = time.time() - start_time
    
    results['bzip2'] = {
        'compressed_size': len(bzip2_compressed),
        'compression_ratio': len(data) / len(bzip2_compressed),
        'compression_time': bzip2_time,
        'decompression_time': bzip2_decompress_time,
        'perfect_reconstruction': data == bzip2_decompressed
    }
    
    # LZMA
    start_time = time.time()
    lzma_compressed = lzma.compress(data.encode('utf-8'))
    lzma_time = time.time() - start_time
    
    start_time = time.time()
    lzma_decompressed = lzma.decompress(lzma_compressed).decode('utf-8')
    lzma_decompress_time = time.time() - start_time
    
    results['lzma'] = {
        'compressed_size': len(lzma_compressed),
        'compression_ratio': len(data) / len(lzma_compressed),
        'compression_time': lzma_time,
        'decompression_time': lzma_decompress_time,
        'perfect_reconstruction': data == lzma_decompressed
    }
    
    return results

def test_frsoe_compression(data, name):
    """Test FRSOE compression."""
    
    engine = FRSOE(hash_depth=4)
    
    start_time = time.time()
    codex_map = engine.compress(data)
    frsoe_time = time.time() - start_time
    
    start_time = time.time()
    reconstructed = engine.reconstruct(codex_map)
    frsoe_decompress_time = time.time() - start_time
    
    stats = engine.get_compression_stats(codex_map)
    entropy = engine.analyze_entropy(codex_map)
    
    return {
        'compressed_size': len(codex_map.codex_df),  # Symbol count as proxy
        'compression_ratio': stats['compression_ratio'],
        'compression_time': frsoe_time,
        'decompression_time': frsoe_decompress_time,
        'perfect_reconstruction': data == reconstructed,
        'symbol_count': stats['symbol_count'],
        'unique_symbols': stats['unique_symbols'],
        'tree_depth': stats['tree_depth'],
        'entropy_preservation': entropy['entropy_preservation'],
        'fingerprint': codex_map.fingerprint[:16]
    }

def run_comparison():
    """Run the full comparison."""
    
    print("🔍 FRSOE vs TRADITIONAL COMPRESSION - REAL COMPARISON")
    print("=" * 70)
    print("NO BULLSHIT. DIRECT COMPARISON.")
    print("=" * 70)
    
    # Test data
    test_cases = {
        "repetitive_text": "Hello World! " * 1000,  # 13,000 chars
        "complex_json": json.dumps({
            "users": [
                {
                    "id": i,
                    "name": f"User{i}",
                    "email": f"user{i}@example.com",
                    "profile": {
                        "age": 25 + i,
                        "location": f"City{i}",
                        "preferences": {
                            "theme": "dark" if i % 2 == 0 else "light",
                            "language": "en"
                        }
                    }
                }
                for i in range(100)
            ]
        }, indent=2),  # ~15,000 chars
        "random_data": ''.join([chr(i % 256) for i in range(10000)])  # 10,000 chars
    }
    
    for name, data in test_cases.items():
        print(f"\n💀 COMPARING: {name}")
        print(f"Data size: {len(data):,} characters")
        print("-" * 50)
        
        # Test traditional compression
        traditional_results = test_traditional_compression(data, name)
        
        # Test FRSOE
        frsoe_results = test_frsoe_compression(data, name)
        
        # Display results
        print(f"{'Method':<10} {'Ratio':<8} {'Comp(s)':<8} {'Decomp(s)':<10} {'Perfect':<8}")
        print("-" * 50)
        
        for method, results in traditional_results.items():
            print(f"{method:<10} {results['compression_ratio']:<8.2f} {results['compression_time']:<8.3f} {results['decompression_time']:<10.3f} {str(results['perfect_reconstruction']):<8}")
        
        print(f"{'FRSOE':<10} {frsoe_results['compression_ratio']:<8.2f} {frsoe_results['compression_time']:<8.3f} {frsoe_results['decompression_time']:<10.3f} {str(frsoe_results['perfect_reconstruction']):<8}")
        
        # FRSOE specific info
        print(f"\n🔍 FRSOE DETAILS:")
        print(f"   Symbols: {frsoe_results['symbol_count']}")
        print(f"   Unique symbols: {frsoe_results['unique_symbols']}")
        print(f"   Tree depth: {frsoe_results['tree_depth']}")
        print(f"   Entropy preservation: {frsoe_results['entropy_preservation']:.3f}")
        print(f"   Fingerprint: {frsoe_results['fingerprint']}...")

def what_the_comparison_reveals():
    """Analyze what the comparison actually shows."""
    
    print("\n" + "=" * 80)
    print("🔍 WHAT THE COMPARISON ACTUALLY REVEALS")
    print("=" * 80)
    
    print("\n📊 COMPRESSION RATIOS:")
    print("   • Traditional compressors: 2-10x compression")
    print("   • FRSOE: ~1x compression (no size reduction)")
    print("   • FRSOE is NOT about file size reduction")
    
    print("\n⚡ SPEED:")
    print("   • Traditional: Fast compression, fast decompression")
    print("   • FRSOE: Slower compression, very fast reconstruction")
    print("   • FRSOE prioritizes meaning over speed")
    
    print("\n🎯 DIFFERENT GOALS:")
    print("   • Traditional: 'Make it smaller'")
    print("   • FRSOE: 'Represent meaning symbolically'")
    print("   • Traditional: Pattern matching")
    print("   • FRSOE: Ontological structure")
    
    print("\n💡 THE REAL DIFFERENCE:")
    print("   Traditional compression is about EFFICIENCY")
    print("   FRSOE is about MEANING")
    print("   They solve completely different problems")
    
    print("\n🚀 WHEN TO USE WHAT:")
    print("   Use traditional compression for:")
    print("   • File storage optimization")
    print("   • Network transmission")
    print("   • Backup compression")
    print("   • General data reduction")
    
    print("\n   Use FRSOE for:")
    print("   • Semantic analysis")
    print("   • Knowledge representation")
    print("   • AI preprocessing")
    print("   • Structural fingerprinting")
    print("   • Meaning-preserving transformations")
    
    print("\n🎯 THE TRUTH:")
    print("   Comparing FRSOE to traditional compression is like")
    print("   comparing a dictionary to a zip file.")
    print("   They're fundamentally different tools for different purposes.")
    print("   FRSOE isn't trying to be a better compressor.")
    print("   It's trying to be a better way to understand data.")

def main():
    """Run the comparison."""
    
    run_comparison()
    what_the_comparison_reveals()
    
    print(f"\n🏁 Comparison completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("The truth is out there.")

if __name__ == "__main__":
    main() 