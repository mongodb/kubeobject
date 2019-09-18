from __future__ import annotations

import random
import time
import yaml
import types

from base64 import b64decode
from string import ascii_lowercase, digits

from typing import Optional

from kubernetes import client


class CustomObject0:
    def __init__(self, name: str, namespace: str, plural: str = None, kind: str = None, api_version: str = None):
        self.name = name
        self.namespace = namespace
        self.plural = plural
        self.api_version = api_version
        self.kind = kind
        self.saved = False

    def load(self) -> CustomObject0:
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

    def save(self) -> CustomObject0:
        api = client.CustomObjectsApi()

        crd = get_crd_names(plural=self.plural, kind=self.kind, api_version=self.api_version)

        if not hasattr(self, 'backing_obj'):
            self.backing_obj = {
                "kind": crd.spec.names.kind,
                "apiVersion": "{}/{}".format(crd.spec.group, crd.spec.version),
                "metadata": {"name": self.name, "namespace": self.namespace},
            }

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

    @classmethod
    def from_yaml(self, yaml_file, name=None, namespace=None):
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

        obj = CustomObject0(name, namespace, kind=kind, api_version=api_version)
        obj.saved = False
        obj.backing_obj = doc

        # Save the yaml definition to when user wants to save
        # it will be interesting to see how to interact with this object while it has not been saved
        # with __getitem__ and __setitem__ functions.
        # obj.body_to_save = doc

        return obj

    def __getitem__(self, key):
        return self.backing_obj[key]

    def __setitem__(self, key, val):
        self.backing_obj[key] = val


class CustomObject:
    @classmethod
    def load(cls, group, version, plural, name, namespace) -> CustomObject:
        """Loads a Kubernetes Object from the API."""
        api = client.CustomObjectsApi()

        # TODO: try errors from the API, retry
        obj = api.get_namespaced_custom_object(group, version, namespace, plural, name)

        # Return a new instance of Kube Object from the API.
        return CustomObject(obj)

    @classmethod
    def create(cls, body, namespace, plural=None) -> CustomObject:
        """Creates a Custom Object."""
        api = client.CustomObjectsApi()

        id = CustomObject.__get_object_id(body)

        if plural is None:
            plural = id["plural"]

        obj = api.create_namespaced_custom_object(
            id["group"], id["version"], namespace, plural, body
        )

        return CustomObject(obj, plural)

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
    def from_yaml(cls, yaml_file, namespace=None, plural=None):
        """Creates a Custom Resource from a yaml file or document"""
        if not isinstance(yaml_file, dict):
            with open(yaml_file, "r") as fd:
                yaml_file = yaml.safe_load_all(fd.read())

        if not isinstance(yaml_file, types.GeneratorType):
            yaml_file = [yaml_file]

        objs = []
        for doc in yaml_file:
            if namespace is None:
                namespace = doc["metadata"]["namespace"]

            objs.append(CustomObject.create(doc, namespace, plural))

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

        # At creation there's no selfLink!
        # The plural is not here, but it is on the selfLink
        if not hasattr(self, "plural"):
            if "selfLink" in doc["metadata"]:
                self_link = doc["metadata"]["selfLink"]
                plural0 = self_link.split("/")[-2]
                if plural != plural0:
                    plural = plural0
        else:
            plural = self.plural

        return {
            "group": group,
            "version": version,
            "plural": plural,
            "name": name,
            "namespace": namespace,
        }

    def __init__(self, rest_object, plural=None):
        self.rest_object = rest_object
        if plural is not None:
            self.plural = plural

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
