# AGENTS.md

Python 3.12+ application to preprocess PageXML/image export from transcription
software (Transkribus, eScriptorium).
The data source can be either a ZIP file containing the PageXML and images
or a HuggingFace Hub repository containing the same data.
For the segmentation part of the application, it uses the flow_segmenter
package (https://github.com/The-Flow-Project/package-segmenter) which is based
on htrflow for Yolo segmentation and Kraken for baseline and linemask detection.
pagexml-hf (https://github.com/The-Flow-Project/pagexml-hf) is the main
package used by the application to process the data and upload it to HuggingFace
Hub in the demanded mode. Those modes can be:

- "raw_xml" for export storage
- "line" for TrOCR training and inference
- "region" for region-based preprocessing

There are few more, which are not used by this package.
It uses uv as package manager and includes a Makefile for easy installation and
development setup.

## Commands

- Makefile @Makefile

## Conventions

- Use the latest flow_segmenter for segmentation tasks.
- Use pagexml-hf for processing and uploading data to HuggingFace Hub.
- Use Pydantic v2 for input and output validation
- Use uv for package management
- Use lxml for XML processing
- Use snake_case for function and variable names
- Use PascalCase for class names
- Use pathlib for file path handling, not os.path

## Rules

- Follow standard Python packaging conventions for structure and distribution
- Use loguru for logging and create an environment variable in .env to
  define the log level (LOGLEVEL) and persistance of logs (LOGTOFILE)
- Ensure all functions and classes are well-documented with docstrings
- Include type hints for all functions and methods
- Do not add new dependencies without asking first
- Do not change dependency versions without asking first
- Do not change the structure of the package without asking first
- Ask when changing pyproject.toml
- Create new git branches for new features or bug fixes and follow a consistent
commit message format

## Testing

- Use pytest for testing and include tests for all major functionalities
- Ensure tests cover edge cases and potential failure points
- Use mocking to isolate tests and avoid dependencies on external services or resources
- Do linting and formating checks as part of the testing process to maintain code quality

## Documentation

- Use Sphinx for documentation and include comprehensive documentation for all functions, classes, and modules
- Include examples and usage guides in the documentation
- Keep documentation up to date with code changes and ensure it is clear and easy to understand
- Do not yet push the documentation, but create it locally and ask for review before pushing to the repository