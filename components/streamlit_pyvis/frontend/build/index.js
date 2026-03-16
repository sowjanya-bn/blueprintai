const Streamlit = window.Streamlit;

let network = null;
let nodeDataset = null;
let edgeDataset = null;

function toNode(item) {
  return {
    id: item.id,
    label: item.label || item.id,
    title: item.title || "",
  };
}

function toEdge(item) {
  return {
    from: item.source,
    to: item.target,
    title: item.title || "",
  };
}

function ensureNetwork(container) {
  if (network) {
    return;
  }

  nodeDataset = new vis.DataSet([]);
  edgeDataset = new vis.DataSet([]);

  network = new vis.Network(
    container,
    { nodes: nodeDataset, edges: edgeDataset },
    {
      interaction: { hover: true },
      nodes: { shape: "dot", size: 16, font: { size: 12 } },
      edges: { arrows: "to" },
      physics: { stabilization: true },
    }
  );

  network.on("click", function onClick(params) {
    if (params.nodes && params.nodes.length > 0) {
      Streamlit.setComponentValue({ selected_node: params.nodes[0] });
    }
  });

  window._blueprint_network = network;
}

function highlightSelectedNode(selectedNode) {
  const ids = nodeDataset.getIds();
  if (ids.length > 0) {
    nodeDataset.update(ids.map(function mapId(id) {
      return { id: id, color: undefined };
    }));
  }

  if (selectedNode && nodeDataset.get(selectedNode)) {
    nodeDataset.update({
      id: selectedNode,
      color: { background: "#f08a8a", border: "#aa0000" },
    });
    network.selectNodes([selectedNode]);
    network.focus(selectedNode, { scale: 1.2, animation: { duration: 250 } });
  }
}

function onRender(event) {
  const args = (event && event.detail && event.detail.args) || {};
  const nodes = Array.isArray(args.nodes) ? args.nodes : [];
  const edges = Array.isArray(args.edges) ? args.edges : [];
  const selected = args.selected_node || null;

  const container = document.getElementById("mynetwork");
  if (!container || typeof vis === "undefined") {
    Streamlit.setFrameHeight();
    return;
  }

  ensureNetwork(container);

  nodeDataset.clear();
  edgeDataset.clear();
  nodeDataset.add(nodes.map(toNode));
  edgeDataset.add(edges.map(toEdge));

  highlightSelectedNode(selected);
  Streamlit.setFrameHeight();
}

if (Streamlit && Streamlit.events) {
  Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
  Streamlit.setComponentReady();
  Streamlit.setFrameHeight();
} else {
  console.error("Streamlit component library did not load.");
}
