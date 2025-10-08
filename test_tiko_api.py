import asyncio
import aiohttp
import json
import time


class TikoAPI:
    """Classe pour tester l'API Tiko - Basée sur le code officiel"""

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.tokens = None
        self.api_url = "https://particuliers-tiko.fr/api/v3/graphql/"

    async def gql_call(self, query, variables=None):
        """Appel GraphQL avec gestion des tokens et cookies"""

        # Générer les headers
        headers = {
            "Content-Type": "application/json",
            "User-agent": "Mozilla/5.0 (Linux; Android 13; Pixel 4a Build/T1B3.221003.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/106.0.5249.126 Mobile Safari/537.36",
        }

        # Ajouter le token si disponible
        if self.tokens and self.tokens.get("token"):
            headers["Authorization"] = f"Token {self.tokens['token']}"

        # Ajouter les cookies si disponibles
        if self.tokens and self.tokens.get("csrf_token") and self.tokens.get("member_space"):
            headers["Cookie"] = (
                f"csrftoken={self.tokens['csrf_token']}; "
                f"USER_SESSION_member_space={self.tokens['member_space']}"
            )

        # Payload
        payload = {"query": query, "variables": variables or {}}

        # Appel HTTP
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        print(f"✗ Erreur HTTP {response.status}: {await response.text()}")
                        return None

                    # Extraire les tokens des cookies
                    out_tokens = {}
                    if "csrftoken" in response.cookies and response.cookies["csrftoken"].value:
                        out_tokens["csrf_token"] = response.cookies["csrftoken"].value
                    if "USER_SESSION_member_space" in response.cookies and response.cookies[
                        "USER_SESSION_member_space"].value:
                        out_tokens["member_space"] = response.cookies["USER_SESSION_member_space"].value

                    # Réponse JSON
                    response_data = await response.json()

                    return [out_tokens, response_data]

            except Exception as e:
                print(f"✗ Erreur de requête: {e}")
                import traceback
                traceback.print_exc()
                return None

    async def login(self):
        """Connexion à l'API Tiko"""

        # Requête de login (exacte du code officiel)
        mutation_login = """
        mutation HA_LOGIN($email: String!, $password: String!, $langCode: String, $retainSession: Boolean) {
          logIn(
            input: {email: $email, password: $password, langCode: $langCode, retainSession: $retainSession}
          ) {
            user {
              id
              __typename
            }
            token
            __typename
          }
        }
        """

        variables = {
            "email": self.email,
            "password": self.password,
            "langCode": "fr",
            "retainSession": True,
        }

        try:
            result = await self.gql_call(mutation_login, variables)

            if not result:
                print("✗ Aucune réponse du serveur")
                return False

            [req_tokens, data] = result

            print("\n" + "=" * 60)
            print("RÉPONSE DE CONNEXION")
            print("=" * 60)
            print(json.dumps(data, indent=2, ensure_ascii=False))

            if "errors" in data:
                print(f"\n✗ Erreur de login: {data['errors']}")
                return False

            if "data" not in data or "logIn" not in data["data"] or data["data"]["logIn"] is None:
                print("\n✗ Structure de réponse invalide")
                return False

            # Extraire les tokens
            self.tokens = {
                "account_id": data["data"]["logIn"]["user"]["id"],
                "token": data["data"]["logIn"]["token"],
                "member_space": req_tokens.get("member_space"),
                "csrf_token": req_tokens.get("csrf_token"),
            }

            print("\n✓ Connexion réussie!")
            print(f"  - Account ID: {self.tokens['account_id']}")
            print(f"  - Token: {self.tokens['token'][:20]}...")
            print(f"  - CSRF Token: {self.tokens.get('csrf_token', 'N/A')}")
            print(f"  - Member Space: {self.tokens.get('member_space', 'N/A')}")

            return True

        except Exception as e:
            print(f"\n✗ Erreur lors de la connexion: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def get_data(self):
        """Récupérer toutes les données des appareils"""

        if not self.tokens:
            print("✗ Vous devez d'abord vous connecter!")
            return None

        # Query exacte du code officiel
        query_get_data = """
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
              __typename
            }
            __typename
          }
        }
        """

        result = await self.gql_call(query_get_data)

        if not result:
            return None

        [_, data] = result

        print("\n" + "=" * 60)
        print("DONNÉES DES APPAREILS")
        print("=" * 60)
        print(json.dumps(data, indent=2, ensure_ascii=False))

        return data

    async def get_consumption_data(self):
        """Récupérer les données de consommation"""

        if not self.tokens:
            print("✗ Vous devez d'abord vous connecter!")
            return None

        # Query exacte du code officiel pour la consommation
        query_consumption = """
        query HA_GET_CONSUMPTION_DATA($timestampStart: BigInt!, $timestampEnd: BigInt!, $resolution: String!) {
          properties {
            id
            fastConsumption(
              start: $timestampStart
              end: $timestampEnd
              resolution: $resolution
            ) {
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
        """
        # Calculer minuit aujourd'hui
        from datetime import datetime, time as dt_time

        now = datetime.now()
        midnight = datetime.combine(now.date(), dt_time.min)
        timestamp_midnight = int(midnight.timestamp() * 1000)
        timestamp_now = int(time.time() * 1000)

        variables = {
            "timestampStart": str(timestamp_midnight),  # Depuis minuit aujourd'hui
            "timestampEnd": str(timestamp_now),  # Maintenant
            "resolution": "d",  # Résolution par heure pour plus de détails
        }
        result = await self.gql_call(query_consumption, variables)

        if not result:
            return None

        [_, data] = result

        print("\n" + "=" * 60)
        print("DONNÉES DE CONSOMMATION")
        print("=" * 60)
        print(json.dumps(data, indent=2, ensure_ascii=False))

        return data


async def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("TEST DE L'API TIKO - VERSION BASÉE SUR LE CODE OFFICIEL")
    print("=" * 60)

    # IMPORTANT: Remplacez par vos identifiants Tiko

    EMAIL = "votre.email@example.com"
    PASSWORD = "monpassword"

    if EMAIL == "votre.email@example.com":
        print("\n⚠️  ATTENTION: Vous devez modifier EMAIL et PASSWORD dans le script!")
        print("   Éditez le fichier et remplacez les valeurs à la fin du script.")
        return

    # Créer une instance de l'API
    api = TikoAPI(EMAIL, PASSWORD)

    # Étape 1: Connexion
    print("\n[ÉTAPE 1] Connexion à l'API Tiko...")
    if not await api.login():
        print("\n❌ Échec de la connexion. Vérifiez vos identifiants.")
        return

    # Étape 2: Récupérer les données
    print("\n[ÉTAPE 2] Récupération des données des appareils...")
    await api.get_data()

    # Étape 3: Récupérer la consommation
    print("\n[ÉTAPE 3] Récupération des données de consommation...")
    await api.get_consumption_data()

    print("\n" + "=" * 60)
    print("TEST TERMINÉ")
    print("=" * 60)
    print("\n📊 ANALYSE:")
    print("   - Si vous voyez 'energyKwh' et 'energyWh' dans les résultats,")
    print("     la consommation est disponible via l'API!")
    print("   - Si les valeurs sont null, l'API ne retourne pas ces données")
    print("     pour votre compte/équipement.")


if __name__ == "__main__":
    asyncio.run(main())