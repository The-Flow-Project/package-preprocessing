"""
Unit tests for the unified preprocessor.

Demonstrates improved testability with Dependency Injection.
Tests both async functionality and configuration-based initialization.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from flow_preprocessor.preprocessing_logic.config import (
    PreprocessorConfig,
    ProcessorState,
)
from flow_preprocessor.preprocessing_logic.converter_factory import ConverterFactory
from flow_preprocessor.preprocessing_logic.preprocess import (
    ZipPreprocessor,
    HuggingFacePreprocessor,
    PreprocessorBuilder,
)


# ===============================================================================
# Configuration Tests
# ===============================================================================

class TestPreprocessorConfig:
    """Tests for PreprocessorConfig."""

    def test_valid_config(self):
        """Test creation of valid configuration."""
        config = PreprocessorConfig(
            huggingface_repo_name="test/dataset",
            export_mode="line"
        )
        assert config.huggingface_repo_name == "test/dataset"
        assert config.export_mode == "line"

    def test_invalid_export_mode(self):
        """Test that invalid export mode raises error."""
        with pytest.raises(ValueError, match="Invalid export_mode"):
            PreprocessorConfig(
                huggingface_repo_name="test/dataset",
                export_mode="invalid_mode"
            )

    def test_invalid_line_dimensions(self):
        """Test that negative line dimensions raise error."""
        with pytest.raises(ValueError, match="positive integer"):
            PreprocessorConfig(
                huggingface_repo_name="test/dataset",
                min_width_line=-10
            )

    def test_invalid_split_ratio(self):
        """Test that invalid split ratio raises error."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            PreprocessorConfig(
                huggingface_repo_name="test/dataset",
                split_train_ratio=1.5
            )

    def test_requires_xml_parsing(self):
        """Test XML parsing requirement detection."""
        config_line = PreprocessorConfig(
            huggingface_repo_name="test/dataset",
            export_mode="line"
        )
        assert config_line.requires_xml_parsing is True

        config_raw = PreprocessorConfig(
            huggingface_repo_name="test/dataset",
            export_mode="raw_xml"
        )
        assert config_raw.requires_xml_parsing is False


# ===============================================================================
# Factory Tests
# ===============================================================================

class TestConverterFactory:
    """Tests for ConverterFactory."""

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')
    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_zip_converter(self, mock_parser_class, mock_converter_class):
        """Test creation of ZIP converter."""
        factory = ConverterFactory()

        _ = factory.create_zip_converter(
            zip_path="/path/to/data.zip",
            parse_xml=True
        )

        # Verify XmlConverter was called with correct arguments
        mock_converter_class.assert_called_once()
        call_kwargs = mock_converter_class.call_args.kwargs
        assert call_kwargs['source_type'] == 'zip'
        assert call_kwargs['source_path'] == '/path/to/data.zip'

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')
    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_zip_url_converter(self, mock_parser_class, mock_converter_class):
        """Test creation of ZIP URL converter."""
        factory = ConverterFactory()

        _ = factory.create_zip_converter(
            zip_path="https://example.com/data.zip",
            parse_xml=True
        )

        # Verify source_type is 'zip_url' for URLs
        call_kwargs = mock_converter_class.call_args.kwargs
        assert call_kwargs['source_type'] == 'zip_url'

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')
    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_huggingface_converter(self, mock_parser_class, mock_converter_class):
        """Test creation of HuggingFace converter."""
        factory = ConverterFactory()

        _ = factory.create_huggingface_converter(
            repo_id="test/dataset",
            token="hf_xxx",
            parse_xml=True
        )

        # Verify source_type and gen_func
        call_kwargs = mock_converter_class.call_args.kwargs
        assert call_kwargs['source_type'] == 'huggingface'


# ===============================================================================
# Preprocessor Tests
# ===============================================================================

class TestZipPreprocessor:
    """Tests for ZipPreprocessor."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PreprocessorConfig(
            huggingface_repo_name="test/dataset",
            export_mode="line"
        )

    @pytest.fixture
    def mock_factory(self):
        """Create mock converter factory."""
        factory = Mock(spec=ConverterFactory)
        mock_converter = Mock()
        # convert_and_upload is called via asyncio.to_thread, so it should be sync
        mock_converter.convert_and_upload = Mock(return_value="https://test.url")
        mock_converter.convert = Mock(return_value=Mock())
        factory.create_zip_converter.return_value = mock_converter
        return factory

    def test_initialization(self, config, mock_factory):
        """Test preprocessor initialization."""
        preprocessor = ZipPreprocessor(
            input_path="test.zip",
            config=config,
            converter_factory=mock_factory
        )

        assert preprocessor.state == ProcessorState.INITIALIZED
        assert preprocessor.config == config

    @pytest.mark.asyncio
    async def test_preprocess_without_segmentation(self, config, mock_factory):
        """Test preprocessing without segmentation."""
        preprocessor = ZipPreprocessor(
            input_path="test.zip",
            config=config,
            converter_factory=mock_factory
        )

        repo_url = await preprocessor.preprocess()

        # Verify state transitions
        assert preprocessor.state == ProcessorState.COMPLETED

        # Verify converter was called
        mock_converter = mock_factory.create_zip_converter.return_value
        mock_converter.convert_and_upload.assert_called_once()

        # Verify return value
        assert repo_url == "https://test.url"

    @pytest.mark.asyncio
    async def test_preprocess_with_segmentation(self, mock_factory):
        """Test preprocessing with segmentation."""
        from flow_segmenter import SegmenterConfig

        config = PreprocessorConfig(
            huggingface_repo_name="test/dataset",
            export_mode="line",
            segment=True,
            segmenter_config=SegmenterConfig(model_names="yolov8n")
        )

        # Mock segmenter
        with patch('flow_preprocessor.preprocessing_logic.preprocess.SegmenterYOLO') as mock_segmenter_class:
            mock_segmenter = Mock()
            mock_segmenter.segment_dataset = Mock(return_value=Mock())
            mock_segmenter_class.return_value = mock_segmenter

            preprocessor = ZipPreprocessor(
                input_path="test.zip",
                config=config,
                converter_factory=mock_factory
            )

            _ = await preprocessor.preprocess()

            # Verify segmentation was called
            mock_segmenter.segment_dataset.assert_called_once()

            # Verify state
            assert preprocessor.state == ProcessorState.COMPLETED

    @pytest.mark.asyncio
    async def test_preprocess_failure(self, config, mock_factory):
        """Test preprocessing failure handling."""
        # Make convert_and_upload raise an exception
        mock_converter = mock_factory.create_zip_converter.return_value
        mock_converter.convert_and_upload.side_effect = Exception("Test error")

        preprocessor = ZipPreprocessor(
            input_path="test.zip",
            config=config,
            converter_factory=mock_factory
        )

        with pytest.raises(Exception, match="Test error"):
            await preprocessor.preprocess()

        # Verify state is FAILED
        assert preprocessor.state == ProcessorState.FAILED


class TestHuggingFacePreprocessor:
    """Tests for HuggingFacePreprocessor."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PreprocessorConfig(
            huggingface_repo_name="test/output-dataset",
            huggingface_token="hf_xxx",
            export_mode="region"
        )

    @pytest.fixture
    def mock_factory(self):
        """Create mock converter factory."""
        factory = Mock(spec=ConverterFactory)
        mock_converter = Mock()
        # convert_and_upload is called via asyncio.to_thread, so it should be sync
        mock_converter.convert_and_upload = Mock(return_value="https://test.url")
        factory.create_huggingface_converter.return_value = mock_converter
        return factory

    def test_initialization(self, config, mock_factory):
        """Test preprocessor initialization."""
        preprocessor = HuggingFacePreprocessor(
            input_path="test/input-dataset",
            config=config,
            converter_factory=mock_factory
        )

        assert preprocessor.state == ProcessorState.INITIALIZED

    @pytest.mark.asyncio
    async def test_preprocess(self, config, mock_factory):
        """Test preprocessing."""
        preprocessor = HuggingFacePreprocessor(
            input_path="test/input-dataset",
            config=config,
            converter_factory=mock_factory
        )

        _ = await preprocessor.preprocess()

        # Verify factory was called with correct arguments
        mock_factory.create_huggingface_converter.assert_called()

        # Verify state
        assert preprocessor.state == ProcessorState.COMPLETED


# ===============================================================================
# Builder Tests
# ===============================================================================

class TestPreprocessorBuilder:
    """Tests for PreprocessorBuilder."""

    def test_basic_builder(self):
        """Test basic builder usage."""
        preprocessor = (
            PreprocessorBuilder("test/dataset")
            .build_for_zip("test.zip")
        )

        assert isinstance(preprocessor, ZipPreprocessor)
        assert preprocessor.config.huggingface_repo_name == "test/dataset"

    def test_builder_with_options(self):
        """Test builder with various options."""
        from flow_segmenter import SegmenterConfig

        _ = SegmenterConfig(model_names="yolov8n")

        preprocessor = (
            PreprocessorBuilder("test/dataset")
            .with_token("hf_xxx")
            .with_export_mode("line")
            .with_crop()
            .with_split(ratio=0.8, seed=42)
            .with_line_filtering(min_width=50, min_height=20)
            .private()
            .build_for_zip("test.zip")
        )

        config = preprocessor.config
        assert config.huggingface_token == "hf_xxx"
        assert config.export_mode == "line"
        assert config.crop is True
        assert config.split_train_ratio == 0.8
        assert config.min_width_line == 50
        assert config.min_height_line == 20
        assert config.huggingface_repo_private is True

    def test_builder_for_huggingface(self):
        """Test builder for HuggingFace preprocessor."""
        preprocessor = (
            PreprocessorBuilder("test/output")
            .build_for_huggingface("test/input")
        )

        assert isinstance(preprocessor, HuggingFacePreprocessor)


# ===============================================================================
# Integration Tests
# ===============================================================================

class TestIntegration:
    """Integration tests for the complete workflow."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_workflow_zip(self):
        """Test full workflow with ZIP file (mocked)."""
        # This would be a real integration test with actual files
        # For now, we use mocks

        config = PreprocessorConfig(
            huggingface_repo_name="test/dataset",
            export_mode="line",
            crop=True,
            batch_size=32
        )

        # Mock the factory
        mock_factory = Mock(spec=ConverterFactory)
        mock_converter = Mock()
        # convert_and_upload is called via asyncio.to_thread, so it should be sync
        mock_converter.convert_and_upload = Mock(return_value="https://test.url")
        mock_factory.create_zip_converter.return_value = mock_converter

        preprocessor = ZipPreprocessor(
            input_path="test.zip",
            config=config,
            converter_factory=mock_factory
        )

        # Run full workflow
        repo_url = await preprocessor.preprocess()

        # Verify everything worked
        assert repo_url == "https://test.url"
        assert preprocessor.state == ProcessorState.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

