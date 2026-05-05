"""
Generate Garment Templates for SMPL Mean Shape (β = 0)
=======================================================
Produces two garments:
  • T-shirt  — collarbone to pubic bone, short sleeves
  • Pants    — high waist to ankle

Design goals
------------
  1. Landmark-anchored Y bounds  (no percentile drift across genders)
  2. Laplacian smoothing (5 iter) → relaxed-fit instead of tight-skin shell
  3. 1.0 cm normal inflation (T-shirt) / 0.8 cm (pants) → realistic gap

Output (NPZ, no OBJ — avoids trimesh vertex deduplication side-effects):
    models/clothing/tshirt_male_template.npz   + tshirt_male_vertex_map.json
    models/clothing/tshirt_female_template.npz + tshirt_female_vertex_map.json
    models/clothing/pants_male_template.npz    + pants_male_vertex_map.json
    models/clothing/pants_female_template.npz  + pants_female_vertex_map.json
    models/clothing/tshirt_template.npz        (alias → female)
    models/clothing/pants_template.npz         (alias → female)

Usage:
    cd backend
    python tools/generate_tshirt_template.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

# ── Paths ────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parent.parent   # backend/
MODEL_DIR = ROOT / "models"
OUT_DIR   = MODEL_DIR / "clothing"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NUM_BETAS = 10

# ── SMPL landmark vertex indices ─────────────────────────────────────────
SMPL_LANDMARKS = {
    "HEAD_TOP":    412,
    "LEFT_HEEL":   3458,
    "RIGHT_HEEL":  6858,
    "PUBIC_BONE":  3145,
}

# ── Tuning constants ──────────────────────────────────────────────────────
# T-shirt collar: start this far below HEAD_TOP.
# HEAD_TOP→chin ≈ 0.22m; +0.04m → base-of-neck; +0.04m more → crew-neck
COLLAR_DROP      = 0.30    # metres below HEAD_TOP  (was 0.26 → turtleneck)
TSHIRT_INFLATION = 0.010   # 1.0 cm outward push (Tight Skinny offset)
PANTS_INFLATION  = 0.010   # 1.0 cm outward push (Tight Skinny offset)
SMOOTH_ITERS     = 15      # Reduced to 15 for tight anatomical tracks


# ════════════════════════════════════════════════════════════════════════════
#  SMPL loader
# ════════════════════════════════════════════════════════════════════════════

def _load_mean_body(gender: str):
    """Return (verts [6890,3], faces [N,3]) for the SMPL mean shape."""
    import smplx, torch

    model = smplx.create(
        model_path=str(MODEL_DIR),
        model_type="smpl",
        gender=gender,
        num_betas=NUM_BETAS,
        batch_size=1,
    )
    model.eval()
    with torch.no_grad():
        out = model(
            betas=torch.zeros(1, NUM_BETAS),
            global_orient=torch.zeros(1, 3),
            body_pose=torch.zeros(1, 69),
            return_verts=True,
        )
    verts = out.vertices.squeeze(0).cpu().numpy()
    faces = np.array(model.faces, dtype=np.int64)
    return verts, faces


# ════════════════════════════════════════════════════════════════════════════
#  Laplacian smoothing
# ════════════════════════════════════════════════════════════════════════════

def _gaussian_blur_mask(verts: np.ndarray, faces: np.ndarray, mask: np.ndarray, iters: int = 3) -> np.ndarray:
    """
    Applies a discrete Gaussian blur to the boolean selection mask over the mesh graph.
    This effectively acts as morphological opening/closing, transforming a sharp, 
    jagged boolean cut into a perfectly clean, smooth-flowing edge definition.
    """
    smoothed_mask = mask.astype(np.float32)
    n = len(verts)
    adj: list[list[int]] = [[] for _ in range(n)]
    for f in faces:
        for i in range(3):
            a, b = int(f[i]), int(f[(i + 1) % 3])
            adj[a].append(b)
            adj[b].append(a)
            
    for _ in range(iters):
        new_m = smoothed_mask.copy()
        for i in range(n):
            if adj[i]:
                # Gaussian weighted average over 1-ring neighbors
                neighbors_val = np.mean([smoothed_mask[nb] for nb in adj[i]])
                new_m[i] = 0.5 * smoothed_mask[i] + 0.5 * neighbors_val
        smoothed_mask = new_m

    # Threshold back to boolean to ensure a smooth continuous selection line
    return smoothed_mask > 0.5


def smooth_mesh_boundaries(verts: np.ndarray, faces: np.ndarray, n_iter: int = 80) -> np.ndarray:
    """
    Radial Constraint Smoothing for all garment openings (Neck, Sleeves, Hems).
    Strictly identifies all 'open edges' of the mesh without creating loops.
    Applies Laplacian Smoothing (80 iterations) explicitly to the identified boundaries
    while enforcing radial consistency to output perfect circular openings.
    """
    n = len(verts)
    adj: list[set] = [set() for _ in range(n)]
    
    # 1. Identify open edges
    edge_counts = {}
    for f in faces:
        for i in range(3):
            a, b = int(f[i]), int(f[(i + 1) % 3])
            adj[a].add(b)
            adj[b].add(a)
            e = tuple(sorted((a, b)))
            edge_counts[e] = edge_counts.get(e, 0) + 1

    boundary_edges = [e for e, count in edge_counts.items() if count == 1]
    if not boundary_edges:
        return verts

    # 2. Extract Boundary Loops
    adjacency_map = {}
    for a, b in boundary_edges:
        adjacency_map.setdefault(a, []).append(b)
        adjacency_map.setdefault(b, []).append(a)
        
    loops = []
    visited = set()
    
    for start_node in list(adjacency_map.keys()):
        if start_node in visited:
            continue
        loop = []
        curr = start_node
        prev = None
        while curr not in visited:
            visited.add(curr)
            loop.append(curr)
            neighbors = adjacency_map[curr]
            next_node = None
            for nb in neighbors:
                if nb != prev and nb not in visited:
                    next_node = nb
                    break
            if next_node is None:
                break
            prev = curr
            curr = next_node
        if len(loop) > 3:
            loops.append(loop)

    # Identify 1-ring neighbors to preserve length
    boundary_verts = set(sum(loops, []))
    active_verts = set(boundary_verts)
    for v in boundary_verts:
        active_verts.update(adj[v])

    out_verts = verts.copy()
    
    # 3. Radial Constraint Smoothing 
    for _ in range(n_iter):
        new_v = out_verts.copy()
        
        # Standard Laplacian to 1-ring
        for i in active_verts:
            if i not in boundary_verts:
                new_v[i] = out_verts[list(adj[i])].mean(axis=0)
                
        # Radial Laplacian to boundaries
        for loop in loops:
            loop_verts = out_verts[loop]
            center = loop_verts.mean(axis=0)
            avg_radius = np.mean(np.linalg.norm(loop_verts - center, axis=1))
            
            for i in loop:
                smooth_pos = out_verts[list(adj[i])].mean(axis=0)
                vec = smooth_pos - center
                norm = np.linalg.norm(vec)
                if norm > 0:
                    rad_pos = center + (vec / norm) * avg_radius
                    # Snap 50% to laplacian and 50% to radial circle
                    new_v[i] = 0.5 * smooth_pos + 0.5 * rad_pos
        out_verts = new_v
        
    return out_verts


# ════════════════════════════════════════════════════════════════════════════
#  Vertex selection
# ════════════════════════════════════════════════════════════════════════════

def _select_tshirt_vertices(verts: np.ndarray, gender: str = "male") -> np.ndarray:
    """
    Boolean mask for the T-shirt region.

    Uses safe geometric bounds to prevent torso fragmentation:
    1. Neckline: U-shaped depth map with a gender-aware neck-cylinder exclusion zone.
    2. Sleeves: Half-Sleeve Gaussian carve down to 0.28m.
    """
    y = verts[:, 1]
    x = verts[:, 0]
    z = verts[:, 2]

    head_y  = verts[SMPL_LANDMARKS["HEAD_TOP"],   1]
    pubic_y = verts[SMPL_LANDMARKS["PUBIC_BONE"], 1]

    # --- 1. Neckline Reconstruction ---
    # Base collar line below the head
    neck_root_y = head_y - 0.20
    
    # Clean 'U' shape by lowering front-center neck by an extra 0.05m
    scoop = 0.05 * np.exp(- (x**2) / (0.06**2)) * (z > 0)
    y_top = neck_root_y - scoop

    # Strict exclusion cylinder for the throat (Gender-Aware fit)
    neck_radius = 0.045 if gender == "female" else 0.050
    r_neck = np.sqrt(x**2 + z**2)
    in_neck_cylinder = (r_neck < neck_radius) & (y > neck_root_y - 0.15)

    # Vertical bands
    y_bot = pubic_y
    mask_y = (y <= y_top) & (~in_neck_cylinder) & (y >= y_bot)

    # --- 2. Armhole Refinement (True Half-Sleeve Upgrade) ---
    # Using a Gaussian transition pointing outwards to create a proper half-sleeve
    armpit_y = neck_root_y - 0.05
    
    # Carve depth sweeps inward gently by 0.04m near the armpit from the 0.32m base torso.
    # This prevents creating a torso gap while supporting the wide 0.28m sleeves.
    carve_depth = 0.04 * np.exp(- ((y - armpit_y)**2) / (0.10**2))
    allowed_x = 0.32 - carve_depth
    
    # 3. Shoulder Peak Normalization (True Half-Sleeve extended length)
    # Keep abs(x) <= 0.28m strictly safe everywhere to protect the peak extending far down the arm
    allowed_x = np.maximum(allowed_x, 0.28)
    
    # 4. Vertical Alignment constraint
    # Force allowed_x = 0.32 for any y below PUBIC_BONE.y + 0.15m 
    # to protect the side-torso coverage absolutely.
    protected_lower_torso = y < (pubic_y + 0.15)
    allowed_x[protected_lower_torso] = 0.32
    
    mask_x = np.abs(x) < allowed_x

    return mask_y & mask_x


def _select_pants_vertices(verts: np.ndarray) -> np.ndarray:
    """
    Boolean mask for the pants region.

    Y bands:
        y_top = PUBIC_BONE.y + 0.02 m   ← high waist (slight overlap w/ shirt hem)
        y_bot = HEEL.y + 0.03 m         ← ankle (excludes sole / feet)

    X band: |x| < 0.30 m (legs only, excludes arms)
    """
    y = verts[:, 1]
    x = verts[:, 0]

    pubic_y = verts[SMPL_LANDMARKS["PUBIC_BONE"],  1]
    lheel_y = verts[SMPL_LANDMARKS["LEFT_HEEL"],   1]
    rheel_y = verts[SMPL_LANDMARKS["RIGHT_HEEL"],  1]
    heel_y  = (lheel_y + rheel_y) / 2.0

    y_top = pubic_y + 0.12
    y_bot = heel_y  + 0.03

    print(f"    Pants  Y: {y_bot:.4f} → {y_top:.4f} m  "
          f"(length {y_top - y_bot:.4f} m)")

    mask_y = (y <= y_top) & (y >= y_bot)
    
    # In A-pose, hands might hang to mid-thigh at abs(x) > 0.40.
    # To avoid missing leg vertices (fragmentation), we widen the X-bound
    # just enough to include thick thighs/calves but exclude hands.
    mask_x = np.abs(x) < 0.45

    return mask_y & mask_x


# ════════════════════════════════════════════════════════════════════════════
#  Mesh builder
# ════════════════════════════════════════════════════════════════════════════

def _build_garment_mesh(
    verts: np.ndarray,
    faces: np.ndarray,
    mask: np.ndarray,
    inflation_m: float,
    smooth_iters: int = SMOOTH_ITERS,
):
    """
    Build a compact garment sub-mesh.

    Steps
    -----
    1. Filter faces — keep only triangles where all 3 verts are in mask
    2. Re-index to a compact [0, N) range
    3. Laplacian smooth to relax the mesh away from the body
    4. Re-compute normals on the smoothed mesh and push outward by inflation_m

    Returns
    -------
    garment : trimesh.Trimesh
    body_indices : np.ndarray  — original SMPL vertex indices (for β-warping)
    """
    selected_idx = np.where(mask)[0]
    idx_set      = set(selected_idx.tolist())

    face_mask = np.array([
        f[0] in idx_set and f[1] in idx_set and f[2] in idx_set
        for f in faces
    ])
    sub_faces = faces[face_mask]

    old_to_new = {old: new for new, old in enumerate(selected_idx)}
    new_faces  = np.vectorize(old_to_new.get)(sub_faces)
    sub_verts  = verts[selected_idx].copy()

    # Boundary-only Radial constraint smoothing: snaps jagged necklines and armholes to perfect circles!
    if smooth_iters > 0:
        sub_verts = smooth_mesh_boundaries(sub_verts, new_faces, n_iter=80)

    # Inflate outward along vertex normals
    tmp     = trimesh.Trimesh(vertices=sub_verts, faces=new_faces, process=False)
    normals = tmp.vertex_normals.copy()
    sub_verts += normals * inflation_m

    garment = trimesh.Trimesh(vertices=sub_verts, faces=new_faces, process=False)
    return garment, selected_idx


# ════════════════════════════════════════════════════════════════════════════
#  Per-garment processing
# ════════════════════════════════════════════════════════════════════════════

def _save_garment(
    name: str,
    gender: str,
    g_verts: np.ndarray,
    g_faces: np.ndarray,
    body_indices: np.ndarray,
    is_last: bool,
):
    """Delete stale files and save NPZ + JSON."""
    npz_path  = OUT_DIR / f"{name}_{gender}_template.npz"
    map_path  = OUT_DIR / f"{name}_{gender}_vertex_map.json"
    alias_npz = OUT_DIR / f"{name}_template.npz"
    alias_map = OUT_DIR / f"{name}_vertex_map.json"

    # Remove every stale file for this garment+gender (OBJ or NPZ)
    for p in (
        list(OUT_DIR.glob(f"{name}_{gender}*"))
        + (list(OUT_DIR.glob(f"{name}_template*")) if is_last else [])
    ):
        if p.exists():
            p.unlink()

    assert len(g_verts) == len(body_indices), (
        f"BUG [{name}/{gender}]: {len(g_verts)} verts ≠ {len(body_indices)} map entries"
    )

    np.savez_compressed(str(npz_path), vertices=g_verts, faces=g_faces)
    with open(map_path, "w") as f:
        json.dump(body_indices.tolist(), f)

    print(f"    Saved → {npz_path.name}  ({len(g_verts)} verts, {len(g_faces)} faces)")
    print(f"    Saved → {map_path.name}  ({len(body_indices)} entries)")

    if is_last:
        np.savez_compressed(str(alias_npz), vertices=g_verts, faces=g_faces)
        with open(alias_map, "w") as f:
            json.dump(body_indices.tolist(), f)
        print(f"    Alias → {alias_npz.name} / {alias_map.name}")


def process_gender(gender: str, is_last: bool):
    print(f"\n── Gender: {gender} {'─' * 50}")
    verts, faces = _load_mean_body(gender)

    # ── T-shirt ───────────────────────────────────────────────────────────
    print("  [T-shirt]")
    mask_ts = _select_tshirt_vertices(verts, gender)
    
    # Gaussian Blur on mask loops to snap a clean boundary
    mask_ts = _gaussian_blur_mask(verts, faces, mask_ts, iters=3)
    
    print(f"    {mask_ts.sum()} / {len(verts)} vertices selected")
    g_ts, idx_ts = _build_garment_mesh(verts, faces, mask_ts, TSHIRT_INFLATION)
    _save_garment("tshirt", gender, g_ts.vertices, g_ts.faces, idx_ts, is_last)

    # ── Pants ─────────────────────────────────────────────────────────────
    print("  [Pants]")
    mask_pt = _select_pants_vertices(verts)
    
    # Apply mask blur to pants waistlines/ankles as well!
    mask_pt = _gaussian_blur_mask(verts, faces, mask_pt, iters=3)
    
    print(f"    {mask_pt.sum()} / {len(verts)} vertices selected")
    g_pt, idx_pt = _build_garment_mesh(verts, faces, mask_pt, PANTS_INFLATION)
    _save_garment("pants", gender, g_pt.vertices, g_pt.faces, idx_pt, is_last)


def main():
    genders = ["male", "female"]
    for i, gender in enumerate(genders):
        process_gender(gender, is_last=(i == len(genders) - 1))
    print("\nDone ✓")


if __name__ == "__main__":
    main()
