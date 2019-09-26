# KubeObject

_A simple to use wrapping on top of Kubernetes custom resources with
object oriented semantics._

KubeObject allows you to use Kubernetes objects in a object oriented
way. Currently this library is capable of managing `CustomResource`s,
`ConfigMap`s, `Secret`s and `Namespace`s.

It tries to simplify your life by defining a few methods that work
everywhere the same. These are: `create`, `update`, `delete` and
`from_yaml`, and they are supposed to hide the complexity and
differences in the Kubernetes Python client.

For instance, to create a Python object to manage an Istio
`CustomResource` you will do:

``` python
# Builds the object, but it is "unbound", this is, it is not referring to an actual object in Kubernetes.
istio = CustomObject("my-istio", "my-namespace", plural="istios", api_version="istio.banzaicloud.io/v1beta1")

# Let's pass the simplest object we can
istio["spec"] = {"version": "1.1.0", "mtls": True}

# And now create it; after creation the object is "bound"
istio.create()
```

Updating the object's `Spec` and checking the object's `Status` is one
of our goals as well, like in the following example:

``` python
# The Istio operator should have started working on deploying this new Custom Resource
# Let's get the status of the object
print(istio["status"])

# This is empty, because since calling `create()` we have not updated from the actual object in Kubernetes
# Let's get an up-to-date object
istio.reload()

# I want to avoid calling `reload()` everytime I need a new version
istio.auto_reload = True

# Now we'll wait until the object has reached a given status:
while istio["status"]["Status"] == "Reconciling": time.sleep(5)

# Check the Status after "Reconciling"
print("Our status is:", istio["status"]["Status"])  # The Status will be "Succeeded"
```

After doing all its work, the `Istio` object might need to be deleted:

``` python
istio.delete()
```

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
    namespace = Namespace(namespace_name).create()

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
namespace = Namespace(name).create()

# We will create a ConfigMap in the namespace we just created
configmap = ConfigMap("my-testing-cm", namespace.name).create()
configmap.data({"key0": "value0", "key1": "value1"})
configmap.update()

# We update the value of one of the key
configmap.data({"key1": "new_value"})
configmap.update()

# Removes the ConfigMap from Kubernetes
configmap.delete()

# Creates a new Secret
secret = Secret("my-testing-secret", namespace.name).create()

# We use values with type string, they will be base64 encoded for us
secret.data({"key0": "value0", "key1": "value1"})
secret.update()

# When getting the data, it will be decoded from base64 back into strings for us
assert secret.data()["key1"] == "value1"

# Removes the Secret
secret.delete()

# Removes the Namespace
namespace.delete()
```
