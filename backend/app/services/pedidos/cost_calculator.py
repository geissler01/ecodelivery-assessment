class CostCalculator:
  @staticmethod
  def calculate_operational_cost(monto: float, tipo_vehiculo: str) -> float:
    """Calcula el costo operativo de entrega según el tipo de transporte ecológico:

    - Bicicleta: 0.10 del monto
    - Moto Eléctrica: 0.15 del monto
    """
    factor = 0.10 if tipo_vehiculo.lower() == "bicicleta" else 0.15
    return round(monto * factor, 2)
