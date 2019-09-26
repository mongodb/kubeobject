import os
import pytest

from kubernetes import config
from kubeobject import ConfigMap, Secret, Namespace, generate_random_name


# TODO: Make sure these tests can run on gitlab-ci
# pytestmark will be evaluated at a module level. In this case we'll skip if the environemnt variable is
# not defined. A very easy solution would be to install kind and do:
#
#   kind create cluster
#   export KUBECONFIG="$(kind get kubeconfig-path --name="kind")"
#
pytestmark = pytest.mark.skipif(os.getenv("KUBECONFIG") is None, reason="No defined Kubernetes Environment")


@pytest.fixture(scope="module")
def kube_config():
    config.load_kube_config()


@pytest.fixture(scope="module")
def config_map(kube_config):
    cm = ConfigMap("my-config-map", "default").create()

    yield cm

    cm.delete()


def test_configmap_is_read(config_map):
    config_map.data({"some-key": "some-value"})

    assert "some-key" in config_map.data()

    config_map.update()


def test_configmap_has_contents():
    cm = ConfigMap("my-config-map", "default").load()

    assert "some-key" in cm.data()


def test_configmap_raises_if_invalid_data(config_map):
    with pytest.raises(ValueError):
        config_map.data("some")


@pytest.fixture(scope="module")
def secret():
    secret = Secret("my-secret", "default").create()

    yield secret

    secret.delete()


def test_secret_is_readable(secret):
    assert secret.data() == dict()


def test_secret_can_write_data_correctly(secret):
    secret.data({"some-key": "some-value"})
    secret.update()

    s1 = Secret("my-secret", "default").load()
    assert s1.data() == {"some-key": "some-value"}


@pytest.fixture(scope="module")
def namespace(kube_config):

    ns = Namespace(generate_random_name()).create()

    yield ns

    ns.delete()


def test_namespace(namespace):
    assert len(namespace.name) > 10


def test_load_namespace(namespace):
    n0 = Namespace(namespace.name).load()

    assert n0.name == namespace.name
