import * as THREE from 'three';

function arcMesh(radius, start, span, color, opacity, tubeRadius) {
  const points = [];
  const steps = Math.max(10, Math.ceil(span * 34));
  for (let i = 0; i <= steps; i++) {
    const angle = start + span * i / steps;
    points.push(new THREE.Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius, 0));
  }
  const geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), steps, tubeRadius, 5, false);
  const material = new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uOpacity: { value: opacity } },
    transparent: true, depthTest: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `varying vec3 vWorld;void main(){vec4 world=modelMatrix*vec4(position,1.);
      vWorld=world.xyz;gl_Position=projectionMatrix*viewMatrix*world;}`,
    fragmentShader: `uniform vec3 uColor;uniform float uOpacity;varying vec3 vWorld;
      void main(){float behind=step(vWorld.z,-.025);
        float inCore=1.-smoothstep(.78,1.17,length(vWorld.xy));
        float alpha=uOpacity*(1.-behind*inCore*.90);
        gl_FragColor=vec4(uColor,alpha);}`,
  });
  return new THREE.Mesh(geometry, material);
}

function createTrack(radius, segments, span, color, opacity, width) {
  const group = new THREE.Group();
  for (let i = 0; i < segments; i++) {
    const gap = (i % 5 === 0 ? .04 : 0);
    group.add(arcMesh(radius, i * Math.PI * 2 / segments + gap,
      span * (i % 5 === 0 ? 1.3 : 1), color,
      opacity * (i % 4 === 0 ? 1.5 : .72), width * (i % 5 === 0 ? 1.45 : 1)));
  }
  return group;
}

function ticks(radius, count, color) {
  const vertices = [];
  for (let i = 0; i < count; i++) {
    const a = i * Math.PI * 2 / count;
    const long = i % 6 === 0;
    for (const r of [radius, radius + (long ? .075 : .027)]) {
      vertices.push(Math.cos(a) * r, Math.sin(a) * r, 0);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  return new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({
    color, transparent: true, opacity: .30, depthTest: true, depthWrite: false,
  }));
}

export function createRings() {
  const group = new THREE.Group();

  // Each track is a true 3D orbit. Inclination puts arcs ahead of and behind the chamber.
  const inner = createTrack(1.23, 9, .43, 0x18bfe5, .64, .009);
  inner.rotation.set(.66, -.42, .15);
  group.add(inner);

  const technical = createTrack(1.62, 22, .17, 0x0da6dc, .54, .008);
  technical.rotation.set(-1.06, .35, -.10);
  technical.add(ticks(1.72, 72, 0x39cae5));
  group.add(technical);

  const outer = createTrack(2.05, 27, .12, 0x1389bd, .40, .007);
  outer.rotation.set(.69, -.47, -.12);
  outer.add(ticks(2.16, 84, 0x17769b));
  group.add(outer);

  const polar = createTrack(1.78, 12, .20, 0x1188c3, .43, .006);
  polar.rotation.set(.21, 1.15, .41);
  group.add(polar);

  const nodeGeometry = new THREE.SphereGeometry(.023, 8, 6);
  const nodeMaterial = new THREE.MeshBasicMaterial({ color: 0x68eafc, toneMapped: false });
  for (let i = 0; i < 7; i++) {
    const angle = i * Math.PI * 2 / 7;
    const node = new THREE.Mesh(nodeGeometry, nodeMaterial);
    node.position.set(Math.cos(angle) * 2.05, Math.sin(angle) * 2.05, 0);
    outer.add(node);
  }

  const pulse = new THREE.Group();
  pulse.add(arcMesh(1.11, 0, Math.PI * 1.99, 0x5affdb, .55, .008));
  pulse.visible = false;
  group.add(pulse);

  return {
    group,
    update(t, reactive) {
      const speed = reactive.ringSpeed;
      inner.rotation.z = .15 + t * speed * .40;
      technical.rotation.z = -.10 - t * speed * 1.12;
      outer.rotation.z = -.12 + t * speed * .42;
      polar.rotation.z = .41 - t * speed * .53;
      technical.rotation.x = -1.06 + (reactive.state === 'THINKING' ? .12 : .025) * Math.sin(t * .8);
      inner.scale.setScalar(1 + reactive.audioLevel * .035);
      const codex = reactive.state === 'CODEX';
      technical.children.forEach(child => {
        if (child.material?.uniforms?.uColor) child.material.uniforms.uColor.value.setHex(codex ? 0x695dff : 0x0da6dc);
      });
      pulse.visible = reactive.transient > .005 || reactive.state === 'SPEAKING';
      pulse.scale.setScalar(1 + (1 - reactive.transient) * .58 + reactive.audioLevel * .22);
      const mat = pulse.children[0].material;
      mat.uniforms.uColor.value.setHex(reactive.state === 'ERROR' ? 0xff6c54 : 0x5affdb);
      mat.uniforms.uOpacity.value = reactive.state === 'SPEAKING'
        ? reactive.audioLevel * .22 : reactive.transient * .40;
    },
  };
}
