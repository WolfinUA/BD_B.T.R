import random

import mesa
import mesa_geo as mg

from src.config import Config
from src.disease_spread.agent import Human
from src.disease_spread.model import TuberculosisSpread
from src.openstreetmap.preloader import OSMPreloader
from src.openstreetmap.tags import TagsConfig
from src.utils.agent_places import AgentPlaces
from src.utils.agent_routines import AgentRoutine
from src.utils.human_state import HumanState


class Colors:
    List = {
        HumanState.Sustainable: "#00AA00",  # green
        HumanState.PrimaryTuberculosis: "#880000",  # red
        HumanState.PostPrimaryTuberculosis: "#e0dd00",  # yellow
        HumanState.Death: "#000000",  # black
        HumanState.Recovered: "#ffc0cb",  # pink
        HumanState.Latent: "#2deda0",  # light green
    }

    @staticmethod
    def with_default(human_state, default='#000'):
        try:
            return Colors.List[human_state]
        except KeyError:
            return default


class Server:

    # TODO: rewrite into location ids
    def __init__(self, locations: list[str | tuple[str, int]]):
        # Set random seed for reproducibility
        random.seed(3232211)

        # Configure OSMnx
        Config.configure_osmnx()

        self.tags = TagsConfig(Config.TAGS_PATH)
        places = AgentPlaces.new(Config.ROUTINES_PATH)

        self.store = OSMPreloader(self.tags, places).preload(locations)

        self.routine_creator = AgentRoutine(
            config_path=Config.ROUTINES_PATH,
            store=self.store
        )

    @staticmethod
    def __ui_chart_data():
        return [
            {"Label": HumanState.Sustainable, "Color": "#00AA00"},  # green
            {"Label": HumanState.PrimaryTuberculosis, "Color": "#880000"},  # red
            {"Label": HumanState.PostPrimaryTuberculosis, "Color": "#e0dd00"},  # yellow
            {"Label": HumanState.Death, "Color": "#000000"},  # black
            {"Label": HumanState.Recovered, "Color": "#ffc0cb"},  # pink
            {"Label": HumanState.Latent, "Color": "#2deda0"},  # light green
        ]

    @staticmethod
    def __ui_line_chert():
        return mesa.visualization.ChartModule(Server.__ui_chart_data())

    @staticmethod
    def __ui_pie_chert():
        return mesa.visualization.PieChartModule(Server.__ui_chart_data())

    @staticmethod
    def __map_renderer(agent):
        # Human Agent
        if isinstance(agent, Human):
            return {
                "radius": 2,
                "color": Colors.with_default(agent.condition, '#ffffff')
            }

        # Sector Agent
        else:
            return {
                "radius": 2,
                "color": agent.color
            }

    def __ui_map(self):
        return mg.visualization.MapModule(self.__map_renderer, map_width=800, map_height=800)

    def __model_params(self):
        return {
            # Data
            "store": self.store,
            "tags": self.tags,

            # UI
            "exposure_distance": 0.000015,  # about 12m
            "infected_percentage": 0.044,
            "routine_creator": self.routine_creator
        }

    def launch(self, port=8521, open_browser=False):
        ui_elements = [
            self.__ui_map(),
            # self.__ui_line_chert(),
            self.__ui_pie_chert(),
        ]

        server = mesa.visualization.ModularServer(
            TuberculosisSpread,
            ui_elements,
            "Tuberculosis Spread",
            self.__model_params(),
        )

        server.launch(port=port, open_browser=open_browser)

    @staticmethod
    def new(location: list[str] | str):
        if isinstance(location, str):
            location = [location]
        return Server(location)


if __name__ == '__main__':
    Server.new([
        'Lviv Raion',
        # ('Zolochiv Raion, Lviv Oblast', 2),
        # 'Drohobych Raion',
        # ('Sambir Raion', 2),
        # 'Stryi Raion',
        # 'Chervonohrad Raion',
        # 'Yavoriv Raion'
    ])
