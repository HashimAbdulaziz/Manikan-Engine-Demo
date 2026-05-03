

# Manikan Engine

**Real-time 3D body avatar generation from anthropometric measurements.**

Manikan takes five body measurements — height, weight, chest, waist, and hips — and produces a physically accurate 3D human mesh in under 5 seconds. The engine uses differentiable optimisation over the SMPL parametric body model to solve for shape parameters that match the target proportions.

Built as a full-stack web application with a React + Three.js frontend and a FastAPI + PyTorch backend.

---

## Demo

<!-- Replace the line below with your demo video or GIF -->
<!-- Example: ![Manikan Demo](./docs/assets/demo.mp4) -->


<div align="center">
  <video src="https://github.com/HashimAbdulaziz/Manikan-Engine-Demo/raw/main/docs/demo.mp4" width="100%" controls muted autoplay loop>
  </video>
</div>

---

## How It Works

The system operates in three stages. For a detailed technical write-up, see [docs/technical-overview.md](./docs/technical-overview.md).

**1. Measurement Input**
The user provides five standard body measurements through the web interface: height (cm), weight (kg), chest circumference (cm), waist circumference (cm), and hip circumference (cm). An optional sex parameter selects the appropriate body model.

**2. Differentiable Optimisation**
The backend solves for the 10 SMPL shape parameters using gradient descent. A forward pass through the SMPL model generates a mesh, circumferences are measured on the mesh surface using vertex rings extracted via convex hull projection, and the loss between measured and target values drives the optimiser. Height is handled separately through global scaling to prevent gradient conflicts between height and shape.

**3. Mesh Export**
The final mesh is uniformly scaled to the exact target height, converted to a GLB binary, and streamed back to the frontend where it is rendered in a Three.js scene with PBR lighting.

---

## Project Structure

```
manikan-investor-demo/
├── backend/
│   ├── main.py              # FastAPI server + SMPL optimisation engine
│   ├── requirements.txt     # Python dependencies
│   ├── models/
│   │   └── smpl/            # SMPL model files (not tracked — see setup)
│   └── tools/
│       └── clean_smpl_pkl.py  # Utility to prepare SMPL pickle files
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Root layout — split-pane dashboard
│   │   ├── index.css         # Design system tokens and global styles
│   │   └── components/
│   │       ├── ControlPanel.jsx      # Measurement sliders + generate button
│   │       ├── MeasurementSlider.jsx  # Reusable range input component
│   │       └── AvatarViewer.jsx      # Three.js 3D viewer + loading overlay
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── docs/
│   ├── technical-overview.md  # Detailed technical documentation
│   └── assets/                # Screenshots, demo videos, diagrams
│
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- SMPL model files (`SMPL_MALE.pkl`, `SMPL_FEMALE.pkl`) from [smpl.is.tue.mpg.de](https://smpl.is.tue.mpg.de/)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Place your SMPL `.pkl` files in `backend/models/smpl/`, then clean them for use with `smplx`:

```bash
python tools/clean_smpl_pkl.py
```

Start the server:

```bash
python -m uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## API

### POST /generate-avatar

Generates a 3D body mesh from measurements.

**Request body:**

```json
{
  "sex": "male",
  "height_cm": 175,
  "weight_kg": 75,
  "chest_cm": 96,
  "waist_cm": 82,
  "hips_cm": 96
}
```

**Response:** Binary GLB file (`application/octet-stream`)

---

## Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Frontend  | React, Three.js, React Three Fiber, Tailwind CSS, Vite |
| Backend   | FastAPI, PyTorch, smplx, trimesh  |
| 3D Model  | SMPL (Skinned Multi-Person Linear Model) |
| Transport | REST API, binary GLB streaming    |

---

## References

- Loper, M., Mahmood, N., Romero, J., Pons-Moll, G., & Black, M. J. (2015). *SMPL: A Skinned Multi-Person Linear Model.* ACM Transactions on Graphics.
- Bogo, F., et al. (2016). *Keep it SMPL: Automatic Estimation of 3D Human Pose and Shape from a Single Image.* ECCV.
- Bojanic, D. (2023). *SMPL-Anthropometry.* GitHub. [github.com/DavidBoja/SMPL-Anthropometry](https://github.com/DavidBoja/SMPL-Anthropometry)

---

## License

This project is provided for demonstration purposes. SMPL model files are subject to the [SMPL Model License](https://smpl.is.tue.mpg.de/modellicense).
