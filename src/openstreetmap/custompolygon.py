import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import pandas as pd
import shapely


class CustomPolygon:
    def __init__(self, location: str | list, match_result: int = 1):
        self.location = location
        self.gdf = ox.geocode_to_gdf(self.location, which_result=match_result)
        self.polygon = self.gdf.unary_union

    def get_bounds(self):
        return dict(zip(['x_min', 'y_min', 'x_max', 'y_max'], self.polygon.bounds))

    def get_polygon_of_area(self,):
        return self.polygon

    def get_network_from_polygon(self, network_type):
        return ox.graph_from_polygon(self.polygon, network_type=network_type, truncate_by_edge=True)

    @staticmethod
    def plot_multi_graph_obj(multi_graph):
        gpd.GeoSeries(multi_graph).plot()
        plt.show()

    @staticmethod
    def plot_road_network(road_network):
        _, _ = ox.plot_graph(road_network)
        plt.show()

    @staticmethod
    def polygon_to_gdf(polygon):
        return gpd.GeoDataFrame(geometry=[polygon], crs=4326)

    @staticmethod
    def save_html_map(gpd_polygon, file_name):
        html_map = gpd_polygon.explore(color='red')
        html_map.save(f'{file_name}.html')


class PolygonUtils:
    def __init__(self, polygon: shapely.Polygon):
        self.polygon = polygon


    def get_raw_features(self, tags):
        return ox.features_from_polygon(self.polygon, tags)


    @staticmethod
    def __filter_dataframe(df: gpd.GeoDataFrame, dict_values: dict) -> gpd.GeoDataFrame:
        """
        Filter dataframe by values in dict_values
        :param df:
        :param dict_values:
        :return:
        """
        for key in dict_values:
            value = dict_values[key]

            if isinstance(value, bool) and value:
                continue
            elif key not in df.columns:
                continue

            df[key] = df[key].where(df[key].isin(value), np.nan)
        return df

    @staticmethod
    def __check_overlap(df: gpd.GeoDataFrame, dict_values: dict) -> gpd.GeoDataFrame:
        """
        Delete rows with any overlaps
        :param df:
        :param dict_values:
        :return:
        """
        columns = list(dict_values.keys())
        overlap_indexes = []
        for i, row in df.iterrows():
            non_null_columns = [col for col in columns if pd.notna(row[col])]
            if len(non_null_columns) > 1:
                overlap_indexes.append(i)

        df_without_overlap = df.drop(overlap_indexes)
        return df_without_overlap

    @staticmethod
    def get_features_geometry_points(polygon, tags: dict) -> gpd.GeoDataFrame:

        features = ox.features_from_polygon(polygon, tags)

        tags_columns = list(tags.keys())

        features = features[['geometry', *tags_columns]]

        features['representative_point'] = features['geometry'].apply(PolygonUtils.get_representative_point)

        features = features.drop(columns=['geometry'], axis=1)

        features = PolygonUtils.__filter_dataframe(features, tags)
        features = PolygonUtils.__check_overlap(features, tags)

        return features

    @staticmethod
    def prepare_housing_df(df: gpd.GeoDataFrame | pd.DataFrame, tags: dict) -> gpd.GeoDataFrame:
        columns_to_marge = list(tags.keys())
        df['home'] = df[columns_to_marge].bfill(axis=1).iloc[:, 0]
        return df.drop(columns=columns_to_marge)


    @staticmethod
    def save_to_csv(df: gpd.GeoDataFrame | pd.DataFrame, file_name: str):
        df.to_csv(f'{file_name}.csv')

    @staticmethod
    def get_columns(features_polygon) -> list[str]:
        return list(features_polygon.columns)

    @staticmethod
    def get_representative_point(geometry):
        if geometry.geom_type == 'Point':
            return geometry
        else:
            return geometry.representative_point()
