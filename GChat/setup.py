"""
Setup configuration for Google Chat Keycloak Integration
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="googlechat-keycloak",
    version="1.0.0",
    author="Divakar",
    author_email="divakar30@drapps.dev",
    description="Google Chat API integration with Keycloak Workload Identity Federation",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/googlechat-keycloak",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "googlechat-keycloak=googlechat_keycloak.cli:main",
            "gchat-setup=googlechat_keycloak.setup:setup_main",
        ],
    },
    include_package_data=True,
    package_data={
        "googlechat_keycloak": [
            "templates/*.json",
            "templates/*.yaml",
        ],
    },
    zip_safe=False,
    keywords="google chat keycloak authentication workload identity federation",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/googlechat-keycloak/issues",
        "Source": "https://github.com/yourusername/googlechat-keycloak",
        "Documentation": "https://github.com/yourusername/googlechat-keycloak/blob/main/README.md",
    },
)