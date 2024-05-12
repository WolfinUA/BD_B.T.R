import mesa
import mesa_geo as mg
import shapely

from src.utils.human_state import HumanState

class SectorAgent(mg.GeoAgent):
    """Neighbourhood agent. Changes color according to number of infected inside it."""

    def __init__(
        self, unique_id, model: mesa.Model, geometry: 'shapely.Geometry', crs, hotspot_threshold=1
    ):
        """
        Create a new Neighbourhood agent.
        :param unique_id:   Unique identifier for the agent
        :param model:       Model in which the agent runs
        :param geometry:    Shape object for the agent
        :param agent_type:  Indicator if agent is infected
                            ("infected", "susceptible", "recovered" or "dead")
        :param hotspot_threshold:   Number of infected agents in region
                                    to be considered a hot-spot
        """
        super().__init__(unique_id, model, geometry, crs)
        self.color = 'Black'
        self.hotspot_threshold = (
            hotspot_threshold  # When a neighborhood is considered a hot-spot
        )

    def step(self):
        """Advance agent one step."""
        self.color_hotspot()

    def color_hotspot(self):
        # Decide if this region agent is a hot-spot
        # (if more than threshold person agents are infected)
        neighbors = self.model.space.get_intersecting_agents(self)

        status = {
            "Green": 0,
            "Red": 0,
        }

        total = 0
        dead = 0

        for neighbor in neighbors:
            if isinstance(neighbor, SectorAgent):
                continue

            condition = neighbor.condition
            total += 1

            if condition in [HumanState.Sustainable, HumanState.Latent, HumanState.Recovered]:
                status['Green'] += 1
            elif condition == HumanState.Death:
                dead += 1
            else:
                status['Red'] += 1

        if total == dead:
            self.color = 'Black'
        else:
            self.color = max(status, key=status.get)

    def __repr__(self):
        return "Sector " + str(self.unique_id)
