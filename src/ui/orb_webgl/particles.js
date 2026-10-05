import * as THREE from 'three';

// Spherical distribution follows the donor scene's particle-network foundation;
// separate depth bands make the space feel three-dimensional.
function cloud(count, minRadius, maxRadius, color, size, opacity, zBias = 0) {
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const radius = minRadius + Math.random() * (maxRadius - minRadius);
    const azimuth = Math.random() * Math.PI * 2;
    const y = (Math.random() * 2 - 1) * radius;
    const horizontal = Math.sqrt(Math.max(0, radius * radius - y * y));
    positions[i * 3] = Math.cos(azimuth) * horizontal;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = Math.sin(azimuth) * horizontal + zBias;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({
    color, size, transparent: true, opacity,
    blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true,
  });
  return new THREE.Points(geometry, material);
}

export function createParticles(scene, world) {
  const background = cloud(120, 3.0, 7.0, 0x236888, .018, .16, -3.2);
  scene.add(background);
  const middle = cloud(100, 1.25, 2.55, 0x32a9c5, .018, .29);
  world.add(middle);
  const foreground = cloud(36, 2.1, 3.6, 0x7adfee, .014, .27, 1.1);
  scene.add(foreground);
  return {
    update(t, reactive) {
      background.rotation.y = t * .003;
      middle.rotation.y = t * (.013 + reactive.activity * .020);
      middle.rotation.x = .10 * Math.sin(t * .11);
      foreground.rotation.y = -t * .004;
      middle.material.opacity = .17 + reactive.particleLevel * .28;
      foreground.material.opacity = reactive.viewMode === 'ORB' ? .29 : .13;
    },
  };
}
