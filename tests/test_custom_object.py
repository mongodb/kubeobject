from unittest import mock

from kubeobject.kubeobject import CustomObject


def mocked_custom_api():
    class MockedApi:
        def get_namespaced_custom_object(group, version, namespace, plural, name):
            return {"name": name}

        def create_namespaced_custom_object(group, version, namespace, plural, body):
            return {"name": body["metadata"]["name"]}

    return MockedApi


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi")
def test_custom_object_creation(mocked_client):
    mocked_client.return_value = mocked_custom_api()

    custom = CustomObject.load("dummy.com", "v1", "dummies", "my-dummy-object", "my-dummy-namespace")

    # Test that __getitem__ is well implemented
    assert custom["name"] == "my-dummy-object"


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi")
def test_custom_object_from_yaml(mocked_client):
    mocked_client.return_value = mocked_custom_api()

    file_dict = {
        "apiVersion": "dummy.com/v1",
        "plural": "dummies",
        "kind": "Dummy",
        "metadata": {"name": "my-dummy-object", "namespace": "my-dummy-namespace"}
    }
    custom = CustomObject.from_yaml(file_dict)

    assert custom["name"] == "my-dummy-object"


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi")
def test_custom_object_read_from_disk(mocked_client):
    mocked_client.return_value = mocked_custom_api()
    yaml_data = """
---
apiVersion: dummy.com/v1
plural: dummies
kind: Dummy
metadata:
  name: my-dummy-object0
  namespace: my-dummy-namespace

---
apiVersion: dummy.com/v1
plural: dummies
kind: Dummy
metadata:
  name: my-dummy-object1
  namespace: my-dummy-namespace
"""

    with mock.patch("kubeobject.kubeobject.open", mock.mock_open(read_data=yaml_data), create=True) as m:
        custom = CustomObject.from_yaml("some-file.yaml")
        m.assert_called_once_with("some-file.yaml", "r")

        assert isinstance(custom, list)
        assert len(custom) == 2

        assert custom[0]["name"] == "my-dummy-object0"
