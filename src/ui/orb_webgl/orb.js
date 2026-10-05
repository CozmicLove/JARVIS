// NOVA 3D Core V2. Donor acknowledgements and licences: LICENSE_THIRD_PARTY.md.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { createCore } from './core.js';
import { createRings } from './rings.js';
import { createParticles } from './particles.js';
import { STATES, VIEWS, createReactiveState, updateReactive } from './states.js';

const viewport = document.getElementById('viewport');
const stateLabel = document.getElementById('state-label');
const errorBox = document.getElementById('render-error');
const stateButtons = [...document.querySelectorAll('[data-state]')];
const viewButtons = [...document.querySelectorAll('[data-view]')];
const reactive = createReactiveState();

// Real depth bands: background space, chamber, tilted orbits, foreground dust.
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, 1, .1, 60);
camera.position.set(0, 0, 7.5);
const world = new THREE.Group();
scene.add(world);

let renderer, composer, bloom;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.06;
  viewport.appendChild(renderer.domElement);
  composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), .45, .48, .72);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
} catch (error) {
  errorBox.hidden = false;
  errorBox.textContent = `WebGL unavailable: ${error.message}`;
  throw error;
}

const core = createCore();
const rings = createRings();
world.add(core.group, rings.group);
const particles = createParticles(scene, world);

let disposed = false;
let raf = 0;
let lastTime = performance.now() / 1000;
let fpsStart = performance.now();
let fpsFrames = 0;
let fps = 0;
let totalFrames = 0;
let pointerX = 0;
let pointerY = 0;
let cameraX = 0;
let cameraY = 0;
let cameraZ = 7.5;
let worldScale = 1;
const lookTarget = new THREE.Vector3(0, 0, 0);

function setState(value) {
  const next = String(value).toUpperCase();
  if (!Object.hasOwn(STATES, next)) return false;
  reactive.state = next;
  reactive.stateSince = performance.now() / 1000;
  stateLabel.textContent = next;
  stateButtons.forEach(button => button.classList.toggle('active', button.dataset.state === next));
  return true;
}

function setViewMode(value) {
  const next = String(value).toUpperCase();
  if (!VIEWS.has(next)) return false;
  reactive.viewMode = next;
  viewButtons.forEach(button => button.classList.toggle('active', button.dataset.view === next));
  return true;
}

function setAudioLevel(level) {
  // Reserved for later host integration. This prototype uses simulated amplitude.
  const value = Number(level);
  if (!Number.isFinite(value)) return false;
  reactive.externalAudioLevel = THREE.MathUtils.clamp(value, 0, 1);
  return true;
}

window.setState = setState;
window.setViewMode = setViewMode;
window.setAudioLevel = setAudioLevel;
window.novaOrbStatus = () => ({
  state: reactive.state, viewMode: reactive.viewMode, fps,
  width: viewport.clientWidth, height: viewport.clientHeight,
  webgl: !!renderer.getContext(), frames: totalFrames,
  camera: [Number(camera.position.x.toFixed(3)), Number(camera.position.y.toFixed(3)), Number(camera.position.z.toFixed(3))],
  activity: Number(reactive.activity.toFixed(2)),
  energyLevel: Number(reactive.energyLevel.toFixed(2)),
  audioLevel: Number(reactive.audioLevel.toFixed(2)),
});

stateButtons.forEach(button => button.addEventListener('click', () => setState(button.dataset.state)));
viewButtons.forEach(button => button.addEventListener('click', () => setViewMode(button.dataset.view)));
viewport.addEventListener('pointermove', event => {
  const rect = viewport.getBoundingClientRect();
  pointerX = THREE.MathUtils.clamp((event.clientX - rect.left) / rect.width * 2 - 1, -1, 1);
  pointerY = THREE.MathUtils.clamp((event.clientY - rect.top) / rect.height * 2 - 1, -1, 1);
});
viewport.addEventListener('pointerleave', () => { pointerX = 0; pointerY = 0; });

function resize() {
  const width = Math.max(1, viewport.clientWidth);
  const height = Math.max(1, viewport.clientHeight);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
  composer.setSize(width, height);
  bloom.resolution.set(width, height);
}
const observer = new ResizeObserver(resize);
observer.observe(viewport);
resize();

function animate(nowMs) {
  if (disposed) return;
  raf = requestAnimationFrame(animate);
  if (document.hidden) return;
  const t = nowMs / 1000;
  const dt = Math.min(.1, Math.max(0, t - lastTime));
  lastTime = t;
  updateReactive(reactive, t, dt);

  const mode = reactive.viewMode === 'ORB' ? 1 : 0;
  const targetZ = mode ? 7.5 : 9.1;
  const targetScale = mode ? 1 : .94;
  const response = 1 - Math.exp(-dt * 2.8);
  cameraZ += (targetZ - cameraZ) * response;
  worldScale += (targetScale - worldScale) * response;
  const driftX = .035 * Math.sin(t * .21);
  const driftY = .025 * Math.sin(t * .17 + .8);
  cameraX += (pointerX * .11 + driftX - cameraX) * response;
  cameraY += (-pointerY * .075 + driftY - cameraY) * response;
  camera.position.set(cameraX, cameraY, cameraZ);
  camera.lookAt(lookTarget);
  world.scale.setScalar(worldScale);
  world.rotation.y = .12 * Math.sin(t * .13);
  world.rotation.x = .055 * Math.sin(t * .11 + .4);

  core.update(t, reactive);
  rings.update(t, reactive);
  particles.update(t, reactive);
  bloom.strength = .36 + reactive.energyLevel * .18 + reactive.audioLevel * .10
    + reactive.transient * .12;
  composer.render();
  totalFrames++;
  fpsFrames++;
  if (nowMs - fpsStart >= 1000) {
    fps = Math.round(fpsFrames * 1000 / (nowMs - fpsStart));
    fpsFrames = 0;
    fpsStart = nowMs;
  }
}
raf = requestAnimationFrame(animate);

window.addEventListener('beforeunload', () => {
  disposed = true;
  cancelAnimationFrame(raf);
  observer.disconnect();
  const geometries = new Set();
  const materials = new Set();
  scene.traverse(object => {
    if (object.geometry) geometries.add(object.geometry);
    if (object.material) {
      for (const material of (Array.isArray(object.material) ? object.material : [object.material])) materials.add(material);
    }
  });
  geometries.forEach(geometry => geometry.dispose());
  materials.forEach(material => material.dispose());
  composer.dispose();
  renderer.dispose();
});
