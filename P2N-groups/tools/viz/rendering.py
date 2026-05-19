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


def _block_span(hl, vertices, color) -> str:
    if not hl.elements:
        content = '&#8709;'
    else:
        sorted_els = interpret(hl, vertices)
        content = ' '.join(format_se(se, vertices) for se in sorted_els)
        content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        f'<span style="background:{color}; padding:2px 8px; margin:2px; '
        f'border-radius:4px; display:inline-block; white-space:nowrap;">{content}</span>'
    )


def render_all_steps_html(steps, vertices, current_idx: int) -> str:
    """
    Render all rewriting steps as a single scrollable HTML list.
    The current step is highlighted with a blue left border; all steps show
    their color-coded blocks and (f1, f2, f3) measure.
    JS scrollIntoView brings the current step into view on each rerender.
    """
    rows = []
    for i, step in enumerate(steps):
        is_current = (i == current_idx)
        border_color = '#2980b9' if is_current else '#ddd'
        bg = '#eaf4fb' if is_current else 'transparent'
        f1, f2, f3 = step.measure

        if step.rule is None:
            label = '<b>Step 0</b> — Initial word (σ)'
        else:
            label = f'<b>Step {i}</b> — {step.description}'

        blocks_html = ''.join(
            _block_span(hl, vertices, COLORS.get(step.annotations.get(j, 'normal'), COLORS['normal']))
            for j, hl in enumerate(step.word)
        )

        rows.append(
            f'<div id="step-{i}" style="padding:6px 10px; margin-bottom:5px; '
            f'border-left:3px solid {border_color}; background:{bg}; border-radius:0 4px 4px 0;">'
            f'<div style="font-size:11px; color:#555; margin-bottom:4px;">'
            f'{label}&nbsp;&nbsp;'
            f'<span style="color:#999;">(f₁={f1}, f₂={f2}, f₃={f3})</span>'
            f'</div>'
            f'<div style="display:flex; flex-wrap:wrap; gap:0; font-size:13px; font-family:monospace;">'
            f'{blocks_html}'
            f'</div></div>'
        )

    all_rows = '\n'.join(rows)
    # Scroll the highlighted step into view whenever the component rerenders
    scroll_js = (
        f'var el=document.getElementById("step-{current_idx}");'
        f'if(el)el.scrollIntoView({{behavior:"smooth",block:"nearest"}});'
    )
    return (
        f'<div style="height:520px; overflow-y:auto; padding:4px; font-family:sans-serif;">'
        f'{all_rows}'
        f'</div>'
        f'<script>{scroll_js}</script>'
    )
