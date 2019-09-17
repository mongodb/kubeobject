# KubeObject

_Easily manage Kubernetes Objects_

KubeObject allows for the management of Kubernetes using a simple object mapper to Rest API objects.

# Example

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
