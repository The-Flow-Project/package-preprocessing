flow_preprocessing
==================

Python package for preprocessing document images and PageXML files for HTR tasks,
developed for the `Flow Project <https://flow-project.net>`_.

.. toctree::
   :maxdepth: 3
   :caption: Contents:

API Reference
=============
Main Package
------------
.. autosummary::
   :toctree: _autosummary
   :recursive:

   flow_preprocessing

Core Modules
------------
Preprocessor
~~~~~~~~~~~~
.. autosummary::
   :toctree: _autosummary

   flow_preprocessing.preprocessing_logic.preprocess.ZipPreprocessor
   flow_preprocessing.preprocessing_logic.preprocess.HuggingFacePreprocessor
   flow_preprocessing.preprocessing_logic.preprocess.PreprocessorBuilder

Configuration
~~~~~~~~~~~~~
.. autosummary::
   :toctree: _autosummary

   flow_preprocessing.preprocessing_logic.config.PreprocessorConfig
   flow_preprocessing.preprocessing_logic.config.PreprocessorBaseConfig
   flow_preprocessing.preprocessing_logic.config.ExportMode

Utilities
~~~~~~~~~
.. autosummary::
   :toctree: _autosummary

   flow_preprocessing.utils.url_validator.validate_url

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
