from __future__ import annotations

import random
import time
import yaml

from base64 import b64decode
from string import ascii_lowercase, digits

from kubernetes import client


class CustomObject:
    """Only supports custom objects from now."""

    @classmethod
    def load(cls, group, version, plural, name, namespace) -> CustomObject:
        """Loads a Kubernetes Object from the API."""
        api = client.CustomObjectsApi()

        # TODO: try errors from the API, retry
        obj = api.get_namespaced_custom_object(group, version, namespace, plural, name)

        # Return a new instance of Kube Object from the API.
        return CustomObject(obj)

    @classmethod
    def create(cls, body, namespace) -> CustomObject:
        """Creates a Custom Object."""
        api = client.CustomObjectsApi()

        id = CustomObject.__get_object_id(body)
        obj = api.create_namespaced_custom_object(
            id["group"], id["version"], namespace, id["plural"], body
        )

        return CustomObject(obj)

    @classmethod
    def update(cls, body, namespace) -> CustomObject:
        if callable(namespace):
            namespace = namespace()

        api = client.CustomObjectsApi()
        id = CustomObject.__get_object_id(body)
        obj = api.patch_namespaced_custom_object(
            id["group"], id["version"], namespace, id["plural"], id["name"], body
        )

        return CustomObject(obj)

    @classmethod
    def from_yaml(cls, yaml_file, namespace):
        """Creates a Custom Resource from a yaml file"""
        with open(yaml_file, "r") as fd:
            yaml_all = yaml.safe_load_all(fd.read())

        objs = []
        for doc in yaml_all:
            if namespace is None:
                namespace = doc["metadata"]["namespace"]

            objs.append(CustomObject.create(doc, namespace))

        if len(objs) == 1:
            return objs[0]

        return objs

    @classmethod
    def __get_object_id(self, doc):
        """Returns group, version, namespace, plural, name for the current object"""
        group, version = doc["apiVersion"].split("/")
        plural = doc["kind"].lower()
        name = doc["metadata"]["name"]
        namespace = doc["metadata"].get("namespace", "")

        return {
            "group": group,
            "version": version,
            "plural": plural,
            "name": name,
            "namespace": namespace,
        }

    def __init__(self, rest_object):
        self.rest_object = rest_object

    def save(self):
        tmpobj = CustomObject.update(
            self.rest_object, self.rest_object["metadata"]["namespace"]
        )
        self.rest_object = tmpobj.rest_object

    def delete(self):
        """Removes this object form Kuberentes API"""
        api = client.CustomObjectsApi()
        body = client.V1DeleteOptions()
        id = CustomObject.__get_object_id(self.rest_object)

        api.delete_namespaced_custom_object(
            id["group"], id["version"], id["namespace"], id["plural"], id["name"], body
        )

    def reload(self):
        """Reloads the object from the Kubernetes API."""
        # TODO: this is really ugly
        tmpobj = CustomObject.load(**CustomObject.__get_object_id(self.rest_object))
        self.rest_object = tmpobj.rest_object

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
        return self.rest_object[key]

    def __setitem__(self, key, val):
        self.rest_object[key] = val

    def __str__(self):
        id = CustomObject.__get_object_id(self.rest_object)
        return "{}.{}/{}".format(id["plural"], id["group"], id["name"])


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

    def __init__(self, name, backing_obj):
        self.name = name
        self.backing_obj = backing_obj

    def delete(self):
        api = client.CoreV1Api()
        body = client.V1DeleteOptions()

        return api.delete_namespace(self.name, body=body)

    def __str__(self):
        return "namespace/{}".format(self.name)


def generate_random_name(prefix="", suffix="", size=63):
    """Generates a random and valid Kubernetes name."""
    max_len = 63
    min_len = 0

    if len(prefix) == 0:
        prefix = random.choice(ascii_lowercase)

    if size > max_len:
        size = max_len
    random_len = size - len(prefix) - len(suffix)
    if random_len < min_len:
        random_len = min_len

    body = [random.choice(ascii_lowercase + digits) for _ in range(random_len)]

    return prefix + "".join(body) + suffix
