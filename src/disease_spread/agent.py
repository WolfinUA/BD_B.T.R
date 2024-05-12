import random

import mesa
import mesa_geo as mg
import numpy as np
import shapely

from src.disease_spread.sector_agent import SectorAgent
from src.utils.agent_routines import Routine
from src.utils.computation import get_rand_in_range
from src.utils.human_age import HumanAgeGroup
from src.utils.human_state import HumanState


class Human(mg.GeoAgent):
    """
    A human agent.
    """

    HEALTHY_OPTIONS = [HumanState.Sustainable, HumanState.Latent, HumanState.PrimaryTuberculosis]
    PATIENT_OPTIONS = [HumanState.Recovered, HumanState.Death]

    def __init__(self,
                 unique_id,
                 model: mesa.Model,
                 geometry: 'shapely.Geometry',
                 crs,
                 exposure_distance: int,
                 routines: Routine
                 ):
        """
        Create a new human.
        Args:
            pos: The human's location on the grid.
            model: Reference to the model the agent belongs to.
        Conditions:
            Sustainable (Healthy)
            Latent
            Primary Tuberculosis (spreading)
            Post-Primary Tuberculosis (spreading)
            Recovered
            Death
        """
        super().__init__(unique_id, model, geometry, crs)
        self.exposure_distance = exposure_distance
        self.condition = HumanState.Sustainable

        # TODO: constant values should be moved to the config
        self.step_per_day = self.model.step_per_day
        self.year_in_steps = 365 * self.step_per_day
        self.lifespan_steps = 96 * self.year_in_steps

        self.healthy_contagious_rate = 0.017

        self.latent_chance = 0.9
        self.primary_chance = 0.1
        self.latent_recovery_chance = 0.1
        self.tuberculosis_recovery_chance = 0.896
        self.mortality_chance = 0.104
        self.post_primary_latent_chance = (0.05, 0.15)
        self.repeated_infection_chance = 0.14

        self.latent_recovery_day_range = (42, 56)

        self.incubation_period_days = 60
        self.IR_constant = 0.0024
        self.constant_a = 90
        self.constant_b = 50
        self.time_spend_with_in_minutes = 1 * 60  # 1-hour step in minutes


        self.steps_lived = HumanAgeGroup.set_random_init_age() * self.year_in_steps # For 24h simulation clock
        # self.steps_lived = HumanAgeGroup.set_random_init_age() * self.year_in_steps + random.randint(0, self.year_in_steps) # For 24h agent clock (more rng)
        self.human_age_group = HumanAgeGroup.set_age_group(self.steps_lived / self.year_in_steps)
        self.routines = routines
        self.steps_infected = 0

        self.random_day_in_life = random.randint(0, int(self.lifespan_steps / self.year_in_steps))

        self.flag_reinfection = False
        self.flag_latent_recovery = False
        self.flag_latent_infection = False

        self.reinfection_step = None
        self.latent_recovery_step = None
        self.latent_infection_step = None

        self.countagious_rate = 0
        self.max_countagious_rate = 0

    def __move(self, new_location: shapely.Point):
        self.geometry = new_location

    def __location_routine(self):
        week_day = self.steps_lived % (7 * self.step_per_day)  # 168 hours in a week
        hour = self.steps_lived % (1 * self.step_per_day)  # 0-23. So can be used as a reference for hours

        self.routines.update(
            age_group=self.human_age_group,
            day_type='weekday' if week_day < 5 * self.step_per_day else 'weekend',
        )

        current_routine = self.routines.current_place(hour)

        if current_routine is None:
            return

        if isinstance(current_routine, shapely.Point):
            self.__move(current_routine)
        else:
            print(f'[Agent][LocationRoutine] I found some piece of *%#$. Current routine is not a Shapely Point!! It\'s: {type(current_routine)}')

    def __set_latent_flags(self):
        """
        Assigns the latent flag to the human.
        """
        inf_chance = random.uniform(*self.post_primary_latent_chance)

        might_be_infected = 1 - self.latent_recovery_chance
        will_be_infected = might_be_infected * inf_chance

        self.flag_latent_recovery: bool = self.latent_recovery_chance > random.random()
        self.flag_latent_infection: bool = will_be_infected > random.random()

        if self.flag_latent_recovery:
            self.latent_recovery_step = get_rand_in_range(*self.latent_recovery_day_range) * self.step_per_day
        if self.flag_latent_infection:
            self.latent_infection_step = get_rand_in_range(self.steps_lived, self.lifespan_steps)

    def __set_reinfection_flags(self):
        self.flag_reinfection: bool = random.random() < self.repeated_infection_chance
        if self.flag_reinfection:
            self.reinfection_step = get_rand_in_range(self.steps_lived, self.lifespan_steps)

    def __set_contagious_rate(self,):
        """
        Calculate the contagious rate of the human for the day.
        :return:
        """
        if self.model.schedule.steps % self.step_per_day == 0:
            if self.steps_infected <= self.incubation_period_days:
                value = 1 - ((self.incubation_period_days - self.random_day_in_life) / self.constant_a)
                value = np.real(value) if np.isreal(value) and value >= 0 else 0
                sqrt_value = np.sqrt(value)
                self.countagious_rate = max(0, sqrt_value)
            else:
                value = np.abs((self.random_day_in_life - self.incubation_period_days) / self.constant_b)
                value = np.power(value, 3)
                self.countagious_rate = np.exp(-value)

    def get_chance_of_infection(self, neighbors: list):
        total_infected_near = 0
        total_contagious_near = 0
        total_near = 0
        for neighbor in neighbors:
            if isinstance(neighbor, SectorAgent):
                continue
            if neighbor.condition == HumanState.PrimaryTuberculosis and \
               neighbor.condition == HumanState.PostPrimaryTuberculosis:
                total_infected_near += 1
                total_contagious_near += neighbor.countagious_rate
            total_near += 1

        p_inf = self.time_spend_with_in_minutes * (self.IR_constant / 360) * (
                    total_infected_near / total_near) * total_contagious_near

        return p_inf

    def set_contagious_state(self, patient_contagious_rate):
        """
        Get the state of the human after contact with infected agent.
        :return: Returns the state of the human after contact with infected agent.
        """

        contagious_latent = patient_contagious_rate * self.latent_chance
        contagious_primary = patient_contagious_rate * self.primary_chance

        weights = [
            1 - contagious_latent - contagious_primary,
            contagious_latent,
            contagious_primary,
        ]

        self.condition = random.choices(Human.HEALTHY_OPTIONS, weights=weights).pop()

        if self.condition == HumanState.Latent:
            self.__set_latent_flags()


    def __set_recovery_state(self):
        """
        Get the state of the human after treatment.
        :return: Returns the state of the human after treatment.
        """

        weights = [
            self.tuberculosis_recovery_chance,
            self.mortality_chance,
        ]
        self.condition = random.choices(Human.PATIENT_OPTIONS, weights=weights).pop()
        # If the patient recovers, check if he will be reinfected
        if self.condition == HumanState.Recovered:
            self.steps_infected = 0
            self.__set_reinfection_flags()

    def __update_infected_steps_count(self):
        self.steps_infected += 1

    def __update_steps_lived_count(self):
        self.steps_lived += 1

    def __update_age_group(self):
        if self.steps_lived % self.year_in_steps == 0:
            agent_age = self.steps_lived / self.year_in_steps
            self.human_age_group = HumanAgeGroup.set_age_group(agent_age)

    def __handle_natural_death(self):
        self.condition = HumanState.Death
        return

    def __handle_infected_state(self):
        self.__update_infected_steps_count()
        self.__set_contagious_rate()
        neighbors_gen = self.model.space.get_neighbors_within_distance(self, self.exposure_distance, center=True)
        neighbors = [neighbor for neighbor in neighbors_gen if not isinstance(neighbor, SectorAgent)]

        # If the countagious rate is lower than healthy contagious rate, the patient recovers
        self.max_countagious_rate = max(self.max_countagious_rate, self.countagious_rate)

        if self.max_countagious_rate > self.countagious_rate and self.countagious_rate < self.healthy_contagious_rate:
            self.__set_recovery_state()
            return

        if len(neighbors) == 0:
            return

        p_inf = self.get_chance_of_infection(neighbors)

        # Influence over neighbors
        for neighbor in neighbors:
            if isinstance(neighbor, SectorAgent):
                continue

            if neighbor.condition == HumanState.Sustainable:
                neighbor.set_contagious_state(p_inf)

    def __handle_latent_state(self):
        # Overcomes infection
        if self.flag_latent_recovery and self.steps_lived >= self.latent_recovery_step:
            self.condition = HumanState.Sustainable
            return

        # If the body does fell for the infection
        if self.flag_latent_infection and self.steps_lived >= self.latent_infection_step:
            self.condition = HumanState.PostPrimaryTuberculosis
            return

    def __handle_recovered_state(self):
        # Calculate if the patient is reinfected
        if self.flag_reinfection and self.steps_lived >= self.reinfection_step:
            self.condition = HumanState.PostPrimaryTuberculosis
            self.flag_reinfection = False

    def step(self):
        """
        Perform a step in the simulation.
        """
        if self.condition == HumanState.Death:
            return

        self.__update_steps_lived_count()
        self.__update_age_group()
        self.__location_routine()

        if self.condition in [HumanState.PrimaryTuberculosis, HumanState.PostPrimaryTuberculosis]:
            self.__handle_infected_state()
        elif self.steps_lived >= self.lifespan_steps:
            self.__handle_natural_death()
        elif self.condition == HumanState.Latent:
            self.__handle_latent_state()
        elif self.condition == HumanState.Recovered:
            self.__handle_recovered_state()
