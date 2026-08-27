import random

# Coordenadas centroidales validadas de Medellín / Valle de Aburrá
ZONE_COORDINATES = {
    "Sur": (6.164962, -75.595357),
    "Occidente": (6.256659, -75.604599),
    "Centro": (6.250269, -75.559476),
    "Chapinero": (6.264949, -75.549764),
    "Norte": (6.283953, -75.565434),
}


class GeoService:
    @staticmethod
    def get_zone_coordinates(zona: str, jitter: bool = True) -> tuple[float, float]:
        """
        Retorna las coordenadas (latitud, longitud) para una zona determinada.
        Si jitter es True, aplica una ligera variación estocástica (+-300m) para simular direcciones reales.
        """
        base = ZONE_COORDINATES.get(zona, (6.250269, -75.559476))
        if jitter:
            lat = round(base[0] + random.uniform(-0.003, 0.003), 6)
            lon = round(base[1] + random.uniform(-0.003, 0.003), 6)
            return lat, lon
        return base[0], base[1]
