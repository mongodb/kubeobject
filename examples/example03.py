#!/usr/bin/env python

"""example03.py

In this example, we'll define a particular variation of `CustomObject`
which will work with Istio's CRD. To find more information about
Istio, visit their Operator at operatorhub.io
(https://operatorhub.io/operator/istio).

In order to run this example, you'll need the Istio CRD and Operator
installed in your Kubernetes cluster. I recommend you use
[kind](https://github.com/kubernetes-sigs/kind) as it is a very
lightweight Kubernetes distribution that starts in just a matter of
seconds. To install the Istio Operator, follow the instructions at
operatorhub.io.

"""

import time
from kubernetes import config
from kubeobject import CustomObject

config.load_kube_config()

# Define an Istio type that will hold `CustomObject`s of type Istio.
Istio = CustomObject.define("Istio", plural="istios", group="istio.banzaicloud.io", version="v1beta1")

# Creates a "my-istio" object in the default namespace
obj = Istio("my-istio", "default")

# Set a very basic configuration
obj["spec"] = {"version": "1.1.0", "mtls": True}

# Save object... give it a few seconds for the Istio operator to pick it up
# and to write an status to it.
obj.create()
time.sleep(5)

# Reload the Custom Object from Kubernetes
obj.reload()

# Waits until object gets to "Available"
obj.auto_reload = True
print("Waiting for {} to reach 'Available' status.".format(obj.name))
while obj["status"]["Status"] != "Available":
    print(".", end="", flush=True)
    time.sleep(5)
print()

# Make sure we got away from "Reconciling"
assert obj["status"]["Status"] != "Reconciling"

# And we are actually in "Available"
assert obj["status"]["Status"] == "Available"

# Delete the object
obj.delete()
