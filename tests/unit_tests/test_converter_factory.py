"""
Unit tests for ConverterFactory.

Tests factory methods and converter creation logic.
"""

from unittest.mock import Mock, patch

from flow_preprocessor.preprocessing_logic.converter_factory import ConverterFactory


class TestConverterFactory:
    """Tests for ConverterFactory."""

    # ==================== Initialization ====================

    def test_init_default_parser(self):
        """Test initialization with default parser."""
        with patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser'):
            factory = ConverterFactory()
            assert factory._parser is not None

    def test_init_custom_parser(self):
        """Test initialization with custom parser."""
        custom_parser = Mock()
        factory = ConverterFactory(parser=custom_parser)
        assert factory._parser == custom_parser

    # ==================== ZIP Converter Creation ====================

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_zip_converter_local(self, mock_converter_class):
        """Test creation of converter for local ZIP file."""
        factory = ConverterFactory()

        _ = factory.create_zip_converter(
            zip_path="/path/to/data.zip",
            parse_xml=True,
            dataset=None
        )

        # Verify XmlConverter was called
        mock_converter_class.assert_called_once()
        call_kwargs = mock_converter_class.call_args.kwargs

        # Verify source_type
        assert call_kwargs['source_type'] == 'zip'
        assert call_kwargs['source_path'] == '/path/to/data.zip'

        # Verify gen_kwargs contains parse_xml
        assert call_kwargs['gen_kwargs']['parse_xml'] is True
        assert call_kwargs['gen_kwargs']['zip_path'] == '/path/to/data.zip'

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_zip_converter_url_http(self, mock_converter_class):
        """Test creation of converter for HTTP ZIP URL."""
        factory = ConverterFactory()

        _ = factory.create_zip_converter(
            zip_path="http://example.com/data.zip",
            parse_xml=False,
            dataset=None
        )

        call_kwargs = mock_converter_class.call_args.kwargs

        # HTTP URLs should use 'zip_url' source type
        assert call_kwargs['source_type'] == 'zip_url'
        assert call_kwargs['source_path'] == 'http://example.com/data.zip'

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_zip_converter_url_https(self, mock_converter_class):
        """Test creation of converter for HTTPS ZIP URL."""
        factory = ConverterFactory()

        _ = factory.create_zip_converter(
            zip_path="https://example.com/data.zip",
            parse_xml=True,
            dataset=None
        )

        call_kwargs = mock_converter_class.call_args.kwargs

        # HTTPS URLs should use 'zip_url' source type
        assert call_kwargs['source_type'] == 'zip_url'

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_zip_converter_with_dataset(self, mock_converter_class):
        """Test creation of converter with existing dataset."""
        factory = ConverterFactory()
        mock_dataset = Mock()

        _ = factory.create_zip_converter(
            zip_path="/path/to/data.zip",
            parse_xml=True,
            dataset=mock_dataset
        )

        call_kwargs = mock_converter_class.call_args.kwargs

        # When dataset is provided, should use 'huggingface' source type
        assert call_kwargs['source_type'] == 'huggingface'
        assert call_kwargs['gen_kwargs']['dataset'] == mock_dataset
        assert call_kwargs['gen_kwargs']['parse_xml'] is True

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_zip_converter_parse_xml_false(self, mock_converter_class):
        """Test that parse_xml parameter is correctly passed."""
        factory = ConverterFactory()

        _ = factory.create_zip_converter(
            zip_path="/path/to/data.zip",
            parse_xml=False
        )

        call_kwargs = mock_converter_class.call_args.kwargs
        assert call_kwargs['gen_kwargs']['parse_xml'] is False

    # ==================== HuggingFace Converter Creation ====================

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_huggingface_converter_from_repo(self, mock_converter_class):
        """Test creation of converter for HuggingFace repository."""
        factory = ConverterFactory()

        _ = factory.create_huggingface_converter(
            repo_id="organization/dataset",
            token="hf_xxx",
            parse_xml=True,
            dataset=None
        )

        call_kwargs = mock_converter_class.call_args.kwargs

        # Verify source_type
        assert call_kwargs['source_type'] == 'huggingface'
        assert call_kwargs['source_path'] == 'organization/dataset'

        # Verify gen_kwargs
        gen_kwargs = call_kwargs['gen_kwargs']
        assert gen_kwargs['dataset'] == 'organization/dataset'  # String repo ID
        assert gen_kwargs['token'] == 'hf_xxx'
        assert gen_kwargs['parse_xml'] is True

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_huggingface_converter_with_dataset(self, mock_converter_class):
        """Test creation of converter with existing dataset."""
        factory = ConverterFactory()
        mock_dataset = Mock()

        _ = factory.create_huggingface_converter(
            repo_id="organization/dataset",
            token="hf_xxx",
            parse_xml=True,
            dataset=mock_dataset
        )

        call_kwargs = mock_converter_class.call_args.kwargs
        gen_kwargs = call_kwargs['gen_kwargs']

        # When dataset is provided, should pass the dataset object
        assert gen_kwargs['dataset'] == mock_dataset
        assert gen_kwargs['token'] == 'hf_xxx'

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_huggingface_converter_no_token(self, mock_converter_class):
        """Test creation of converter without token."""
        factory = ConverterFactory()

        _ = factory.create_huggingface_converter(
            repo_id="organization/dataset",
            token=None,
            parse_xml=True,
            dataset=None
        )

        call_kwargs = mock_converter_class.call_args.kwargs
        gen_kwargs = call_kwargs['gen_kwargs']

        assert gen_kwargs['token'] is None

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_huggingface_converter_parse_xml_false(self, mock_converter_class):
        """Test that parse_xml parameter is correctly passed."""
        factory = ConverterFactory()

        _ = factory.create_huggingface_converter(
            repo_id="organization/dataset",
            token="hf_xxx",
            parse_xml=False
        )

        call_kwargs = mock_converter_class.call_args.kwargs
        assert call_kwargs['gen_kwargs']['parse_xml'] is False

    # ==================== Private Method: _create_dataset__ ====================

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_create_dataset_converter(self, mock_converter_class):
        """Test private method _create_dataset_converter."""
        factory = ConverterFactory()
        mock_dataset = Mock()

        _ = factory._create_dataset_converter(
            dataset=mock_dataset,
            parse_xml=True,
            source_path="/original/path"
        )

        call_kwargs = mock_converter_class.call_args.kwargs

        assert call_kwargs['source_type'] == 'huggingface'
        assert call_kwargs['source_path'] == '/original/path'
        assert call_kwargs['gen_kwargs']['dataset'] == mock_dataset
        assert call_kwargs['gen_kwargs']['parse_xml'] is True

    # ==================== Integration Tests ====================

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_multiple_converters_from_same_factory(self, mock_converter_class):
        """Test that same factory can create multiple converters."""
        factory = ConverterFactory()

        # Create multiple converters
        _ = factory.create_zip_converter("/path/to/data1.zip", True)
        _ = factory.create_zip_converter("/path/to/data2.zip", False)
        _ = factory.create_huggingface_converter("org/dataset", "token", True)

        # Verify all were created
        assert mock_converter_class.call_count == 3

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_factory_uses_same_parser(self, _, mock_parser_class):
        """Test that factory reuses the same parser instance."""
        mock_parser_instance = Mock()
        mock_parser_class.return_value = mock_parser_instance

        factory = ConverterFactory()

        # Create multiple converters
        factory.create_zip_converter("/path/to/data.zip", True)
        factory.create_huggingface_converter("org/dataset", "token", True)

        # Parser should be created only once
        mock_parser_class.assert_called_once()


class TestConverterFactoryEdgeCases:
    """Tests for edge cases and error handling."""

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_empty_zip_path(self, mock_converter_class):
        """Test handling of empty zip path."""
        factory = ConverterFactory()

        # Empty path should still work (validation is not factory's responsibility)
        _ = factory.create_zip_converter(
            zip_path="",
            parse_xml=True
        )

        call_kwargs = mock_converter_class.call_args.kwargs
        assert call_kwargs['source_path'] == ""

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_special_characters_in_path(self, mock_converter_class):
        """Test handling of special characters in paths."""
        factory = ConverterFactory()

        special_path = "/path/with spaces/and-dashes/file (1).zip"
        _ = factory.create_zip_converter(
            zip_path=special_path,
            parse_xml=True
        )

        call_kwargs = mock_converter_class.call_args.kwargs
        assert call_kwargs['source_path'] == special_path

    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlConverter')    @patch('flow_preprocessor.preprocessing_logic.converter_factory.XmlParser')
    def test_url_with_query_parameters(self, mock_converter_class):
        """Test handling of URL with query parameters."""
        factory = ConverterFactory()

        url = "https://example.com/data.zip?token=abc&version=1"
        _ = factory.create_zip_converter(
            zip_path=url,
            parse_xml=True
        )

        call_kwargs = mock_converter_class.call_args.kwargs
        assert call_kwargs['source_type'] == 'zip_url'
        assert call_kwargs['source_path'] == url

