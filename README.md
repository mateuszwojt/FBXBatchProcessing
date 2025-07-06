# FBX Batch Processing Tool

This tool allows you to process FBX files in batch from zip archives downloaded via URLs listed in a text file.

## Features

1. **Batch Processing**: Process multiple FBX files from zip archives
2. **Texture Assignment**: Automatically assigns textures based on naming patterns
3. **Transform Normalization**: Resets transforms without moving geometry
4. **Flexible Configuration**: Customize texture patterns via JSON config

## How to Use?

### Prerequisites

- Blender 3.0+
- Python 3.7+

### Installation

1. Clone the repository:

```bash
git clone https://github.com/mateuszwojt/FBXBatchProcessing.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

### CLI Usage

```bash
# Process URLs from a file
python fbx_batch_processor.py urls.txt --output ./output

# With custom config
python fbx_batch_processor.py urls.txt --output ./output --config config.json
```

### Configuration

The tool supports configuration via a JSON file. See `config.example.json` for an example.
