"""
FRACKTAL Utilities: Visualization and Analysis Tools

Optional utilities for analyzing and visualizing FRACKTAL compression results.
These functions require matplotlib and seaborn to be installed.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import hashlib
import json
from datetime import datetime

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    _has_visualization = True
except ImportError:
    _has_visualization = False
    print("Warning: matplotlib/seaborn not available. Visualization functions disabled.")


def entropy_analysis(codex_map: CodexMap, hash_depths: List[int] = None) -> Dict[str, Any]:
    """
    Perform comprehensive entropy analysis on a CodexMap.
    
    Args:
        codex_map: CodexMap object to analyze
        hash_depths: List of hash depths to test (default: 1-10)
        
    Returns:
        Dictionary containing entropy analysis results
    """
    if hash_depths is None:
        hash_depths = list(range(1, 11))
    
    results = {
        "original_entropy": _calculate_entropy(codex_map.original_data),
        "symbolic_entropy": _calculate_entropy("".join(codex_map.get_symbol_sequence())),
        "hash_depths": hash_depths,
        "fractal_entropies": [],
        "entropy_preservation": []
    }
    
    # Calculate fractal entropy for different depths
    for depth in hash_depths:
        fractal_hashes = []
        for symbol in codex_map.get_symbol_sequence():
            h = symbol
            for _ in range(depth):
                h = hashlib.sha256(h.encode()).hexdigest()
            fractal_hashes.append(h)
        
        fractal_entropy = _calculate_entropy("".join(fractal_hashes))
        results["fractal_entropies"].append(fractal_entropy)
        results["entropy_preservation"].append(fractal_entropy / results["original_entropy"])
    
    return results


def _calculate_entropy(data: str) -> float:
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


def visualize_tree(symbolic_tree: SymbolicTree, 
                  output_path: Optional[str] = None,
                  interactive: bool = True) -> go.Figure:
    """
    Create an interactive visualization of the Recursive Symbolic Ontology tree.
    
    Args:
        symbolic_tree: SymbolicTree object to visualize
        output_path: Optional path to save the visualization
        interactive: Whether to create an interactive plotly figure
        
    Returns:
        Plotly figure object
    """
    # Create NetworkX graph
    G = nx.DiGraph()
    
    # Add nodes and edges
    for symbol, data in symbolic_tree.nodes.items():
        G.add_node(symbol, **data)
        if data.get("link"):
            G.add_edge(data["link"], symbol)
    
    # Calculate layout
    pos = nx.spring_layout(G, k=3, iterations=50)
    
    if interactive:
        # Create interactive plotly visualization
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"Symbol: {node}<br>Depth: {G.nodes[node]['depth']}")
            node_colors.append(G.nodes[node]['depth'])
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[node for node in G.nodes()],
            textposition="middle center",
            marker=dict(
                showscale=True,
                colorscale='Viridis',
                size=20,
                color=node_colors,
                colorbar=dict(
                    thickness=15,
                    title='Tree Depth',
                    xanchor="left",
                    len=0.5
                ),
                line_width=2))
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Recursive Symbolic Ontology Tree',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        if output_path:
            fig.write_html(output_path)
        
        return fig
    
    else:
        # Create static matplotlib visualization
        plt.figure(figsize=(12, 8))
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=1000, font_size=8, font_weight='bold',
                arrows=True, edge_color='gray', arrowsize=20)
        plt.title("Recursive Symbolic Ontology Tree")
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
        
        plt.show()


def generate_codex(codex_map: CodexMap, 
                  output_path: Optional[str] = None,
                  include_visualizations: bool = True) -> Dict[str, Any]:
    """
    Generate a comprehensive codex report with visualizations and analysis.
    
    Args:
        codex_map: CodexMap object to analyze
        output_path: Optional path to save the report
        include_visualizations: Whether to include visualizations
        
    Returns:
        Dictionary containing the complete codex report
    """
    report = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "original_length": len(codex_map.original_data),
            "symbol_count": codex_map.symbol_count,
            "unique_symbols": codex_map.unique_symbols,
            "tree_depth": codex_map.tree_depth,
            "compression_ratio": codex_map.compression_ratio,
            "fingerprint": codex_map.fingerprint
        },
        "symbol_analysis": {
            "symbol_sequence": codex_map.get_symbol_sequence(),
            "symbol_frequency": codex_map.get_symbol_frequency(),
            "most_common_symbols": sorted(
                codex_map.get_symbol_frequency().items(), 
                key=lambda x: x[1], reverse=True
            )[:10]
        },
        "hash_analysis": {
            "hash_sequence": codex_map.get_hash_sequence(),
            "hash_frequency": codex_map.get_hash_frequency(),
            "most_common_hashes": sorted(
                codex_map.get_hash_frequency().items(), 
                key=lambda x: x[1], reverse=True
            )[:10]
        },
        "entropy_analysis": entropy_analysis(codex_map),
        "tree_structure": {
            "max_depth": codex_map.symbolic_tree.max_depth,
            "node_count": codex_map.symbolic_tree.node_count,
            "root_nodes": codex_map.symbolic_tree.root_nodes,
            "depth_distribution": _get_depth_distribution(codex_map.symbolic_tree)
        }
    }
    
    if include_visualizations:
        report["visualizations"] = {
            "tree_plot": visualize_tree(codex_map.symbolic_tree),
            "entropy_plot": _create_entropy_plot(report["entropy_analysis"]),
            "symbol_frequency_plot": _create_frequency_plot(
                report["symbol_analysis"]["symbol_frequency"], 
                "Symbol Frequency Distribution"
            ),
            "hash_frequency_plot": _create_frequency_plot(
                report["hash_analysis"]["hash_frequency"], 
                "Fractal Hash Frequency Distribution"
            )
        }
    
    if output_path:
        # Save report as JSON
        import json
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
    
    return report


def _get_depth_distribution(symbolic_tree: SymbolicTree) -> Dict[int, int]:
    """Get distribution of nodes by depth."""
    depth_counts = {}
    for node_data in symbolic_tree.nodes.values():
        depth = node_data.get("depth", 0)
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    return depth_counts


def _create_entropy_plot(entropy_data: Dict[str, Any]) -> go.Figure:
    """Create entropy analysis plot."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=entropy_data["hash_depths"],
        y=entropy_data["fractal_entropies"],
        mode='lines+markers',
        name='Fractal Entropy',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))
    
    fig.add_hline(
        y=entropy_data["original_entropy"],
        line_dash="dash",
        line_color="red",
        annotation_text="Original Entropy"
    )
    
    fig.add_hline(
        y=entropy_data["symbolic_entropy"],
        line_dash="dash",
        line_color="green",
        annotation_text="Symbolic Entropy"
    )
    
    fig.update_layout(
        title="Entropy Analysis Across Hash Depths",
        xaxis_title="Hash Depth",
        yaxis_title="Entropy (bits)",
        showlegend=True
    )
    
    return fig


def _create_frequency_plot(frequency_data: Dict[str, int], title: str) -> go.Figure:
    """Create frequency distribution plot."""
    # Sort by frequency
    sorted_items = sorted(frequency_data.items(), key=lambda x: x[1], reverse=True)
    labels, values = zip(*sorted_items[:20])  # Top 20
    
    fig = go.Figure(data=[
        go.Bar(x=labels, y=values, marker_color='lightblue')
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Items",
        yaxis_title="Frequency",
        showlegend=False
    )
    
    return fig


def compare_codexes(codex_maps: List[CodexMap], 
                   labels: Optional[List[str]] = None) -> go.Figure:
    """
    Compare multiple CodexMaps side by side.
    
    Args:
        codex_maps: List of CodexMap objects to compare
        labels: Optional labels for each codex
        
    Returns:
        Plotly figure with comparison visualizations
    """
    if labels is None:
        labels = [f"Codex {i+1}" for i in range(len(codex_maps))]
    
    # Prepare comparison data
    comparison_data = {
        "labels": labels,
        "compression_ratios": [cm.compression_ratio for cm in codex_maps],
        "symbol_counts": [cm.symbol_count for cm in codex_maps],
        "unique_symbols": [cm.unique_symbols for cm in codex_maps],
        "tree_depths": [cm.tree_depth for cm in codex_maps],
        "entropies": [_calculate_entropy(cm.original_data) for cm in codex_maps]
    }
    
    # Create subplots
    fig = go.Figure()
    
    # Compression ratio comparison
    fig.add_trace(go.Bar(
        x=labels,
        y=comparison_data["compression_ratios"],
        name="Compression Ratio",
        marker_color='lightblue'
    ))
    
    fig.update_layout(
        title="Codex Comparison",
        xaxis_title="Codex",
        yaxis_title="Compression Ratio",
        showlegend=True
    )
    
    return fig


def create_symbolic_heatmap(codex_map: CodexMap, 
                          window_size: int = 5) -> go.Figure:
    """
    Create a heatmap showing symbolic patterns in the codex.
    
    Args:
        codex_map: CodexMap object to analyze
        window_size: Size of sliding window for pattern analysis
        
    Returns:
        Plotly heatmap figure
    """
    symbols = codex_map.get_symbol_sequence()
    
    # Create sliding window patterns
    patterns = []
    for i in range(len(symbols) - window_size + 1):
        pattern = symbols[i:i+window_size]
        patterns.append(pattern)
    
    # Count pattern frequencies
    pattern_counts = {}
    for pattern in patterns:
        pattern_str = " → ".join(pattern)
        pattern_counts[pattern_str] = pattern_counts.get(pattern_str, 0) + 1
    
    # Create heatmap data
    unique_symbols = list(set(symbols))
    symbol_to_idx = {symbol: i for i, symbol in enumerate(unique_symbols)}
    
    # Create transition matrix
    matrix = np.zeros((len(unique_symbols), len(unique_symbols)))
    for i in range(len(symbols) - 1):
        current = symbol_to_idx[symbols[i]]
        next_symbol = symbol_to_idx[symbols[i+1]]
        matrix[current][next_symbol] += 1
    
    # Normalize
    matrix = matrix / matrix.sum(axis=1, keepdims=True)
    matrix = np.nan_to_num(matrix, 0)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=unique_symbols,
        y=unique_symbols,
        colorscale='Viridis',
        text=np.round(matrix, 3),
        texttemplate="%{text}",
        textfont={"size": 8}
    ))
    
    fig.update_layout(
        title=f"Symbolic Transition Matrix (Window Size: {window_size})",
        xaxis_title="Next Symbol",
        yaxis_title="Current Symbol"
    )
    
    return fig 