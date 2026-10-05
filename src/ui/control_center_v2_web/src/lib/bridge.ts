export interface ConversationEntry {
  time: string;
  role: string;
  text: string;
}

export interface Telemetry {
  cpu: number | null;
  gpu: number | null;
  gpu_temp: number | null;
  ram: number | null;
  disk: number | null;
  vram: number | null;
  cpu_name: string;
  gpu_name: string;
  ram_text: string;
  vram_text: string;
  disk_text: string;
  battery: string;
}

export interface UiSnapshot {
  status: string;
  conversation: ConversationEntry[];
  telemetry: Telemetry | null;
  uptime_seconds: number;
  current_task: string | null;
  model: string | null;
  agent: string;
  voice: string;
  floating_orb_diameter: number;
}

interface QtBridge {
  requestSnapshot: (callback: (raw: string) => void) => void;
  snapshotChanged: { connect: (callback: (raw: string) => void) => void; disconnect: (callback: (raw: string) => void) => void };
  requestViewMode: (callback: (mode: string) => void) => void;
  modeChanged: { connect: (callback: (mode: string) => void) => void; disconnect: (callback: (mode: string) => void) => void };
  enterCompactOrbMode: () => void;
  leaveCompactOrbMode: () => void;
  moveOrbWindow: (dx: number, dy: number) => void;
  showOrbContextMenu: () => void;
  notifyFrontendReady: () => void;
  notifyFrameReady: () => void;
}

declare global {
  interface Window {
    qt?: { webChannelTransport: unknown };
    QWebChannel?: new (transport: unknown, ready: (channel: { objects: { nova: QtBridge } }) => void) => void;
    novaBridge?: QtBridge;
    __NOVA_UI_SNAPSHOT__?: UiSnapshot;
  }
}

// One channel owns the transport; React mounts own only their subscriptions.
let connection: { transport: unknown; ready: Promise<QtBridge> } | undefined;

export function connectNovaBridge(update: (snapshot: UiSnapshot) => void, updateMode: (mode: "control" | "orb") => void): () => void {
  if (!window.qt?.webChannelTransport || !window.QWebChannel) return () => {};
  const transport = window.qt.webChannelTransport;
  if (!connection || connection.transport !== transport) {
    const Channel = window.QWebChannel;
    connection = { transport, ready: new Promise(resolve => {
      new Channel(transport, ({ objects }) => resolve(objects.nova));
    }) };
  }
  let disposed = false;
  let disconnect = () => {};
  connection.ready.then((bridge) => {
    if (disposed) return;
    window.novaBridge = bridge;
    const consume = (raw: string) => {
      if (disposed) return;
      try {
        const snapshot = JSON.parse(raw) as UiSnapshot;
        window.__NOVA_UI_SNAPSHOT__ = snapshot;
        update(snapshot);
      } catch (error) {
        console.error("Invalid NOVA UI snapshot", error);
      }
    };
    bridge.snapshotChanged.connect(consume);
    bridge.requestSnapshot(consume);
    const consumeMode = (mode: string) => {
      if (!disposed) updateMode(mode === "orb" ? "orb" : "control");
    };
    bridge.modeChanged.connect(consumeMode);
    bridge.requestViewMode(consumeMode);
    disconnect = () => {
      bridge.snapshotChanged.disconnect(consume);
      bridge.modeChanged.disconnect(consumeMode);
      if (window.novaBridge === bridge) delete window.novaBridge;
    };
  });
  return () => {
    disposed = true;
    disconnect();
    disconnect = () => {};
  };
}
