"""
Unit tests for PreprocessorConfig.

Tests configuration validation, defaults, and properties.
"""

import pytest
from flow_preprocessor.preprocessing_logic.config import (
    PreprocessorConfig,
    ExportMode,
    DataSourceConfig,
    EXPORT_MODES_REQUIRING_XML_PARSING
)


class TestPreprocessorConfig:
    """Tests for PreprocessorConfig dataclass."""

    def test_minimal_config(self):
        """Test creation with only required parameters."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset"
        )

        assert config.huggingface_target_repo_name == "test/dataset"
        assert config.export_mode == "line"  # Default
        assert config.batch_size == 32  # Default
        assert config.crop is False  # Default

    def test_all_parameters(self):
        """Test creation with all parameters."""
        from flow_segmenter import SegmenterConfig

        segmenter_config = SegmenterConfig(model_names="yolov8n")

        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            huggingface_token="hf_xxx",
            huggingface_target_repo_private=True,
            append=True,
            export_mode="region",
            crop=True,
            allow_empty_lines=True,
            batch_size=64,
            min_width_line=50,
            min_height_line=20,
            split_train_ratio=0.8,
            split_seed=123,
            split_shuffle=False,
            segment=True,
            segmenter_config=segmenter_config
        )

        assert config.huggingface_target_repo_name == "test/dataset"
        assert config.huggingface_token == "hf_xxx"
        assert config.huggingface_target_repo_private is True
        assert config.append is True
        assert config.export_mode == "region"
        assert config.crop is True
        assert config.allow_empty_lines is True
        assert config.batch_size == 64
        assert config.min_width_line == 50
        assert config.min_height_line == 20
        assert config.split_train_ratio == 0.8
        assert config.split_seed == 123
        assert config.split_shuffle is False
        assert config.segment is True
        assert config.segmenter_config == segmenter_config

    # ==================== Export Mode Validation ====================

    def test_valid_export_modes(self):
        """Test all valid export modes."""
        for mode in ExportMode:
            config = PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                export_mode=mode.value
            )
            assert config.export_mode == mode.value

    def test_invalid_export_mode(self):
        """Test that invalid export mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid export_mode"):
            PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                export_mode="invalid_mode"
            )

    def test_export_mode_typo(self):
        """Test that typo in export mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid export_mode: 'lien'"):
            PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                export_mode="lien"  # Typo
            )

    # ==================== Line Dimensions Validation ====================

    def test_valid_line_dimensions(self):
        """Test valid line dimensions."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            min_width_line=100,
            min_height_line=50
        )
        assert config.min_width_line == 100
        assert config.min_height_line == 50

    def test_negative_min_width(self):
        """Test that negative min_width raises ValueError."""
        with pytest.raises(ValueError, match="positive integer"):
            PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                min_width_line=-10
            )

    def test_zero_min_width(self):
        """Test that zero min_width raises ValueError."""
        with pytest.raises(ValueError, match="positive integer"):
            PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                min_width_line=0
            )

    def test_negative_min_height(self):
        """Test that negative min_height raises ValueError."""
        with pytest.raises(ValueError, match="positive integer"):
            PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                min_height_line=-5
            )

    def test_none_line_dimensions(self):
        """Test that None line dimensions are valid."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            min_width_line=None,
            min_height_line=None
        )
        assert config.min_width_line is None
        assert config.min_height_line is None

    # ==================== Split Ratio Validation ====================

    def test_valid_split_ratios(self):
        """Test valid split ratios."""
        valid_ratios = [0.1, 0.5, 0.8, 0.9, 1.0]
        for ratio in valid_ratios:
            config = PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                split_train_ratio=ratio
            )
            assert config.split_train_ratio == ratio

    def test_split_ratio_too_high(self):
        """Test that split ratio > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                split_train_ratio=1.5
            )

    def test_split_ratio_zero(self):
        """Test that split ratio = 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                split_train_ratio=0.0
            )

    def test_split_ratio_negative(self):
        """Test that negative split ratio raises ValueError."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                split_train_ratio=-0.5
            )

    def test_none_split_ratio(self):
        """Test that None split ratio is valid (no split)."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            split_train_ratio=None
        )
        assert config.split_train_ratio is None

    # ==================== Segmentation Validation ====================

    def test_segmentation_without_config(self):
        """Test that segment=True without config raises ValueError."""
        with pytest.raises(ValueError, match="segmenter_config must be provided"):
            PreprocessorConfig(
                huggingface_target_repo_name="test/dataset",
                segment=True,
                segmenter_config=None
            )

    def test_segmentation_with_config(self):
        """Test valid segmentation configuration."""
        from flow_segmenter import SegmenterConfig

        segmenter_config = SegmenterConfig(model_names="yolov8n")

        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            segment=True,
            segmenter_config=segmenter_config
        )

        assert config.segment is True
        assert config.segmenter_config == segmenter_config

    def test_no_segmentation(self):
        """Test segment=False with no config is valid."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            segment=False,
            segmenter_config=None
        )

        assert config.segment is False
        assert config.segmenter_config is None

    # ==================== XML Parsing Property ====================

    def test_requires_xml_parsing_line_mode(self):
        """Test that line mode requires XML parsing."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            export_mode="line"
        )
        assert config.requires_xml_parsing is True

    def test_requires_xml_parsing_region_mode(self):
        """Test that region mode requires XML parsing."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            export_mode="region"
        )
        assert config.requires_xml_parsing is True

    def test_requires_xml_parsing_text_mode(self):
        """Test that text mode requires XML parsing."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            export_mode="text"
        )
        assert config.requires_xml_parsing is True

    def test_requires_xml_parsing_window_mode(self):
        """Test that window mode requires XML parsing."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            export_mode="window"
        )
        assert config.requires_xml_parsing is True

    def test_requires_xml_parsing_raw_xml_mode(self):
        """Test that raw_xml mode does NOT require XML parsing."""
        config = PreprocessorConfig(
            huggingface_target_repo_name="test/dataset",
            export_mode="raw_xml"
        )
        assert config.requires_xml_parsing is False

    def test_xml_parsing_constant_completeness(self):
        """Test that EXPORT_MODES_REQUIRING_XML_PARSING is correct."""
        modes_requiring_parsing = {
            ExportMode.LINE,
            ExportMode.REGION,
            ExportMode.TEXT,
            ExportMode.WINDOW
        }
        assert EXPORT_MODES_REQUIRING_XML_PARSING == modes_requiring_parsing


class TestDataSourceConfig:
    """Tests for DataSourceConfig."""

    def test_auto_detect_zip(self):
        """Test auto-detection of ZIP file."""
        config = DataSourceConfig(input_path="data/file.zip")
        assert config.source_type == "zip"
        assert config.is_zip is True
        assert config.is_remote is False

    def test_auto_detect_zip_url(self):
        """Test auto-detection of ZIP URL (http)."""
        config = DataSourceConfig(input_path="http://example.com/data.zip")
        assert config.source_type == "zip_url"
        assert config.is_zip is True
        assert config.is_remote is True

    def test_auto_detect_zip_url_https(self):
        """Test auto-detection of ZIP URL (https)."""
        config = DataSourceConfig(input_path="https://example.com/data.zip")
        assert config.source_type == "zip_url"
        assert config.is_zip is True
        assert config.is_remote is True

    def test_auto_detect_huggingface(self):
        """Test auto-detection of HuggingFace dataset."""
        config = DataSourceConfig(input_path="organization/dataset")
        assert config.source_type == "huggingface"
        assert config.is_zip is False
        assert config.is_remote is True

    def test_manual_source_type(self):
        """Test manually specified source type."""
        config = DataSourceConfig(
            input_path="data/file",
            source_type="custom"
        )
        assert config.source_type == "custom"


class TestExportModeEnum:
    """Tests for ExportMode enum."""

    def test_all_modes_defined(self):
        """Test that all expected modes are defined."""
        expected_modes = {"raw_xml", "text", "region", "line", "window"}
        actual_modes = {mode.value for mode in ExportMode}
        assert actual_modes == expected_modes

    def test_enum_from_string(self):
        """Test creating enum from string value."""
        mode = ExportMode("line")
        assert mode == ExportMode.LINE

    def test_enum_invalid_value(self):
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            ExportMode("invalid")

