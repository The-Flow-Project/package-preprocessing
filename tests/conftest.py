"""
Pytest configuration and shared fixtures.

This file contains fixtures that are available to all tests.
"""

import pytest
from unittest.mock import Mock
from pathlib import Path

import datasets
from pagexml_hf import XmlConverter

from flow_preprocessor.preprocessing_logic.config import PreprocessorConfig
from flow_preprocessor.preprocessing_logic.converter_factory import ConverterFactory


# ===============================================================================
# Directory Fixtures
# ===============================================================================

@pytest.fixture(scope="session")
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def test_images_dir(test_data_dir):
    """Get test images' directory."""
    return test_data_dir / "images"


# ===============================================================================
# Configuration Fixtures
# ===============================================================================

@pytest.fixture
def basic_config():
    """Create a basic preprocessor configuration."""
    return PreprocessorConfig(
        huggingface_target_repo_name="test/dataset",
        export_mode="line",
        batch_size=32
    )


@pytest.fixture
def config_with_segmentation():
    """Create configuration with segmentation enabled."""
    from flow_segmenter import SegmenterConfig

    return PreprocessorConfig(
        huggingface_target_repo_name="test/dataset",
        export_mode="line",
        segment=True,
        segmenter_config=SegmenterConfig(model_names="yolov8n")
    )


@pytest.fixture
def config_with_splitting():
    """Create configuration with train/test split."""
    return PreprocessorConfig(
        huggingface_target_repo_name="test/dataset",
        export_mode="line",
        split_train_ratio=0.8,
        split_seed=42,
        split_shuffle=True
    )


@pytest.fixture
def config_with_filtering():
    """Create configuration with line filtering."""
    return PreprocessorConfig(
        huggingface_target_repo_name="test/dataset",
        export_mode="line",
        min_width_line=50,
        min_height_line=20,
        allow_empty_lines=False
    )


# ===============================================================================
# Mock Fixtures
# ===============================================================================

@pytest.fixture
def mock_xml_parser():
    """Create a mock XmlParser."""
    parser = Mock()
    parser.parse_zip = Mock()
    parser.parse_dataset = Mock()
    return parser


@pytest.fixture
def mock_xml_converter():
    """Create a mock XmlConverter."""
    converter = Mock(spec=XmlConverter)
    converter.convert = Mock(return_value=Mock(spec=datasets.Dataset))
    converter.convert_and_upload = Mock(return_value="https://huggingface.co/test/dataset")
    return converter


@pytest.fixture
def mock_converter_factory(mock_xml_converter):
    """Create a mock ConverterFactory."""
    factory = Mock(spec=ConverterFactory)
    factory.create_zip_converter = Mock(return_value=mock_xml_converter)
    factory.create_huggingface_converter = Mock(return_value=mock_xml_converter)
    return factory


@pytest.fixture
def mock_segmenter():
    """Create a mock SegmenterYOLO."""
    segmenter = Mock()
    segmenter.segment_dataset = Mock(return_value=Mock(spec=datasets.Dataset))
    return segmenter


@pytest.fixture
def mock_dataset():
    """Create a mock datasets.Dataset."""
    dataset = Mock(spec=datasets.Dataset)
    dataset.__len__ = Mock(return_value=100)
    return dataset


# ===============================================================================
# Pytest Configuration
# ===============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_network: marks tests that require network access"
    )
    config.addinivalue_line(
        "markers", "requires_files: marks tests that require actual test files"
    )

