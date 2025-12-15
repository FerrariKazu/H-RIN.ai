import os
import glob
import json

files = glob.glob('temp_*.json')
if files:
    latest = sorted(files, reverse=True)[0]
    print(f"Latest file: {latest}")
    with open(latest) as f:
        data = json.load(f)
    print(f"Keys: {list(data.keys())}")
    print(f"Name field: {data.get('name', 'NOT FOUND')}")
    if 'summary' in data:
        print(f"Summary field: {data['summary'][:300]}")
    else:
        print("NO SUMMARY FIELD")
else:
    print("No temp JSON files found")
