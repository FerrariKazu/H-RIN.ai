import * as THREE from 'three';

const canvas = document.querySelector('#bg-canvas');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

// Light Pillar Geometry (Cylinder with additive blending)
const geometry = new THREE.CylinderGeometry(2, 2, 20, 32, 1, true);
const material = new THREE.ShaderMaterial({
    uniforms: {
        time: { value: 0 },
        color: { value: new THREE.Color('#3da9fa') }
    },
    vertexShader: `
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `,
    fragmentShader: `
        uniform float time;
        uniform vec3 color;
        varying vec2 vUv;
        
        void main() {
            // Gradient fade from bottom to top
            float opacity = (1.0 - vUv.y) * 0.5;
            
            // Dynamic pulse
            float pulse = 0.8 + 0.2 * sin(time * 2.0);
            
            // Scanlines
            float scanline = sin(gl_FragCoord.y * 0.1 - time * 5.0) * 0.1;
            
            vec3 finalColor = color + scanline;
            gl_FragColor = vec4(finalColor, opacity * pulse);
        }
    `,
    transparent: true,
    side: THREE.DoubleSide,
    depthWrite: false,
    blending: THREE.AdditiveBlending
});

const pillar = new THREE.Mesh(geometry, material);
scene.add(pillar);

// Particles
const particlesGeometry = new THREE.BufferGeometry();
const particlesCount = 200;
const posArray = new Float32Array(particlesCount * 3);

for(let i = 0; i < particlesCount * 3; i++) {
    posArray[i] = (Math.random() - 0.5) * 15;
}

particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
const particlesMaterial = new THREE.PointsMaterial({
    size: 0.05,
    color: '#ff8906',
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending
});

const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
scene.add(particlesMesh);

// Post-processing setup could go here, but keeping it simple for raw three.js

camera.position.z = 8;
camera.position.y = 2;
camera.lookAt(0, 0, 0);

const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);
    
    const elapsedTime = clock.getElapsedTime();
    
    // Animate shader
    material.uniforms.time.value = elapsedTime;
    
    // Rotate pillar
    pillar.rotation.y = elapsedTime * 0.1;
    
    // Float particles
    particlesMesh.rotation.y = -elapsedTime * 0.05;
    particlesMesh.position.y = Math.sin(elapsedTime * 0.5) * 0.5;

    // Mouse parallax (simple)
    // camera.position.x += (mouseX - camera.position.x) * 0.05;
    
    renderer.render(scene, camera);
}

// Handle Resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

animate();
