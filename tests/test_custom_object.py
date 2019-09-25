from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from unittest import mock
from types import SimpleNamespace

from kubeobject.kubeobject import CustomObject


yaml_data0 = """
---
apiVersion: dummy.com/v1
kind: Dummy
metadata:
  name: my-dummy-object0
  namespace: my-dummy-namespace
spec:
  attrStr: value0
  attrInt: 10
  subDoc:
    anotherAttrStr: value1
"""

yaml_data1 = """
---
apiVersion: dummy.com/v1
kind: Dummy
spec:
  attrStr: value0
  attrInt: 10
  subDoc:
    anotherAttrStr: value1
"""


def mocked_custom_api():
    stored_body = []

    class MockedApi:
        def get_namespaced_custom_object(group, version, namespace, plural, name):
            if len(stored_body) > 0:
                return stored_body[-1]
            return {"name": name}

        def create_namespaced_custom_object(group, version, namespace, plural, body: dict):
            body.update({"name": body["metadata"]["name"]})
            stored_body.append(body)
            return body

    return MockedApi


def mocked_crd_return_value():
    return SimpleNamespace(
        spec=SimpleNamespace(
            group="dummy.com", version="v1",
            names=SimpleNamespace(plural="dummies", kind="Dummy"),
        )
    )


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi", return_value=mocked_custom_api())
@mock.patch("kubeobject.kubeobject.get_crd_names", return_value=mocked_crd_return_value())
def test_custom_object_creation(mocked_get_crd_names, mocked_client):
    custom = CustomObject("my-dummy-object", "my-dummy-namespace", kind="Dummy", group="dummy.com", version="v1").create()

    # Test that __getitem__ is well implemented
    assert custom["name"] == "my-dummy-object"


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi", return_value=mocked_custom_api())
@mock.patch("kubeobject.kubeobject.get_crd_names", return_value=mocked_crd_return_value())
def test_custom_object_read_from_disk(mocked_get_crd_names, mocked_client):
    with mock.patch("kubeobject.kubeobject.open", mock.mock_open(read_data=yaml_data0), create=True) as m:
        custom = CustomObject.from_yaml("some-file.yaml")
        m.assert_called_once_with("some-file.yaml")

        assert custom.name == "my-dummy-object0"

        custom.create()

        # Check the values passed are not lost!
        assert custom["spec"]["attrStr"] == "value0"
        assert custom["spec"]["attrInt"] == 10
        assert custom["spec"]["subDoc"]["anotherAttrStr"] == "value1"


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi", return_value=mocked_custom_api())
@mock.patch("kubeobject.kubeobject.get_crd_names", return_value=mocked_crd_return_value())
def test_custom_object_read_from_disk_with_dat_from_yaml(mocked_get_crd_names, mocked_client):
    with mock.patch("kubeobject.kubeobject.open", mock.mock_open(read_data=yaml_data0), create=True) as m:
        custom = CustomObject.from_yaml("some-file.yaml")
        m.assert_called_once_with("some-file.yaml")

        assert custom.name == "my-dummy-object0"

        custom.create()

        # Check the values passed are not lost!
        assert custom["kind"] == "Dummy"
        assert custom["apiVersion"] == "dummy.com/v1"
        assert custom["metadata"]["name"] == "my-dummy-object0"
        assert custom["metadata"]["namespace"] == "my-dummy-namespace"

        # TODO: check why "name" is set but "namespace" is not.
        assert custom["name"] == "my-dummy-object0"
        # assert custom["namespace"] == "my-dummy-namespace"  # this one is not set!

        assert custom.name == "my-dummy-object0"
        assert custom.namespace == "my-dummy-namespace"
        assert custom.plural == "dummies"


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi", return_value=mocked_custom_api())
@mock.patch("kubeobject.kubeobject.get_crd_names", return_value=mocked_crd_return_value())
def test_custom_object_can_be_subclassed_create(mocked_crd_return_value, mocked_client):
    class Subklass(CustomObject):
        pass

    a = Subklass("my-dummy-object", "my-dummy-namespace", kind="Dummy", group="dummy.com", version="v1").create()

    assert a.__class__.__name__ == "Subklass"


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi", return_value=mocked_custom_api())
@mock.patch("kubeobject.kubeobject.get_crd_names", return_value=mocked_crd_return_value())
def test_custom_object_can_be_subclassed_from_yaml(mocked_crd_return_value, mocked_client):
    class Subklass(CustomObject):
        pass

    with mock.patch("kubeobject.kubeobject.open", mock.mock_open(read_data=yaml_data0), create=True) as m:
        a = Subklass.from_yaml("some-other-file.yaml")
        m.assert_called_once_with("some-other-file.yaml")

        assert a.__class__.__name__ == "Subklass"


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi", return_value=mocked_custom_api())
@mock.patch("kubeobject.kubeobject.get_crd_names", return_value=mocked_crd_return_value())
def test_custom_object_defined(mocked_crd_return_value, mocked_client):
    klass = CustomObject.define("Dummy", plural="dummies", group="dummy.com", version="v1")

    k = klass("my-dummy", "default").create()

    # TODO: How to make this?
    # assert k.__class__.__name__ == "Dummy"
    assert k.__class__.__name__ == "_defined"

    assert repr(k) == "Dummy('my-dummy', 'default')"


def test_defined_failed_with_no_name():
    with pytest.raises(ValueError, match="Need to pass a class name"):
        CustomObject.define(None, plural="some-plural", group="some.api", version="version")


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi", return_value=mocked_custom_api())
@mock.patch("kubeobject.kubeobject.get_crd_names", return_value=mocked_crd_return_value())
def test_custom_object_auto_reload(mocked_get_crd_names, mocked_client):
    klass = CustomObject.define("Dummy", plural="dummies", group="dummy.com", version="v1")

    k = klass("my-dummy", "default")
    assert k.last_update is None

    k["status"] = "something"
    k.create()
    assert k.last_update is not None

    k.auto_reload = True
    assert k["status"] == "something"
    assert k.last_update is not None
    last_update_recorded = k.last_update

    # If getting the status after 1 second, we don't reload
    with freeze_time(datetime.now() + timedelta(milliseconds=1000)):
        k["status"]
        assert k.last_update == last_update_recorded

    # If getting the status after 2.1 seconds, we reload!
    with freeze_time(datetime.now() + timedelta(milliseconds=2100)):
        k["status"]
        assert k.last_update > last_update_recorded


def test_raises_if_no_name():
    with mock.patch("kubeobject.kubeobject.open", mock.mock_open(read_data=yaml_data1), create=True) as _:
        with pytest.raises(ValueError, match=r".*needs to be passed as part of the function call.*"):
            CustomObject.from_yaml("some-other-file.yaml")


def test_raises_if_no_namespace():
    with mock.patch("kubeobject.kubeobject.open", mock.mock_open(read_data=yaml_data1), create=True) as _:
        with pytest.raises(ValueError, match=r".*needs to be passed as part of the function call.*"):
            CustomObject.from_yaml("some-other-file.yaml", name="some-name")


@mock.patch("kubeobject.kubeobject.get_crd_names", return_value=mocked_crd_return_value())
def test_name_is_set_as_argument(_):
    with mock.patch("kubeobject.kubeobject.open", mock.mock_open(read_data=yaml_data1), create=True) as _:
        CustomObject.from_yaml("some-other-file.yaml", name="some-name", namespace="some-namespace")
