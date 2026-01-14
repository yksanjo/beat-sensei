"""Setup script for Beat-Sensei."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="beat-sensei",
    version="1.0.0",
    author="Beat-Sensei",
    description="Your AI Sample Master - A terminal chatbot for beat production",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yksanjo/beat-sensei",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "audio": [
            "librosa>=0.10.0",
            "soundfile>=0.12.0",
            "pygame>=2.5.0",
        ],
        "ai": [
            "replicate>=0.15.0",
            "openai>=1.0.0",
        ],
        "full": [
            "librosa>=0.10.0",
            "soundfile>=0.12.0",
            "pygame>=2.5.0",
            "replicate>=0.15.0",
            "openai>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "beat-sensei=beat_sensei.cli:run",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    keywords="audio, samples, music production, hip-hop, ai, chatbot, cli",
)
