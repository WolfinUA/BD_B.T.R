from src.utils.yaml_reader import YamlReader


class AgentPlaces:
    PLACES = None
    def __init__(self, config_path=None):
        if AgentPlaces.PLACES:
            self.__places = AgentPlaces.PLACES
        elif config_path:
            yaml_reader = YamlReader(config_path)
            places =  yaml_reader.read(with_root='places')

            for name in places:
                place = places[name]
                tag = place['tag']

                if name != tag:
                    raise Exception(
                        f'For performance purposes places must contain hashmap with same KEY and TAG.\nFound: Key ({name}) != Tag ({place.tag})')
            AgentPlaces.PLACES = places
            self.__places = places
        else:
            raise Exception('[AgentPlaces] Missing `config_path`')


    def __getitem__(self, item):
        return self.__places[item]

    def __getattr__(self, item):
        return self.__places[item]

    def __iter__(self):
        for _, place in self.__places.items():
            yield place

    def raw(self):
        return self.__places

    @staticmethod
    def new(config_path=None):
        return AgentPlaces(config_path)
