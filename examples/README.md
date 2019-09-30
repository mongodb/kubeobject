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


### Adding a Sample Custom Resource Definition

For examples 01 and 02 we'll use a `Dummy` CRD, which you can install
in your Kubernetes cluster simply by applying the `dummy.crd.yaml` file.

    $ kubectl apply -f dummy.crd.yaml
    customresourcedefinition.apiextensions.k8s.io/dummies.kubeobject.com created

When the `Dummy` object has been created, you can go ahead and run
`example01.py` and `example02.py`.

### Installing the Istio Operator

I built this module while building the MongoDB Operator, but to not be
biased, I have created a few samples using the Istio Operator and CRD.

The easiest way of installing the Istio Operator is to do it from
[operatorhub](https://operatorhub.io/operator/istio). Click on the
"Install" button and follow the instructions. This is as simple as
installing OLM (Operator Lifecycle Management) and finally apply a
yaml file with the Istio Operator installation.

This step will allow you to run `example03.py` and `example04.py`.
