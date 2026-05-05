# Manikan Engine Demo - 3D Garment Integration

A professional-grade backend engine that dynamically generates and rigs 3D garments (T-shirts and Pants) to an optimized SMPL body model in real-time. Built specifically for providing a "Skinny Fit", anatomically accurate representation of user measurements.

## Core Highlights

*   **Real-time Scaling:** Garments exhibit 1:1 Dynamic Vertex Tracking. As you adjust Chest, Waist, or Hip sliders, the clothing directly maps to the exact underlying coordinates.
*   **Skinny Fit & Zero Ballooning:** Garments are structurally constrained to a 1.2cm (0.012m) envelope directly driven by the `Body Normal` geometry. This ensures clothes never "balloon" out excessively while physically preventing any topological skin-clipping.
*   **Clean-Circle Boundaries:** Utilizes custom Radial Constraint Boundary Smoothing (80 Laplacian iterations). It explicitly tracks down the sleeves, cuffs, and necklines, forcing rough geometric boolean cuts into professionally tailored circular layouts. 
*   **Gender-Aware Physics:** Features dynamic exclusions, including a tailored `0.045m` neckline sweep specifically mapped for the female anatomical model.

## Installation & Requirements

Ensure you are running inside a compatible Python environment. Install dependencies via pip:

```bash
pip install -r requirements.txt
```

*Required packages include: `numpy`, `scipy`, `trimesh`, `torch`, `fastapi`, and `uvicorn`.*

## How to Run

### 1. Template Generation (Prerequisite)

**IMPORTANT:** Before launching the backend server, you *must* generate the baseline clothing templates. This creates the exact binary configurations necessary for the engine to operate.

Run the template generator from the backend folder:

```bash
cd backend
python tools/generate_tshirt_template.py
```
*This will output the required `.npz` binary mappings into the local array storage.*

### 2. Launching the Backend

Once the templates are generated, you can start the API Engine:

```bash
uvicorn main:app --reload --port 8000
```
*(Or simply run `python main.py` if your environment script is handled.)*

The endpoint `/generate-avatar` will actively accept body parameter sliders and return fully-rigged binary `.glb` scenes containing the SMPL core and perfectly scaled T-shirt and Pants.
