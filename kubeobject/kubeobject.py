from __future__ import annotations

import time
import random
import yaml

from base64 import b64decode
from string import ascii_lowercase, digits

from typing import Optional

from kubernetes import client


class CustomObject:
    def __init__(self, name: str, namespace: str, plural: str = None, kind: str = None, api_version: str = None):
        self.name = name
        self.namespace = namespace
        self.plural = plural
        self.api_version = api_version
        if api_version is not None:
            self.group, self.version = api_version.split("/")
        self.kind = kind
        self.saved = False
        self.auto_save = False

    def load(self) -> CustomObject:
        """Loads this object from the API."""
        api = client.CustomObjectsApi()

        crd = get_crd_names(plural=self.plural, kind=self.kind, api_version=self.api_version)

        obj = api.get_namespaced_custom_object(
            crd.spec.group,
            crd.spec.version,
            self.namespace,
            crd.spec.names.plural,
            self.name,
        )

        self.backing_obj = obj
        self.saved = True

        return self

    def create(self) -> CustomObject:
        api = client.CustomObjectsApi()

        crd = get_crd_names(plural=self.plural, kind=self.kind, api_version=self.api_version)

        if not hasattr(self, 'backing_obj'):
            self.backing_obj = {
                "kind": crd.spec.names.kind,
                "apiVersion": "{}/{}".format(crd.spec.group, crd.spec.version),
                "metadata": {"name": self.name, "namespace": self.namespace},
            }
        else:
            self.backing_obj["metadata"] = {"name": self.name, "namespace": self.namespace}

        obj = api.create_namespaced_custom_object(
            crd.spec.group,
            crd.spec.version,
            self.namespace,
            crd.spec.names.plural,
            self.backing_obj,
        )

        self.backing_obj = obj
        self.saved = True

        return self

    def update(self) -> CustomObject:
        api = client.CustomObjectsApi()

        crd = get_crd_names(plural=self.plural, kind=self.kind, api_version=self.api_version)

        self.backing_obj["metadata"] = {"name": self.name, "namespace": self.namespace}

        obj = api.patch_namespaced_custom_object(
            crd.spec.group,
            crd.spec.version,
            self.namespace,
            crd.spec.names.plural,
            self.name,
            self.backing_obj,
        )

        self.backing_obj = obj
        self.saved = True

        return self

    @classmethod
    def from_yaml(cls, yaml_file, name=None, namespace=None):
        doc = yaml.safe_load(open(yaml_file))

        if name is None:
            name = doc["metadata"]["name"]
        else:
            doc["metadata"]["name"] = name

        if namespace is None:
            namespace = doc["metadata"]["namespace"]
        else:
            doc["metadata"]["namespace"] = namespace

        kind = doc["kind"]
        api_version = doc["apiVersion"]
        crd = get_crd_names(kind=kind, api_version=api_version)

        obj = CustomObject(name, namespace, kind=kind, api_version=api_version, plural=crd.spec.names.plural)
        obj.saved = False
        obj.backing_obj = doc

        return obj

    def delete(self):
        api = client.CustomObjectsApi()
        body = client.V1DeleteOptions()

        api.delete_namespaced_custom_object(
            self.group, self.version, self.namespace, self.plural, self.name, body
        )

    def reload(self):
        """Reloads the object from the Kubernetes API."""
        return self.load()

    def wait_for_phase(self, phase, timeout=240):
        """Waits until object reaches given state. The solution currently
        implemented is super simple and very similar to what we already have,
        but does the job well.

        # TODO: Maybe an implementation based on futures will be better in this case?
        """
        return self.wait_for(lambda s: s["status"].get("phase") == phase)

    def wait_for(self, fn, timeout=240):
        wait = 5
        while True:
            self.reload()
            try:
                if fn(self):
                    return True
            except Exception:
                pass

            if timeout > 0:
                timeout -= wait
                time.sleep(wait)
            else:
                break

    def reaches_phase(self, phase):
        return self.wait_for_phase(phase)

    def abandons_phase(self, phase):
        return self.wait_for(lambda s: s["status"].get("phase") != phase)

    def __getitem__(self, key):
        return self.backing_obj[key]

    def __setitem__(self, key, val):
        self.backing_obj[key] = val

        if self.auto_save:
            self.update()


class KubeObjectGeneric:
    @classmethod
    def create(cls):
        pass

    @classmethod
    def read(cls):
        pass

    def delete(self):
        pass

    def update(self):
        pass

    @property
    def data(self):
        if isinstance(self, ConfigMap):
            return self.backing_obj.data
        elif isinstance(self, Secret):
            return {
                k: b64decode(v).decode("utf-8")
                for (k, v) in self.backing_obj.data.items()
            }


class ConfigMap(KubeObjectGeneric):
    @classmethod
    def create(cls, name, namespace, data):
        api = client.CoreV1Api()
        metadata = client.V1ObjectMeta(name=name)
        body = client.V1ConfigMap(metadata=metadata, data=data)
        return ConfigMap(
            name, namespace, api.create_namespaced_config_map(namespace, body)
        )

    @classmethod
    def read(cls, name, namespace):
        api = client.CoreV1Api()
        return ConfigMap(
            name, namespace, api.read_namespaced_config_map(name, namespace)
        )

    def __init__(self, name, namespace, backing_obj):
        self.name = name
        self.namespace = namespace
        self.backing_obj = backing_obj

    def delete(self):
        api = client.CoreV1Api()
        body = client.V1DeleteOptions()

        return api.delete_namespaced_config_map(self.name, self.namespace, body=body)

    def update(self, data):
        api = client.CoreV1Api()
        configmap = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(name=self.name), data=data
        )

        self.backing_obj = api.patch_namespaced_config_map(
            self.name, self.namespace, configmap
        )

    def __str__(self):
        return "configmap/{}".format(self.name)


class Secret(KubeObjectGeneric):
    @classmethod
    def create(cls, name, namespace, data):
        api = client.CoreV1Api()
        metadata = client.V1ObjectMeta(name=name)
        body = client.V1Secret(metadata=metadata, string_data=data)
        return Secret(name, namespace, api.create_namespaced_secret(namespace, body))

    @classmethod
    def read(cls, name, namespace):
        api = client.CoreV1Api()
        return Secret(name, namespace, api.read_namespaced_secret(name, namespace))

    def __init__(self, name, namespace, backing_obj):
        self.name = name
        self.namespace = namespace
        self.backing_obj = backing_obj

    def delete(self):
        api = client.CoreV1Api()
        body = client.V1DeleteOptions()

        return api.delete_namespaced_secret(self.name, self.namespace, body=body)

    def update(self, data):
        api = client.CoreV1Api()
        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(name=self.name), string_data=data
        )

        self.backing_obj = api.patch_namespaced_secret(
            self.name, self.namespace, secret
        )

    def __str__(self):
        return "secret/{}".format(self.name)


class Namespace(KubeObjectGeneric):
    @classmethod
    def create(cls, name):
        api = client.CoreV1Api()
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=name))

        return Namespace(name, api.create_namespace(namespace))

    @classmethod
    def exists(cls, name):
        api = client.CoreV1Api()
        try:
            api.read_namespace(name)
        except client.rest.ApiException:
            return False

        return True

    def __init__(self, name, backing_obj):
        self.name = name
        self.backing_obj = backing_obj

    def delete(self):
        api = client.CoreV1Api()
        body = client.V1DeleteOptions()

        return api.delete_namespace(self.name, body=body)

    def __str__(self):
        return "namespace/{}".format(self.name)


def generate_random_name(prefix="", suffix="", size=63) -> str:
    """Generates a random and valid Kubernetes name."""
    max_len = 63
    min_len = 0

    if size > max_len:
        size = max_len

    random_len = size - len(prefix) - len(suffix)
    if random_len < min_len:
        random_len = min_len

    body = []
    if random_len > 0:
        body = [random.choice(ascii_lowercase + digits) for _ in range(random_len - 1)]
        body = [random.choice(ascii_lowercase)] + body

    return prefix + "".join(body) + suffix


def get_crd_names(plural=None, kind=None, api_version=None) -> Optional[dict]:
    """Gets the names, group and version by the identifier."""
    api = client.ApiextensionsV1beta1Api()

    if plural == kind == api_version is None:
        return None

    group = version = ""
    if api_version is not None:
        group, version = api_version.split("/")

    crds = api.list_custom_resource_definition()
    for crd in crds.items:
        found = True
        if group != "":
            if crd.spec.group != group:
                found = False

        if version != "":
            if crd.spec.version != version:
                found = False

        if kind is not None:
            if crd.spec.names.kind != kind:
                found = False

        if plural is not None:
            if crd.spec.names.plural != plural:
                found = False

        if found:
            return crd
