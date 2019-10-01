from __future__ import annotations

from base64 import b64decode, b64encode
from kubernetes import client

from . import CustomObject


class GenericDataObject(CustomObject):
    """Holds a Kubernetes Data Object, like ConfigMap & Secret."""
    def __init__(self, name: str, namespace: str, kind: str = None, singular: str = None, plural: str = None):
        super(GenericDataObject, self).__init__(
            name,
            namespace,
            plural=plural,
            kind=kind,
            group="",
            version="v1",
        )

        # _data object will contain the data that we'll be updating
        # in the underlying resource.
        self._data = {}

        # Name of the resource type
        self.singular = singular

    def load(self):
        obj = self._read_fn(self.name, self.namespace)
        if obj.data is not None:
            self._data = {k: self.deserialize(v) for k, v in obj.data.items()}
        else:
            self._data = {}

        self.backing_obj = obj
        self.bound = True

        self._register_updated()
        return self

    def create(self):
        body = self._constructor(
            data={k: self.serialize(v) for k, v in self._data.items()},
            metadata=client.V1ObjectMeta(name=self.name),
        )

        obj = self._create_fn(self.namespace, body)

        self.backing_obj = obj
        self.bound = True

        self._register_updated()
        return self

    def delete(self):
        body = client.V1DeleteOptions()
        return self._delete_fn(self.name, self.namespace, body=body)

    def update(self):
        obj = self._constructor(
            data={k: self.serialize(v) for k, v in self._data.items()},
            metadata=client.V1ObjectMeta(name=self.name),
        )

        self.backing_obj = self._patch_fn(
            self.name, self.namespace, obj
        )

    def data(self, _data: dict = None):
        if _data is None:
            return self._data

        if not isinstance(_data, dict):
            raise ValueError("data() expects a dictionary")

        self._data.update(_data)

    def deserialize(self, val):
        """deserialize returns the string representation of a value
        as returned by the Kubernetes API. It needs to be implemented by
        a subclass when required, for example, by `Secret` which needs
        the data to be base64 decoded."""
        return val

    def serialize(self, val):
        return val

    def _data_update_param(self):
        return {"data": self._data}

    def __str__(self):
        return "{}/{}".format(self.singular, self.name)


class ConfigMap(GenericDataObject):
    def __init__(self, name: str, namespace: str):
        super(self.__class__, self).__init__(
            name,
            namespace,
            kind="ConfigMap",
            singular="configmap",
            plural="configmaps",
        )

        self.api = client.CoreV1Api()

        self._read_fn = self.api.read_namespaced_config_map
        self._create_fn = self.api.create_namespaced_config_map
        self._delete_fn = self.api.delete_namespaced_config_map
        self._patch_fn = self.api.patch_namespaced_config_map
        self._constructor = client.V1ConfigMap


class Secret(GenericDataObject):
    def __init__(self, name: str, namespace: str):
        super(self.__class__, self).__init__(
            name,
            namespace,
            kind="Secret",
            singular="secret",
            plural="secrets",
        )

        self.api = client.CoreV1Api()

        self._read_fn = self.api.read_namespaced_secret
        self._create_fn = self.api.create_namespaced_secret
        self._delete_fn = self.api.delete_namespaced_secret
        self._patch_fn = self.api.patch_namespaced_secret
        self._constructor = client.V1Secret

    # def _data_update_param(self):
    #     return {"string_data": self._data}

    def data(self, _data: dict = None):
        if _data is None:
            return self._data

        if not isinstance(_data, dict):
            raise ValueError("data() expects a dictonary")

        self._data.update(_data)

    def deserialize(self, val):
        return b64decode(val).decode("utf-8")

    def serialize(self, val):
        if val is None:
            return val
        return b64encode(val.encode('ascii')).decode()


class Namespace(CustomObject):
    def __init__(self, name: str):
        super(self.__class__, self).__init__(
            name,
            namespace="",
            kind="Namespace",
            plural="namespaces",
            group="",
            version="v1",
        )

        self.api = client.CoreV1Api

    def create(self) -> Namespace:
        api = client.CoreV1Api()
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=self.name))

        obj = api.create_namespace(namespace)

        self.backing_obj = obj
        self.bound = True

        self._register_updated()
        return self

    def load(self) -> Namespace:
        api = self.api()

        obj = api.read_namespace(self.name)

        self.backing_obj = obj
        self.bound = True

        self._register_updated()
        return self

    def delete(self):
        api = client.CoreV1Api()
        body = client.V1DeleteOptions()

        api.delete_namespace(self.name, body=body)
        self.bound = False

        self._register_updated()

    @classmethod
    def exists(cls, name):
        api = client.CoreV1Api()
        try:
            api.read_namespace(name)
        except client.rest.ApiException:
            return False

        return True

    def __str__(self):
        return "namespace/{}".format(self.name)
