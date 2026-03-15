from __future__ import annotations

from pathlib import Path
from streamlit.components.v1 import declare_component

_HERE = Path(__file__).parent
_frontend_dir = str(_HERE / "frontend" / "build")

# In dev mode users can run `npm run build` which copies files into frontend/build
# declare the component (points to built frontend)
_component = declare_component("streamlit_pyvis", path=_frontend_dir)


def streamlit_pyvis(nodes: list[dict], edges: list[dict]):
    """Render an interactive graph and return the clicked node id or None.

    nodes: list of {id: str, label: str, title: str}
    edges: list of {source: str, target: str, title: str}
    """
    # pass nodes and edges to the frontend; it will call setComponentValue with {selected_node}
    return _component(nodes=nodes, edges=edges)
