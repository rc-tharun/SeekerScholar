#!/usr/bin/env python3
"""
Quick script to check if data files exist and their sizes.
Useful for debugging deployment issues.
"""
import os
import sys

data_dir = os.getenv("DATA_DIR", "../data")
if not os.path.isabs(data_dir):
    data_dir = os.path.abspath(data_dir)

print(f"Checking data directory: {data_dir}")
print(f"Absolute path: {os.path.abspath(data_dir)}")
print(f"Directory exists: {os.path.exists(data_dir)}")

if os.path.exists(data_dir):
    print(f"\nContents of {data_dir}:")
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isfile(item_path):
            size_mb = os.path.getsize(item_path) / (1024 * 1024)
            print(f"  {item}: {size_mb:.2f} MB")
        else:
            print(f"  {item}/ (directory)")

required_files = ["df.pkl", "bm25.pkl", "embeddings.pt", "graph.pkl"]
print(f"\nRequired files check:")
all_exist = True
for filename in required_files:
    filepath = os.path.join(data_dir, filename)
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"  {status} {filename}: {'Found' if exists else 'MISSING'}")
    if exists:
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"      Size: {size_mb:.2f} MB")
    all_exist = all_exist and exists

if not all_exist:
    print("\n✗ Some required files are missing!")
    sys.exit(1)
else:
    print("\n✓ All required files are present!")








