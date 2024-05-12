from os.path import abspath, join, dirname as up


class PathFinder:
    @staticmethod
    def root_path():
        current_file_folder = up(abspath(__file__))
        return up(up(current_file_folder))

    @staticmethod
    def find(file_name):
        return join(PathFinder.root_path(), file_name)