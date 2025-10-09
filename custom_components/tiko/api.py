"""Tiko API module - Optimized version."""
import aiohttp
import logging
import time
from datetime import datetime, time as dt_time

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
    if tokens and tokens.get("token"):
        headers["Authorization"] = f"Token {tokens['token']}"
    if tokens and tokens.get("csrf_token") and tokens.get("member_space"):
        headers["Cookie"] = (
            f"csrftoken={tokens['csrf_token']}; "
            f"USER_SESSION_member_space={tokens['member_space']}"
        )

    # Payload
    payload = {"query": query, "variables": variables or {}}

    # Init HTTP session
    async with aiohttp.ClientSession() as session:
        try:
            # Exec HTTP POST query
            async with session.post(gqlApi, json=payload, headers=headers) as response:
                # If not successful
                if response.status != 200:
                    _LOGGER.error(
                        "Request error %d: %s", response.status, await response.text()
                    )
                    return None

                # Get tokens from cookies
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
        result = await gqlCall(apiUrl, MUTATION_LOGIN, variables)

        if not result:
            _LOGGER.error("No response from login request")
            return False

        reqTokens, data = result

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

        # Extract and merge user information
        tokens = {
            "account_id": data["data"]["logIn"]["user"]["id"],
            "token": data["data"]["logIn"]["token"],
            "member_space": reqTokens.get("member_space"),
            "csrf_token": reqTokens.get("csrf_token"),
        }

        if not tokens.get("token"):
            _LOGGER.error("Missing token in response")
            return False

        return tokens

    except Exception as error:
        _LOGGER.error("Login error: %s", error)
        return False


async def getData(apiUrl, tokens=None):
    """Fetch all devices information."""
    if not tokens:
        _LOGGER.error("No tokens provided for getData")
        return None

    # Get data from API
    result = await gqlCall(apiUrl, QUERY_GET_DATA, {}, tokens)

    if not result:
        return None

    _, data = result
    _LOGGER.debug("API::getData: %s", data)

    return data


async def getConsumptionData(apiUrl, tokens=None, period="today"):
    """
    Fetch devices consumption information.

    Args:
        apiUrl: API endpoint URL
        tokens: Authentication tokens
        period: Period for consumption data
            - "today": depuis minuit aujourd'hui
            - "yesterday": hier complet
            - "last_7_days": 7 derniers jours
            - tuple (timestamp_start, timestamp_end): période personnalisée en ms

    Returns:
        Consumption data from API
    """
    if not tokens:
        _LOGGER.error("No tokens provided for getConsumptionData")
        return None

    now = datetime.now()

    # Calculate timestamps based on period
    if period == "today":
        midnight = datetime.combine(now.date(), dt_time.min)
        timestamp_start = int(midnight.timestamp() * 1000)
        timestamp_end = int(time.time() * 1000)
        resolution = "h"  # Hourly for current day
    elif period == "yesterday":
        from datetime import timedelta
        yesterday = now - timedelta(days=1)
        midnight_yesterday = datetime.combine(yesterday.date(), dt_time.min)
        midnight_today = datetime.combine(now.date(), dt_time.min)
        timestamp_start = int(midnight_yesterday.timestamp() * 1000)
        timestamp_end = int(midnight_today.timestamp() * 1000)
        resolution = "h"
    elif period == "last_7_days":
        from datetime import timedelta
        week_ago = now - timedelta(days=7)
        timestamp_start = int(week_ago.timestamp() * 1000)
        timestamp_end = int(time.time() * 1000)
        resolution = "d"  # Daily for week view
    elif isinstance(period, tuple) and len(period) == 2:
        timestamp_start, timestamp_end = period
        # Auto-detect resolution based on period length
        days_diff = (timestamp_end - timestamp_start) / (1000 * 60 * 60 * 24)
        resolution = "h" if days_diff <= 2 else "d"
    else:
        _LOGGER.error("Invalid period: %s", period)
        return None

    _LOGGER.debug(
        "Fetching consumption from %s to %s with resolution %s",
        timestamp_start,
        timestamp_end,
        resolution,
    )

    # Get consumption data from API
    result = await gqlCall(
        apiUrl,
        QUERY_GET_CONSUMPTION_DATA,
        {
            "timestampStart": str(timestamp_start),
            "timestampEnd": str(timestamp_end),
            "resolution": resolution,
        },
        tokens,
    )

    if not result:
        return None

    _, data = result
    _LOGGER.debug("API::getConsumptionData: %s", data)

    return data


async def setRoomMode(apiUrl, tokens, propertyId, roomId, mode):
    """Set the room mode."""
    if not tokens:
        _LOGGER.error("No tokens provided for setRoomMode")
        return None

    # Prepare variables
    variables = {
        "propertyId": propertyId,
        "roomId": roomId,
        "mode": mode,
    }

    # Call mutation
    result = await gqlCall(apiUrl, MUTATION_SET_ROOM_MODE, variables, tokens)

    if not result:
        return None

    _, data = result
    _LOGGER.debug("API::setRoomMode: %s", data)

    return data


async def setRoomTemperature(apiUrl, tokens, propertyId, roomId, temperature):
    """Set the room temperature."""
    if not tokens:
        _LOGGER.error("No tokens provided for setRoomTemperature")
        return None

    # Prepare variables
    variables = {
        "propertyId": propertyId,
        "roomId": roomId,
        "temperature": temperature,
    }

    # Call mutation
    result = await gqlCall(apiUrl, MUTATION_SET_ROOM_TEMPERATURE, variables, tokens)

    if not result:
        return None

    _, data = result
    _LOGGER.debug("API::setRoomTemperature: %s", data)

    return data