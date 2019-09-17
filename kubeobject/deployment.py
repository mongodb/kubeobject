from __future__ import annotations

from .serviceaccount import ServiceAccount

from kubernetes import client


class Deployment:
    """This is a super simple Deployment wrapper. The only reason it is here it is because I will use it
    to deploy the MongoDB Kubernetes Operator.
    """
    @classmethod
    def create(cls, name, namespace, service_account: ServiceAccount, container_image, env) -> Deployment:
        api = client.AppsV1Api()
        spec = client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={"app": name},
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={"app": name},
                ),
                spec=client.V1PodSpec(
                    service_account_name=service_account.name,
                    containers=[
                        client.V1Container(
                            name=name,
                            image=container_image,
                            image_pull_policy="IfNotPresent",
                            env=env,
                        ),
                    ],
                ),
            )
        )
        body = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=namespace,
            ),
            spec=spec,
        )

        return Deployment(name, namespace, api.create_namespaced_deployment(namespace, body))

    def __init__(self, name, namespace, backing_obj):
        self.name = name
        self.namespace = namespace
        self.backing_obj = backing_obj
