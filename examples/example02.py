#!/usr/bin/env python

"""example02.py

This example is very similar to `example01.py`, but we'll be creating an
object described in a yaml file. We use a similar approach to assert that
the data is written and read correctly from the Kubernetes API.

As in the previous example, the `Dummy` CRD needs to be created.

$ kubectl apply -f dummy.crd.yaml
customresourcedefinition.apiextensions.k8s.io/dummies.kubeobject.com created

"""

from kubernetes import config
from kubeobject import CustomObject

config.load_kube_config()

# Initialize a `CustomObject`, this time from a yaml file.
# Our `dummy.yaml` file has a `metadata.name` attribute set to
# "my-dummy-object", but it does not have a `metadata.namespace`
# set, so we have to provide it.
obj0 = CustomObject.from_yaml("dummy.yaml", namespace="default")

# The object is not bound at this time, there's no "connection" with an
# object in Kubernetes
assert obj0.bound is False

# Create this `CustomObject` in Kubernetes.
obj0.create()

# And not the object is bound, there's an actual object in Kubernetes we
# are referring to
assert obj0.bound

# Make sure the spec was passed correctly
assert obj0["spec"]["answer"] == "fourty two"

# Use a second object to read from the previous one
obj1 = CustomObject(
    "my-dummy-object", "default", group="kubeobject.com", version="v1", plural="dummies"
)

# Load the object from Kubernetes
obj1.load()
# Let's confirm the data read from Kubernetes is correct
assert obj1["spec"]["answer"] == "fourty two"

# Remove the object
obj0.delete()

# But remove the object just once!
# obj1.delete()
