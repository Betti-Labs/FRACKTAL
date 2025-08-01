#!/usr/bin/env python3
"""
FRACKTAL Command Line Interface

Provides command-line access to FRACKTAL's compression and analysis capabilities.
"""

import argparse
import sys
import json
import time
from pathlib import Path
from typing import Optional

from .recursive_compression import RecursiveFRSOE
from .core import FRSOE


def compress_file(input_path: str, output_path: Optional[str] = None, 
                  hash_depth: int = 4, min_pattern_length: int = 4, 
                  min_occurrences: int = 3, verbose: bool = False):
    """Compress a file using FRACKTAL."""
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        data = f.read()
    
    if verbose:
        print(f"📁 Reading file: {input_path}")
        print(f"📊 File size: {len(data):,} characters")
    
    # Initialize FRACKTAL
    engine = RecursiveFRSOE(
        hash_depth=hash_depth,
        min_pattern_length=min_pattern_length,
        min_occurrences=min_occurrences
    )
    
    # Compress
    start_time = time.time()
    compressed_result = engine.compress(data)
    compression_time = time.time() - start_time
    
    # Get statistics
    stats = compressed_result['combined_stats']
    
    if verbose:
        print(f"⚡ Compression time: {compression_time:.3f}s")
        print(f"📈 Compression ratio: {stats['overall_compression_ratio']:.2f}x")
        print(f"💾 Space saved: {stats['total_space_saved']} symbols")
        print(f"🔍 Patterns detected: {stats['pattern_count']}")
    
    # Save compressed result
    if output_path is None:
        output_path = input_path + '.fracktal'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(compressed_result, f, indent=2)
    
    if verbose:
        print(f"💾 Saved compressed data to: {output_path}")
    
    return compressed_result


def decompress_file(input_path: str, output_path: Optional[str] = None, verbose: bool = False):
    """Decompress a FRACKTAL compressed file."""
    
    # Read compressed file
    with open(input_path, 'r', encoding='utf-8') as f:
        compressed_result = json.load(f)
    
    if verbose:
        print(f"📁 Reading compressed file: {input_path}")
    
    # Initialize FRACKTAL
    engine = RecursiveFRSOE()
    
    # Reconstruct
    start_time = time.time()
    reconstructed = engine.reconstruct(compressed_result)
    reconstruction_time = time.time() - start_time
    
    if verbose:
        print(f"⚡ Reconstruction time: {reconstruction_time:.3f}s")
        print(f"📊 Reconstructed size: {len(reconstructed):,} characters")
    
    # Save reconstructed data
    if output_path is None:
        output_path = input_path.replace('.fracktal', '.decompressed')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(reconstructed)
    
    if verbose:
        print(f"💾 Saved reconstructed data to: {output_path}")
    
    return reconstructed


def analyze_file(input_path: str, hash_depth: int = 4, verbose: bool = False):
    """Analyze a file using FRACKTAL."""
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        data = f.read()
    
    if verbose:
        print(f"📁 Analyzing file: {input_path}")
        print(f"📊 File size: {len(data):,} characters")
    
    # Initialize FRACKTAL
    engine = RecursiveFRSOE(hash_depth=hash_depth)
    
    # Compress and analyze
    compressed_result = engine.compress(data)
    analysis = engine.get_detailed_analysis(compressed_result)
    
    # Display analysis
    print("\n🔬 FRACKTAL Analysis Results")
    print("=" * 50)
    
    # Basic stats
    stats = compressed_result['combined_stats']
    print(f"Compression Ratio: {stats['overall_compression_ratio']:.2f}x")
    print(f"Space Saved: {stats['total_space_saved']} symbols")
    print(f"Patterns Detected: {stats['pattern_count']}")
    
    # Pattern details
    if analysis['pattern_analysis']['pattern_details']:
        print(f"\n📊 Pattern Analysis:")
        for pattern_id, details in analysis['pattern_analysis']['pattern_details'].items():
            print(f"  {pattern_id}: {details['length']} symbols, "
                  f"{details['occurrences']} occurrences, "
                  f"{details['space_saved']} symbols saved")
    
    # Entropy analysis
    entropy = analysis['frsoe_analysis']
    print(f"\n🧮 Entropy Analysis:")
    print(f"  Structural Entropy: {entropy['structural_entropy']:.3f}")
    print(f"  Symbolic Entropy: {entropy['symbolic_entropy']:.3f}")
    print(f"  Entropy Preservation: {entropy['entropy_preservation']:.3f}")
    
    return analysis


def benchmark_file(input_path: str, verbose: bool = False):
    """Run compression benchmarks on a file."""
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        data = f.read()
    
    if verbose:
        print(f"📁 Benchmarking file: {input_path}")
        print(f"📊 File size: {len(data):,} characters")
    
    # Test different configurations
    configurations = [
        {"hash_depth": 3, "min_pattern_length": 3, "min_occurrences": 2},
        {"hash_depth": 4, "min_pattern_length": 4, "min_occurrences": 3},
        {"hash_depth": 5, "min_pattern_length": 5, "min_occurrences": 3},
    ]
    
    results = []
    
    for i, config in enumerate(configurations):
        if verbose:
            print(f"\n🧪 Test {i+1}: {config}")
        
        engine = RecursiveFRSOE(**config)
        
        start_time = time.time()
        compressed_result = engine.compress(data)
        compression_time = time.time() - start_time
        
        stats = compressed_result['combined_stats']
        results.append({
            'config': config,
            'compression_ratio': stats['overall_compression_ratio'],
            'space_saved': stats['total_space_saved'],
            'pattern_count': stats['pattern_count'],
            'compression_time': compression_time
        })
        
        if verbose:
            print(f"  Compression ratio: {stats['overall_compression_ratio']:.2f}x")
            print(f"  Compression time: {compression_time:.3f}s")
    
    # Display results
    print("\n📊 Benchmark Results")
    print("=" * 50)
    
    best_result = max(results, key=lambda x: x['compression_ratio'])
    
    for i, result in enumerate(results):
        config = result['config']
        print(f"Test {i+1}: hash_depth={config['hash_depth']}, "
              f"min_pattern={config['min_pattern_length']}, "
              f"min_occurrences={config['min_occurrences']}")
        print(f"  Compression: {result['compression_ratio']:.2f}x "
              f"({'🏆 BEST' if result == best_result else ''})")
        print(f"  Time: {result['compression_time']:.3f}s")
        print(f"  Patterns: {result['pattern_count']}")
    
    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FRACKTAL: Advanced semantic compression through recursive symbolic pattern recognition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fracktal compress input.txt                    # Compress a file
  fracktal compress input.txt -o output.fracktal # Specify output
  fracktal decompress input.fracktal             # Decompress a file
  fracktal analyze input.txt                     # Analyze file structure
  fracktal benchmark input.txt                   # Run compression benchmarks
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Compress command
    compress_parser = subparsers.add_parser('compress', help='Compress a file')
    compress_parser.add_argument('input', help='Input file path')
    compress_parser.add_argument('-o', '--output', help='Output file path')
    compress_parser.add_argument('--hash-depth', type=int, default=4, help='Hash depth (default: 4)')
    compress_parser.add_argument('--min-pattern-length', type=int, default=4, help='Minimum pattern length (default: 4)')
    compress_parser.add_argument('--min-occurrences', type=int, default=3, help='Minimum pattern occurrences (default: 3)')
    compress_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Decompress command
    decompress_parser = subparsers.add_parser('decompress', help='Decompress a file')
    decompress_parser.add_argument('input', help='Input compressed file path')
    decompress_parser.add_argument('-o', '--output', help='Output file path')
    decompress_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze file structure')
    analyze_parser.add_argument('input', help='Input file path')
    analyze_parser.add_argument('--hash-depth', type=int, default=4, help='Hash depth (default: 4)')
    analyze_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Run compression benchmarks')
    benchmark_parser.add_argument('input', help='Input file path')
    benchmark_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'compress':
            compress_file(
                args.input, args.output, 
                args.hash_depth, args.min_pattern_length, args.min_occurrences,
                args.verbose
            )
        elif args.command == 'decompress':
            decompress_file(args.input, args.output, args.verbose)
        elif args.command == 'analyze':
            analyze_file(args.input, args.hash_depth, args.verbose)
        elif args.command == 'benchmark':
            benchmark_file(args.input, args.verbose)
    
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 