from base64 import b64decode
from kubernetes import client


class KubeObjectGeneric:
    @classmethod
    def create(cls):
        pass

    @classmethod
    def read(cls):
        pass

    def delete(self):
        pass

    def update(self):
        pass

    @property
    def data(self):
        if isinstance(self, ConfigMap):
            return self.backing_obj.data
        elif isinstance(self, Secret):
            return {
                k: b64decode(v).decode("utf-8")
                for (k, v) in self.backing_obj.data.items()
            }


class ConfigMap(KubeObjectGeneric):
    @classmethod
    def create(cls, name, namespace, data):
        api = client.CoreV1Api()
        metadata = client.V1ObjectMeta(name=name)
        body = client.V1ConfigMap(metadata=metadata, data=data)
        return ConfigMap(
            name, namespace, api.create_namespaced_config_map(namespace, body)
        )

    @classmethod
    def read(cls, name, namespace):
        api = client.CoreV1Api()
        return ConfigMap(
            name, namespace, api.read_namespaced_config_map(name, namespace)
        )

    def __init__(self, name, namespace, backing_obj):
        self.name = name
        self.namespace = namespace
        self.backing_obj = backing_obj

    def delete(self):
        api = client.CoreV1Api()
        body = client.V1DeleteOptions()

        return api.delete_namespaced_config_map(self.name, self.namespace, body=body)

    def update(self, data):
        api = client.CoreV1Api()
        configmap = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(name=self.name), data=data
        )

        self.backing_obj = api.patch_namespaced_config_map(
            self.name, self.namespace, configmap
        )

    def __str__(self):
        return "configmap/{}".format(self.name)


class Secret(KubeObjectGeneric):
    @classmethod
    def create(cls, name, namespace, data):
        api = client.CoreV1Api()
        metadata = client.V1ObjectMeta(name=name)
        body = client.V1Secret(metadata=metadata, string_data=data)
        return Secret(name, namespace, api.create_namespaced_secret(namespace, body))

    @classmethod
    def read(cls, name, namespace):
        api = client.CoreV1Api()
        return Secret(name, namespace, api.read_namespaced_secret(name, namespace))

    def __init__(self, name, namespace, backing_obj):
        self.name = name
        self.namespace = namespace
        self.backing_obj = backing_obj

    def delete(self):
        api = client.CoreV1Api()
        body = client.V1DeleteOptions()

        return api.delete_namespaced_secret(self.name, self.namespace, body=body)

    def update(self, data):
        api = client.CoreV1Api()
        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(name=self.name), string_data=data
        )

        self.backing_obj = api.patch_namespaced_secret(
            self.name, self.namespace, secret
        )

    def __str__(self):
        return "secret/{}".format(self.name)


class Namespace(KubeObjectGeneric):
    @classmethod
    def create(cls, name):
        api = client.CoreV1Api()
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=name))

        return Namespace(name, api.create_namespace(namespace))

    @classmethod
    def exists(cls, name):
        api = client.CoreV1Api()
        try:
            api.read_namespace(name)
        except client.rest.ApiException:
            return False

        return True

    def __init__(self, name, backing_obj):
        self.name = name
        self.backing_obj = backing_obj

    def delete(self):
        api = client.CoreV1Api()
        body = client.V1DeleteOptions()

        return api.delete_namespace(self.name, body=body)

    def __str__(self):
        return "namespace/{}".format(self.name)
