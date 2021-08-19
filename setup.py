import subprocess
from pathlib import Path
from datetime import datetime
from setuptools import setup


def shell(*args):
    out = subprocess.check_output(args)
    return out.decode("ascii").strip()


def write_version(version_core, pre_release=True):
    if pre_release:
        time = shell("git", "log", "-1", "--format=%cd", "--date=iso")
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S %z")
        time = time.strftime("%Y%m%d%H%M%S")
        dirty = shell("git", "status", "--porcelain")
        version = f"{version_core}-dev{time}"
        if dirty:
            version += ".dirty"
    else:
        version = version_core

    with open(Path("zouqi", "version.py"), "w") as f:
        f.write('__version__ = "{}"\n'.format(version))

    return version


with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="zouqi",
    python_requires=">=3.6.0",
    version=write_version("1.0.10", True),
    description="zouqi is a CLI starter similar to python-fire. It is purely built on argparse.",
    author="enhuiz",
    author_email="niuzhe.nz@outlook.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["zouqi"],
    install_requires=["pyyaml"],
    url="https://github.com/enhuiz/zouqi",
)
