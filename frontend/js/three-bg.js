import * as THREE from 'three';

const canvas = document.querySelector('#bg-canvas');
const scene = new THREE.Scene();

// Camera setup
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 1000;

// Render setup
const renderer = new THREE.WebGLRenderer({ 
    canvas, 
    alpha: true, 
    antialias: true,
    powerPreference: "high-performance"
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

// STARFIELD CONFIGURATION
const particlesGeometry = new THREE.BufferGeometry();
const particlesCount = 1500; // Optimal for 60fps on most devices

const posArray = new Float32Array(particlesCount * 3);
// Brightness/Size variation
const sizesArray = new Float32Array(particlesCount); 

for(let i = 0; i < particlesCount; i++) {
    // Spread stars in a large volume
    const i3 = i * 3;
    posArray[i3] = (Math.random() - 0.5) * 2000;
    posArray[i3 + 1] = (Math.random() - 0.5) * 2000;
    posArray[i3 + 2] = (Math.random() - 0.5) * 2000;
    
    // Random sizes for depth perception (Increased size for visibility)
    sizesArray[i] = 1.0 + Math.random() * 4.0;
}

particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
particlesGeometry.setAttribute('size', new THREE.BufferAttribute(sizesArray, 1));

// Custom Shader for soft, glowing stars
const material = new THREE.ShaderMaterial({
    uniforms: {
        time: { value: 0 },
        pointTexture: { value: new THREE.TextureLoader().load('https://assets.codepen.io/16327/particle.png') } // Fallback or procedural
    },
    vertexShader: `
        attribute float size;
        varying vec3 vColor;
        uniform float time;
        void main() {
            vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
            
            // Parallax movement effect based on position
            float timeOffset = position.y * 0.001;
            float pulse = 1.0 + sin(time * 2.0 + timeOffset) * 0.2;
            
            // Increased scale for better clearity
            gl_PointSize = size * (400.0 / -mvPosition.z) * pulse;
            gl_Position = projectionMatrix * mvPosition;
        }
    `,
    fragmentShader: `
        void main() {
            // Circular particle drawing (procedural texture)
            vec2 uv = gl_PointCoord.xy - 0.5;
            float r = length(uv);
            if (r > 0.5) discard;
            
            // Soft glow (white center, varying opacity)
            float alpha = 1.0 - smoothstep(0.3, 0.5, r);
            
            gl_FragColor = vec4(1.0, 1.0, 1.0, alpha * 0.8); // Pure white stars
        }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
});

const starField = new THREE.Points(particlesGeometry, material);
scene.add(starField);

// Subtle fog for depth blending into the dark blue background
scene.fog = new THREE.FogExp2(0x0a192f, 0.0005); // Matches dark blue theme

// Animation Loop
const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);
    const elapsedTime = clock.getElapsedTime();

    // Update shader uniforms
    material.uniforms.time.value = elapsedTime;

    // Slow, soothing rotation
    starField.rotation.y = elapsedTime * 0.05;
    starField.rotation.x = elapsedTime * 0.02;

    renderer.render(scene, camera);
}

// Handle Resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
});

animate();
