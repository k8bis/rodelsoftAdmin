import requests
import sys

GATEWAY = "http://localhost:8080"
APP1 = f"{GATEWAY}/app1"
APP2 = f"{GATEWAY}/app2"

USERNAME = "admin"
PASSWORD = "adminpass"

def main():
    # 1) Login en FastAPI (vía Nginx)
    print("🔹 Haciendo login en FastAPI (gateway)...")
    login_url = f"{APP1}/login"
    r = requests.post(login_url, json={"username": USERNAME, "password": PASSWORD})
    if r.status_code != 200:
        print("❌ Error en login:", r.status_code, r.text)
        sys.exit(1)

    token = r.json().get("access_token")
    if not token:
        print("❌ No se recibió access_token:", r.text)
        sys.exit(1)

    print("✅ Login OK. JWT obtenido.")
    headers = {"Authorization": f"Bearer {token}"}

    # 2) Salud de DB desde app1
    print("\n🔹 Checando /health en App1 (FastAPI) ...")
    rh = requests.get(f"{APP1}/health")
    print("   ↳", rh.status_code, rh.text)

    # 3) Permisos en App1 (FastAPI)
    print("\n🔹 Permisos en App1 (FastAPI):")
    r1 = requests.get(f"{APP1}/permissions", headers=headers)
    if r1.status_code == 200:
        for p in r1.json():
            print(f"   - App: {p['app']}, Cliente: {p['client']}")
    else:
        print("❌ Error permisos App1:", r1.status_code, r1.text)

    # 4) Permisos en App2 (Express)
    print("\n🔹 Permisos en App2 (Express):")
    r2 = requests.get(f"{APP2}/permissions", headers=headers)
    if r2.status_code == 200:
        # App2 devuelve columnas app_name/client
        data = r2.json()
        # uniformar salida si ya viene como dicts planos
        for p in data:
            app = p.get("app_name") or p.get("app")
            client = p.get("client")
            print(f"   - App: {app}, Cliente: {client}")
    else:
        print("❌ Error permisos App2:", r2.status_code, r2.text)

if __name__ == "__main__":
    main()

