from __future__ import annotations

from .serviceaccount import ServiceAccount

from kubernetes import client


class Deployment:
    @classmethod
    def create(cls, name, namespace, service_account: ServiceAccount):
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
                            image="quay.io/mongodb/mongodb-enterprise-operator:1.2.3",
                            image_pull_policy="IfNotPresent",
                            env=[
                                client.V1EnvVar(
                                    name="OPERATOR_ENV",
                                    value="dev",
                                ),
                                client.V1EnvVar(
                                    name="WATCH_NAMESPACE",
                                    value=namespace,
                                ),
                                client.V1EnvVar(
                                    name="CURRENT_NAMESPACE",
                                    value=namespace,
                                ),
                                client.V1EnvVar(
                                    name="MANAGED_SECURITY_CONTEXT",
                                    value="true",
                                ),
                                client.V1EnvVar(
                                    name="MONGODB_ENTERPRISE_DATABASE_IMAGE",
                                    value="quay.io/mongodb/mongodb-enterprise-database:1.2.3"
                                ),
                                client.V1EnvVar(
                                    name="IMAGE_PULL_POLICY",
                                    value="Always"
                                ),
                                client.V1EnvVar(
                                    name="OPS_MANAGER_IMAGE_REPOSITORY",
                                    value="",
                                ),
                                client.V1EnvVar(
                                    name="OPS_MANAGER_IMAGE_PULL_POLICY",
                                    value="",
                                ),
                            ],
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
