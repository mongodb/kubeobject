# KubeObject

_Easily manage Kubernetes Objects_

KubeObject allows for the management of Kubernetes using a simple object mapper to Rest API objects.

# Examples

## Creating and updating a Custom Object

* Make sure you apply the `deploy/dummy.crd.yaml` file before trying this!

``` python
from kubeobject import CustomObject, Namespace
from kubernetes import config

config.load_kube_config()

namespace_name = "my-namespace"

if not Namespace.exists(namespace_name):
    print("Namespace does not exist, creating it")
    Namespace.create(namespace_name)

print("Creating a custom resource from a yaml file")

# TODO: replace the following `plural` attribute by fetching this plural name
# from CRD API.
CustomObject.from_yaml("deploy/dummy.yaml", namespace=namespace_name, plural="dummies")

dummy = CustomObject.load("kubeobject.com", "v1", "dummies", "my-dummy-object", namespace_name)
print("Our dummy object:", dummy["metadata"]["name"])

print("And the answer is:", dummy["spec"]["answer"])

dummy["status"] = {"message": "You have been updated"}
dummy.save()

dummy.delete()
print("Resource has been removed")
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
