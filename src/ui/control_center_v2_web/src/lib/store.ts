import { create } from "zustand";

export type OrbState = "idle" | "listening" | "thinking" | "speaking" | "processing" | "codex" | "success" | "error";

interface OrbStore {
  orbState: OrbState;
  audioLevel: number;
  setOrbState: (value: OrbState) => void;
  setAudioLevel: (value: number) => void;
}

export const useStore = create<OrbStore>((set) => ({
  orbState: "idle",
  audioLevel: 0,
  setOrbState: (orbState) => set({ orbState }),
  setAudioLevel: (audioLevel) => set({ audioLevel }),
}));
