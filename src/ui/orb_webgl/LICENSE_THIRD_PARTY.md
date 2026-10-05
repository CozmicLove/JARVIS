# Third-party notices

## Three.js

The local bundle `vendor/nova-orb.bundle.js` includes Three.js 0.185.1 and its post-processing modules. Source: https://github.com/mrdoob/three.js

The MIT License

Copyright © 2010-2026 three.js authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

## Donor renderer references

The NOVA V2 scene adapts technical patterns from the following MIT projects.
All scene code was rewritten for NOVA; no donor assets, branding, UI, gesture
control, camera input, or application framework were copied.

- **Primary:** https://github.com/joehehe0426/jarvis-orb, `lib/orbScene.ts`.
  Adapted its icosahedron-edge shell, spherical particle distribution, layered
  scene graph, independent rotations, and composer/bloom structure. The README
  states MIT; the repository had no separate `LICENSE` file when consulted on
  2026-09-27. Attribution: joehehe0426.
- **Secondary:** https://github.com/Anshchopra07/jarvis, `lib/orbScene.ts`.
  Adapted its concept of a curved 3D spiral inner core and mutually tilted
  layers. Copyright (c) 2026 Sagar Tamang. MIT license.
- **Reactive visual reference:** https://github.com/dyoburon/jarvis,
  `legacy/metal-app/Sources/JarvisBootup/Visualizer/VisualizerManager.swift`,
  `jarvis-rs/crates/jarvis-config/src/schema/visualizer.rs`, and
  `docs/manual/10-renderer.md`. Adapted the separation of state, intensity,
  power and audio-level parameters; no source code was copied. Copyright (c)
  2026 Dylan. MIT license.

For MIT-licensed donor patterns, the applicable permission and disclaimer are:

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
