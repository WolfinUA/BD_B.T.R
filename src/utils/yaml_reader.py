import yaml


class YamlReader:
    def __init__(self, file_path, storable=False):
        self.__file_path = file_path
        self._storable = storable
        self._data = None

    def read(self, with_root=None, transform=None):
        with open(self.__file_path) as file:
            data = yaml.safe_load(file)
            if with_root:
                data = data[with_root]

            if transform:
                data = transform(data)

            if self._storable:
                self._data = data

            return data

    def data(self):
        return self._data

    def __getitem__(self, key):
        if not self._storable or not self._data:
            raise '[YamlReader] Error: File not read. Use `read()` before calling this method'
        if key not in self._data:
            raise f'[YamlReader] Missing key: {key}'
        return self._data[key]
