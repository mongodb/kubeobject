from __future__ import annotations

from kubernetes import client


class ServiceAccount:
    @classmethod
    def create(cls, name, namespace):
        api = client.CoreV1Api()
        body = client.V1ServiceAccount(
            metadata=client.V1ObjectMeta(name=name, namespace=namespace)
        )

        return ServiceAccount(name, namespace, api.create_namespaced_service_account(namespace, body=body))

    def __init__(self, name, namespace, backing_obj):
        self.name = name
        self.namespace = namespace
        self.backing_obj = backing_obj

    def delete(self):
        api = client.CoreV1Api()

        return api.delete_namespaced_service_account(self.name, self.namespace, client.V1DeleteOptions())
