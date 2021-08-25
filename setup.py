from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()


packages = []
with open("requirements.txt") as requirements:
    packages = [r.strip() for r in requirements.readlines()]

setup(
    name="kubeobject",
    version="0.2.0",

    author="Rodrigo Valin",
    author_email="rodrigo.valin@mongodb.com",
    description="Easily Manage Kubernetes Objects.",
    url='https://github.com/mongodb/kubeobject',

    long_description=long_description,
    long_description_content_type="text/markdown",

    install_requires=packages,

    packages=find_packages(),
)
