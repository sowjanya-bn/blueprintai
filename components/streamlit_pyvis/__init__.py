from __future__ import annotations

from pathlib import Path
from streamlit.components.v1 import declare_component

_HERE = Path(__file__).parent
_frontend_dir = str(_HERE / "frontend" / "build")

# In dev mode users can run `npm run build` which copies files into frontend/build
# declare the component (points to built frontend)
_component = declare_component("streamlit_pyvis", path=_frontend_dir)


def streamlit_pyvis(nodes: list[dict], edges: list[dict], selected_node: str = None):
    """Render an interactive graph and return the clicked node id or None.

    nodes: list of {id: str, label: str, title: str}
    edges: list of {source: str, target: str, title: str}
    selected_node: optional node id to pre-select/highlight in the frontend
    """
    # pass nodes and edges to the frontend; frontend may accept `selected_node` to pre-highlight
    return _component(nodes=nodes, edges=edges, selected_node=selected_node)
