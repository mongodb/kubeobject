#!/usr/bin/env python

"""example03.py


In this example we'll create a new MongoDB object, using KubeObject.

This example requires the MongoDB community operator to be installed.
More information is available in the README.md file in this directory.
"""

import time
from kubernetes import config, client
from kubeobject import create_custom_object

# We will configure our Kubernetes client using standard `kubectl`
# configuration.
config.load_kube_config()

NAMESPACE = "default"

MongoDB = create_custom_object("mongodbcommunity.mongodbcommunity.mongodb.com")
mdb = MongoDB.read_from_yaml_file(open("examples/mongodb-example03.yaml"))

# This object won't be created because we need to set a password for
# at least one user. We need to create a Secret to do that!

api = client.CoreV1Api()
secret_body = client.V1Secret(
    metadata=client.V1ObjectMeta(name=mdb.spec.users[0].passwordSecretRef.name),
    string_data=dict(password="non-secure"),
)

try:
    secret = api.create_namespaced_secret(namespace=NAMESPACE, body=secret_body)
except client.ApiException as e:
    # We assume secret already exist. Do not fail in that case
    if e.status != 409:
        raise


mdb.create(namespace=NAMESPACE)

# Every time an attribute it read, it will fetch the bound object from the
# Kubernetes API.
mdb.auto_reload = True
while not mdb.status.phase == "Running":
    time.sleep(3)
    print(
        "Waiting for mdb to reach Running phase. Current state is: {}".format(
            mdb.status.phase
        )
    )

print("MongoDB resource has reached Running state")

# Now what do we do with a MongoDB database? We connect to it of course!

print("MongoDB Connection URI is: {}".format(mdb.status.mongoUri))

# The following kubectl command will execute a mongo shell connected to
# our just deployed database.
#

# kubectl exec -it mongo -- mongo --password --username my-user \
#   --host mongodb://example-mongodb-0.example-mongodb-svc.default.svc.cluster.local:27017,example-mongodb-1.example-mongodb-svc.default.svc.cluster.local:27017,example-mongodb-2.example-mongodb-svc.default.svc.cluster.local:27017
