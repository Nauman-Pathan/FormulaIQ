import urllib.request, json
url = "http://localhost:8000/api/v1/races?season=2026"
with urllib.request.urlopen(url) as r:
    data = json.load(r)
print(f"Total races: {len(data)}")
for d in data:
    print(f"  R{d['round_number']:02d} {d['grand_prix_name']:30s} [{d['session_status']}]  {d['race_date']}")
