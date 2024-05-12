import random
from enum import IntEnum

import pandas as pd


class HumanAge(IntEnum):
    Newborn = 1
    Preschooler = 2
    Kid = 3
    Teenager = 4
    Adult = 5
    Elderly = 6

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.name)

    @staticmethod
    def from_string(string: str):
        mapping = {
            'newborn': HumanAge.Newborn,
            'preschooler': HumanAge.Preschooler,
            'kid': HumanAge.Kid,
            'teenager': HumanAge.Teenager,
            'adult': HumanAge.Adult,
            'elderly': HumanAge.Elderly
        }

        try:
            return mapping[string.lower()]
        except Exception as e:
            return None


class HumanAgeGroup:
    AGE_CUTS = [-1, 2, 5, 17, 21, 64, 100]
    AGE_OPTIONS = list(range(0, 101))
    AGE_DISTRIBUTIONS = None

    @staticmethod
    def init(population_file_path: str, age_sum_column: str = 'sum'):
        population_distribution = pd.read_csv(population_file_path)
        total_residence = population_distribution[age_sum_column].sum()
        population_distribution['proportion'] = population_distribution[age_sum_column] / total_residence
        HumanAgeGroup.AGE_DISTRIBUTIONS = population_distribution['proportion'].tolist()

    @staticmethod
    def set_age_group(age: int):
        age_group = HumanAgeGroup.AGE_CUTS
        if age <= age_group[1]:
            return HumanAge.Newborn
        elif age <= age_group[2]:
            return HumanAge.Preschooler
        elif age <= age_group[3]:
            return HumanAge.Kid
        elif age <= age_group[4]:
            return HumanAge.Teenager
        elif age <= age_group[5]:
            return HumanAge.Adult
        return HumanAge.Elderly

    @staticmethod
    def set_random_init_age():
        if not HumanAgeGroup:
            raise '[HumanAgeGroup] Not initialized'
        return random.choices(HumanAgeGroup.AGE_OPTIONS, HumanAgeGroup.AGE_DISTRIBUTIONS).pop()
