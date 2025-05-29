import aiohttp
import logging
import time

from .queries import (
    MUTATION_LOGIN,
    MUTATION_SET_ROOM_MODE,
    MUTATION_SET_ROOM_TEMPERATURE,
    QUERY_GET_DATA,
    QUERY_GET_CONSUMPTION_DATA,
)

_LOGGER = logging.getLogger(__name__)


async def gqlCall(apiUrl, query, variables=None, tokens=None):
    """Call the GraphQL API using auth tokens."""

    gqlApi = (
        apiUrl if apiUrl is not None else "https://particuliers-tiko.fr/api/v3/graphql/"
    )

    # Generate headers
    headers = {
        "Content-Type": "application/json",
        "User-agent": "Mozilla/5.0 (Linux; Android 13; Pixel 4a Build/T1B3.221003.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/106.0.5249.126 Mobile Safari/537.36",
    }
    if tokens and tokens["token"]:
        headers["Authorization"] = f"Token {tokens['token']}"
    if tokens and tokens["csrf_token"] and tokens["member_space"]:
        headers["Cookie"] = (
            f"csrftoken={tokens['csrf_token']}; USER_SESSION_member_space={tokens['member_space']}"
        )

    # Payload
    payload = {"query": query, "variables": variables or {}}

    # Init HTTP session
    async with aiohttp.ClientSession() as session:
        try:
            # Exec HTTP POST query
            async with session.post(gqlApi, json=payload, headers=headers) as response:
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


async def login(apiUrl, email, password):
    """Use login and password to authenticate the user and return tokens."""
    try:
        # Prepare POST data
        variables = {
            "email": email,
            "password": password,
            "langCode": "fr",
            "retainSession": True,
        }

        # Call login mutation
        [reqTokens, data] = await gqlCall(apiUrl, MUTATION_LOGIN, variables)

        if not data:
            _LOGGER.error("No response data from login request")
            return False

        if "errors" in data:
            _LOGGER.error("Login errors: %s", data["errors"])
            return False

        if (
            "data" not in data
            or "logIn" not in data["data"]
            or data["data"]["logIn"] is None
        ):
            _LOGGER.error("Invalid login response structure")
            return False

        # Extract and merge user informations
        tokens = {
            "account_id": data["data"]["logIn"]["user"]["id"],
            "token": data["data"]["logIn"]["token"],
            "member_space": reqTokens.get("member_space"),
            "csrf_token": reqTokens.get("csrf_token"),
        }

        if not all(tokens.values()):
            _LOGGER.error("Missing required tokens in response")
            return False

        return tokens

    except Exception as error:
        _LOGGER.error("Login error: %s", error)
        return False


async def getData(apiUrl, tokens=None):
    """Fetch all devices informations."""

    # Get data from API
    [_, data] = await gqlCall(apiUrl, QUERY_GET_DATA, {}, tokens)
    _LOGGER.info("API::getData: %s", data)

    return data


async def getConsumptionData(apiUrl, tokens=None):
    """Fetch all devices consumption informations."""

    # Get consumption data from API
    [_, data] = await gqlCall(
        apiUrl,
        QUERY_GET_CONSUMPTION_DATA,
        {
            "timestampStart": "1609455600000",  # 2021-01-01
            "timestampEnd": str(int((time.time() + 5 * 60) * 1000)),  # Now + 5 minutes
            "resolution": "d",
        },
        tokens,
    )
    _LOGGER.info("API::getConsumptionData: %s", data)

    return data


async def setRoomMode(apiUrl, tokens, propertyId, roomId, mode):
    """Set the room mode."""

    # Prepare variables
    variables = {
        "propertyId": propertyId,
        "roomId": roomId,
        "mode": mode,
    }

    # Call login mutation
    [_, data] = await gqlCall(apiUrl, MUTATION_SET_ROOM_MODE, variables, tokens)
    _LOGGER.info("API::setRoomMode: %s", data)

    return data


async def setRoomTemperature(apiUrl, tokens, propertyId, roomId, temperature):
    """Set the room temperature."""

    # Prepare variables
    variables = {
        "propertyId": propertyId,
        "roomId": roomId,
        "temperature": temperature,
    }

    # Call login mutation
    [_, data] = await gqlCall(apiUrl, MUTATION_SET_ROOM_TEMPERATURE, variables, tokens)
    _LOGGER.info("API::setRoomTemperature: %s", data)

    return data
