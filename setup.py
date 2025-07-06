from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fbx-batch-processor",
    version="0.1.0",
    author="Mateusz Wojt",
    author_email="mateusz.wojt@outlook.com",
    description="A tool for batch processing FBX files with Blender",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mateuszwojt/FBXBatchProcessing",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.31.0",
        "tqdm>=4.66.0",
    ],
    entry_points={
        'console_scripts': [
            'fbx-batch-processor=fbx_batch_processor.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'fbx_batch_processor': ['*.json'],
    },
)
