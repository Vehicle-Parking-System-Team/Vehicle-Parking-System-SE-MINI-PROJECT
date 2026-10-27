import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'
import { STATUS, slotState } from '../utils/parkingLayout'

function disposeGroup(group) {
  const geometries = new Set()
  const materials = new Set()
  group.traverse((object) => {
    if (object.geometry) geometries.add(object.geometry)
    if (object.material)
      for (const material of [object.material].flat()) materials.add(material)
  })
  for (const geometry of geometries) geometry.dispose()
  for (const material of materials) {
    material.map?.dispose()
    material.dispose()
  }
}

function addLabel(
  group,
  text,
  x,
  z,
  width = 1.9,
  color = '#e0ded7',
  size = 36,
) {
  const canvas = document.createElement('canvas')
  canvas.width = 384
  canvas.height = 96
  const ctx = canvas.getContext('2d')
  ctx.font = `600 ${size}px system-ui, sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillStyle = color
  ctx.fillText(text, 192, 48, 360)
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  const label = new THREE.Mesh(
    new THREE.PlaneGeometry(width, width / 4),
    new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    }),
  )
  label.rotation.x = -Math.PI / 2
  label.position.set(x, 0.08, z)
  group.add(label)
}

function populateDeck(layout) {
  const group = new THREE.Group()
  const targets = []
  const materialCache = new Map()
  const geometryCache = new Map()
  const material = (color, metalness = 0) => {
    const key = `${color}-${metalness}`
    if (!materialCache.has(key))
      materialCache.set(
        key,
        new THREE.MeshStandardMaterial({
          color,
          roughness: metalness ? 0.3 : 0.8,
          metalness,
        }),
      )
    return materialCache.get(key)
  }
  function box(parent, dimensions, position, color, radius = 0, metalness = 0) {
    const key = dimensions.join(',') + radius
    if (!geometryCache.has(key))
      geometryCache.set(
        key,
        radius
          ? new RoundedBoxGeometry(...dimensions, 2, radius)
          : new THREE.BoxGeometry(...dimensions),
      )
    const mesh = new THREE.Mesh(
      geometryCache.get(key),
      material(color, metalness),
    )
    mesh.position.set(...position)
    mesh.castShadow = true
    mesh.receiveShadow = true
    parent.add(mesh)
    return mesh
  }
  const { width, depth } = layout
  box(group, [width + 0.4, 0.7, depth + 0.4], [0, -0.65, 0], '#292828', 0.18)
  box(group, [width, 0.25, depth], [0, -0.18, 0], '#777777', 0.14)
  box(
    group,
    [width - 0.4, 0.035, 0.07],
    [0, -0.02, depth / 2 - 0.12],
    '#eeeae0',
  )
  box(
    group,
    [0.07, 0.035, depth - 0.4],
    [-width / 2 + 0.12, -0.02, 0],
    '#eeeae0',
  )
  // Cutaway perimeter barriers; the open foreground keeps the floor readable.
  for (const side of [-1, 1]) {
    box(
      group,
      [0.25, 0.7, depth - 0.8],
      [side * (width / 2 - 0.3), 0.25, 0],
      '#8e8c8a',
      0.06,
    )
    for (let z = -depth / 2 + 2; z < depth / 2; z += 7.5) {
      box(
        group,
        [0.55, 2.1, 0.55],
        [side * (width / 2 - 0.6), 0.95, z],
        '#a3a29f',
        0.05,
      )
      box(
        group,
        [0.57, 0.22, 0.57],
        [side * (width / 2 - 0.6), 0.6, z],
        '#eeeae0',
      )
    }
  }
  for (const band of layout.bands) {
    // Central driving aisle with road markings and directional chevrons.
    box(group, [width - 1.4, 0.018, 3], [0, -0.035, band.z], '#575a59')
    for (let x = -8.5; x <= 8.5; x += 2.6)
      box(group, [1.15, 0.025, 0.075], [x, 0.01, band.z], '#abaaa7')
    addLabel(group, `ZONE ${band.zone}`, -8.8, band.z - 1, 3.2, '#eeeae0', 34)
    const arrow = new THREE.Shape()
    arrow.moveTo(-0.7, -0.25)
    arrow.lineTo(0.15, -0.25)
    arrow.lineTo(0.15, -0.6)
    arrow.lineTo(0.85, 0)
    arrow.lineTo(0.15, 0.6)
    arrow.lineTo(0.15, 0.25)
    arrow.lineTo(-0.7, 0.25)
    const mesh = new THREE.Mesh(
      new THREE.ShapeGeometry(arrow),
      new THREE.MeshBasicMaterial({ color: '#cbc9c6', side: THREE.DoubleSide }),
    )
    mesh.rotation.x = -Math.PI / 2
    mesh.position.set(6.5, 0.04, band.z + 0.8)
    group.add(mesh)
  }
  for (const { slot, x, z, rotation } of layout.placements) {
    const state = slotState(slot)
    const color = STATUS[state]?.color || '#808587'
    const bay = new THREE.Group()
    bay.position.set(x, 0, z)
    bay.rotation.y = rotation
    group.add(bay)
    const surface = new THREE.Mesh(
      new THREE.BoxGeometry(2.8, 0.02, 5.65),
      new THREE.MeshStandardMaterial({
        color,
        transparent: true,
        opacity: state === 'AVAILABLE' ? 0.2 : 0.055,
        roughness: 1,
      }),
    )
    surface.position.y = -0.02
    surface.userData.slotId = slot.id
    bay.add(surface)
    targets.push(surface)
    for (const side of [-1, 1])
      box(
        bay,
        [0.055, 0.025, 5.5],
        [side * 1.38, 0.01, 0],
        state === 'AVAILABLE' ? '#d7d8cd' : '#a2a09e',
      )
    box(bay, [2.8, 0.025, 0.055], [0, 0.01, -2.75], '#a8a6a4')
    box(
      bay,
      [1.15, 0.08, 0.2],
      [0, 0.04, -1.9],
      state === 'AVAILABLE' ? '#eeeae0' : '#bab8b6',
      0.025,
    )
    addLabel(
      bay,
      slot.slot_number,
      0,
      2.18,
      2.1,
      state === 'AVAILABLE' ? '#f5f1de' : '#cfccc9',
      32,
    )
    if (slot.vehicle_type === 'EV Charging') {
      box(bay, [0.4, 0.95, 0.28], [1, 0.45, -2.5], '#c5c3c0', 0.04)
      box(bay, [0.25, 0.27, 0.03], [1, 0.63, -2.34], '#282827')
    }
    if (state === 'OCCUPIED') {
      const car = new THREE.Group()
      bay.add(car)
      const palette = [
        '#d9dbd8',
        '#a4a8a8',
        '#3d474d',
        '#bdb8a8',
        '#7d868a',
        '#ced3d4',
      ]
      const paint = palette[Math.abs(slot.id) % palette.length]
      const suv = slot.vehicle_type === 'SUV'
      const bike = slot.vehicle_type === 'Two-Wheeler'
      if (bike) {
        box(car, [0.6, 0.5, 1.8], [0, 0.55, 0], paint, 0.1, 0.3)
        box(car, [0.55, 0.16, 0.9], [0, 0.88, 0.1], '#222221', 0.06)
      } else {
        box(
          car,
          [1.85, suv ? 0.7 : 0.55, 3.65],
          [0, 0.6, -0.2],
          paint,
          0.18,
          0.35,
        )
        box(
          car,
          [1.58, suv ? 0.7 : 0.56, 1.95],
          [0, suv ? 1.16 : 1.02, -0.3],
          '#29353d',
          0.2,
          0.55,
        )
        box(
          car,
          [1.43, 0.1, 1.36],
          [0, suv ? 1.51 : 1.31, -0.31],
          paint,
          0.06,
          0.4,
        )
        for (const side of [-1, 1]) {
          box(
            car,
            [0.12, 0.25, 1.62],
            [side * 0.81, 0.99, -0.3],
            '#68777d',
            0.04,
          )
          for (const axle of [-1.3, 1])
            box(
              car,
              [0.23, 0.51, 0.57],
              [side * 0.89, 0.31, axle],
              '#1b2024',
              0.1,
            )
          box(
            car,
            [0.4, 0.11, 0.06],
            [side * 0.57, 0.68, 1.65],
            '#eceae6',
            0.025,
          )
          box(
            car,
            [0.45, 0.08, 0.06],
            [side * 0.57, 0.65, -2.04],
            '#b5a298',
            0.02,
          )
          box(car, [0.18, 0.12, 0.36], [side * 0.98, 0.92, 0.3], paint, 0.035)
        }
      }
      car.traverse((child) => {
        if (child.isMesh) {
          child.userData.slotId = slot.id
          targets.push(child)
        }
      })
    } else if (state === 'MAINTENANCE') {
      for (const side of [-1, 1]) {
        const cone = new THREE.Mesh(
          new THREE.ConeGeometry(0.22, 0.65, 12),
          material('#c9a57c'),
        )
        cone.position.set(side * 0.65, 0.32, 0.5)
        bay.add(cone)
        box(bay, [0.6, 0.05, 0.6], [side * 0.65, 0.02, 0.5], '#cbc9c5')
      }
    } else if (state === 'RESERVED')
      addLabel(bay, 'RESERVED', 0, 0, 2.2, '#d1c9b8', 25)
  }
  return { group, targets }
}

export default function ParkingScene({
  layout,
  selectedId,
  onSelect,
  view,
  resetKey,
  onUnavailable,
}) {
  const hostRef = useRef(null)
  const engineRef = useRef(null)

  useEffect(() => {
    const host = hostRef.current
    let renderer
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: 'low-power',
      })
    } catch {
      onUnavailable(
        '3D is unavailable on this device. The 2D plan has the same bay selection controls.',
      )
      return
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6))
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFShadowMap
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.3
    renderer.domElement.setAttribute(
      'aria-label',
      '3D parking floor. Drag to orbit; scroll to zoom. Use the 2D plan for keyboard bay selection.',
    )
    renderer.domElement.setAttribute('role', 'img')
    host.appendChild(renderer.domElement)
    const scene = new THREE.Scene()
    const camera = new THREE.OrthographicCamera(-30, 30, 25, -25, 0.1, 300)
    camera.position.set(30, 38, 38)
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.target.set(0, 0, 0)
    controls.minPolarAngle = 0.05
    controls.maxPolarAngle = Math.PI / 2.25
    controls.minZoom = 0.55
    controls.maxZoom = 3.5
    controls.enablePan = true
    controls.update()
    scene.add(new THREE.HemisphereLight('#ffffff', '#656565', 3))
    const sun = new THREE.DirectionalLight('#ffffff', 4.5)
    sun.position.set(-16, 35, 18)
    sun.castShadow = true
    sun.shadow.mapSize.set(1024, 1024)
    Object.assign(sun.shadow.camera, {
      left: -45,
      right: 45,
      top: 50,
      bottom: -50,
    })
    sun.shadow.normalBias = 0.06
    scene.add(sun)
    const grid = new THREE.GridHelper(140, 70, '#51504f', '#403f3e')
    grid.position.y = -1.1
    grid.material.transparent = true
    grid.material.opacity = 0.1
    scene.add(grid)
    const selection = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(2.95, 0.1, 5.85)),
      new THREE.LineBasicMaterial({ color: '#fff9e6' }),
    )
    selection.visible = false
    scene.add(selection)
    const render = () => renderer.render(scene, camera)
    controls.addEventListener('change', render)
    const engine = {
      renderer,
      scene,
      camera,
      controls,
      render,
      deck: null,
      targets: [],
      selection,
      layout: null,
    }
    engineRef.current = engine
    function resize() {
      const width = host.clientWidth,
        height = host.clientHeight
      if (!width || !height) return
      renderer.setSize(width, height)
      const aspect = width / height
      const depth = engine.layout?.depth || 35
      const deckWidth = engine.layout?.width || 24
      camera.updateMatrixWorld()
      const corners = []
      for (const x of [-deckWidth / 2, deckWidth / 2]) {
        for (const y of [-1, 2.2]) {
          for (const z of [-depth / 2, depth / 2])
            corners.push(
              new THREE.Vector3(x, y, z).applyMatrix4(
                camera.matrixWorldInverse,
              ),
            )
        }
      }
      const xs = corners.map((point) => point.x),
        ys = corners.map((point) => point.y)
      const minX = Math.min(...xs),
        maxX = Math.max(...xs),
        minY = Math.min(...ys),
        maxY = Math.max(...ys)
      const span =
        Math.max(
          (maxY - minY) / Math.max(0.6, (height - 80) / height),
          (maxX - minX) / aspect,
        ) * 1.07
      const centerX = (minX + maxX) / 2,
        centerY = (minY + maxY) / 2 + span * 0.05
      camera.left = centerX - (span * aspect) / 2
      camera.right = centerX + (span * aspect) / 2
      camera.top = centerY + span / 2
      camera.bottom = centerY - span / 2
      camera.updateProjectionMatrix()
      render()
    }
    engine.resize = resize
    const observer = new ResizeObserver(resize)
    observer.observe(host)
    const onLost = (event) => {
      event.preventDefault()
      onUnavailable('The 3D context was lost. Use the 2D plan to continue.')
    }
    renderer.domElement.addEventListener('webglcontextlost', onLost)
    resize()
    return () => {
      observer.disconnect()
      controls.dispose()
      renderer.domElement.removeEventListener('webglcontextlost', onLost)
      disposeGroup(scene)
      renderer.dispose()
      renderer.domElement.remove()
      engineRef.current = null
    }
  }, [onUnavailable])

  useEffect(() => {
    const engine = engineRef.current
    if (!engine) return
    if (engine.deck) {
      engine.scene.remove(engine.deck)
      disposeGroup(engine.deck)
    }
    const { group, targets } = populateDeck(layout)
    engine.deck = group
    engine.targets = targets
    engine.layout = layout
    engine.scene.add(group)
    engine.selection.visible = false
    engine.resize()
  }, [layout])

  useEffect(() => {
    const engine = engineRef.current
    if (!engine) return
    const placement = layout.placements.find(
      (item) => item.slot.id === selectedId,
    )
    engine.selection.visible = Boolean(placement)
    if (placement) engine.selection.position.set(placement.x, 0.16, placement.z)
    engine.render()
  }, [layout, selectedId])

  useEffect(() => {
    const engine = engineRef.current
    if (!engine) return
    engine.camera.zoom = 1
    engine.camera.position.set(
      ...(view === 'top' ? [0, 60, 0.1] : [30, 38, 38]),
    )
    engine.controls.target.set(0, 0, 0)
    engine.controls.update()
    engine.resize()
  }, [view, resetKey])

  useEffect(() => {
    const engine = engineRef.current
    if (!engine) return
    const canvas = engine.renderer.domElement
    const raycaster = new THREE.Raycaster()
    const pointer = new THREE.Vector2()
    let down = null
    function pointerDown(event) {
      down = [event.clientX, event.clientY]
    }
    function pointerUp(event) {
      if (
        !down ||
        Math.hypot(event.clientX - down[0], event.clientY - down[1]) > 6
      )
        return
      const bounds = canvas.getBoundingClientRect()
      pointer.set(
        ((event.clientX - bounds.left) / bounds.width) * 2 - 1,
        (-(event.clientY - bounds.top) / bounds.height) * 2 + 1,
      )
      raycaster.setFromCamera(pointer, engine.camera)
      const hit = raycaster.intersectObjects(engine.targets, false)[0]
      if (hit) onSelect(hit.object.userData.slotId)
      down = null
    }
    canvas.addEventListener('pointerdown', pointerDown)
    canvas.addEventListener('pointerup', pointerUp)
    return () => {
      canvas.removeEventListener('pointerdown', pointerDown)
      canvas.removeEventListener('pointerup', pointerUp)
    }
  }, [onSelect])

  return <div className="bay-scene-host" ref={hostRef} />
}
