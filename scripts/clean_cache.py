#!/usr/bin/env python3
"""
Clean up Python cache files and directories.

Removes:
  * __pycache__ directories
  * .pyc, .pyo, .pyd files
"""

import os
import shutil


def clean_pycache(root="."):
    for dirpath, dirnames, filenames in os.walk(root):
        # Remove __pycache__ directories
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            print(f"Removing directory: {pycache_path}")
            shutil.rmtree(pycache_path, ignore_errors=True)

        # Remove .pyc/.pyo/.pyd files
        for filename in filenames:
            if filename.endswith((".pyc", ".pyo", ".pyd")):
                file_path = os.path.join(dirpath, filename)
                print(f"Removing file: {file_path}")
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Failed to remove {file_path}: {e}")


if __name__ == "__main__":
    clean_pycache(".")
    print("Cleanup complete!")
