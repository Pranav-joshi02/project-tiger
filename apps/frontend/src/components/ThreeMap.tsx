import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface TelemetryPoint {
  id: string;
  lat: number;
  lng: number;
  type: 'tiger' | 'deer' | 'station' | 'alert';
  label: string;
}

interface ThreeMapProps {
  points?: TelemetryPoint[];
}

export default function ThreeMap({ points = [] }: ThreeMapProps) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // 1. Scene Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#081c15'); // forest-900
    scene.fog = new THREE.FogExp2('#081c15', 0.04);

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(
      45,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      1000
    );
    // Position camera at an isometric angle
    camera.position.set(0, 15, 20);
    camera.lookAt(0, 0, 0);

    // 3. Renderer Setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    
    // Clear old canvas if any
    if (mountRef.current.children.length > 0) {
      mountRef.current.innerHTML = '';
    }
    mountRef.current.appendChild(renderer.domElement);

    // 4. Procedural Terrain (Wireframe Grid)
    const gridSize = 40;
    const gridDivisions = 40;
    const gridHelper = new THREE.GridHelper(gridSize, gridDivisions, '#1b4332', '#1b4332');
    gridHelper.position.y = -0.5;
    
    // 4. Base Map (Pench Reserve Texture)
    const textureLoader = new THREE.TextureLoader();
    const mapTexture = textureLoader.load('/pench_map.jpg');
    
    const planeGeo = new THREE.PlaneGeometry(gridSize, gridSize);
    const planeMat = new THREE.MeshBasicMaterial({ 
      map: mapTexture,
      transparent: true,
      opacity: 0.8,
      depthWrite: false
    });
    const plane = new THREE.Mesh(planeGeo, planeMat);
    plane.rotation.x = -Math.PI / 2;
    plane.position.y = -0.51;

    const terrainGroup = new THREE.Group();
    terrainGroup.add(gridHelper);
    terrainGroup.add(plane);
    scene.add(terrainGroup);

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);
    
    const dirLight = new THREE.DirectionalLight(0xffffff, 1);
    dirLight.position.set(10, 20, 10);
    scene.add(dirLight);

    // 6. Holographic Markers
    const markers: THREE.Mesh[] = [];

    // Helper to map lat/lng to roughly fit our 40x40 grid (mock projection)
    // Assuming Pench lat ~21.6, lng ~79.2
    const mapCoordsToWorld = (lat: number, lng: number) => {
      const baseLat = 21.6;
      const baseLng = 79.2;
      const scale = 200; // Spread factor
      
      return {
        x: (lng - baseLng) * scale,
        z: -(lat - baseLat) * scale // negative because Z goes 'into' screen
      };
    };

    // Helper to create a glowing mesh
    const createMarker = (x: number, z: number, type: string) => {
      let geo: THREE.BufferGeometry;
      let mat: THREE.Material;

      if (type === 'tiger') {
        // Glowing Amber Diamond (Tiger)
        geo = new THREE.OctahedronGeometry(0.5, 0);
        mat = new THREE.MeshStandardMaterial({ 
          color: '#e5a44d', // Luxe Gold/Amber
          emissive: '#e5a44d',
          emissiveIntensity: 1,
          wireframe: true,
          transparent: true,
          opacity: 0.9
        });
      } else if (type === 'deer') {
        // Glowing Cyan Tetrahedron (Prey)
        geo = new THREE.TetrahedronGeometry(0.3, 0);
        mat = new THREE.MeshStandardMaterial({
          color: '#2dd4bf', // Teal
          emissive: '#2dd4bf',
          emissiveIntensity: 0.5,
          wireframe: true,
          transparent: true,
          opacity: 0.6
        });
      } else if (type === 'alert') {
        // Pulsing Red Sphere
        geo = new THREE.SphereGeometry(0.6, 8, 8);
        mat = new THREE.MeshStandardMaterial({
          color: '#ef4444',
          emissive: '#ef4444',
          emissiveIntensity: 1.5,
          wireframe: true,
          transparent: true,
          opacity: 0.8
        });
      } else {
        // Station - Emerald Cylinder
        geo = new THREE.CylinderGeometry(0.2, 0.2, 0.8, 8);
        mat = new THREE.MeshStandardMaterial({
          color: '#10b981',
          emissive: '#10b981',
          emissiveIntensity: 0.5,
          transparent: true,
          opacity: 0.7
        });
      }

      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(x, type === 'station' ? 0 : 0.5, z);
      
      // Store custom data for animation
      mesh.userData = { type, baseZ: mesh.position.y };
      return mesh;
    };

    // Generate mock background prey just to make the map look alive
    for (let i = 0; i < 30; i++) {
      const rx = (Math.random() - 0.5) * 30;
      const rz = (Math.random() - 0.5) * 30;
      const deer = createMarker(rx, rz, 'deer');
      markers.push(deer);
      scene.add(deer);
    }

    // Add provided dynamic points
    points.forEach(p => {
      const { x, z } = mapCoordsToWorld(p.lat, p.lng);
      const marker = createMarker(x, z, p.type);
      markers.push(marker);
      scene.add(marker);
    });

    // 7. Animation Loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const renderLoop = () => {
      const elapsedTime = clock.getElapsedTime();

      // Slowly rotate the entire terrain for a telemetry scan effect
      terrainGroup.rotation.y = elapsedTime * 0.02;

      // Animate markers
      markers.forEach(mesh => {
        // Reverse terrain rotation so markers stay world-aligned
        const localPos = mesh.position.clone();
        
        if (mesh.userData.type === 'tiger') {
          mesh.rotation.y = elapsedTime;
          mesh.rotation.x = elapsedTime * 0.5;
          mesh.position.y = mesh.userData.baseZ + Math.sin(elapsedTime * 2) * 0.2;
        } else if (mesh.userData.type === 'deer') {
          mesh.rotation.y = elapsedTime * 0.5;
          mesh.position.y = mesh.userData.baseZ + Math.sin(elapsedTime * 1.5 + mesh.position.x) * 0.1;
        } else if (mesh.userData.type === 'alert') {
          const scale = 1 + Math.sin(elapsedTime * 5) * 0.3;
          mesh.scale.set(scale, scale, scale);
        }
      });

      renderer.render(scene, camera);
      animationFrameId = window.requestAnimationFrame(renderLoop);
    };
    renderLoop();

    // 8. Handle Resize
    const handleResize = () => {
      if (!mountRef.current) return;
      camera.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      window.cancelAnimationFrame(animationFrameId);
      if (mountRef.current) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
      // Normally we'd traverse and dispose geometries/materials here for perfection
    };
  }, [points]);

  return (
    <div className="w-full h-full relative group">
      <div 
        ref={mountRef} 
        className="w-full h-full cursor-crosshair"
      />
      
      {/* UI Overlay on map */}
      <div className="absolute top-4 left-4 z-10 bg-white/95 backdrop-blur-sm border border-ink-100 shadow-card rounded-xl p-4 inline-flex flex-col gap-1 pointer-events-none fade-in">
        <h3 className="font-serif text-gold-500 text-sm tracking-widest uppercase font-bold">Pench Core Zone</h3>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-xs text-ink-600 font-mono">Live Telemetry Active</span>
        </div>
      </div>
      
      {/* Legend overlay */}
      <div className="absolute bottom-4 right-4 z-10 bg-white/95 backdrop-blur-sm border border-ink-100 shadow-card rounded-xl p-4 flex gap-6 pointer-events-none fade-in">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-gold-400 border border-gold-500 rounded-sm rotate-45"></div>
          <span className="text-xs font-mono text-ink-600">Target</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[10px] border-b-forest-500"></div>
          <span className="text-xs font-mono text-ink-600">Prey</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500 border border-red-600 animate-pulse"></div>
          <span className="text-xs font-mono text-ink-600">Alert</span>
        </div>
      </div>
    </div>
  );
}
