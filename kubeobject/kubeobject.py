from __future__ import annotations

from kubernetes import client
import time
import yaml


class KubeObject:
    """Only supports custom objects from now."""

    @classmethod
    def load(cls, group, version, plural, name, namespace):
        """Loads a Kubernetes Object from the API."""
        api = client.CustomObjectsApi()

        # TODO: try errors from the API, retry
        obj = api.get_namespaced_custom_object(group, version, namespace, plural, name)

        # Return a new instance of Kube Object from the API.
        return KubeObject(obj)

    @classmethod
    def create(cls, body, namespace) -> KubeObject:
        """Creates a Custom Object."""
        api = client.CustomObjectsApi()

        id = KubeObject.__get_object_id(body)
        obj = api.create_namespaced_custom_object(
            id["group"], id["version"], namespace, id["plural"], body
        )

        return KubeObject(obj)

    @classmethod
    def update(cls, body, namespace) -> KubeObject:
        if callable(namespace):
            namespace = namespace()

        api = client.CustomObjectsApi()
        id = KubeObject.__get_object_id(body)
        obj = api.patch_namespaced_custom_object(
            id["group"], id["version"], namespace, id["plural"], id["name"], body
        )

        return KubeObject(obj)

    @classmethod
    def from_yaml(cls, yaml_file, namespace):
        """Creates a Custom Resource from a yaml file"""
        with open(yaml_file, "r") as fd:
            yaml_all = yaml.safe_load_all(fd.read())

        objs = []
        for doc in yaml_all:
            if namespace is None:
                namespace = doc["metadata"]["namespace"]

            objs.append(KubeObject.create(doc, namespace))

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
        tmpobj = KubeObject.update(
            self.rest_object, self.rest_object["metadata"]["namespace"]
        )
        self.rest_object = tmpobj.rest_object

    def delete(self):
        """Removes this object form Kuberentes API"""
        api = client.CustomObjectsApi()
        body = client.V1DeleteOptions()
        id = KubeObject.__get_object_id(self.rest_object)

        api.delete_namespaced_custom_object(
            id["group"], id["version"], id["namespace"], id["plural"], id["name"], body
        )

    def reload(self):
        """Reloads the object from the Kubernetes API."""
        # TODO: this is really ugly
        tmpobj = KubeObject.load(
            **KubeObject.__get_object_id(self.rest_object)
        )
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
            if fn(self):
                return True

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
        """Mimics the behaviour of a dict. Gets []"""
        return self.rest_object[key]

    def __setitem__(self, key, val):
        """Mimics the behaviour of a dict. Sets []"""
        self.rest_object[key] = val
