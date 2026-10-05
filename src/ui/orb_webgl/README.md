# NOVA Orb WebGL prototype

Run from the repository root with `kokoro_env\Scripts\python.exe src\ui\orb_preview.py`
or an equivalent Python environment with PySide6 WebEngine installed. F5 reloads
the page. Use the eight small state buttons and the two view buttons to compare
the animations and camera compositions.

The page loads only local files. `orb.js`, `core.js`, `rings.js`,
`particles.js`, and `states.js` are the editable source;
`vendor/nova-orb.bundle.js` is the offline runtime bundle containing Three.js.
After editing `orb.js`, rebuild the bundle with esbuild and Three.js 0.185.1:

```powershell
npm install --prefix <temporary-build-dir> three@0.185.1 esbuild@0.25.12
$env:NODE_PATH = '<temporary-build-dir>\node_modules'
& '<temporary-build-dir>\node_modules\.bin\esbuild.cmd' src/ui/orb_webgl/orb.js --bundle --minify --format=iife --target=chrome120 --outfile=src/ui/orb_webgl/vendor/nova-orb.bundle.js
```

This prototype is separate from the production Control Center.
