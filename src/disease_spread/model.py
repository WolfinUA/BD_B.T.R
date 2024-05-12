import random

import mesa
import mesa_geo as mg
import geopandas as gpd
import shapely
from geopandas import GeoDataFrame

from src.config import Config
from src.disease_spread.agent import Human
from src.disease_spread.sector_agent import SectorAgent
from src.openstreetmap.custompolygon import CustomPolygon, PolygonUtils
from src.openstreetmap.mapping.housing import HOUSING_MAPPING
from src.openstreetmap.tags import TagsConfig
from src.utils.agent_routines import AgentRoutine, Routine
from src.utils.human_age import HumanAgeGroup, HumanAge
from src.utils.human_state import HumanState
from src.utils.random_points import RandomPoint


class TuberculosisSpread(mesa.Model):
    """
    A model for simulating the spread of tuberculosis.
    """

    def __init__(
            self,
            store: dict[str, dict[str, gpd.GeoDataFrame | CustomPolygon]],
            tags: TagsConfig,
            exposure_distance,
            infected_percentage,
            routine_creator: AgentRoutine
    ):
        """
        Create a new tuberculosis spread model.
        Args:
            width, height: The size of the grid to model
        """
        super().__init__()
        self.store = store
        self.tags = tags

        # Preload data from files
        HumanAgeGroup.init(Config.POPULATION_PATH)

        # self.schedule = mesa.time.RandomActivation(self)
        self.schedule = mesa.time.BaseScheduler(self)
        self.space = mg.GeoSpace('epsg:4326')

        self.step_per_day = 24  # Simulation step set to 24 hours. Base value is 1 corresponding to a day
        self.birth_coefficient = 9.2

        self.exposure_distance = exposure_distance
        self.routine_creator = routine_creator

        self.datacollector = mesa.DataCollector(self.__data_collector())
        self.pending_newborns = []

        # Add sectors

        # Add people to the model
        print('[TuberculosisSpread] Placing Human Agents...', end=' ')
        self.__place_agents(infected_percentage)
        print('Done!')

        # Add sectors to the model | Sectors are added after people to avoid intersection checks
        print('[TuberculosisSpread] Placing Sector Agents...', end=' ')

        for raion_name, raion in store.items():
            self.__add_sector(raion['polygon'].gdf, raion_name)

        print('Done!')

        self.running = True
        self.datacollector.collect(self)
        print(f'Total agents: {len(self.space.agents)}')
        print('Model is ready')

    def __place_agents(self, infected_percentage: float):
        person_index = 0
        self.sector_factory = mg.AgentCreator(SectorAgent, model=self)
        for raion_name, raion in self.store.items():
            housing_df = PolygonUtils.prepare_housing_df(raion['places']['home'], self.tags['home'])

            for row in housing_df.itertuples():
                # In this case, we can omit try-except construction, because we expect error here ;D
                amount_per_building = HOUSING_MAPPING[row.home]
                home_point = row.representative_point
                human_life_routine = self.routine_creator.generate(home_point, raion_name)

                for i in range(amount_per_building):
                    agent: Human = self.__add_human(f"H_{i}_{person_index}", home_point, human_life_routine)

                    # Change to normal infected distribution
                    # TODO Change to distribution all_agents * 11/25000
                    if random.uniform(a=0, b=100) < infected_percentage:
                        agent.condition = HumanState.PrimaryTuberculosis

                    person_index += 1

    def __data_collector(self):
        keys = HumanState.all()
        values = map(lambda key: (lambda m: self.count_type(m, key)), keys)

        return dict(zip(keys, values))

    def __add_sector(self, gdf: GeoDataFrame, group_prefix):
        sector_agents: list[SectorAgent] = self.sector_factory.from_GeoDataFrame(gdf)

        for agent in sector_agents:
            agent.unique_id = f"{group_prefix}_{agent.unique_id}"
            self.space.add_agents(agent)
            self.schedule.add(agent)

        return sector_agents

    def __add_human(self, unique_id, point: shapely.Point, agent_routines: Routine):
        agent = Human(
            unique_id=unique_id,
            model=self,
            geometry=point,
            crs=self.space.crs,
            exposure_distance=self.exposure_distance,
            routines=agent_routines
        )

        self.space.add_agents(agent)
        self.schedule.add(agent)

        return agent

    def __add_newborn_agent(self, newborn_id: str, housing_key='home'):
        """
        Add a new agents to the model.
        Args:
        """
        raion = random.choice(list(self.store.keys()))
        housing_df = PolygonUtils.prepare_housing_df(self.store[raion]['places'][housing_key], self.tags[housing_key])

        home_point = RandomPoint.single(housing_df)
        agent_routine = self.routine_creator.generate(home_point, raion)
        agent = self.__add_human(newborn_id, home_point, agent_routine)
        agent.steps_lived = 0
        agent.human_age_group = HumanAge.Newborn

    def __generate_newborn_birthdays(self):
        year_duration = 365 * self.step_per_day
        total_alive = self.count_type(self, HumanState.Death, invert=True)
        total_newborns_per_year = int(total_alive / 1000 * self.birth_coefficient)
        return [
            random.randint(self.schedule.steps, year_duration + self.schedule.steps - 1)
            for _ in range(total_newborns_per_year)
        ]

    def __try_to_add_newborn(self):
        if self.schedule.steps in self.pending_newborns:
            total_agents = len(self.space.agents)
            amount = self.pending_newborns.count(self.schedule.steps)
            print(f'Adding {amount} newborns to the model. Total agents: {total_agents}')
            for i in range(amount):
                self.__add_newborn_agent(f"NB_{total_agents}_{i}")

    def __schedule_newborns(self):
        birthdays = self.__generate_newborn_birthdays()
        self.pending_newborns.extend(birthdays)
        return len(birthdays)

    def step(self):
        """
        Advance the model by one step.
        """
        # print(f'Infected: {self.count_type(self, HumanState.PrimaryTuberculosis), self.count_type(self, HumanState.PostPrimaryTuberculosis)}')
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

        # Check for newborns and add them
        if self.schedule.steps % (365 * self.step_per_day) == 0:
            amount = self.__schedule_newborns()
            print(f'Newborns for this year: {amount}')

        self.__try_to_add_newborn()

        # if self.count_type(self, HumanState.PrimaryTuberculosis) == 0 and \
        #    self.count_type(self, HumanState.PostPrimaryTuberculosis) == 0:
        #     self.running = False

    @staticmethod
    def count_type(model, human_condition, invert=False):
        """
        Helper method to count the number of humans in a given condition in the model.
        Args:
            model: Reference to the model.
            human_condition: The condition to count.
            invert: If True, count the number of humans not in the given condition.
        """
        count = 0
        for agent in model.schedule.agents:
            if not isinstance(agent, Human):
                continue

            if invert:
                if agent.condition != human_condition:
                    count += 1
            else:
                if agent.condition == human_condition:
                    count += 1
        return count
