from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="zouqi",
    python_requires=">=3.6.0",
    version="1.0.9",
    description="zouqi is a CLI starter similar to python-fire. It is purely built on argparse.",
    author="enhuiz",
    author_email="niuzhe.nz@outlook.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["zouqi"],
    install_requires=["pyyaml"],
    url="https://github.com/enhuiz/zouqi",
)
