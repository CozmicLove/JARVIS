// State values are renderer parameters, not separate scene implementations.
export const STATES = Object.freeze({
  STANDBY:    { activity: .22, energy: .30, ring: .09, flow: .35, turbulence: .20, particles: .26, shell: .30 },
  LISTENING:  { activity: .60, energy: .62, ring: .18, flow: .65, turbulence: .36, particles: .48, shell: .55 },
  PROCESSING: { activity: .72, energy: .69, ring: .30, flow: .82, turbulence: .54, particles: .47, shell: .46 },
  THINKING:   { activity: .82, energy: .77, ring: .36, flow: 1.05, turbulence: .82, particles: .68, shell: .59 },
  SPEAKING:   { activity: .70, energy: .70, ring: .23, flow: .78, turbulence: .48, particles: .50, shell: .56 },
  CODEX:      { activity: .79, energy: .75, ring: .36, flow: .95, turbulence: .61, particles: .53, shell: .62 },
  SUCCESS:    { activity: .73, energy: .79, ring: .27, flow: .78, turbulence: .42, particles: .56, shell: .64 },
  ERROR:      { activity: .65, energy: .59, ring: .22, flow: .75, turbulence: .68, particles: .43, shell: .51 },
});

export const VIEWS = new Set(['CONTROL_CENTER', 'ORB']);

export function createReactiveState() {
  return {
    state: 'STANDBY', viewMode: 'ORB', stateSince: 0,
    activity: .22, energyLevel: .30, audioLevel: 0,
    ringSpeed: .09, flowSpeed: .35, turbulence: .20,
    particleLevel: .26, shellGlow: .30, transient: 0,
  };
}

export function updateReactive(reactive, elapsed, dt) {
  const target = STATES[reactive.state];
  const blend = 1 - Math.exp(-Math.min(dt, .1) * 4.5);
  const lerp = (value, goal) => value + (goal - value) * blend;
  reactive.activity = lerp(reactive.activity, target.activity);
  reactive.energyLevel = lerp(reactive.energyLevel, target.energy);
  reactive.ringSpeed = lerp(reactive.ringSpeed, target.ring);
  reactive.flowSpeed = lerp(reactive.flowSpeed, target.flow);
  reactive.turbulence = lerp(reactive.turbulence, target.turbulence);
  reactive.particleLevel = lerp(reactive.particleLevel, target.particles);
  reactive.shellGlow = lerp(reactive.shellGlow, target.shell);
  const simulatedAudio = reactive.state === 'SPEAKING'
    ? .30 + .28 * Math.sin(elapsed * 8.7) ** 2 + .16 * Math.sin(elapsed * 13.1) ** 2
    : reactive.state === 'LISTENING' ? .09 + .10 * Math.sin(elapsed * 4.5) ** 2 : 0;
  reactive.audioLevel = lerp(reactive.audioLevel,
    reactive.externalAudioLevel ?? simulatedAudio);
  const age = elapsed - reactive.stateSince;
  reactive.transient = (reactive.state === 'SUCCESS' || reactive.state === 'ERROR')
    ? Math.max(0, 1 - age / 1.25) : 0;
  return reactive;
}
