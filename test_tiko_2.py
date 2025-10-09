import asyncio
import aiohttp
import json
import time
from datetime import datetime, time as dt_time

# ============================================================
# CONFIGURATION - Modifiez vos identifiants ici
# ============================================================
TIKO_EMAIL = "votre.email@example.com"
TIKO_PASSWORD = "votre_mot_de_passe"
# ============================================================


class TikoClient:
    """Client Python simple pour l'API Tiko - GraphQL masqué"""

    def __init__(self, email, password, api_url=None):
        self.email = email
        self.password = password
        self.api_url = api_url or "https://particuliers-tiko.fr/api/v3/graphql/"
        self._tokens = None
        self._session = None

    async def _request(self, operation, variables=None):
        """Envoie une requête à l'API (GraphQL masqué en interne)"""
        headers = {
            "Content-Type": "application/json",
            "User-agent": "Mozilla/5.0 (Linux; Android 13; Pixel 4a) AppleWebKit/537.36",
        }

        if self._tokens and self._tokens.get("token"):
            headers["Authorization"] = f"Token {self._tokens['token']}"

        if self._tokens and self._tokens.get("csrf_token") and self._tokens.get("member_space"):
            headers["Cookie"] = (
                f"csrftoken={self._tokens['csrf_token']}; "
                f"USER_SESSION_member_space={self._tokens['member_space']}"
            )

        # Requêtes GraphQL encapsulées
        queries = {
            "login": """
                mutation HA_LOGIN($email: String!, $password: String!, $langCode: String, $retainSession: Boolean) {
                  logIn(input: {email: $email, password: $password, langCode: $langCode, retainSession: $retainSession}) {
                    user { id __typename }
                    token
                    __typename
                  }
                }
            """,
            "get_properties": """
                query HA_GET_DATA {
                  properties {
                    id
                    name
                    mode
                    rooms {
                      id
                      name
                      currentTemperatureDegrees
                      targetTemperatureDegrees
                      humidity
                      sensors
                      mode { comfort absence frost sleep disableHeating __typename }
                      status { heatingOperating sensorBatteryLow __typename }
                      __typename
                    }
                    __typename
                  }
                }
            """,
            "get_consumption": """
                query HA_GET_CONSUMPTION_DATA($timestampStart: BigInt!, $timestampEnd: BigInt!, $resolution: String!) {
                  properties {
                    id
                    fastConsumption(start: $timestampStart, end: $timestampEnd, resolution: $resolution) {
                      roomsConsumption {
                        id
                        name
                        energyKwh
                        energyWh
                        __typename
                      }
                      __typename
                    }
                    __typename
                  }
                }
            """,
            "get_schedules": """
                query HA_GET_ALL_FIELDS {
                  properties {
                    id
                    name
                    mode
                    rooms {
                      id
                      name
                      currentTemperatureDegrees
                      targetTemperatureDegrees
                      humidity
                      sensors
                      mode {
                        comfort
                        absence
                        frost
                        sleep
                        disableHeating
                        __typename
                      }
                      status {
                        heatingOperating
                        sensorBatteryLow
                        __typename
                      }
                      adjustTemperature {
                        active
                        temperature
                        endDateTime
                        __typename
                      }
                      __typename
                    }
                    __typename
                  }
                }
            """,
        }

        payload = {
            "query": queries[operation],
            "variables": variables or {}
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")

                # Extraire cookies
                cookies = {}
                if "csrftoken" in response.cookies:
                    cookies["csrf_token"] = response.cookies["csrftoken"].value
                if "USER_SESSION_member_space" in response.cookies:
                    cookies["member_space"] = response.cookies["USER_SESSION_member_space"].value

                data = await response.json()

                if "errors" in data:
                    raise Exception(f"API Error: {data['errors']}")

                return cookies, data.get("data", {})

    async def connect(self):
        """Se connecter à Tiko"""
        variables = {
            "email": self.email,
            "password": self.password,
            "langCode": "fr",
            "retainSession": True,
        }

        cookies, data = await self._request("login", variables)

        if not data or "logIn" not in data:
            raise Exception("Échec de connexion")

        self._tokens = {
            "account_id": data["logIn"]["user"]["id"],
            "token": data["logIn"]["token"],
            "member_space": cookies.get("member_space"),
            "csrf_token": cookies.get("csrf_token"),
        }

        return True

    async def get_properties(self):
        """Récupère toutes les propriétés et pièces"""
        if not self._tokens:
            raise Exception("Pas connecté. Appelez d'abord connect()")

        _, data = await self._request("get_properties")
        return data.get("properties", [])

    async def get_rooms(self):
        """Récupère toutes les pièces avec leurs données"""
        properties = await self.get_properties()

        rooms = []
        for prop in properties:
            for room in prop.get("rooms", []):
                rooms.append({
                    "property_id": prop["id"],
                    "property_name": prop["name"],
                    "room_id": room["id"],
                    "room_name": room["name"],
                    "temperature": room.get("currentTemperatureDegrees"),
                    "target_temperature": room.get("targetTemperatureDegrees"),
                    "humidity": room.get("humidity"),
                    "heating": room.get("status", {}).get("heatingOperating", False),
                    "battery_low": room.get("status", {}).get("sensorBatteryLow", False),
                })

        return rooms

    async def get_consumption_since_midnight(self, resolution="h"):
        """Récupère la consommation depuis minuit aujourd'hui"""
        return await self.get_consumption_for_period("today", resolution)

    async def get_consumption_for_period(self, period="today", resolution="h"):
        """
        Récupère la consommation pour une période donnée

        Args:
            period: "today", "yesterday", "last_7_days", "this_month", ou tuple (start_datetime, end_datetime)
            resolution: "h" (heure), "d" (jour), "w" (semaine), "m" (mois)

        Returns:
            Liste de consommations par pièce avec energyKwh et energyWh
        """
        if not self._tokens:
            raise Exception("Pas connecté. Appelez d'abord connect()")

        now = datetime.now()

        # Calculer les timestamps selon la période
        if period == "today":
            start = datetime.combine(now.date(), dt_time.min)
            end = now
        elif period == "yesterday":
            from datetime import timedelta
            yesterday = now - timedelta(days=1)
            start = datetime.combine(yesterday.date(), dt_time.min)
            end = datetime.combine(yesterday.date(), dt_time.max)
        elif period == "last_7_days":
            from datetime import timedelta
            start = now - timedelta(days=7)
            end = now
        elif period == "this_month":
            start = datetime.combine(now.replace(day=1).date(), dt_time.min)
            end = now
        elif isinstance(period, tuple) and len(period) == 2:
            start, end = period
        else:
            raise ValueError(f"Période invalide: {period}")

        variables = {
            "timestampStart": str(int(start.timestamp() * 1000)),
            "timestampEnd": str(int(end.timestamp() * 1000)),
            "resolution": resolution,
        }

        _, data = await self._request("get_consumption", variables)

        # Transformer les données en format simple
        result = []
        for prop in data.get("properties", []):
            fast_consumption = prop.get("fastConsumption", {})
            rooms_consumption = fast_consumption.get("roomsConsumption", [])

            for room in rooms_consumption:
                result.append({
                    "property_id": prop["id"],
                    "room_id": room["id"],
                    "room_name": room["name"],
                    "energy_kwh": room.get("energyKwh"),
                    "energy_wh": room.get("energyWh"),
                })

        return result

    async def get_total_consumption(self, period="today"):
        """Calcule la consommation totale pour une période"""
        consumptions = await self.get_consumption_for_period(period)

        total_kwh = sum(c["energy_kwh"] or 0 for c in consumptions)
        total_wh = sum(c["energy_wh"] or 0 for c in consumptions)

        return {
            "total_kwh": total_kwh,
            "total_wh": total_wh,
            "rooms": consumptions,
        }

    async def get_schedules(self):
        """
        Tente de récupérer tous les champs disponibles pour les pièces
        Pour découvrir si un champ 'schedule' ou équivalent existe

        Returns:
            Données brutes des pièces avec tous les champs disponibles
        """
        if not self._tokens:
            raise Exception("Pas connecté. Appelez d'abord connect()")

        _, data = await self._request("get_schedules")

        print("\n" + "=" * 60)
        print("DONNÉES BRUTES (pour analyse)")
        print("=" * 60)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("=" * 60)

        # Chercher tous les champs disponibles
        result = []
        for prop in data.get("properties", []):
            for room in prop.get("rooms", []):
                room_data = {
                    "property_id": prop["id"],
                    "property_name": prop["name"],
                    "room_id": room["id"],
                    "room_name": room["name"],
                    "all_fields": list(room.keys()),  # Liste de tous les champs disponibles
                    "raw_data": room  # Données brutes complètes
                }
                result.append(room_data)

        return result

    async def get_room_schedule(self, room_name):
        """
        Récupère le planning d'une pièce spécifique

        Args:
            room_name: Nom de la pièce

        Returns:
            Planning de la pièce ou None si non trouvé
        """
        schedules = await self.get_schedules()

        for schedule in schedules:
            if schedule["room_name"].lower() == room_name.lower():
                return schedule

        return None

    async def get_current_schedule_mode(self, room_name):
        """
        Détermine le mode programmé pour une pièce à l'heure actuelle

        Args:
            room_name: Nom de la pièce

        Returns:
            dict avec mode et température actuels selon le planning
        """
        schedule = await self.get_room_schedule(room_name)

        if not schedule or not schedule["schedule_enabled"]:
            return {"mode": None, "temperature": None, "scheduled": False}

        now = datetime.now()
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        current_day = day_names[now.weekday()]
        current_time = now.strftime("%H:%M")

        # Chercher le créneau horaire actuel
        for day in schedule["days"]:
            if day["day"] == current_day:
                for time_slot in day["times"]:
                    if time_slot["start"] <= current_time < time_slot["end"]:
                        return {
                            "mode": time_slot["mode"],
                            "temperature": time_slot["temperature"],
                            "scheduled": True,
                            "time_slot": f"{time_slot['start']} - {time_slot['end']}"
                        }

        return {"mode": None, "temperature": None, "scheduled": False}


async def example_usage():
    """Exemple d'utilisation simple du client"""

    # Créer le client
    tiko = TikoClient(TIKO_EMAIL, TIKO_PASSWORD)

    print("=" * 60)
    print("EXEMPLE D'UTILISATION DU CLIENT TIKO")
    print("=" * 60)

    # 1. Connexion
    print("\n[1] Connexion...")
    await tiko.connect()
    print("✓ Connecté!")

    # 2. Récupérer toutes les pièces
    print("\n[2] Récupération des pièces...")
    rooms = await tiko.get_rooms()
    print(f"✓ {len(rooms)} pièce(s) trouvée(s):")
    for room in rooms:
        print(f"   - {room['room_name']}: {room['temperature']}°C "
              f"(cible: {room['target_temperature']}°C, "
              f"chauffage: {'ON' if room['heating'] else 'OFF'})")

    # 3. Consommation depuis minuit
    print("\n[3] Consommation depuis minuit...")
    consumption = await tiko.get_consumption_since_midnight(resolution="h")
    print(f"✓ Consommation par pièce:")
    for c in consumption:
        if c['energy_kwh'] is not None:
            print(f"   - {c['room_name']}: {c['energy_kwh']:.2f} kWh ({c['energy_wh']} Wh)")
        else:
            print(f"   - {c['room_name']}: Pas de données")

    # 4. Consommation totale aujourd'hui
    print("\n[4] Consommation totale aujourd'hui...")
    total = await tiko.get_total_consumption("today")
    print(f"✓ Total: {total['total_kwh']:.2f} kWh ({total['total_wh']} Wh)")

    # 5. Consommation des 7 derniers jours
    print("\n[5] Consommation des 7 derniers jours...")
    week_total = await tiko.get_total_consumption("last_7_days")
    print(f"✓ Total 7 jours: {week_total['total_kwh']:.2f} kWh")

    # 6. Récupérer tous les champs disponibles
    print("\n[6] Analyse des champs disponibles...")
    all_fields = await tiko.get_schedules()
    if all_fields:
        print(f"✓ Champs disponibles pour '{all_fields[0]['room_name']}':")
        print(f"   {', '.join(all_fields[0]['all_fields'])}")

        # Vérifier si 'schedule' existe
        if 'schedule' in all_fields[0]['all_fields']:
            print("\n   ✓ Le champ 'schedule' existe!")
        else:
            print("\n   ✗ Le champ 'schedule' n'existe pas dans l'API")
            print("   → Les plannings ne sont pas disponibles via cette API GraphQL")

    print("\n" + "=" * 60)
    print("EXEMPLE TERMINÉ")
    print("=" * 60)


async def custom_period_example():
    """Exemple avec une période personnalisée"""
    from datetime import timedelta

    tiko = TikoClient(TIKO_EMAIL, TIKO_PASSWORD)
    await tiko.connect()

    # Période personnalisée: du 1er au 15 du mois
    now = datetime.now()
    start = datetime.combine(now.replace(day=1).date(), dt_time.min)
    end = datetime.combine(now.replace(day=15).date(), dt_time.max)

    consumption = await tiko.get_consumption_for_period((start, end), resolution="d")

    print(f"Consommation du {start.date()} au {end.date()}:")
    for c in consumption:
        print(f"  {c['room_name']}: {c['energy_kwh']} kWh")


if __name__ == "__main__":
    # Vérifier que les identifiants ont été modifiés
    if TIKO_EMAIL == "votre.email@example.com":
        print("⚠️  ATTENTION: Modifiez TIKO_EMAIL et TIKO_PASSWORD en haut du script!")
    else:
        # Lancer l'exemple
        asyncio.run(example_usage())

    # Pour utiliser l'exemple avec période personnalisée:
    # asyncio.run(custom_period_example())