"""Command-line interface for FBX Batch Processor."""
import os
import sys
import logging
import argparse
from typing import List, Optional

from .processor import FBXProcessor
from .downloader import process_download_url


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def process_urls(
    urls: List[str],
    output_dir: str,
    config_path: Optional[str] = None,
    temp_dir: Optional[str] = None
) -> None:
    """Process a list of URLs.
    
    Args:
        urls: List of URLs to process
        output_dir: Base directory for output
        config_path: Path to config file
        temp_dir: Directory for temporary files
    """
    if not urls:
        logging.warning("No URLs to process")
        return
    
    # Set up temp directory
    import tempfile
    temp_dir = temp_dir or tempfile.mkdtemp(prefix="fbx_batch_")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Initialize processor
    processor = FBXProcessor(config_path)
    
    # Process each URL
    for url in urls:
        try:
            logging.info(f"Processing {url}")
            
            # Download and extract
            fbx_path, texture_paths = process_download_url(url, temp_dir)
            
            # Create output directory for this item
            item_name = os.path.splitext(os.path.basename(fbx_path))[0]
            item_output_dir = os.path.join(output_dir, item_name)
            os.makedirs(item_output_dir, exist_ok=True)
            
            # Process FBX
            success = processor.process_fbx(fbx_path, item_output_dir)
            
            if success:
                logging.info(f"Successfully processed {url}")
            else:
                logging.error(f"Failed to process {url}")
                
        except Exception as e:
            logging.error(f"Error processing {url}: {e}", exc_info=True)
            continue


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="FBX Batch Processor - Process FBX files with automatic texture assignment"
    )
    
    parser.add_argument(
        'input',
        help="Text file containing one URL per line"
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help="Output directory for processed files"
    )
    
    parser.add_argument(
        '-c', '--config',
        help="Path to config file"
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output"
    )
    
    parser.add_argument(
        '-t', '--temp-dir',
        help="Temporary directory for downloads"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Read URLs from file
    try:
        with open(args.input, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logging.error(f"Failed to read input file: {e}")
        sys.exit(1)
    
    # Process URLs
    process_urls(
        urls=urls,
        output_dir=args.output,
        config_path=args.config,
        temp_dir=args.temp_dir
    )


if __name__ == "__main__":
    main()
