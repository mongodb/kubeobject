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


@pytest.fixture()
def config_map(kube_config):
    cm = ConfigMap("my-config-map", "default").create()

    yield cm

    cm.delete()


def test_configmap_is_added_and_emptied(config_map):
    config_map.data({"some-key": "some-value"})

    config_map.update()
    config_map.reload()

    assert config_map.data()["some-key"] == "some-value"
    assert len(config_map.data()) == 1

    config_map.data({
        "some-key1": "some-value1",
        "some-key2": "some-value2"
    })

    config_map.update()
    config_map.reload()

    assert config_map.data() == {
        "some-key": "some-value",
        "some-key1": "some-value1",
        "some-key2": "some-value2",
    }

    config_map.data({"some-key": None})
    config_map.update()
    config_map.reload()

    assert config_map.data() == {
        "some-key1": "some-value1",
        "some-key2": "some-value2",
    }

    config_map.data({"some-key1": None})
    config_map.update()
    config_map.reload()

    assert config_map.data() == {
        "some-key2": "some-value2",
    }

    config_map.data({"some-key2": None})
    config_map.update()
    config_map.reload()

    assert config_map.data() == {}

    config_map.data({"some-key": "some-value"})

    config_map.update()
    config_map.reload()

    assert config_map.data()["some-key"] == "some-value"
    assert len(config_map.data()) == 1

    config_map.data({
        "some-key1": "some-value1",
        "some-key2": "some-value2"
    })

    config_map.update()
    config_map.reload()

    assert config_map.data() == {
        "some-key": "some-value",
        "some-key1": "some-value1",
        "some-key2": "some-value2",
    }

    config_map.data({"some-key": None})
    config_map.update()
    config_map.reload()

    assert config_map.data() == {
        "some-key1": "some-value1",
        "some-key2": "some-value2",
    }

    config_map.data({"some-key1": None})
    config_map.update()
    config_map.reload()

    assert config_map.data() == {
        "some-key2": "some-value2",
    }


def test_configmap_is_cleared(config_map):
    config_map.reload()

    assert config_map.data() == {}

    config_map.data({"some-key": "some-value"})
    config_map.update()
    config_map.reload()

    assert config_map.data() == {"some-key": "some-value"}

    config_map.data({"some-key": None})
    config_map.update()
    config_map.reload()

    assert len(config_map.data()) == 0


def test_configmap_raises_if_invalid_data(config_map):
    with pytest.raises(ValueError):
        config_map.data("some")


@pytest.fixture()
def secret(kube_config):
    secret = Secret("my-secret", "default").create()

    yield secret

    secret.delete()


def test_secret_is_readable(secret):
    assert secret.data() == dict()


def test_secret_can_write_and_read_data(secret):
    with pytest.raises(KeyError):
        assert secret.data()["some"]

    secret.data({"key0": "value0"})
    secret.update()
    secret.reload()

    assert secret.data()["key0"] == "value0"

    secret.data({"another-key": "another-value"})
    secret.update()
    secret.reload()

    assert secret.data() == {
        "key0": "value0",
        "another-key": "another-value",
    }

    secret.data({"one-last-key": "one-last-value"})
    secret.update()
    secret.reload()

    assert secret.data() == {
        "key0": "value0",
        "another-key": "another-value",
        "one-last-key": "one-last-value"
    }

    assert secret.data()


def test_secret_is_readed_and_emptied(secret):
    secret.data({"my-data": "my-value"})
    secret.update()
    secret.reload()
    assert secret.data() == {"my-data": "my-value"}

    secret.data({"my-data": None})
    secret.update()
    secret.reload()
    assert secret.data() == {}

    secret.data({"new-key": "new-value"})
    secret.update()
    secret.reload()
    assert secret.data() == {"new-key": "new-value"}

    secret.data({
        "new-key1": "new-value1",
        "new-key2": "new-value2",
    })
    secret.update()
    secret.reload()
    assert secret.data() == {
        "new-key": "new-value",
        "new-key1": "new-value1",
        "new-key2": "new-value2",
    }


def test_secret_values_are_updated(secret):
    secret.data({
        "new-key0": "new-value0",
        "new-key1": "new-value1",
        "new-key2": "new-value2",
    })
    secret.update()
    secret.reload()

    assert secret.data() == {
        "new-key0": "new-value0",
        "new-key1": "new-value1",
        "new-key2": "new-value2",
    }

    secret.data({
        "new-key0": "changed-value0",
        "new-key1": "changed-value1",
        "new-key2": "changed-value2",
    })
    secret.update()

    s = Secret(secret.name, "default").load()
    assert s.data() == {
        "new-key0": "changed-value0",
        "new-key1": "changed-value1",
        "new-key2": "changed-value2",
    }


def test_secret_values_are_updated_again(secret):
    secret.data({
        "new-key0": "new-value0",
        "new-key1": "new-value1",
        "new-key2": "new-value2",
    })
    secret.update()
    secret.reload()

    assert secret.data() == {
        "new-key0": "new-value0",
        "new-key1": "new-value1",
        "new-key2": "new-value2",
    }

    secret.data({
        "new-key0": "changed-value0",
        "new-key1": None,
        "new-key2": "changed-value2",
    })
    secret.update()
    secret.reload()

    assert secret.data() == {
        "new-key0": "changed-value0",
        "new-key2": "changed-value2",
    }


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
