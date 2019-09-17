# KubeObject

_Easily manage Kubernetes Objects_

KubeObject allows for the management of Kubernetes using a simple object mapper to Rest API objects.

# Examples

## Creating and updating a Custom Object

``` python
from kubeobject import KubeObject

resource = KubeObject.load("mongodb.com", "v1", "mongodb", "my-replica-set", "my-namespace")
print("Current phase is:", resource["status"]["phase"])

resource.delete()
print("Resource has been removed")

print("Creating a custom resource from a yaml file")
resource = KubeObject.from_yaml("replica-set.yaml", "my-namespace")

print("Waiting until custom resource reaches phase Running")
resource.wait_for_phase("Running")

print("Custom resource has reached Running phase")
resource.delete()
```

## Creating a Namespace and ConfigMaps and Secrets on it

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
