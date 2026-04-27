"""
HTML block rendering and Plotly hypergraph figure.
"""

import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import math
from tools.core.hyperletter import interpret
from tools.viz.word_parser import format_se

import plotly.graph_objects as go
import networkx as nx


COLORS = {
    'normal':      '#f0f0f0',
    'r1_dest':     '#aed6f1',
    'r1_src':      '#fadbd8',
    'r2_left':     '#d5f5e3',
    'r2_right':    '#fdebd0',
    'new_price_r': '#e8daef',
    'new_price_l': '#e8daef',
}


def render_hyperword_html(word, vertices, annotations: dict) -> str:
    """
    Return HTML with one color-coded <span> per block.
    annotations = {block_index: kind_str}
    """
    spans = []
    for idx, hl in enumerate(word):
        kind = annotations.get(idx, 'normal')
        color = COLORS.get(kind, COLORS['normal'])

        if not hl.elements:
            content = '&#8709;'  # ∅
        else:
            sorted_els = interpret(hl, vertices)
            content = ' '.join(format_se(se, vertices) for se in sorted_els)
            # HTML-escape < and > just in case
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        spans.append(
            f'<span style="background:{color}; padding:4px 10px; margin:3px; '
            f'border-radius:5px; font-family:monospace; font-size:15px; '
            f'display:inline-block;">{content}</span>'
        )

    inner = '\n'.join(spans)
    return (
        '<div style="display:flex; flex-wrap:wrap; gap:4px; padding:8px;">'
        + inner
        + '</div>'
    )


def make_hypergraph_figure(hg) -> go.Figure:
    """Build a Plotly figure visualizing the hypergraph."""
    G = nx.Graph()
    G.add_nodes_from(hg.vertices)
    for edge in hg.E2:
        v1, v2 = tuple(edge)
        G.add_edge(v1, v2)

    pos = nx.spring_layout(G, seed=42, k=2.0)

    fig = go.Figure()

    # Draw E2 edges
    for v1, v2 in G.edges():
        x0, y0 = pos[v1]
        x1, y1 = pos[v2]
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode='lines',
            line=dict(color='#888', width=2),
            hoverinfo='none',
            showlegend=False,
        ))

    # Draw hyperedges of size > 2 as filled polygons
    for edge in hg.maximal_edges:
        if len(edge) > 2:
            vs = sorted(edge, key=lambda v: hg.vertices.index(v))
            xs = [pos[v][0] for v in vs] + [pos[vs[0]][0]]
            ys = [pos[v][1] for v in vs] + [pos[vs[0]][1]]
            fig.add_trace(go.Scatter(
                x=xs, y=ys,
                fill='toself',
                fillcolor='rgba(174,214,241,0.25)',
                line=dict(color='rgba(100,150,200,0.4)', width=1),
                hoverinfo='none',
                showlegend=False,
            ))

    # Draw vertex nodes
    node_x = [pos[v][0] for v in hg.vertices]
    node_y = [pos[v][1] for v in hg.vertices]
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(size=20, color='#2980b9', line=dict(width=2, color='white')),
        text=list(hg.vertices),
        textposition='top center',
        textfont=dict(size=14, family='monospace'),
        hoverinfo='text',
        showlegend=False,
    ))

    fig.update_layout(
        title='Hypergraph χ',
        title_font_size=14,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        height=280,
    )
    return fig


def estimate_html_height(word) -> int:
    """Estimate pixel height for the HTML component."""
    return max(80, 60 + 40 * math.ceil(len(word) / 6))
