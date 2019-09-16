from testaccio import KubeObject
from kubernetes import config

config.load_kube_config()

print("Creating a new Replica Set")
my_replica_set = KubeObject.create_from_yaml("replica-set.yaml", "testing-24")

print("Waiting for the Replica Set '{}' to reach Running phase".format(
    my_replica_set["metadata"]["name"]))
my_replica_set.wait_for_phase("Running")

print("Replica Set '{}' reached Running state! Will delete it now".format(
    my_replica_set["namespace"]["name"]))

my_replica_set.delete()
