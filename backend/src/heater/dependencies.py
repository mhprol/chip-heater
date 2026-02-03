from heater.evolution import EvolutionClient
from heater.config import settings

evolution_client = EvolutionClient(base_url=settings.evolution_url, api_key=settings.evolution_api_key)

def get_evolution():
    return evolution_client
