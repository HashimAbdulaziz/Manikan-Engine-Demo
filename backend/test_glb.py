import requests

res = requests.post("http://127.0.0.1:8000/generate-avatar", json={
    "sex":"male", "height_cm":175, "weight_kg":75, "chest_cm":98, "waist_cm":82, "hips_cm":96
})

print("Status:", res.status_code)
print("Content length:", len(res.content))
if len(res.content) < 100:
    print("Content:", res.content)
