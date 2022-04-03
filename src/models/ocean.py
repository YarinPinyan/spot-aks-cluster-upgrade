# region Ocean

class Ocean:
    """
    # Arguments
    id: str
    name: str
    controller_cluster_id: str
    aks: Aks
    auto_scaler: AutoScaler
    health: Health
    strategy: Strategy
    virtual_node_group_template: Json
    """

    def __init__(
            self,
            name=None,
            controller_cluster_id=None,
            aks=None,
            auto_scaler=None,
            health=None,
            strategy=None,
            virtual_node_group_template=None):
        self.name = name
        self.controller_cluster_id = controller_cluster_id
        self.aks = aks
        self.auto_scaler = auto_scaler
        self.virtual_node_group_template = virtual_node_group_template
        self.strategy = strategy
        self.health = health


# endregion

class Aks:
    """
    # Arguments
    name: str
    resource_group_name: str
    """

    def __init__(self, name=None, resource_group_name=None):
        self.name = name
        self.resource_group_name = resource_group_name


# region AutoScaler
class AutoScaler:
    """
        # Arguments
        is_enabled: bool
        cooldown: int
        resource_limits: ResourceLimits
        down: Down
        headroom: Headroom
        is_auto_config: bool
        """

    def __init__(
            self,
            is_enabled=None,
            cooldown=None,
            resource_limits=None,
            down=None,
            headroom=None,
            is_auto_config=None):
        self.is_enabled = is_enabled
        self.cooldown = cooldown
        self.resource_limits = resource_limits
        self.down = down
        self.headroom = headroom
        self.is_auto_config = is_auto_config


class ResourceLimits:
    """
        # Arguments
        max_memory_gib: nint
        max_vCpu: int
        """

    def __init__(
            self,
            max_memory_gib=None,
            max_vCpu=None):
        self.max_memory_gib = max_memory_gib
        self.max_vCpu = max_vCpu


class Down:
    """
        # Arguments
        evaluation_periods: int
        """

    def __init__(
            self,
            evaluation_periods=None):
        self.evaluation_periods = evaluation_periods


class Headroom:
    """
        # Arguments
        cpu_per_unit: int
        memory_per_unit: int
        num_of_units: int
        """

    def __init__(
            self,
            cpu_per_unit=None,
            memory_per_unit=None,
            num_of_units=None):
        self.cpu_per_unit = cpu_per_unit
        self.memory_per_unit = memory_per_unit
        self.num_of_units = num_of_units
# endregion
