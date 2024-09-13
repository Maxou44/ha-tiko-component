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
      type
      color
      heaters
      hasTemperatureSchedule
      currentTemperatureDegrees
      targetTemperatureDegrees
      humidity
      sensors
      mode {
        boost
        absence
        frost
        disableHeating
        passive
        summer
        bypass
        __typename
      }
      status {
        disconnected
        heaterDisconnected
        heatingOperating
        sensorBatteryLow
        sensorDisconnected
        temporaryAdjustment
        __typename
      }
      devices {
        id
        code
        type
        name
        mac
        __typename
      }
      __typename
    }
    __typename
  }
}
"""
