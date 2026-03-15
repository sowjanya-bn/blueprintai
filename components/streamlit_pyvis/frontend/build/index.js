// Minimal frontend for the Streamlit PyVis-style component
const Streamlit = window.streamlitComponentReady ? window.streamlitComponentReady() : window.Streamlit;

function renderNetwork(nodes, edges) {
  const container = document.getElementById('mynetwork');
  const nodeDataset = new vis.DataSet(nodes.map(n => ({id: n.id, label: n.label || n.id, title: n.title || ''})));
  const edgeDataset = new vis.DataSet(edges.map(e => ({from: e.source, to: e.target, title: e.title || ''})));
  const data = { nodes: nodeDataset, edges: edgeDataset };

  const options = {
    interaction: {hover: true},
    nodes: {shape: 'dot', size: 16, font: {size: 12}},
    edges: {arrows: 'to'},
    physics: {stabilization: true}
  };

  const network = new vis.Network(container, data, options);

  network.on('click', function(params) {
    if (params.nodes && params.nodes.length > 0) {
      const nid = params.nodes[0];
      // send clicked node id back to Streamlit
      Streamlit.setComponentValue({selected_node: nid});
    }
  });

  // expose to window for debugging
  window._blueprint_network = network;

  return {network, nodeDataset, edgeDataset};

  // expose to window for debugging
  window._blueprint_network = network;
}

// Wait for initial props from Python
window.addEventListener('message', (event) => {
  const data = event.data;
  if (data && data.type === 'STREAMLIT:SET_COMPONENT_VALUE') return;
});

// Using the streamlit component API to receive args
if (window.Streamlit) {
  window.Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, (event) => {
    const args = window.Streamlit.getComponentArgs();
    const nodes = (args && args.nodes) ? args.nodes : [];
    const edges = (args && args.edges) ? args.edges : [];
      const selected = args && args.selected_node ? args.selected_node : null;
      const rendered = renderNetwork(nodes, edges);

      // if there's a preselected node, highlight it
      try {
        const {network, nodeDataset} = rendered;
        // reset previous colors
        nodeDataset.getIds().forEach(id => {
          nodeDataset.update({id: id, color: undefined});
        });

        if (selected) {
          // apply highlight color
          nodeDataset.update({id: selected, color: {background: '#f08a8a', border: '#aa0000'}});
          network.selectNodes([selected]);
          network.focus(selected, {scale: 1.2});
        }
      } catch (e) {
        // ignore
      }

      Streamlit.setFrameHeight();
  });
}
