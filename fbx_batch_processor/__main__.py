"""Main entry point for the FBX Batch Processor."""
import sys
from pathlib import Path

def main():
    """Entry point for the application script."""
    # Add the project root to the Python path
    project_root = str(Path(__file__).parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Run as standalone CLI
    from .cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
