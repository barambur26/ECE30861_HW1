#!/usr/bin/env python3
"""
Quick check after fixes
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_dir = "/Users/blas/Documents/Obsidian Vault/School/F25/ECE 461/Project Repo/ECE30861_HW1"
    os.chdir(project_dir)
    
    output_file = Path("post_fix_check.txt")
    
    with open(output_file, "w") as f:
        f.write("🔧 POST-FIX DIAGNOSTIC CHECK\n")
        f.write("=" * 40 + "\n\n")
        
        # Check run file permissions
        run_file = Path("./run")
        f.write(f"✅ Run file executable: {os.access(run_file, os.X_OK)}\n")
        
        # Try pytest
        try:
            result = subprocess.run([sys.executable, '-m', 'pytest', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                f.write(f"✅ Pytest working: {result.stdout.strip()}\n")
            else:
                f.write(f"❌ Pytest still not working\n")
        except Exception as e:
            f.write(f"❌ Pytest error: {e}\n")
        
        # Try imports
        try:
            from acemcli.logging_setup import setup_logging
            f.write("✅ acemcli module importable\n")
        except Exception as e:
            f.write(f"❌ acemcli still not importable: {e}\n")
        
        f.write("\nReady to test!\n")
    
    print(f"Post-fix check written to {output_file}")

if __name__ == "__main__":
    main()
