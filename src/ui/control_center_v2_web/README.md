# NOVA Control Center V2 presentation

This directory is the presentation-only web layer embedded by the existing
PySide6 `ControlCenter` through `QWebEngineView`. It is not a replacement for
the NOVA runtime. The visual foundation and orb renderer are adapted from
Dix01/JARVIS; see the repository-root `LICENSE_THIRD_PARTY.md` and
`DONOR_LICENSE`.

To rebuild the local assets from this directory:

```powershell
npm ci --ignore-scripts --no-audit --no-fund
npm run build
```

The application loads `dist/index.html` directly. Keep `dist/` available with
the source for startup; `node_modules/` and `*.tsbuildinfo` are not needed at
runtime. `NOVA_UI_LEGACY=1` selects the previous PySide6 layout for comparison.

Python publishes an allowlisted JSON snapshot over QWebChannel: status,
conversation, SystemMonitor telemetry, uptime, and known metadata. The only
web-to-Python action is `openOrbMode()`. Missing data is displayed as `—`,
`IDLE`, or `NO ACTIVE TASK`; the browser does not call donor APIs or run
backend commands.
