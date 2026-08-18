import React, { useEffect, useRef } from "react"
import * as THREE from "three"
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js"

interface CameraStation {
  code: string
  name: string
  lat: number
  lon: number
  status: string
}

interface Map3DProps {
  stations: CameraStation[]
  onStationClick?: (stationCode: string) => void
  activeStationCode?: string | null
}

export const ReserveMap3D: React.FC<Map3DProps> = ({ stations, onStationClick, activeStationCode }) => {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const width = containerRef.current.clientWidth
    const height = containerRef.current.clientHeight

    // Scene
    const scene = new THREE.Scene()
    scene.background = null // Transparent to show glassmorphic backdrop

    // Camera
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
    camera.position.set(0, 45, 60)

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    containerRef.current.innerHTML = ""
    containerRef.current.appendChild(renderer.domElement)

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.maxPolarAngle = Math.PI / 2.1 // Prevent looking under ground plane

    // Lights
    const ambientLight = new THREE.AmbientLight(0x0e2b1f, 1.5)
    scene.add(ambientLight)

    const sunLight = new THREE.DirectionalLight(0xe5a44d, 2.0)
    sunLight.position.set(20, 40, 20)
    scene.add(sunLight)

    // Add a glowing spotlight for Sunbeam effect
    const spotLight = new THREE.SpotLight(0x2d6a4f, 4.0)
    spotLight.position.set(-10, 50, -10)
    spotLight.angle = Math.PI / 6
    spotLight.penumbra = 0.8
    scene.add(spotLight)

    // --- RENDER 3D TERRAIN ---
    const terrainSize = 80
    const terrainGeo = new THREE.PlaneGeometry(terrainSize, terrainSize, 40, 40)
    
    // Add procedural hills using math
    const pos = terrainGeo.attributes.position
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i)
      const y = pos.getY(i)
      // Generates elevation ripples representing hills
      const z = Math.sin(x * 0.1) * Math.cos(y * 0.1) * 3.5 + Math.sin(x * 0.05) * 1.5
      pos.setZ(i, z)
    }
    terrainGeo.computeVertexNormals()

    // Materials
    const terrainMat = new THREE.MeshStandardMaterial({
      color: 0x0f241a,
      roughness: 0.8,
      metalness: 0.1,
      flatShading: true,
    })
    
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x2d6a4f,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    })

    const terrainMesh = new THREE.Mesh(terrainGeo, terrainMat)
    terrainMesh.rotation.x = -Math.PI / 2
    scene.add(terrainMesh)

    const wireMesh = new THREE.Mesh(terrainGeo, wireMat)
    wireMesh.rotation.x = -Math.PI / 2
    wireMesh.position.y = 0.05 // Offset slightly to avoid z-fighting
    scene.add(wireMesh)

    // --- RENDER CAMERA STATIONS ---
    const stationObjects: THREE.Object3D[] = []
    
    // Calculate bounding box of coordinates to center the stations
    const lats = stations.map(s => s.lat)
    const lons = stations.map(s => s.lon)
    const minLat = Math.min(...lats, 22.69)
    const maxLat = Math.max(...lats, 22.79)
    const minLon = Math.min(...lons, 79.26)
    const maxLon = Math.max(...lons, 79.36)

    const mapCoords = (lat: number, lon: number) => {
      // Map GPS to -25 to 25 local coords
      const x = ((lon - minLon) / (maxLon - minLon) - 0.5) * 50
      const z = ((lat - minLat) / (maxLat - minLat) - 0.5) * 50
      
      // Get height from terrain grid
      const terrainX = Math.round(((x + terrainSize/2) / terrainSize) * 40)
      const terrainY = Math.round(((z + terrainSize/2) / terrainSize) * 40)
      // Standard elevation height or fallback
      const y = Math.sin(x * 0.1) * Math.cos(z * 0.1) * 3.5 + Math.sin(x * 0.05) * 1.5
      return { x, y: y + 0.5, z }
    }

    stations.forEach(station => {
      const pos = mapCoords(station.lat, station.lon)
      
      // Pin cylinder representation
      const isSelected = activeStationCode === station.code
      const pinColor = isSelected ? 0xe5a44d : (station.status === "ACTIVE" ? 0x4ade80 : 0xf87171)
      
      const pinGeo = new THREE.CylinderGeometry(0.3, 0.3, 1.8, 8)
      const pinMat = new THREE.MeshStandardMaterial({
        color: pinColor,
        emissive: pinColor,
        emissiveIntensity: isSelected ? 0.9 : 0.2,
      })
      const pinMesh = new THREE.Mesh(pinGeo, pinMat)
      pinMesh.position.set(pos.x, pos.y + 0.9, pos.z)
      pinMesh.name = `station:${station.code}`
      scene.add(pinMesh)
      stationObjects.push(pinMesh)

      // Pulsing glow ring around pin
      const ringGeo = new THREE.RingGeometry(0.8, 1.0, 16)
      const ringMat = new THREE.MeshBasicMaterial({
        color: pinColor,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.6,
      })
      const ringMesh = new THREE.Mesh(ringGeo, ringMat)
      ringMesh.position.set(pos.x, pos.y + 0.02, pos.z)
      ringMesh.rotation.x = Math.PI / 2
      scene.add(ringMesh)
      
      // Add simple animation properties
      ringMesh.userData = { scaleRate: 0.02 + Math.random() * 0.01, maxScale: 2.2 }
      
      // Store reference to animate rings
      scene.userData.rings = scene.userData.rings || []
      scene.userData.rings.push(ringMesh)
    })

    // --- ADD 3D TIGER & DEER MARKERS (THE DYNAMIC UX!) ---
    // Instead of heavy models, we build beautiful glowing low-poly 3D markers!
    
    // 3D Tigers (Glowing Orange Cubes/Sightings)
    const tigerGeo = new THREE.BoxGeometry(1.2, 1.2, 1.2)
    const tigerMat = new THREE.MeshStandardMaterial({
      color: 0xe5a44d, // Gold/Orange tiger color
      emissive: 0xd47a22,
      emissiveIntensity: 0.7,
      roughness: 0.2,
      metalness: 0.8
    })
    
    // 3D Deers (Glowing Green Pyramids/Sightings)
    const deerGeo = new THREE.ConeGeometry(0.7, 1.8, 4)
    const deerMat = new THREE.MeshStandardMaterial({
      color: 0x4ade80, // Moss/Light Green deer color
      emissive: 0x228b22,
      emissiveIntensity: 0.5,
      roughness: 0.4,
    })

    const sightings: THREE.Mesh[] = []

    // Distribute a few mock wildlife sightings around active stations
    stations.filter(s => s.status === "ACTIVE").slice(0, 5).forEach((station, idx) => {
      const basePos = mapCoords(station.lat, station.lon)
      const isTiger = idx % 2 === 0
      
      // Displace sighting slightly from the camera pin
      const offsetX = (Math.random() - 0.5) * 8
      const offsetZ = (Math.random() - 0.5) * 8
      const pos = mapCoords(station.lat + offsetX * 0.001, station.lon + offsetZ * 0.001)

      const mesh = new THREE.Mesh(isTiger ? tigerGeo : deerGeo, isTiger ? tigerMat : deerMat)
      mesh.position.set(pos.x, pos.y + 0.9, pos.z)
      scene.add(mesh)
      sightings.push(mesh)
    })

    // --- PARTICLES (Atmospheric forest dust) ---
    const particleCount = 200
    const particleGeo = new THREE.BufferGeometry()
    const positions = new Float32Array(particleCount * 3)

    for (let i = 0; i < particleCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 90 // X
      positions[i + 1] = Math.random() * 25      // Y
      positions[i + 2] = (Math.random() - 0.5) * 90 // Z
    }

    particleGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3))
    const particleMat = new THREE.PointsMaterial({
      color: 0xe5a44d,
      size: 0.25,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
    })
    const particleSystem = new THREE.Points(particleGeo, particleMat)
    scene.add(particleSystem)

    // --- INTERACTION / RAYCASTING ---
    const raycaster = new THREE.Raycaster()
    const mouse = new THREE.Vector2()

    const onPointerDown = (event: MouseEvent) => {
      // Calculate mouse position in normalized device coordinates
      const rect = renderer.domElement.getBoundingClientRect()
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

      raycaster.setFromCamera(mouse, camera)
      const intersects = raycaster.intersectObjects(stationObjects)

      if (intersects.length > 0) {
        const name = intersects[0].object.name // e.g. "station:CT-01"
        if (name && name.startsWith("station:") && onStationClick) {
          const code = name.split(":")[1]
          onStationClick(code)
        }
      }
    }

    renderer.domElement.addEventListener("pointerdown", onPointerDown)

    // --- ANIMATION LOOP ---
    let animId: number
    const clock = new THREE.Clock()

    const animate = () => {
      animId = requestAnimationFrame(animate)

      const time = clock.getElapsedTime()

      // Rotate camera slightly over time for automatic cinematic scan if controls aren't interacting
      if ((controls as any).state === -1) {
        scene.rotation.y = time * 0.015
      }

      // Animate sightings (hovering bobbing and rotating)
      sightings.forEach((mesh, index) => {
        mesh.rotation.y += 0.01
        mesh.rotation.x += 0.005
        mesh.position.y += Math.sin(time * 2 + index) * 0.005
      })

      // Animate rings pulsing
      if (scene.userData.rings) {
        scene.userData.rings.forEach((ring: THREE.Mesh) => {
          const rate = ring.userData.scaleRate
          const max = ring.userData.maxScale
          ring.scale.x += rate
          ring.scale.y += rate
          
          // Fade out as it expands
          const ratio = ring.scale.x / max
          if (ring.material instanceof THREE.Material) {
            ring.material.opacity = Math.max(0, 0.6 * (1 - ratio))
          }

          if (ring.scale.x >= max) {
            ring.scale.set(1, 1, 1)
          }
        })
      }

      // Animate particle dust drifting
      const particlePos = particleGeo.attributes.position
      if (particlePos) {
        for (let i = 1; i < particlePos.count * 3; i += 3) {
          // Slow vertical drift
          let y = particlePos.getY(i / 3) - 0.02
          if (y < 0) y = 25
          particlePos.setY(i / 3, y)
        }
        particlePos.needsUpdate = true
      }

      controls.update()
      renderer.render(scene, camera)
    }

    animate()

    // --- RESIZE ---
    const handleResize = () => {
      if (!containerRef.current) return
      const w = containerRef.current.clientWidth
      const h = containerRef.current.clientHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }

    window.addEventListener("resize", handleResize)

    // Cleanup
    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener("resize", handleResize)
      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.removeEventListener("pointerdown", onPointerDown)
        renderer.domElement.remove()
      }
      scene.clear()
    }
  }, [stations, activeStationCode])

  return (
    <div className="relative w-full h-full rounded-xl overflow-hidden glass border border-forest-500/20">
      {/* 3D Container */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
      
      {/* Legends Overlay */}
      <div className="absolute bottom-4 left-4 glass p-3 rounded-lg text-xs flex flex-col gap-1.5 z-10 pointer-events-none">
        <h4 className="font-semibold text-slate-300 mb-1">Interactive 3D Grid</h4>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          <span>Active Station (Cylinder)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
          <span>Maintenance (Cylinder)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 bg-luxe-gold" />
          <span>Tiger Sighting (Floating Cube)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-0 h-0 border-l-[5px] border-l-transparent border-r-[5px] border-r-transparent border-b-[9px] border-b-emerald-400" />
          <span>Deer Sighting (Floating Cone)</span>
        </div>
      </div>
      
      <div className="absolute top-4 right-4 glass px-3 py-1 rounded text-[10px] text-slate-400 font-mono pointer-events-none">
        DRAG TO ROTATE • PINCH TO ZOOM
      </div>
    </div>
  )
}
