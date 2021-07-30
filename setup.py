import os
import re

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()


def get_version():
    commit_tag = os.getenv("CI_COMMIT_TAG", "latest")
    stage = os.getenv("CI_JOB_STAGE", "local")

    if stage == "publish":
        if commit_tag == "latest":
            raise ValueError("Did not get a commit tag during publishing.")

        if not re.match(r"^release-\d+\.\d+\.\d+$", commit_tag):
            raise ValueError("Wrong tag format.")

        commit_tag = commit_tag.split("-")[1]

    return commit_tag


setup(
    name="kubeobject",
    version=get_version(),

    author="Rodrigo Valin",
    author_email="rodrigo.valin@mongodb.com",
    description="Easily Manage Kubernetes Objects.",
    url='https://github.com/10gen/kubeobject',

    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=find_packages(),
)
