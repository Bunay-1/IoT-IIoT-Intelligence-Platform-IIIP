import pandas as pd


class MultiTenantResourceManagement:
    def __init__(self, tenant_data):
        """
        Инициализира управлението на ресурсите за множество тенанти.
        Args:
            tenant_data (DataFrame): Данни за тенантите.
        """
        self.tenant_data = tenant_data

    def allocate_resources(self):
        """
        Разпределя ресурсите между тенантите.
        """
        resource_allocation = self.tenant_data.groupby("tenant_id").apply(
            lambda x: x.sum() / len(self.tenant_data), axis=1
        )
        return resource_allocation

    def monitor_usage(self):
        """
        Мониторинг на използването на ресурсите.
        """
        resource_usage = self.tenant_data.groupby("tenant_id").apply(
            lambda x: x.sum() / len(self.tenant_data), axis=1
        )
        print("Resource Usage:")
        print(resource_usage)

    def ensure_isolation(self):
        """
        Осигурява безопасността между данните на тенантите.
        """
        for tenant_id in self.tenant_data["tenant_id"].unique():
            tenant_resources = self.tenant_data[
                self.tenant_data["tenant_id"] == tenant_id
            ]
            other_tenants_resources = self.tenant_data[
                self.tenant_data["tenant_id"] != tenant_id
            ]
            isolated_resources = tenant_resources.apply(lambda x: x - x.mean(), axis=1)
            if not isolated_resources.empty:
                raise ValueError(f"Resources for tenant {tenant_id} are not isolated!")


# Пример данни за демонстрация
tenant_data = pd.DataFrame(
    {
        "tenant_id": ["tenant_1", "tenant_2", "tenant_3"],
        "resource_1": [100, 200, 300],
        "resource_2": [150, 250, 350],
    }
)

# Създаване и стартиране на управлението на ресурсите
resource_management = MultiTenantResourceManagement(tenant_data)
allocation = resource_management.allocate_resources()
usage = resource_management.monitor_usage()
isolation = resource_management.ensure_isolation()
