from unittest import mock

from kubeobject.kubeobject import CustomObject


def mocked_custom_api():
    class MockedApi:
        def get_namespaced_custom_object(group, version, namespace, plural, name):
            return {"name": "mocked_object"}

        def create_namespaced_custom_object(group, version, namespace, plural, body):
            return {"name": "created_with_mocked_api"}

    return MockedApi


@mock.patch("kubeobject.kubeobject.client.CustomObjectsApi")
def test_custom_object_creation(mocked_client):
    mocked_client.return_value = mocked_custom_api()

    custom = CustomObject.load("dummy.com", "v1", "dummies", "my-dummy-object", "my-dummy-namespace")

    # Test that __getitem__ is well implemented
    assert custom["name"] == "mocked_object"


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

    assert custom["name"] == "created_with_mocked_api"
