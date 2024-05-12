from src.utils.deep_merge import deep_merge
from src.utils.yaml_reader import YamlReader


class TagsConfig:
    def __init__(self, file_path):
        self.__yr = YamlReader(file_path, storable=True)
        self.reload()

    def __validate_and_fix(self, data):
        self.__validate(data)
        return self.__config_merge(data)

    def reload(self):
        return self.__yr.read(with_root='tags', transform=lambda data: self.__validate_and_fix(data))

    @staticmethod
    def __validate(config):
        if config is None:
            return False

        for key in ['list', 'selected']:
            try:
                config[key]
            except KeyError:
                return False

    @staticmethod
    def __config_merge(config, config_key='selected'):
        for key, to_merge in config[config_key].items():
            merged = {}
            if isinstance(to_merge, list):
                for item in to_merge:
                    merged = deep_merge(item, merged)
            config[config_key][key] = merged
        return config

    def __getattr__(self, item):
        return self.__yr.data()['selected'][item]

    def __getitem__(self, key):
        return self.__yr.data()['selected'][key]

    def __contains__(self, item):
        return item in self.__yr.data()['selected']

    def __iter__(self):
        for key in self.__yr.data()['selected']:
            yield key
