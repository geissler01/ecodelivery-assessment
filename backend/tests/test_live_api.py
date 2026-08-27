"""
Script de Pruebas de Integración y End-to-End para EcoDelivery API
Ejecuta validaciones automáticas contra la API desplegada en producción o localmente.
"""
import sys
import json
import os
import urllib.parse
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = os.getenv("API_BASE_URL", "http://ecodelivery.geisler.coderhivex.com")


def run_tests():
    print("=" * 70)
    print(f"🚀 INICIANDO PRUEBAS E2E CONTRA: {BASE_URL}")
    print("=" * 70)

    # 1. Health Check
    req = urllib.request.Request(f"{BASE_URL}/health", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as res:
        health = json.loads(res.read().decode("utf-8"))
        assert health.get("status") == "healthy"
        print("✅ [1/9] Health Check -> OK (status: healthy)")

    # 2. Login Administrador
    login_admin = urllib.parse.urlencode({
        "username": "admin@ecodelivery.com",
        "password": "Admin1234!",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_admin,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        token_data = json.loads(res.read().decode("utf-8"))
        admin_token = token_data["access_token"]
        assert token_data.get("token_type") == "bearer"
        print("✅ [2/9] Login Superadmin -> OK (Token JWT emitido)")

    # 3. Login Cliente Semilla (Hash Argon2id)
    login_cliente = urllib.parse.urlencode({
        "username": "diego.gonzalez7@ecodelivery.com",
        "password": "EcoDelivery2026!",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_cliente,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        token_data = json.loads(res.read().decode("utf-8"))
        cliente_token = token_data["access_token"]
        print("✅ [3/9] Login Cliente Semilla -> OK (Argon2id verificado)")

    # 4. Perfil de Usuario (/users/me)
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/users/me",
        headers={"Authorization": f"Bearer {cliente_token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        me = json.loads(res.read().decode("utf-8"))
        print(f"✅ [4/9] Perfil /me -> {me['full_name']} | Rol: {me['role']} | Zona: {me.get('zona_principal')}")

    # 5. Resumen de Actividad (/users/me/resumen)
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/users/me/resumen",
        headers={"Authorization": f"Bearer {cliente_token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        resumen = json.loads(res.read().decode("utf-8"))
        print(f"✅ [5/9] Resumen Usuario -> Pedidos: {resumen['total_pedidos']} | Gasto: ${resumen['monto_total']:,.2f}")

    # 6. Listado de Pedidos (/pedidos/)
    req = urllib.request.Request(f"{BASE_URL}/api/v1/pedidos/?limit=5", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as res:
        pedidos = json.loads(res.read().decode("utf-8"))
        assert len(pedidos) > 0
        sample = pedidos[0]
        print(f"✅ [6/9] Listar Pedidos -> {len(pedidos)} obtenidos (Muestra: ID {sample['id_pedido'][:8]}... | {sample['zona']})")

    # 7. Filtros Combinados de Pedidos
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/pedidos/?zona=Chapinero&estado=entregado&limit=5",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        pedidos_filt = json.loads(res.read().decode("utf-8"))
        print(f"✅ [7/9] Filtros Combinados (?zona=Chapinero&estado=entregado) -> {len(pedidos_filt)} pedidos")

    # 8. Estadísticas Generales (/pedidos/estadisticas/resumen)
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/pedidos/estadisticas/resumen",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        stats = json.loads(res.read().decode("utf-8"))
        print(f"✅ [8/9] KPIs Operativos -> Total: {stats['total_pedidos']} | Ingresos: ${stats['ingresos_totales']:,.2f} | Tiempo Prom: {stats['tiempo_promedio_entrega_minutos']} min")

    # 9. Crear Pedido y Transición de Estado (Máquina de Estados)
    create_payload = json.dumps({
        "zona": "Norte",
        "metodo_pago": "app",
        "monto": 42000.0,
        "tipo_vehiculo": "moto_electrica",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/pedidos/",
        data=create_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cliente_token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        nuevo_pedido = json.loads(res.read().decode("utf-8"))
        nuevo_id = nuevo_pedido["id_pedido"]
        assert nuevo_pedido["estado"] == "pendiente"

    patch_payload = json.dumps({
        "nuevo_estado": "en_camino",
        "tipo_vehiculo": "moto_electrica",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/pedidos/{nuevo_id}/estado",
        data=patch_payload,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        pedido_actualizado = json.loads(res.read().decode("utf-8"))
        assert pedido_actualizado["estado"] == "en_camino"
        assert pedido_actualizado.get("fecha_asignacion") is not None
        print(f"✅ [9/9] Ciclo de Pedido (POST y PATCH Máquina de Estados) -> OK (ID: {nuevo_id[:8]}... | Estado: en_camino)")

    print("=" * 70)
    print("🎉 ¡TODAS LAS PRUEBAS E2E FUERON EXITOSAS AL 100%!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"❌ Error durante la ejecución de pruebas: {e}")
        sys.exit(1)
