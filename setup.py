"""
Bhisma Framework Setup
======================
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="bhisma",
    version="3.0.0",
    author="Bhisma Team",
    description="AI-Powered Autonomous Multi-Protocol Offensive WiFi Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bhisma-team/bhisma",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "bhisma.dashboard": ["templates/*.html", "static/css/*", "static/js/*", "static/img/*"],
    },
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bhisma=bhisma.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
)
