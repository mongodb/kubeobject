# KubeObject

_A simple to use wrapping on top of Kubernetes custom resources with
object oriented semantics._

KubeObject allows you to use Kubernetes Custom Objects in an object
oriented way. It works by defining an object, by instantiating it with
a `name` and `namespace` and then "bounding" this object to a
Kubernetes object by creating it, or loading it, if it already exists.

# Quick Start

In the following example we create an "Istio" object, which will
manage one of the Custom Objects defined by the
[Istio](https://operatorhub.io/operator/istio) operator. A simple
lifecycle is explained below.

``` python
# Builds the object, but it is "unbound", this is, it is not
# referring to an actual object in Kubernetes.
istio = CustomObject("my-istio", "my-namespace", plural="istios", api_version="istio.banzaicloud.io/v1beta1")

# Let's pass the simplest spec we can
istio["spec"] = {"version": "1.1.0", "mtls": True}

# And now create it; after creation the object is "bound"
istio.create()
```

Updating the object's `Spec` and checking the object's `Status` is one
of our goals as well, like in the following example:

``` python
# The Istio operator should have started working on deploying
# this new Custom Resource. Let's get the status of the object
print(istio["status"])

# This is empty, because since calling `create()` we have not
# updated from the actual object in Kubernetes. Let's get an
# up-to-date object.
istio.reload()

# I want to avoid calling `reload()` everytime I need a new
# version
istio.auto_reload = True

# Now we'll wait until the object has reached a given status:
while istio["status"]["Status"] == "Reconciling": time.sleep(5)

# Check the Status after "Reconciling"
print("Our status is:", istio["status"]["Status"])
```

After doing all its work, the `Istio` object might need to be deleted:

``` python
istio.delete()
```
