from src.utils.path_finder import PathFinder
from src.openstreetmap.tags import TagsConfig
from osmnx import settings

class Config:
    TAGS_PATH = PathFinder.find('tags.yaml')
    POPULATION_PATH = PathFinder.find('lviv_obl_population.csv')
    ROUTINES_PATH = PathFinder.find('routines.yaml')

    @staticmethod
    def configure_osmnx():
        # Set cache path
        settings.use_cache = True
        settings.cache_folder = PathFinder.find('cache')
        # osmnx.config(log_file=PathFinder.find('osmnx.log'))
