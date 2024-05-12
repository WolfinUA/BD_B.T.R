import random

import pandas as pd
import shapely

from src.config import Config
from src.utils.agent_places import AgentPlaces
from src.utils.random_points import RandomPoint
from src.utils.yaml_reader import YamlReader


class Routine:
    def __init__(self, places: dict[str, shapely.Point], routines: dict):
        self.__places = places
        self.__routines = routines
        self.__current_routine = None
        self.__current_age_group = None
        self.__current_day_type = None

        # Routine not defined for weekday or weekend
        self.__no_day_type_routine = False

    def update(self, age_group, day_type):
        if self.__current_age_group is None or \
                self.__current_routine is None or \
                self.__current_age_group != age_group or \
                self.__current_day_type != day_type:
            # Reset
            self.__reset(age_group, day_type)

    def __reset(self, age_group, day_type):
        self.__no_day_type_routine = False

        self.__current_age_group = age_group
        self.__current_day_type = day_type

        age = str(age_group).lower()
        routines = self.__routines[age][day_type]

        if not routines:
            print(f'[Routine] Missing routines: {age} | {day_type}')

        self.__current_routine = random.choice(routines)
        if self.__current_routine is None:
            self.__no_day_type_routine = True

    def __set_no_routine(self, day_type):
        if day_type == 'weekday':
            self.__no_weekday_routine = True
        else:
            self.__no_weekend_routine = True

    def current_place(self, hour):
        if self.__no_day_type_routine:
            return None
        elif not self.__current_routine:
            print('[Routine] Step is not defined')
            return None
        elif hour not in self.__current_routine:
            return None

        place = self.__current_routine[hour]
        if isinstance(place, list):
            place = random.choice(place)

        return self.__place2point(place)

    def __place2point(self, place):
        try:
            return self.__places[place]
        except KeyError:
            print(f'[Routine] Invalid place: {place}')
            return None


class AgentRoutine:
    def __init__(self,
                 store: dict,
                 config_path: str | None = None,
                 ):
        self.__places = AgentPlaces.new(Config.ROUTINES_PATH).raw()
        self.__store = store
        self.__locations = list(store.keys())

        yaml_reader = YamlReader(config_path)
        self.__routines = yaml_reader.read('routines')

        # load points for each kind of place
        # for tag in self.__places:
        #
        #     if tag not in tags:
        #         raise Exception(f'Unknown tag: {tag}')
        #     elif tag not in kwargs:
        #         raise Exception(f'Missing DataFrame for place: {tag}')
        #
        #     self.__dfs[tag] = kwargs[tag]

    def __map_routine(self, amount=1):
        routines = self.__routines.copy()
        for age, week in self.__routines.items():
            for day_type, possible_routines in week.items():
                if possible_routines is not None:
                    routines[age][day_type] = random.choices(possible_routines, k=amount)

        return routines

    def __map_place(self, place, raion, home_point: shapely.Point) -> shapely.Point | list[shapely.Point]:
        if place['type'] == 'home':
            return home_point

        scope = place['scope']

        if place['type'] == 'single':
            df = self.__find_df_in_scope(place['tag'], raion, scope)
            return RandomPoint.single(df)
        elif place['type'] == 'multiple':
            amount = place['amount']
            if not isinstance(amount, int):
                raise Exception('Invalid amount type. Expected: int')
            elif amount < 1:
                raise Exception('Invalid amount value. Expected at least 1')
            if scope == 'local':
                return RandomPoint.multiple(self.__store[raion]['places'][place['tag']], amount)
            elif scope == 'global':
                for i in range(amount):
                    df = self.__find_df_in_scope(place['tag'], raion, scope)
                    return RandomPoint.single(df)

    def __find_df_in_scope(self, tag, raion, scope='local') -> pd.DataFrame:
        if scope == 'local':
            return self.__store[raion]['places'][tag]
        elif scope == 'global':
            random_raion = random.choice(self.__locations)
            return self.__store[random_raion]['places'][tag]
        else:
            raise Exception('Invalid scope value. Expected: local | global')

    def generate(self, home_point: shapely.Point, raion: str):
        places = {}  # dict[str, shapely.Point | list[shapely.Point]]
        for _, place in self.__places.items():
            places[place['tag']] = self.__map_place(place, raion, home_point)

        return Routine(places, self.__map_routine())
