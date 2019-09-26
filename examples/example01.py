#!/usr/bin/env python

"""example01.py

In this example we'll show how to manage a Custom Resource in
Kubernetes. We do so by initializing a `CustomObject` with its `group`
and `version`, and also its name and the namespace where it resides.

In order to run this example, you have to apply the "dummy.crd.yaml",
in order to create the "Dummy" Custom Resource Definition.

$ kubectl apply -f dummy.crd.yaml
customresourcedefinition.apiextensions.k8s.io/dummies.kubeobject.com created

"""

from kubernetes import config, client
from kubeobject import CustomObject

config.load_kube_config()

# Initialize a `CustomObject`
obj0 = CustomObject(
    "my-dummy-object", "default", group="kubeobject.com", version="v1", plural="dummies"
)
# The object is not bound at this time, there's no "connection" with an
# object in Kubernetes
assert obj0.bound is False

# Create this `CustomObject` in Kubernetes
obj0.create()

# And not the object is bound, there's an actual object in Kubernetes we
# are referring to
assert obj0.bound

# Change a bit of the Spec
obj0["spec"] = {"thisAttribute": "this value"}
obj0.update()

assert obj0["spec"]["thisAttribute"] == "this value"

# We'll read this object again and confirm that our values were saved.
obj1 = CustomObject(
    "my-dummy-object", "default", group="kubeobject.com", version="v1", plural="dummies"
)

# Load the object from Kubernetes
obj1.load()
# Let's confirm the data read from Kubernetes is correct
assert obj1["spec"]["thisAttribute"] == "this value"

# Now, let's change the attribute with our own value
obj1["spec"]["thisAttribute"] = "no, this value!"
obj1.update()

# What's the value read from Kubernetes?
obj0.reload()
assert obj0["spec"]["thisAttribute"] == "no, this value!"

# Ok, I get your point, let's delete this object
obj0.delete()

# Let's not try to delete it again!
try:
    obj1.delete()
except client.rest.ApiException as e:
    # The object was not found, as it was already deleted!
    assert e.status == 404
