#!/usr/bin/env python3
"""
Convert heavy artifacts to lightweight formats for reduced RAM usage.

Converts:
- df.pkl -> df.parquet (compressed, columnar format)
- embeddings.pt -> embeddings.f16.npy (float16 numpy memmap format)

Run this script locally once, then upload the new artifacts to GitHub Releases.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
import torch
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def convert_df_to_parquet(input_path: str, output_path: str):
    """
    Convert DataFrame pickle to Parquet format.
    
    Args:
        input_path: Path to df.pkl
        output_path: Path to output df.parquet
    """
    print(f"Loading DataFrame from {input_path}...")
    df = pd.read_pickle(input_path)
    print(f"  Loaded DataFrame: {len(df)} rows, {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}")
    
    # Keep only necessary columns for API (title, abstract, and index)
    # The index will be preserved as a column if needed
    required_cols = ["title", "abstract"]
    
    # Check which columns exist
    available_cols = [col for col in required_cols if col in df.columns]
    if len(available_cols) < len(required_cols):
        missing = set(required_cols) - set(available_cols)
        print(f"  ⚠ Warning: Missing columns {missing}, keeping all columns")
        available_cols = list(df.columns)
    else:
        # Keep index as a column for lookup
        if df.index.name is None:
            df = df.reset_index()
        available_cols = ["index"] + available_cols if "index" not in available_cols else available_cols
    
    # Select only needed columns
    df_subset = df[available_cols].copy()
    print(f"  Keeping columns: {available_cols}")
    
    # Save as parquet with compression
    print(f"  Writing to {output_path}...")
    df_subset.to_parquet(
        output_path,
        engine="pyarrow",
        compression="snappy",
        index=False
    )
    
    # Verify
    file_size = os.path.getsize(output_path)
    original_size = os.path.getsize(input_path)
    size_mb = file_size / (1024 * 1024)
    original_mb = original_size / (1024 * 1024)
    reduction = (1 - file_size / original_size) * 100
    
    print(f"  ✓ Converted: {original_mb:.2f} MB -> {size_mb:.2f} MB ({reduction:.1f}% reduction)")


def convert_embeddings_to_npy(input_path: str, output_path: str, meta_path: str):
    """
    Convert embeddings PyTorch tensor to float16 numpy memmap format.
    
    Args:
        input_path: Path to embeddings.pt
        output_path: Path to output embeddings.f16.npy
        meta_path: Path to output embeddings.meta.json
    """
    print(f"Loading embeddings from {input_path}...")
    embeddings = torch.load(input_path, map_location="cpu")
    
    # Handle different tensor formats
    if isinstance(embeddings, torch.Tensor):
        emb_array = embeddings.numpy()
    elif isinstance(embeddings, dict) and "embeddings" in embeddings:
        emb_array = embeddings["embeddings"].numpy()
    elif isinstance(embeddings, np.ndarray):
        emb_array = embeddings
    else:
        raise ValueError(f"Unexpected embeddings format: {type(embeddings)}")
    
    print(f"  Loaded embeddings: shape {emb_array.shape}, dtype {emb_array.dtype}")
    
    # Convert to float16
    print(f"  Converting to float16...")
    emb_f16 = emb_array.astype(np.float16)
    
    # Save as numpy array
    print(f"  Writing to {output_path}...")
    np.save(output_path, emb_f16)
    
    # Create metadata file
    metadata = {
        "shape": list(emb_f16.shape),
        "dtype": str(emb_f16.dtype),
        "format": "numpy_float16"
    }
    
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Verify
    file_size = os.path.getsize(output_path)
    original_size = os.path.getsize(input_path)
    size_mb = file_size / (1024 * 1024)
    original_mb = original_size / (1024 * 1024)
    reduction = (1 - file_size / original_size) * 100
    
    print(f"  ✓ Converted: {original_mb:.2f} MB -> {size_mb:.2f} MB ({reduction:.1f}% reduction)")
    print(f"  ✓ Metadata saved to {meta_path}")


def main():
    """Main conversion function."""
    # Get data directory
    data_dir = os.getenv("DATA_DIR", "data")
    if not os.path.isabs(data_dir):
        # Resolve relative to backend root
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.abspath(os.path.join(backend_root, data_dir))
    
    print(f"{'='*60}")
    print(f"SeekerScholar Artifact Converter")
    print(f"{'='*60}")
    print(f"Data directory: {data_dir}")
    print()
    
    # Check input files
    df_pkl = os.path.join(data_dir, "df.pkl")
    embeddings_pt = os.path.join(data_dir, "embeddings.pt")
    
    if not os.path.exists(df_pkl):
        print(f"✗ ERROR: {df_pkl} not found")
        sys.exit(1)
    
    if not os.path.exists(embeddings_pt):
        print(f"✗ ERROR: {embeddings_pt} not found")
        sys.exit(1)
    
    # Convert DataFrame
    print("Converting DataFrame...")
    df_parquet = os.path.join(data_dir, "df.parquet")
    try:
        convert_df_to_parquet(df_pkl, df_parquet)
    except Exception as e:
        print(f"✗ ERROR converting DataFrame: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    
    # Convert embeddings
    print("Converting embeddings...")
    embeddings_npy = os.path.join(data_dir, "embeddings.f16.npy")
    embeddings_meta = os.path.join(data_dir, "embeddings.meta.json")
    try:
        convert_embeddings_to_npy(embeddings_pt, embeddings_npy, embeddings_meta)
    except Exception as e:
        print(f"✗ ERROR converting embeddings: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print(f"{'='*60}")
    print("✓ Conversion complete!")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"1. Upload these files to GitHub Releases:")
    print(f"   - {df_parquet}")
    print(f"   - {embeddings_npy}")
    print(f"   - {embeddings_meta}")
    print(f"2. Update render.yaml with new URLs")
    print(f"3. Redeploy backend")


if __name__ == "__main__":
    main()

