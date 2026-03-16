/*
  Shim for Streamlit custom component loader.
  Loads vis-network.min.js first, then the main index.js bundle.
  This file satisfies Streamlit's expectation for
  streamlit_component_lib.js in the frontend build folder.
*/
(function(){
  function loadScript(src, cb) {
    var s = document.createElement('script');
    s.src = src;
    s.onload = function() { if (cb) cb(); };
    s.onerror = function(e) { console.error('Error loading script', src, e); if (cb) cb(); };
    document.head.appendChild(s);
  }

  // Load vis-network first to ensure `vis` is available for index.js
  loadScript('./vis-network.min.js', function(){
    loadScript('./index.js');
  });
})();
