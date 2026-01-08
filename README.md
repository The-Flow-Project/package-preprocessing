# Flow Preprocessing Package

Python package for preprocessing PageXML datasets for OCR/HTR tasks with HuggingFace integration.

## Features

- ✅ Process ZIP files (local or remote URLs)
- ✅ Process HuggingFace datasets
- ✅ Optional image segmentation with YOLO (GPU-accelerated)
- ✅ Multiple export modes (line, region, text, window, raw_xml)
- ✅ Train/test splitting
- ✅ Line filtering by dimensions
- ✅ Direct upload to HuggingFace Hub
- ✅ FastAPI-compatible (non-blocking async with `asyncio.to_thread()`)
- ✅ GPU support with optimal performance

## Quick Start

### Option 1: Using PreprocessorConfig (Explicit)

```python
from flow_preprocessor import ZipPreprocessor
from flow_preprocessor.preprocessing_logic.config import PreprocessorConfig

# Create configuration
config = PreprocessorConfig(
    huggingface_target_repo_name="username/dataset-name",
    huggingface_token="your_hf_token",
    export_mode="line",
    min_width_line=40,
)

# Create and run preprocessor (async)
preprocessor = ZipPreprocessor("path/to/data.zip", config)
repo_url = await preprocessor.preprocess()
print(f"Dataset available at: {repo_url}")
```

### Option 2: Using Builder Pattern (Fluent API)

```python
from flow_preprocessor import PreprocessorBuilder

# Build and run preprocessor with fluent API
preprocessor = (PreprocessorBuilder("username/dataset-name")
    .with_token("your_hf_token")
    .with_export_mode("line")
    .with_line_filtering(min_width=40)
    .build_for_zip("path/to/data.zip"))

repo_url = await preprocessor.preprocess()
print(f"Dataset available at: {repo_url}")
```

## Installation

### Install with pip:

```bash
# Clone the repository
git clone <repository-url>
cd package-preprocessing

# Install the package
pip install .
```

### Install with uv:

```bash
# Clone and navigate to directory
cd package-preprocessing

# Install with uv
uv pip install .
```

