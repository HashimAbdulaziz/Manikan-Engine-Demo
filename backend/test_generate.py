import asyncio
from main import generate_dressed_avatar_mesh
import time
import sys

def test():
    print("Starting generation...", flush=True)
    start = time.time()
    try:
        res = generate_dressed_avatar_mesh(
            sex="male",
            height_cm=175,
            weight_kg=75,
            chest_cm=96,
            waist_cm=82,
            hips_cm=96,
            tshirt_color_hex="#1a202c"
        )
        print(f"Generated successfully in {time.time() - start:.2f}s. Size: {len(res)} bytes", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    test()
