from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="flow_preprocessor",
    version="0.1.1",
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    description="A package to preprocess PageXMl files for a TrOCR training.",
    author="Dana Meyer",
    author_email="dameyer@techfak.uni-bielefeld.de",
    url="https://github.com/The-Flow-Project/package-preprocessing",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
