#!/usr/bin/env python3
"""
FBX Batch Processor - A tool for batch processing FBX files with Blender.

This script provides a command-line interface to process FBX files with Blender.
"""
import os
import sys
import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path

def get_blender_executable():
    """Find the Blender executable."""
    # Common Blender executable names
    blender_names = [
        "blender",
        "blender.exe",
        "Blender",
        "Blender.app/Contents/MacOS/Blender"
    ]
    
    # Check common installation directories
    common_paths = []
    
    # Windows
    if sys.platform == "win32":
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        common_paths.extend([
            os.path.join(program_files, "Blender Foundation"),
            os.path.join(program_files_x86, "Blender Foundation"),
            os.path.join(program_files, "Blender"),
            os.path.join(program_files_x86, "Blender")
        ])
    # macOS
    elif sys.platform == "darwin":
        common_paths.extend([
            "/Applications/Blender.app/Contents/MacOS",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS")
        ])
    # Linux
    else:
        common_paths.extend([
            "/usr/bin",
            "/usr/local/bin",
            "/snap/bin"
        ])
    
    # Check PATH
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    
    # Search for Blender executable
    for path in common_paths + path_dirs:
        for name in blender_names:
            blender_path = os.path.join(path, name)
            if os.path.isfile(blender_path) and os.access(blender_path, os.X_OK):
                return blender_path
    
    return None

def run_blender_script(blender_exec, script_path, args, module_path):
    """Run a Python script in Blender with the given arguments."""
    # Create a wrapper script that sets up the Python path correctly
    wrapper_script = f"""
import sys
import os

# Add the module path to Python path
sys.path.insert(0, r"{module_path}")

# Import and run the original script
import runpy
sys.argv = ["blender"] + {args}
runpy.run_path(r"{script_path}", run_name="__main__")
"""
    
    # Write the wrapper script to a temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
        f.write(wrapper_script)
        wrapper_path = f.name
    
    try:
        # Run Blender with the wrapper script
        cmd = [blender_exec, "--background", "--python", wrapper_path]
        
        # Run the command
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"Error running Blender: {e}", file=sys.stderr)
        if e.stdout:
            print("\nOutput:", e.stdout, file=sys.stderr)
        if e.stderr:
            print("\nError:", e.stderr, file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Blender executable not found. Please make sure Blender is installed and in your PATH.", file=sys.stderr)
        return False
    finally:
        # Clean up the temporary file
        try:
            os.unlink(wrapper_path)
        except:
            pass

def main():
    """Main entry point for the CLI."""
    # Find Blender executable
    blender_exec = get_blender_executable()
    if not blender_exec:
        print("Error: Could not find Blender executable. Please install Blender and make sure it's in your PATH.", file=sys.stderr)
        sys.exit(1)
    
    # Create a temporary directory for the script
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy the processor module to the temp directory
        module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fbx_batch_processor")
        temp_module_dir = os.path.join(temp_dir, "fbx_batch_processor")
        
        # Create the directory structure
        os.makedirs(temp_module_dir, exist_ok=True)
        
        # Copy all Python files from the module
        for file in os.listdir(module_dir):
            if file.endswith(".py"):
                shutil.copy2(
                    os.path.join(module_dir, file),
                    os.path.join(temp_module_dir, file)
                )
        
        # Create a temporary script to run the CLI
        temp_script = os.path.join(temp_dir, "run_cli.py")
        with open(temp_script, "w") as f:
            f.write("""
import sys
import os

# Add the temp directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the CLI
from fbx_batch_processor.cli import main as cli_main

if __name__ == "__main__":
    cli_main()
""")
        
        # Get the absolute path to the module
        module_path = os.path.dirname(os.path.abspath(__file__))
        
        # Run the script with Blender
        success = run_blender_script(
            blender_exec, 
            temp_script, 
            sys.argv[1:],
            module_path
        )
        
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
