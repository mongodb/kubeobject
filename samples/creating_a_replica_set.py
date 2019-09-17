from kubeobject import CustomObject, Namespace, generate_random_name
from kubernetes import config

# kubeobject does not handle loading Kubernetes configuration
config.load_kube_config()

name = generate_random_name(size=20)
print("Creating a Namespace:", name)
namespace = Namespace.create(name)

print("Creating a new Replica Set")
my_replica_set = CustomObject.from_yaml("replica-set.yaml", namespace.name)

print(
    "Waiting for the Replica Set '{}' to reach Running phase".format(
        my_replica_set["metadata"]["name"]
    )
)
reached = my_replica_set.wait_for_phase("Running", 10)

print(
    "Replica Set '{}' reached Running state? {}! Will delete it now".format(
        my_replica_set["namespace"]["name"], reached
    )
)

my_replica_set.delete()

namespace.delete()
