"""Send random readings to the API running in the same container: python simulate.py [COUNT]"""
import json
import random
import sys
import urllib.request

URL = "http://localhost:5000/readings"
SENSORS = ["amphi-a", "library", "bloc-b", "cafeteria"]
count = int(sys.argv[1]) if len(sys.argv) > 1 else 20

for _ in range(count):
    reading = {"sensor": random.choice(SENSORS),
               "pm25": round(random.uniform(5, 60), 1)}
    req = urllib.request.Request(URL, data=json.dumps(reading).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        print(resp.status, resp.read().decode().strip())
