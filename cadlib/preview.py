"""Write a self-contained HTML page that shows a part in the browser."""

import base64
from pathlib import Path

from build123d import Part

from cadlib.export import export_part

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>{title}</title>
<style>
  html, body {{ margin: 0; height: 100%; background: #f2f2f2; font: 13px/1.4 system-ui, sans-serif; }}
  #info {{ position: fixed; left: 12px; top: 10px; color: #333; }}
</style>
<div id="info"><b>{title}</b><br>{dims}<br>drag: rotate · right-drag: pan · wheel: zoom</div>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/controls/OrbitControls.js"></script>
<script>
const bytes = Uint8Array.from(atob("{stl}"), c => c.charCodeAt(0));
const view = new DataView(bytes.buffer);
const count = view.getUint32(80, true);
const pos = new Float32Array(count * 9);
for (let i = 0, o = 84; i < count; i++, o += 50)
  for (let k = 0; k < 9; k++) pos[i * 9 + k] = view.getFloat32(o + 12 + k * 4, true);
const geometry = new THREE.BufferGeometry();
geometry.setAttribute("position", new THREE.BufferAttribute(pos, 3));
geometry.computeVertexNormals();
geometry.computeBoundingBox();
const box = geometry.boundingBox, centre = box.getCenter(new THREE.Vector3());
const size = box.getSize(new THREE.Vector3()).length();

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf2f2f2);
const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({{ color: 0xe0851c, roughness: 0.6 }}));
mesh.position.sub(centre);
scene.add(mesh);
scene.add(new THREE.HemisphereLight(0xffffff, 0x666666, 1.0));
const sun = new THREE.DirectionalLight(0xffffff, 1.2);
sun.position.set(1, 2, 1.5);
scene.add(sun);
const grid = new THREE.GridHelper(Math.ceil(size / 50) * 100, Math.ceil(size / 50) * 10, 0x999999, 0xcccccc);
grid.position.y = box.min.y - centre.y;
scene.add(grid);

const camera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 1, size * 10);
camera.position.set(size * 0.8, size * 0.6, size * 1.0);
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setPixelRatio(devicePixelRatio);
document.body.appendChild(renderer.domElement);
const controls = new THREE.OrbitControls(camera, renderer.domElement);
function resize() {{
  renderer.setSize(innerWidth, innerHeight);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}}
addEventListener("resize", resize);
resize();
(function frame() {{ controls.update(); renderer.render(scene, camera); requestAnimationFrame(frame); }})();
</script>
"""


def write_preview(part: Part, stl_path: Path) -> Path:
    """Export `part` as STL to `stl_path` and write an HTML viewer for it alongside."""
    export_part(part, stl_path)
    size = part.bounding_box().size
    html_path = stl_path.with_suffix(".html")
    html_path.write_text(
        PAGE.format(
            title=stl_path.stem,
            dims=f"{size.X:.1f} × {size.Y:.1f} × {size.Z:.1f} mm",
            stl=base64.b64encode(stl_path.read_bytes()).decode(),
        )
    )
    return html_path
