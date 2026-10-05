import * as THREE from 'three';

// The dark back-facing chamber leaves the interior readable and avoids a planet surface.
export function createCore() {
  const group = new THREE.Group();
  const chamber = new THREE.Mesh(
    new THREE.SphereGeometry(.95, 48, 36),
    new THREE.MeshBasicMaterial({ color: 0x010a1b, side: THREE.BackSide, depthWrite: false })
  );
  group.add(chamber);

  const shellUniforms = {
    uTime: { value: 0 }, uGlow: { value: .3 }, uAccent: { value: new THREE.Color(0x1fdfff) },
  };
  const shell = new THREE.Mesh(new THREE.SphereGeometry(1.02, 64, 48), new THREE.ShaderMaterial({
    uniforms: shellUniforms, side: THREE.FrontSide, transparent: true,
    depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `varying vec3 vNormal; varying vec3 vView; varying vec3 vPos;
      void main(){vec4 p=modelViewMatrix*vec4(position,1.);vNormal=normalize(normalMatrix*normal);
        vView=normalize(-p.xyz);vPos=position;gl_Position=projectionMatrix*p;}`,
    fragmentShader: `uniform float uTime;uniform float uGlow;uniform vec3 uAccent;
      varying vec3 vNormal;varying vec3 vView;varying vec3 vPos;
      void main(){float rim=pow(1.-max(dot(normalize(vNormal),normalize(vView)),0.),3.25);
        float current=sin(vPos.y*18.+uTime*.45+sin(vPos.x*11.-uTime*.32)*1.6);
        float filament=smoothstep(.72,.98,current)*.038;
        float alpha=(.012+rim*(.18+.21*uGlow)+filament)*(.8+uGlow*.35);
        gl_FragColor=vec4(uAccent*.79+vec3(.02,.07,.18),alpha);}`,
  }));
  shell.renderOrder = 7;
  group.add(shell);

  // A restrained geodesic cage follows the primary donor's icosahedron-edge idea.
  const cageGeometry = new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(1.065, 2));
  const cage = new THREE.LineSegments(cageGeometry, new THREE.LineBasicMaterial({
    color: 0x0b87b4, transparent: true, opacity: .10, depthWrite: false,
  }));
  group.add(cage);

  // Spiral construction follows the secondary donor's 3D inner-core approach.
  // Each stream occupies a distinct helix, with a moving energy packet shader.
  const streamUniforms = [];
  const streams = new THREE.Group();
  for (let strand = 0; strand < 3; strand++) {
    const points = [];
    const turns = strand === 2 ? 1.65 : 2.15;
    for (let i = 0; i <= 160; i++) {
      const f = i / 160;
      const y = -.71 + f * 1.42;
      const taper = Math.pow(Math.max(0, 1 - (y / .77) ** 2), .55);
      const radius = (.22 + .34 * taper) * (strand === 2 ? .63 : 1);
      const angle = f * turns * Math.PI * 2 * (strand === 1 ? -1 : 1)
        + strand * Math.PI * .78;
      points.push(new THREE.Vector3(Math.cos(angle) * radius, y,
        Math.sin(angle) * radius * .88));
    }
    const curve = new THREE.CatmullRomCurve3(points);
    const uniforms = {
      uTime: { value: 0 }, uFlow: { value: .35 }, uEnergy: { value: .3 },
      uColor: { value: new THREE.Color(strand === 1 ? 0x00c6bd : 0x24cfff) },
    };
    const material = new THREE.ShaderMaterial({
      uniforms, transparent: true, depthWrite: false,
      blending: THREE.AdditiveBlending,
      vertexShader: `varying vec2 vUv;varying vec3 vPos;
        void main(){vUv=uv;vPos=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
      fragmentShader: `uniform float uTime;uniform float uFlow;uniform float uEnergy;uniform vec3 uColor;
        varying vec2 vUv;varying vec3 vPos;
        void main(){float packet=pow(max(0.,sin(vUv.x*48.-uTime*(2.+uFlow*3.))),6.);
          float movement=.32+.22*sin(vUv.x*31.+uTime*.6+vPos.z*4.);
          vec3 color=uColor*(movement+.35*uEnergy+packet*(.65+.45*uEnergy));
          gl_FragColor=vec4(color,.48+packet*.38);}`,
    });
    const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 220, strand === 2 ? .012 : .017, 6, false), material);
    streams.add(tube);
    streamUniforms.push(uniforms);
  }
  group.add(streams);

  const hotspot = new THREE.Mesh(new THREE.SphereGeometry(.095, 24, 16),
    new THREE.MeshBasicMaterial({ color: 0xb5ffff, toneMapped: false }));
  group.add(hotspot);
  const glow = new THREE.Mesh(new THREE.SphereGeometry(.18, 24, 16),
    new THREE.MeshBasicMaterial({ color: 0x15cfff, transparent: true,
      opacity: .095, depthWrite: false, blending: THREE.AdditiveBlending }));
  group.add(glow);

  const innerPoints = new Float32Array(72 * 3);
  for (let i = 0; i < 72; i++) {
    const r = .13 + Math.random() * .63;
    const a = Math.random() * Math.PI * 2;
    const z = (Math.random() * 2 - 1) * r;
    const xy = Math.sqrt(Math.max(0, r * r - z * z));
    innerPoints[i * 3] = Math.cos(a) * xy;
    innerPoints[i * 3 + 1] = Math.sin(a) * xy;
    innerPoints[i * 3 + 2] = z;
  }
  const innerGeo = new THREE.BufferGeometry();
  innerGeo.setAttribute('position', new THREE.BufferAttribute(innerPoints, 3));
  const innerParticles = new THREE.Points(innerGeo, new THREE.PointsMaterial({
    color: 0x62faff, size: .022, transparent: true, opacity: .48,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  group.add(innerParticles);

  return {
    group,
    update(t, reactive) {
      shellUniforms.uTime.value = t;
      shellUniforms.uGlow.value = reactive.shellGlow;
      shellUniforms.uAccent.value.setHex(reactive.state === 'CODEX' ? 0x7771f4 : 0x17d5ec);
      for (const uniforms of streamUniforms) {
        uniforms.uTime.value = t;
        uniforms.uFlow.value = reactive.flowSpeed;
        uniforms.uEnergy.value = reactive.energyLevel + reactive.audioLevel * .42;
      }
      streams.rotation.y = t * (.10 + reactive.flowSpeed * .17);
      streams.rotation.z = .07 * Math.sin(t * .47);
      cage.rotation.y = -t * .035;
      innerParticles.rotation.y = -t * (.045 + reactive.turbulence * .08);
      const pulse = 1 + .07 * Math.sin(t * 1.65) + reactive.audioLevel * .17
        + reactive.transient * (reactive.state === 'SUCCESS' ? .35 : .08);
      hotspot.scale.setScalar(pulse);
      glow.scale.setScalar(pulse * (1 + reactive.energyLevel * .3));
      glow.material.opacity = .055 + reactive.energyLevel * .09;
    },
  };
}
