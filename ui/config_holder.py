from pz.config import PzProjectConfig


class ConfigHolder:
    config: PzProjectConfig

    def __init__(self, config: PzProjectConfig):
        self.config = config

    def set_config(self, config: PzProjectConfig):
        self.config = config

    def get_config(self) -> PzProjectConfig:
        return self.config
