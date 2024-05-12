import multiprocessing
import shapely
from src.openstreetmap.custompolygon import CustomPolygon, PolygonUtils
from src.openstreetmap.tags import TagsConfig
from src.utils.agent_places import AgentPlaces

from multiprocessing import Pool


def preload_worker_polygon(args: tuple[str, int]):
    location, match_result = args
    custom_polygon = OSMPreloader.load_polygon(location, match_result)
    return (
        location,
        custom_polygon
    )


def preload_worker_place(args :tuple[str, CustomPolygon, str, dict]):
    location, custom_polygon, tag, tags = args

    result = PolygonUtils.get_features_geometry_points(
        custom_polygon.polygon,
        tags
    )

    return (
        location,
        tag,
        result
    )


class OSMPreloader:
    def __init__(self, tags: TagsConfig, places: AgentPlaces):
        self.tags = tags
        self.places = places

    @staticmethod
    def fix_location(location: str | tuple[str, int]):
        if isinstance(location, tuple):
            if len(location) != 2:
                raise Exception('Invalid Tuple. Expected: str, int')
            return location  # location, match_result
        return location, 1

    @staticmethod
    def load_polygon(location: str, match_result: int):
        return CustomPolygon(location, match_result)

    def chunk_locations_to_places(self, custom_polygons: list[tuple[str, shapely.Polygon]]):
        for location, polygon in custom_polygons:
            for place in self.places.raw().values():
                tag = place['tag']
                yield location, polygon, tag, self.tags[tag]

    def preload(self, locations: list[str | tuple[str, int]]):
        result = {}  # dict[location, {"polygon": CustomPolygon, "Places": dict[tag, DataFrame]}]
        # 0. fix locations
        locations = [self.fix_location(loc) for loc in locations]

        # 1. Preload polygons
        print('[OSMPreloader] Loading Polygons... ', end='')
        with Pool(multiprocessing.cpu_count()) as pool:
            for location, custom_polygon in pool.map(preload_worker_polygon, locations):
                result[location] = {
                    "polygon": custom_polygon,
                    "places": {}
                }

        # 2. Preload places
        print('Done!\n[OSMPreloader] Loading Places... ', end='')
        places_to_preload = self.chunk_locations_to_places([(location, result[location]["polygon"]) for location in result])
        with Pool(multiprocessing.cpu_count()) as pool:
            for location, tag, df in pool.map(preload_worker_place, places_to_preload):
                result[location]["places"][tag] = df

        # # DEBUG TAGS & PLACES
        #
        # import pandas as pd
        # from src.utils.path_finder import PathFinder
        #
        # omited_columns = ['representative_point', 'geometry', 'geometry_point', 'geometry_point_str', 'osmid']
        # for raion_name, raion in result.items():
        #     str_res = []
        #
        #     result = {
        #         # tag: {
        #         #    column: {
        #         #      item_type: count
        #         #    }
        #         # }
        #     }
        #
        #     for tag, df in raion['places'].items():
        #         columns = df.columns
        #         for column in columns:
        #             if column in omited_columns:
        #                 continue
        #
        #             item_types = df[column].unique()
        #             # filter not nan values
        #             item_types = item_types[~pd.isna(item_types)]
        #             for item_type in item_types:
        #                 if item_type is None:
        #                     continue
        #
        #                 if tag not in result:
        #                     result[tag] = {}
        #                 if column not in result[tag]:
        #                     result[tag][column] = {}
        #                 if item_type not in result[tag][column]:
        #                     result[tag][column][item_type] = 0
        #
        #                 result[tag][column][item_type] += len(df[df[column] == item_type])
        #
        #     total_items = 0
        #     for tag, columns in result.items():
        #         tag_amount = 0
        #         column_amount = 0
        #         tmp_str_res = []
        #
        #         for column, value in columns.items():
        #             for item_type, count in value.items():
        #                 column_amount += count
        #                 tmp_str_res.append(f'    • {item_type}: {count}')
        #             tmp_str_res.append(f'  >> {column} ({column_amount}) ]==')
        #             tag_amount += column_amount
        #         tmp_str_res.append(f'\n==[ Tag: {tag} ({tag_amount})]==')
        #         str_res.extend(reversed(tmp_str_res))
        #         total_items += tag_amount
        #
        #     write_path = PathFinder.find(f'tmp/{raion_name}.txt')
        #     with open(write_path, 'w') as f:
        #         f.write('\n'.join([
        #             f'==[ Raion: {raion_name} ({total_items})] ==\n',
        #             *str_res
        #         ]))

        print('Done!')

        return result
