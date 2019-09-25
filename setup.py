import os
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

commit_tag = os.getenv("CI_COMMIT_TAG", "latest")
stage = os.getenv("CI_JOB_STAGE", "local")

if stage == "publish" and commit_tag == "latest":
    raise ValueError("Did not get a commit tag during publishing.")

if stage == "publish":
    commit_tag = commit_tag.split("-")[1]

setup(
    name="kubeobject",
    version=commit_tag,

    author="Rodrigo Valin",
    author_email="licorna@gmail.com",
    description="Easily Manage Kubernetes Objects.",
    url='https://gitlab.com/licorna/kubeobject',

    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=find_packages(),
)
