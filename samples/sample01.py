from kubeobject import Namespace, Secret, ConfigMap, generate_random_name
from kubernetes import config

config.load_kube_config()

name = generate_random_name(prefix="some-", suffix="-end", size=20)
print("Creating Namespace with name", name)
namespace = Namespace.create(name)

configmap = ConfigMap.create(
    "my-testing-cm", namespace.name, {"key0": "value0", "key1": "value1"}
)

print(configmap.data)

configmap.update({"key1": "new_value"})
print("ConfigMap Updated: ", configmap.data)

print("ConfigMap Deleted")
configmap.delete()

print("Creating a new Secret")
secret = Secret.create(
    "my-testing-secret", namespace.name, {"key0": "value0", "key1": "value1"}
)

secret.update({"key1": "my updated value"})
print("Secret Updated", secret.data)

print("Secret Deleted")
secret.delete()

print("Namespace Deleted")
namespace.delete()
