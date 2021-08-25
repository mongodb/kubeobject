import os
import re

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()


packages = []
with open("requirements.txt") as requirements:
    packages = [r.strip() for r in requirements.readlines()]

release_version = os.environ['RELEASE_VERSION'].strip()
if not re.match(r'^\d{1,2}\.\d{1,2}\.\d{1,2}$', release_version):
    raise ValueError("TAG should be x.y.z")

setup(
    name="kubeobject",
    version=release_version,

    author="Rodrigo Valin",
    author_email="rodrigo.valin@mongodb.com",
    description="Easily Manage Kubernetes Objects.",
    url='https://github.com/mongodb/kubeobject',

    long_description=long_description,
    long_description_content_type="text/markdown",

    install_requires=packages,

    packages=find_packages(),
)
