import copy

import pytest
from unittest.mock import MagicMock, Mock, create_autospec, patch, call
from box import Box

from kubeobject import KubeObject, create_custom_object

from kubernetes import config, client

config.load_kube_config()


def test_box0():
    b = Box({"a": "first", "b": "second"})

    assert b.a == "first"
    assert b.b == "second"


def test_box1():
    """Adds a dict to a box"""

    b = Box({"a": {}})
    b.a = {"some": "data"}

    assert b.a.some == "data"


def test_box2():
    """Tries to use KubeObject as a proxy to a box"""
    k = KubeObject("group", "version", "plural")
    k.a = "attribute a"

    assert k.a == "attribute a"

    with pytest.raises(AttributeError):
        assert k.b == "attribute b"

    k.b = "now this works"
    assert k.b == "now this works"

    k.c = {"name": "some object"}
    assert k.c.name == "some object"

    # Can't access attributes before defining them
    with pytest.raises(AttributeError):
        assert k.d.n.m.k is None

    k.d = {"n": {"m": {"k": "deep value"}}}

    # Now we can fetch the deep object using dot notation
    assert k.d.n.m.k == "deep value"

    # Also the previous to last key should be a box!
    assert isinstance(k.d.n.m, Box)

    # This will get a mutable reference to m
    borrow_box = k.d.n.m
    borrow_box.x = "and a final attribute"

    assert k.d.n.m.x == "and a final attribute"


def test_box3():
    """Tests that if an attribute exists, then calling it directly will not
    proxy the call through the getter."""
    k = KubeObject("group", "version", "plural")

    with pytest.raises(AttributeError):
        # Raises because whoami is not a valid attribute
        k.whoami()

    whoami = Mock(return_value="I'm you")

    # but if we add it, then we get what we want
    k.whoami = whoami
    assert k.whoami() == "I'm you"

    whoami.assert_called_once()

    # TODO: Some magic methods are not easy to mock, see:
    #
    # https://docs.python.org/3/library/unittest.mock.html#mocking-magic-methods
    #
    # I would like to be able to test that __getattr__ was *not called*, but not
    # really sure how to do it. Not that you could change KubeObject's __getattr__ as
    #
    # KubeObject.__getattr__ = SOMETHING
    #
    # but we'll break the rest of the tests? better not to contaminate the tests
    # for now.


def test_box4():
    k = KubeObject("group", "version", "plural")

    k.a = {"hello": "hola"}

    assert k.a.hello == "hola"

    assert isinstance(k.a, Box)

    assert k.a["hello"] == "hola"

    assert isinstance(k.a, Box)
    assert isinstance(k["a"], dict)


def test_kubeobject0():
    k = KubeObject("group0", "version0", "plural0")
    assert k.crd == {"group": "group0", "version": "version0", "plural": "plural0"}


class CustomResource:
    def __init__(self, name):
        self.name = name


@pytest.mark.skip
def test_kubeobject1():
    # currently it is
    Some = create_custom_object(
        "dummies.kubeobject.com"
    )  # -> returns a concrete instance to work with

    with pytest.raises(client.ApiException, match=r".* 404 page not found"):
        some = Some.read("some-name", "namespace")


@patch("kubeobject.kubeobject.CustomObjectsApi")
def test_can_create_objects(patched_custom_objects_api: Mock):
    api = Mock()
    api.get_namespaced_custom_object.return_value = {
        "metadata": {"name": "this-name", "namespace": "this-namespace"},
        "spec": {"attribute": "this is my value"},
    }
    patched_custom_objects_api.return_value = api

    C = create_custom_object("dummies.kubeobject.com")

    c = C.read("this-name", "this-namespace")

    api.get_namespaced_custom_object.assert_called_once()

    assert c.spec.attribute == "this is my value"

    assert isinstance(c.spec, Box)
    assert isinstance(c["spec"], dict)


def test_can_read_my_dummy_object():
    """In order to run this test, examples/dummy.yaml needs to be applied"""
    D = create_custom_object("dummies.kubeobject.com")
    d = D.read("my-dummy-object", "default")

    assert d.spec.thisAttribute == "fourty two"

    d.spec.thisAttribute = "fourty three"
    d.update()

    d2 = D.read("my-dummy-object", "default")

    assert d.spec.thisAttribute == "fourty three"
    d.spec.thisAttribute = "fourty two"
    d.update()


class MockedCustomObjectsApi:
    store = {
        "metadata": {"name": "my-dummy-object", "namespace": "default"},
        "spec": {"thisAttribute": "fourty two"},
    }

    @staticmethod
    def get_namespaced_custom_object(name, namespace, **kwargs):
        return MockedCustomObjectsApi.store

    @staticmethod
    def patch_namespaced_custom_object(
        name, namespace=None, group=None, version=None, plural=None, body=None
    ):
        # body needs to be passed always
        assert body is not None
        MockedCustomObjectsApi.store = body

        return body


@patch("kubeobject.kubeobject.CustomObjectsApi")
def test_can_read_and_update(patched_custom_objects_api: Mock):
    api = Mock(wraps=MockedCustomObjectsApi)
    patched_custom_objects_api.return_value = api

    C = KubeObject("example.com", "v1", "dummies")
    c = C.read("my-dummy-object", "default")

    # Read API was called once
    api.get_namespaced_custom_object.assert_called_once()

    assert c.spec.thisAttribute == "fourty two"

    c.spec.thisAttribute = "fourty three"
    c.update()

    # We expect this body to be one sent to the API.
    updated_body = copy.deepcopy(MockedCustomObjectsApi.store)
    updated_body["spec"]["thisAttribute"] = "fourty three"
    api.patch_namespaced_custom_object.assert_called_once_with(
        **dict(
            name="my-dummy-object",
            namespace="default",
            plural="dummies",
            group="example.com",
            version="v1",
            body=updated_body,
        )
    )

    read_calls = [
        call(
            **dict(
                name="my-dummy-object",
                namespace="default",
                plural="dummies",
                group="example.com",
                version="v1",
            )
        ),
        call(
            **dict(
                name="my-dummy-object",
                namespace="default",
                plural="dummies",
                group="example.com",
                version="v1",
            )
        ),
    ]
    c1 = C.read("my-dummy-object", "default")
    # We expect the calls to read from API are identical
    api.get_namespaced_custom_object.assert_has_calls(read_calls)

    assert c1.spec.thisAttribute == "fourty three"


@pytest.mark.skip
def test_set_and_get_attrs():
    """Studying __setattr__ and __getattr__

    * __getattr__ is only called for attributes that are not found in the instance
    * __setattr__ is always called!
    """

    class A:
        def __init__(self):
            self.a = "this is value a"
            self.b = "this is value b"

        def __setattr__(self, item, value):
            print("setattr")

            self.__dict__[item] = value

        def __getattr__(self, item):
            print("getattr")
            return self.__dict__[item]

    a = A()

    assert a.a == "this is value a"
    assert a.b == "this is value b"

    a.b = "this is new value of b"
    a.c = "this is completely new attribute c"

    with pytest.raises(KeyError):
        assert a.d
