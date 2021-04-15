from __future__ import annotations

import yaml
from datetime import datetime, timedelta
from typing import Optional, Union, TextIO
import io
import copy

from kubernetes import client
from kubernetes.client.api import ApiextensionsV1Api, CustomObjectsApi

from box import Box

from kubeobject.exceptions import ObjectNotBoundException


class KubeObject(object):
    BACKING_OBJ = "__backing_obj"

    def __init__(
        self,
        group: str,
        version: str,
        plural: str,
    ):
        self.init_attributes()

        # And now we initialize it with actual values, so we know over what kind
        # of object to operate.
        self.__dict__["crd"] = {"plural": plural, "group": group, "version": version}

    def init_attributes(self):
        """This is separated from __init__ because here we initialize empty attributes of
        KubeObject instance, but we don't incorporate business logic."""

        # Initialize an "empty" CRD, which means that this object is not bound
        # to an specific CRD.
        self.__dict__["crd"] = {}

        # A KubeObject is bound when it is pointing at a given CRD on a name/namespace
        self.__dict__["bound"] = {}

        # This is the object that will contain the definition of the Custom Object when bound
        self.__dict__[KubeObject.BACKING_OBJ] = Box()

        # Set an API to work with.
        # TODO: Allow for a better experience; api could be defined from env variables,
        # in_cluster or whatever. See if this is needed. Can we run our samples with
        # in_cluster, or based on different clusters pointed at by env variables?
        self.__dict__["api"] = CustomObjectsApi()

    def read(self, name: str, namespace: str):
        obj = self.api.get_namespaced_custom_object(
            name=name, namespace=namespace, **self.crd
        )

        self.__dict__[KubeObject.BACKING_OBJ] = Box(obj)
        self.__dict__["bound"] = True
        self.__dict__["name"] = obj["metadata"]["name"]
        self.__dict__["namespace"] = obj["metadata"]["namespace"]

        return self

    def update(self):
        if not self.bound:
            # there's no corresponding object in the Kubernetes cluster
            raise ObjectNotBoundException

        obj = self.api.patch_namespaced_custom_object(
            name=self.name,
            namespace=self.namespace,
            **self.crd,
            body=self.__dict__[KubeObject.BACKING_OBJ].to_dict(),
        )

        self.__dict__[KubeObject.BACKING_OBJ] = Box(obj)

        return self

    def delete(self):
        if not self.bound:
            raise ObjectNotBoundException

        # TODO: body is supposed to be client.V1DeleteOptions()
        # but for now we are just passing the empty dict.

        self.api.delete_namespaced_custom_object(
            name=self.name,
            namespace=self.namespace,
            body={},
            **self.crd,
        )

        # Not bound any more!
        self.bound = False

    def create(
        self,
    ) -> KubeObject:
        """Attempts to create an object using the Kubernetes API. This object needs to
        have been defined first! This is a complete metadata, spec or any other fields
        need to have been populated first."""
        api: CustomObjectsApi = self.api

        obj = api.create_namespaced_custom_object(
            namespace=self.namespace,
            **self.crd,
            body=self.__dict__[KubeObject.BACKING_OBJ].to_dict(),
        )

        # This object has been bound to an existing object in Kube
        self.bound = True

    def read_from_yaml_file(self, object_definition: TextIO):
        return self._read_from(object_definition)

    def read_from_dict(self, object_definition: dict):
        return self._read_from(object_definition)

    def _read_from(self, object_definition=Union[TextIO, dict]):
        """Populates this object from object_definition.

        * type(io.IOBase): opens the file and reads a yaml doc from it
        * type(dict): Uses it as backing_object
        """
        if isinstance(object_definition, io.IOBase):
            obj = yaml.safe_load(object_definition.read())
        elif isinstance(object_definition, dict):
            obj = copy.deepcopy(object_definition)
        else:
            raise ValueError("argument should be a file-like object or a dict")

        self.__dict__[KubeObject.BACKING_OBJ] = Box(obj)
        self.__dict__["bound"] = False

        return self

    def __setattr__(self, item, value):
        if item.startswith("__"):
            self.__dict__[item] = value
        else:
            self.__dict__[KubeObject.BACKING_OBJ][item] = value

    def __getattr__(self, item):
        if item not in self.__dict__[KubeObject.BACKING_OBJ]:
            raise AttributeError(item)

        return getattr(self.__dict__[KubeObject.BACKING_OBJ], item)

    def __getitem__(self, key):
        """Similar to what dot notation (getattr) produces, but this
        will get the dictionary that corresponds to that attribute."""
        d = self.__getattr__(key)
        if isinstance(d, Box):
            return d.to_dict()

        return d


def create_custom_object(name: str, api=None) -> KubeObject:
    """This function returns a Class type that can be used to initialize
    custom objects of the type name."""

    # Get the full name from the API
    # Kind is not used, but it should be stored somewhere in case we want
    # to pretty print this object or something.
    _kind, plural, group, version = full_crd_name(name, api)

    # To be able to work with the objects we only need group, version and plural
    return KubeObject(group, version, plural)


def full_crd_name(
    name: str, api: Optional[ApiextensionsV1Api] = None
) -> Tuple[str, str, str, str, str]:
    """Fetches this CRD from the kubernetes API by name and returns its
    name, kind, plural, group and version."""
    if api is None:
        # Use default (already configured) client
        api = client.ApiextensionsV1Api()

    # The name here is something like: resource.group (dummy.example.com)
    response = api.read_custom_resource_definition(name)

    group = response.spec.group
    kind = response.spec.names.kind
    plural = response.spec.names.plural
    version = [v.name for v in response.spec.versions if v.served][0]

    return (kind, plural, group, version)
