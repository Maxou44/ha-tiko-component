import aiohttp
import logging

from .queries import (
    MUTATION_LOGIN,
    MUTATION_SET_ROOM_MODE,
    MUTATION_SET_ROOM_TEMPERATURE,
    QUERY_GET_DATA,
)

GQL_API_URL = "https://particuliers-tiko.fr/api/v3/graphql/"
_LOGGER = logging.getLogger(__name__)


async def gqlCall(query, variables=None, tokens=None):
    """Call the GraphQL API using auth tokens."""

    # Generate headers
    headers = {
        "Content-Type": "application/json",
        "User-agent": "Mozilla/5.0 (Linux; Android 13; Pixel 4a Build/T1B3.221003.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/106.0.5249.126 Mobile Safari/537.36",
    }
    if tokens and tokens["token"]:
        headers["Authorization"] = f"Token {tokens["token"]}"
    if tokens and tokens["csrf_token"] and tokens["member_space"]:
        headers["Cookie"] = (
            f"csrftoken={tokens["csrf_token"]}; USER_SESSION_member_space={tokens["member_space"]}"
        )

    # Payload
    payload = {"query": query, "variables": variables or {}}

    # Init HTTP session
    async with aiohttp.ClientSession() as session:
        try:
            # Exec HTTP POST query
            async with session.post(
                GQL_API_URL, json=payload, headers=headers
            ) as response:
                # If not sucessful
                if response.status != 200:
                    _LOGGER.error(
                        "Request error %d: %s", response.status, await response.text()
                    )
                    return None

                # Get tokens
                outTokens = {}
                if (
                    "csrftoken" in response.cookies
                    and response.cookies["csrftoken"].value
                ):
                    outTokens["csrf_token"] = response.cookies["csrftoken"].value
                if (
                    "USER_SESSION_member_space" in response.cookies
                    and response.cookies["USER_SESSION_member_space"].value
                ):
                    outTokens["member_space"] = response.cookies[
                        "USER_SESSION_member_space"
                    ].value

                # Get JSON response
                response_data = await response.json()

                # Return JSON data
                return [outTokens, response_data]

        except aiohttp.ClientError as e:
            _LOGGER.error("Request failed: %s", str(e))
            return None


async def login(email, password):
    """Use login and password to authentificate the user and return tokens."""

    # Prepare POST data
    variables = {
        "email": email,
        "password": password,
        "langCode": "fr",
        "retainSession": True,
    }

    # Call login mutation
    [reqTokens, data] = await gqlCall(MUTATION_LOGIN, variables)

    # Login failed
    if data["data"]["logIn"] is None:
        return False

    # Extract and merge user informations
    tokens = {
        "account_id": data["data"]["logIn"]["user"]["id"],
        "token": data["data"]["logIn"]["token"],
        "member_space": reqTokens["member_space"],
        "csrf_token": reqTokens["csrf_token"],
    }

    return tokens


async def getData(tokens=None):
    """Fetch all devices informations."""

    # Call login mutation
    [_, data] = await gqlCall(QUERY_GET_DATA, {}, tokens)
    _LOGGER.info("Data: %s", data)

    return data


async def setRoomMode(tokens, propertyId, roomId, mode):
    """Set the room mode."""

    # Prepare variables
    variables = {
        "propertyId": propertyId,
        "roomId": roomId,
        "mode": mode,
    }

    # Call login mutation
    [_, data] = await gqlCall(MUTATION_SET_ROOM_MODE, variables, tokens)
    _LOGGER.info("Set room mode: %s", data)

    return data


async def setRoomTemperature(tokens, propertyId, roomId, temperature):
    """Set the room mode."""

    # Prepare variables
    variables = {
        "propertyId": propertyId,
        "roomId": roomId,
        "temperature": temperature,
    }

    # Call login mutation
    [_, data] = await gqlCall(MUTATION_SET_ROOM_TEMPERATURE, variables, tokens)
    _LOGGER.error("Set room temperature: %s", data)

    return data
