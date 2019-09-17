from __future__ import annotations
from .serviceaccount import ServiceAccount

from kubernetes import client


class Role:
    @classmethod
    def create(cls, name, namespace, rules):
        api = client.RbacAuthorizationV1Api()

        body = client.V1Role(
            metadata=client.V1ObjectMeta(name=name, namespace=namespace),
            rules=rules
        )

        return Role(name, namespace, api.create_namespaced_role(namespace, body))

    def __init__(self, name, namespace, backing_obj):
        self.name = name
        self.namespace = namespace
        self.backing_obj = backing_obj


class RoleBinding:
    @classmethod
    def create(cls, name, namespace, role: Role, service_account: ServiceAccount):
        api = client.RbacAuthorizationV1Api()

        # TODO: Look for this info in the role object
        role_ref = client.V1RoleRef(
            api_group="rbac.authorization.k8s.io",
            kind="Role",
            name=role.name,
        )
        # TODO: Same as above
        subjects = [
            client.V1Subject(
                kind="ServiceAccount",
                name=service_account.name,
                namespace=service_account.namespace,
            )
        ]
        body = client.V1RoleBinding(
            metadata=client.V1ObjectMeta(name=name, namespace=namespace),
            role_ref=role_ref,
            subjects=subjects,
        )

        return Role(name, namespace, api.create_namespaced_role_binding(namespace, body))

    def __init__(self, name, namespace, backing_obj):
        self.name = name
        self.namespace = namespace
        self.backing_obj = backing_obj


def build_rules_from_yaml(doc):
    rules = []
    for rule in doc["rules"]:
        api_groups = rule.get("apiGroups", [""])
        resources = rule.get("resources", [""])
        verbs = rule.get("verbs", [""])
        rules.append(
            client.V1PolicyRule(
                api_groups=api_groups,
                resources=resources,
                verbs=verbs,
            )
        )

    return rules
