# Examples

There are a few examples here that can help you to start using
`kubeobject`.

## Prerequisites


### Installing a local Kubernetes Cluster
You need a running Kubernetes cluster, and a configured `kubectl` and
you are all set. I've been using
[kind](https://github.com/kubernetes-sigs/kind) for a while now and it
gives you everything you need. First [install
kind](https://kind.sigs.k8s.io/docs/user/quick-start/) and then create
a cluster, test your `kubectl` configuration by running:

    kubectl cluster-info


### Installing the MongoDB Community Operator

In the following examples, we'll use the MongoDB Community Operator, that will
allow us to deploy MongoDB databases into our cluster.

1. Visit [the official
   documentation](https://github.com/mongodb/mongodb-kubernetes-operator/blob/master/docs/install-upgrade.md)
   and install the Operator from there.

And that's basically all of it, now you can proceed to see the example files and
manage MongoDB resources with `KubeObject`.
