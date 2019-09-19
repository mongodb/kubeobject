from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="kubeobject",
    version="0.1.2",

    author="Rodrigo Valin",
    author_email="licorna@gmail.com",
    description="Easily Manage Kubernetes Objects.",
    url='https://gitlab.com/licorna/kubeobject',

    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=find_packages(),
)
