import { useEffect, useRef, useState } from "react";
import Atmosphere from "./components/HUD/Atmosphere";
import CornerFrame from "./components/HUD/CornerFrame";
import StatusBar from "./components/HUD/StatusBar";
import TopBar from "./components/HUD/TopBar";
import Orb from "./components/Orb/Orb";
import { connectNovaBridge, type UiSnapshot } from "./lib/bridge";
import { useStore, type OrbState } from "./lib/store";
import "./styles/nova.css";

function orbState(status: string): OrbState {
  const normalized = status.toUpperCase();
  if (normalized === "LISTENING") return "listening";
  if (normalized === "SPEAKING") return "speaking";
  if (normalized === "THINKING") return "thinking";
  if (normalized === "PROCESSING") return "processing";
  if (normalized === "CODEX") return "codex";
  if (normalized === "SUCCESS") return "success";
  if (normalized === "ERROR") return "error";
  return "idle";
}

function percent(value: number | null | undefined): string {
  return value == null ? "—" : `${value}%`;
}

function Panel({ title, note, className, children }: {
  title: string; note?: string; className: string; children: React.ReactNode;
}) {
  return (
    <section className={`holo-panel nova-panel ${className}`}>
      <div className="nova-panel-head">
        <span className="nova-label"><span className="nova-dot" />{title}</span>
        {note && <span className="nova-panel-note">{note}</span>}
      </div>
      <div className="nova-panel-body">{children}</div>
    </section>
  );
}

function displayRole(role: string): string {
  const normalized = role.toUpperCase().replace(/\./g, "");
  if (normalized === "USER" || normalized === "ALFRED") return "ALFRED";
  if (normalized === "SYSTEM") return "SYSTEM";
  if (["NOVA", "JARVIS", "ASSISTANT"].includes(normalized)) return "N.O.V.A";
  return role.toUpperCase();
}

function sameConversation(a: UiSnapshot["conversation"], b: UiSnapshot["conversation"]): boolean {
  return a.length === b.length && a.every((entry, index) =>
    entry.time === b[index].time && entry.role === b[index].role && entry.text === b[index].text);
}

export default function App() {
  const [snapshot, setSnapshot] = useState<UiSnapshot | null>(null);
  const [viewMode, setViewMode] = useState<"control" | "orb">("control");
  const setOrbState = useStore((state) => state.setOrbState);
  const setAudioLevel = useStore((state) => state.setAudioLevel);
  const dialogueRef = useRef<HTMLDivElement>(null);
  const dragStart = useRef<{ x: number; y: number } | null>(null);
  const startupNotified = useRef(false);
  const firstFrameNotified = useRef(false);
  const hasSnapshot = snapshot !== null;

  useEffect(() => connectNovaBridge((next) => setSnapshot((previous) =>
    previous && sameConversation(previous.conversation, next.conversation)
      ? { ...next, conversation: previous.conversation }
      : next), setViewMode), []);
  useEffect(() => {
    if (!hasSnapshot || viewMode !== "control" || firstFrameNotified.current) return;
    if (!startupNotified.current) {
      startupNotified.current = true;
      window.novaBridge?.notifyFrontendReady();
    }
    const main = document.querySelector<HTMLElement>(".nova-control-mode");
    if (!main) return;
    let frame = 0;
    const observer = new ResizeObserver(() => {
      if (frame || firstFrameNotified.current || main.clientWidth < 1000 || main.clientHeight < 600) return;
      frame = requestAnimationFrame(() => { frame = requestAnimationFrame(() => { frame = requestAnimationFrame(() => {
        firstFrameNotified.current = true;
        window.novaBridge?.notifyFrameReady();
        observer.disconnect();
      }); }); });
    });
    observer.observe(main);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [hasSnapshot, viewMode]);
  useEffect(() => {
    if (viewMode !== "orb") return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") window.novaBridge?.leaveCompactOrbMode();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [viewMode]);
  useEffect(() => {
    const floating = viewMode === "orb";
    for (const element of [document.documentElement, document.body, document.getElementById("root")]) {
      element?.classList.toggle("nova-floating", floating);
    }
  }, [viewMode]);
  useEffect(() => {
    setOrbState(orbState(snapshot?.status ?? "STANDBY"));
  }, [snapshot?.status, setOrbState]);
  useEffect(() => {
    if (snapshot?.status !== "SPEAKING") {
      setAudioLevel(0);
      return;
    }
    const timer = window.setInterval(() => {
      const tick = performance.now() / 1000;
      setAudioLevel(0.28 + 0.21 * Math.abs(Math.sin(tick * 6.1)));
    }, 70);
    return () => window.clearInterval(timer);
  }, [snapshot?.status, setAudioLevel]);
  useEffect(() => {
    const pane = dialogueRef.current;
    if (pane) pane.scrollTop = pane.scrollHeight;
  }, [snapshot?.conversation, viewMode]);

  const telemetry = snapshot?.telemetry;
  const messages = snapshot?.conversation ?? [];
  const uptime = snapshot?.uptime_seconds ?? 0;
  const uptimeText = `${String(Math.floor(uptime / 3600)).padStart(2, "0")}:${String(Math.floor(uptime / 60) % 60).padStart(2, "0")}:${String(uptime % 60).padStart(2, "0")}`;

  return (
    <main className={`nova-screen ${viewMode === "orb" ? "nova-orb-mode" : "nova-control-mode"}`} data-nova-status={snapshot?.status ?? "CONNECTING"}
      style={snapshot ? { "--floating-orb-diameter": `${snapshot.floating_orb_diameter}px` } as React.CSSProperties : undefined}>
      <Atmosphere />
      <Orb />
      <CornerFrame />
      {viewMode === "control" ? <>
      <TopBar snapshot={snapshot} />
      <div className="nova-dashboard">
      <div className="nova-left-column">

      <Panel className="nova-telemetry" title="SYSTEM / TELEMETRY" note="LIVE">
        <span>CPU {percent(telemetry?.cpu)}</span><span>GPU {percent(telemetry?.gpu)}</span>
        <span>RAM {percent(telemetry?.ram)}</span>
      </Panel>

      <div className="nova-left-stack">

      <Panel className="nova-uptime" title="UPTIME" note="HUD">
        <div className="nova-micro">ONLINE DURATION</div>
        <div className="nova-uptime-value">{uptimeText}</div>
        <div className="nova-micro">NOVA · ALFRED'S PERSONAL ASSISTANT</div>
      </Panel>

      <Panel className="nova-mission" title="MISSION LOG" note={snapshot?.current_task ? "ACTIVE" : "IDLE"}>
        <span>{snapshot?.current_task || "NO ACTIVE TASK"}</span>
      </Panel>

      <Panel className="nova-tools" title="TOOL FEED" note="LIVE">
        <span>{snapshot?.current_task ? snapshot.current_task : "no tool activity"}</span>
      </Panel>
      </div>
      </div>

      <Panel className="nova-dialogue" title="DIALOGUE" note="CONVERSATION">
        <div className="nova-dialogue-scroll" ref={dialogueRef}>
          {messages.length === 0 && <div className="nova-empty">Awaiting NOVA conversation…</div>}
          {messages.map((entry, index) => (
            <div className="nova-dialogue-line" key={`${entry.time}-${index}`}>
              <span className="nova-prompt">{displayRole(entry.role)} &gt;</span>
              <span>{entry.text}</span>
            </div>
          ))}
        </div>
      </Panel>
      </div>

      <div className="holo-panel nova-command">
        <span className="nova-command-icon" aria-hidden="true">◉</span>
        <span className="nova-command-icon" aria-hidden="true">◖))</span>
        <div className="nova-command-status"><span className="nova-prompt">›</span> {snapshot ? `VOICE / COMMAND · ${snapshot.status}` : "Connecting to NOVA…"}</div>
        <button type="button" onClick={() => window.novaBridge?.enterCompactOrbMode()}>ORB MODE</button>
      </div>
      <StatusBar snapshot={snapshot} />
      </> : <>
        <div className="nova-floating-hitarea"
          onPointerDown={(event) => { if (event.button === 0) dragStart.current = { x: event.screenX, y: event.screenY }; }}
          onPointerMove={(event) => {
            const start = dragStart.current;
            if (start && (event.buttons & 1) && Math.hypot(event.screenX - start.x, event.screenY - start.y) > 3) {
              window.novaBridge?.moveOrbWindow(Math.round(event.screenX - start.x), Math.round(event.screenY - start.y));
              dragStart.current = { x: event.screenX, y: event.screenY };
            }
          }}
          onPointerUp={() => { dragStart.current = null; }}
          onDoubleClick={() => window.novaBridge?.leaveCompactOrbMode()}
          onContextMenu={(event) => { event.preventDefault(); window.novaBridge?.showOrbContextMenu(); }}
        >
          <div className="nova-orb-state">{snapshot?.status ?? "CONNECTING"}</div>
        </div>
      </>}
      {viewMode === "control" && <div className="nova-identity"><span>N.O.V.A</span><small>{snapshot?.status ?? "CONNECTING"}</small></div>}
    </main>
  );
}
