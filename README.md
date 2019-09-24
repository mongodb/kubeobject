# KubeObject

_Easily manage Kubernetes Objects_

KubeObject allows for the management of Kubernetes using a simple object mapper to Rest API objects.

# Examples

## Using kubeobject to read a Custom Resource.

``` python
from kubeobject import CustomObject

# This is how you load objects from the API

# Load a CustomObject from given api_version and plural
obj = CustomObject("my-dummy-object", "my-namespace", api_version="kubeobject.com/v1", plural="dummies").load()

# Load a CustomObject from given kind and api_version
obj = CustomObject("my-dummy-object", "my-namespace", kind="Dummy", api_version="kubeobject.com/v1").load()

# This is how you create objects from the API
obj = CustomObject("name", "my-namespace", api_version="kubeobject.com/v1", plural="dummies").create()
obj = CustomObject.from_yaml("yaml_file.yaml", "my-namespace").create()

# And finally, this is how you read a YAML file, apply changes to it and then create with your changes:
obj = CustomObject.from_yaml("yaml_file.yaml", "my-namespace")
obj["spec"]["answer"] = "The correct anser is 42"
obj.create()

obj.auto_save = True
obj["spec"]["newField"] = "this is a new value"  # and will be auto-saved!

obj.saved == True # this is true!

# All of them return an initialized CustomObject() (unless save() raises an exception)
```

## Subclassing to better manage Istio Resources

``` python
import time

from kubeobject import CustomObject
from kubernetes import config

config.load_kube_config()

# Define an Istio type that will hold `CustomObject`s of type Istio.
Istio = CustomObject.define("Istio", plural="istios", api_version="istio.banzaicloud.io/v1beta1")

# Creates a "my-istio" object in the default namespace
obj = Istio("my-istio", "default")
obj["spec"] = {"version": "1.1.0", "mtls": True}

# Save object
obj.create()

# Reload the Custom Object from Kubernetes
obj.reload()

# Gets the current status
assert obj["status"]["Status"] == "Reconciling"

# Waits until object gets to "Available"
obj.auto_reload = True
while obj["status"]["Status"] != "Available":
  print(".", end="", flush=True)
  time.sleep(5)

# Make sure we got away from "Reconciling"
assert obj["status"]["Status"] != "Reconciling"

# And we are actually in "Available"
assert obj["status"]["Status"] == "Available"

# Delete the object
obj.delete()
```

## Creating and updating a Custom Object

* Make sure you apply the `deploy/dummy.crd.yaml` file before trying this!

``` python
from kubeobject import CustomObject, Namespace
from kubernetes import config

config.load_kube_config()

namespace_name = "my-namespace"

if not Namespace.exists(namespace_name):
    print("Namespace does not exist, creating it")
    namespace = Namespace.create(namespace_name)

print("Creating a custom resource from a yaml file")

CustomObject.from_yaml("deploy/dummy.yaml", "my-namespace").load()

dummy = CustomObject("my-dummy-object", namespace_name, api_version="dummy.com/v1", plural="dummies").create()
print("Our dummy object:", dummy["metadata"]["name"])

print("And the answer is:", dummy["spec"]["answer"])

dummy["status"] = {"message": "You have been updated"}
dummy.update()

dummy.delete()
print("Resource has been removed")

namespace.delete()


```

## Creating a Namespace with a ConfigMap and a Secret on it

``` python
from kubeobject import Namespace, Secret, ConfigMap, generate_random_name
from kubernetes import config

config.load_kube_config()

name = generate_random_name(prefix="some-", suffix="-end", size=20)
print("Creating Namespace with name", name)
namespace = Namespace.create(name)

configmap = ConfigMap.create(
    "my-testing-cm",
    namespace.name,
    {"key0": "value0", "key1": "value1"}
)
configmap.update({"key1": "new_value"})

print("ConfigMap Deleted")
configmap.delete()

print("Creating a new Secret")
secret = Secret.create(
    "my-testing-secret",
    namespace.name,
    {"key0": "value0", "key1": "value1"}
)
secret.update({"key1": "my updated value"})

print("Secret Deleted")
secret.delete()

print("Namespace Deleted")
namespace.delete()
```
