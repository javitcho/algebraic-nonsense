"""
Streamlit app: P2N Normal Form Explorer

Run from P2N-groups/:
    streamlit run tools/viz/app.py
"""

import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
import streamlit.components.v1 as components

from tests.fixtures import HEISENBERG, PATH, TRIANGLE
from tools.core.hypergraph import Hypergraph
from tools.core.alphabet import is_vertex, total_order_key
from tools.viz.trace import normal_form_with_trace
from tools.viz.word_parser import parse_word, format_se, format_hyperword
from tools.viz.rendering import render_hyperword_html, make_hypergraph_figure, estimate_html_height, render_all_steps_html

st.set_page_config(page_title='P2N Normal Form Explorer', layout='wide')

# ---------------------------------------------------------------------------
# Preset hypergraphs
# ---------------------------------------------------------------------------

PRESETS = {
    'Heisenberg': HEISENBERG,
    'Path':       PATH,
    'Triangle':   TRIANGLE,
}


def _build_custom_hg(vertices_text: str, edges_text: str):
    """Build a Hypergraph from raw user text. Returns (hg, error_str)."""
    try:
        verts = tuple(v.strip() for v in vertices_text.split(',') if v.strip())
        if not verts:
            return None, 'Enter at least one vertex.'
        explicit_edges = []
        for line in edges_text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split()]
            for p in parts:
                if p not in verts:
                    return None, f"Unknown vertex '{p}' in edge. Vertices: {list(verts)}"
            explicit_edges.append(frozenset(parts))

        # Dense closure
        all_edges = {frozenset()}
        for e in explicit_edges:
            subs = [frozenset(s) for k in range(len(e)+1) for s in _subsets(e, k)]
            for s in subs:
                all_edges.add(s)

        return Hypergraph(vertices=verts, edges=frozenset(all_edges)), None
    except Exception as exc:
        return None, str(exc)


def _subsets(s, k):
    s = list(s)
    if k == 0:
        yield []
    elif k > len(s):
        return
    else:
        first, rest = s[0], s[1:]
        for sub in _subsets(rest, k-1):
            yield [first] + sub
        yield from _subsets(rest, k)


def _alphabet_str(hg):
    verts = list(hg.vertices)
    edges = sorted(hg.E2, key=lambda e: tuple(sorted(e, key=lambda v: hg.vertices.index(v))))
    seps = ',' if any(len(v) > 1 for v in hg.vertices) else ''
    edge_names = []
    for e in edges:
        v1, v2 = sorted(e, key=lambda v: hg.vertices.index(v))
        edge_names.append(f'e_{{{v1}{seps}{v2}}}')
    return 'A = {' + ', '.join(verts + edge_names) + '}'


# ---------------------------------------------------------------------------
# Sidebar — hypergraph selector
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header('Hypergraph')
    preset_name = st.selectbox('Preset', list(PRESETS.keys()) + ['Custom'])

    if preset_name == 'Custom':
        verts_in = st.text_input('Vertices (comma-separated)', value='x, y, z')
        edges_in = st.text_area('Edges (one per line, space-separated vertices)',
                                value='x y\ny z', height=100)
        hg, err = _build_custom_hg(verts_in, edges_in)
        if err:
            st.error(err)
            hg = HEISENBERG
    else:
        hg = PRESETS[preset_name]

    st.plotly_chart(make_hypergraph_figure(hg), use_container_width=True)  # noqa: deprecated in newer Streamlit
    st.caption(_alphabet_str(hg))


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

st.title('P2N Normal Form Explorer')

col_input, col_btn = st.columns([5, 1])
with col_input:
    word_text = st.text_input('Word in A±', placeholder='x^-1 y^-1 x y',
                              label_visibility='collapsed')
with col_btn:
    compute = st.button('Compute', use_container_width=True)

# Store hypergraph in session state so step navigation doesn't re-parse with wrong hg
if 'hg_key' not in st.session_state:
    st.session_state['hg_key'] = preset_name

hg_changed = st.session_state.get('hg_key') != preset_name
if hg_changed:
    st.session_state['hg_key'] = preset_name
    st.session_state.pop('steps', None)

if compute and word_text.strip():
    try:
        lifted = parse_word(word_text.strip(), hg)
        steps = normal_form_with_trace(lifted, hg)
        st.session_state['steps'] = steps
        st.session_state['step_slider'] = 0  # reset slider to step 0
    except ValueError as exc:
        st.error(str(exc))

if not word_text.strip() and compute:
    st.info('Enter a word in A± above, then click Compute.')

# ---------------------------------------------------------------------------
# Step viewer
# ---------------------------------------------------------------------------

if 'steps' in st.session_state:
    steps = st.session_state['steps']
    n = len(steps)

    # Callbacks write directly to the slider's session-state key.
    def _prev():
        st.session_state['step_slider'] = max(0, st.session_state['step_slider'] - 1)

    def _next():
        st.session_state['step_slider'] = min(n - 1, st.session_state['step_slider'] + 1)

    nav_left, nav_slider, nav_right = st.columns([1, 10, 1])
    with nav_left:
        st.button('◀', on_click=_prev, use_container_width=True)
    with nav_slider:
        st.slider('Step', 0, n - 1, key='step_slider', format=f'%d / {n - 1}')
    with nav_right:
        st.button('▶', on_click=_next, use_container_width=True)

    idx = st.session_state['step_slider']
    step = steps[idx]

    # Termination measure cards for the highlighted step: f(w) = (n_V, K, T, len)
    n_V, K, T, length = step.measure
    if idx > 0:
        pn_V, _, pT, plength = steps[idx - 1].measure
        dn_V, dT, dlength = n_V - pn_V, T - pT, length - plength
    else:
        dn_V = dT = dlength = None

    m1, m2, m3 = st.columns(3)
    m1.metric('n_V', n_V, delta=dn_V, delta_color='inverse')
    m2.metric('T', T, delta=dT, delta_color='inverse')
    m3.metric('len', length, delta=dlength, delta_color='inverse')
    st.caption(f'K = {K}')

    # Scrollable history — all steps, highlighted step scrolled into view
    components.html(render_all_steps_html(steps, hg.vertices, idx), height=560)

    # Final normal form banner
    nf = steps[-1].word
    if nf:
        st.success(f'Normal form: {format_hyperword(nf, hg.vertices)}')
    else:
        st.success('Normal form: ε (identity)')
