#!/usr/bin/env python

"""example04.py

This example is very similar to the previous one, but describes a way
of creating your own class with your own behaviour on top of
`CustomObect`.  We'll use the `define` method once again to create a
new class, from where we will subclass a new class with the added
behaviour we want.

This also uses the "Istio" operator as an example.

"""

import time
from kubernetes import config
from kubeobject import CustomObject

config.load_kube_config()

# Define an Istio type that will hold `CustomObject`s of type Istio.
IstioBase = CustomObject.define(
    "Istio", plural="istios", group="istio.banzaicloud.io", version="v1beta1"
)


# New class definition with added behaviour: "is_available". In this
# simple example we are only creating a new method, but we can do
# whatever we wanted with this new class, like overloading
# superclass's attributes and methods, even defining our own
# `__init__`.
#
class Istio(IstioBase):
    def is_available(self):
        try:
            return self["status"]["Status"] == "Available"
        except KeyError:
            pass

        return False


# Creates a "my-istio" object in the default namespace.  The returned
# class will have a constructor with 2 parameters: name and namespace
# and those need to be provided.
obj = Istio("my-istio", "default")

# Set a very basic configuration
obj["spec"] = {"version": "1.1.0", "mtls": True}

# Save object
obj.create()

# Auto reload object from the API. The API object is cached for 2
# seconds, but this period can change by setting
# `obj.auto_reload_period` to some `datetime.timedelta` value.
obj.auto_reload = True

# Spot the difference! With this version of the code, we don't have to
# wait for the "Status" attribute to exist in our Custom Object, because
# it has been encapsulated inside the `is_available` method.
print("Waiting for {} to reach 'Available' status.".format(obj.name))
while not obj.is_available():
    # Print a dot and wait for a few seconds, while the object is
    # reconciled.
    print(".", end="", flush=True)
    time.sleep(5)
print()

# Make sure we got away from "Reconciling"
assert obj["status"]["Status"] != "Reconciling"

# And we are actually in "Available"
assert obj["status"]["Status"] == "Available"

# Delete the object
obj.delete()
