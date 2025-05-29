MUTATION_LOGIN = """
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

QUERY_GET_DATA = """
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

QUERY_GET_CONSUMPTION_DATA = """
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

MUTATION_SET_ROOM_MODE = """
mutation HA_SET_ROOM_MODE($propertyId: Int!, $roomId: Int!, $mode: String) {
  activateRoomMode(input: {propertyId: $propertyId, roomId: $roomId, mode: $mode}) {
    id
    mode {
      comfort
      absence
      frost
      sleep
      disableHeating
      __typename
    }
    __typename
  }
}
"""


MUTATION_SET_ROOM_TEMPERATURE = """
mutation HA_SET_ROOM_TEMPERATURE($propertyId: Int!, $roomId: Int!, $temperature: Float!) {
  setRoomAdjustTemperature(
    input: {propertyId: $propertyId, roomId: $roomId, temperature: $temperature}
  ) {
    id
    adjustTemperature {
      active
      endDateTime
      temperature
      __typename
    }
    __typename
  }
}
"""
