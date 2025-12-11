import React, { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { EffectComposer, Bloom } from "@react-three/postprocessing";

function Beam({ position, color, width, height, speed, delay, opacity }) {
  const mesh = useRef();
  const material = useRef();

  // Random initial offset
  const initialY = useMemo(() => Math.random() * 5 - 2.5, []);
  
  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    
    // Vertical movement (floating)
    mesh.current.position.y = initialY + Math.sin(t * speed + delay) * 0.5;
    
    // Pulse opacity
    if (material.current) {
        material.current.opacity = opacity * (0.8 + Math.sin(t * speed * 2) * 0.2);
    }
  });

  return (
    <mesh ref={mesh} position={position}>
      <cylinderGeometry args={[width, width, height, 32, 1, true]} />
      <meshBasicMaterial
        ref={material}
        color={color}
        transparent
        opacity={opacity}
        side={THREE.DoubleSide}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </mesh>
  );
}

function PillarScene() {
  // Create a cluster of beams
  const beams = useMemo(() => {
    const count = 12;
    const items = [];
    const colors = ["#4f46e5", "#7c3aed", "#2563eb", "#db2777"]; // Indigo, Violet, Blue, Pink

    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2;
      const radius = 3 + Math.random() * 4;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const color = colors[Math.floor(Math.random() * colors.length)];
      
      items.push({
        position: [x, 0, z],
        color: color,
        width: 0.2 + Math.random() * 0.5,
        height: 10 + Math.random() * 10,
        speed: 0.2 + Math.random() * 0.3,
        delay: Math.random() * Math.PI,
        opacity: 0.1 + Math.random() * 0.2
      });
    }
    return items;
  }, []);

  return (
    <group rotation={[0, 0, Math.PI / 12]}> {/* Slight tilt */}
        {beams.map((props, i) => (
            <Beam key={i} {...props} />
        ))}
    </group>
  );
}

const LightPillar = () => {
  return (
    <div style={{ position: "fixed", top: 0, left: 0, width: "100%", height: "100%", zIndex: 0, pointerEvents: "none", background: "#0f0e17" }}>
      <Canvas camera={{ position: [0, 0, 10], fov: 45 }}>
        <fog attach="fog" args={["#0f0e17", 5, 20]} />
        <ambientLight intensity={0.5} />
        
        <PillarScene />
        
        <EffectComposer>
          <Bloom luminanceThreshold={0.2} luminanceSmoothing={0.9} height={300} intensity={1.5} radius={0.8} />
        </EffectComposer>
      </Canvas>
      
      {/* Overlay gradient for better text readability */}
      <div style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        background: "radial-gradient(circle at 50% 50%, transparent 0%, #0f0e17 90%)"
      }} />
    </div>
  );
};

export default LightPillar;
