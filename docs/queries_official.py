MUTATION_LOGIN = """
mutation LOGIN($email: String!, $password: String!, $langCode: String, $retainSession: Boolean) {
  logIn(
    input: {email: $email, password: $password, langCode: $langCode, retainSession: $retainSession}
  ) {
    settings {
      client {
        name
        __typename
      }
      support {
        serviceActive
        phone
        email
        __typename
      }
      __typename
    }
    user {
      id
      clientCustomerId
      agreements
      properties {
        id
        allInstalled
        __typename
      }
      inbox(modes: ["app"]) {
        actions {
          label
          type
          value
          __typename
        }
        id
        lockUser
        maxNumberOfSkip
        messageBody
        messageHeader
        __typename
      }
      __typename
    }
    token
    firstLogin
    __typename
  }
}
"""

QUERY_GET_PROPERTIES_MODE = """
query GET_PROPERTIES_MODE {
  properties {
    id
    name
    mode
    __typename
  }
}
"""

QUERY_GET_PROPERTIES = """
query GET_PROPERTIES {
  ...Settings
  properties {
    id
    name
    organisationalUnit
    isDecentralised
    valueProposition
    selfConsumptionSettings {
      photovoltaic
      savings
      optimisationBoiler
      optimisationDevices
      optimisationExternalDevices
      optimisationEvc
      __typename
    }
    __typename
  }
}

fragment Settings on Query {
  settings {
    client {
      code
      brandName
      __typename
    }
    auth {
      isSmsEnabled
      __typename
    }
    mystrom {
      isEnabled
      linkAccountUrl
      storeUrl
      __typename
    }
    notifications {
      isAppEnabled
      isSmsEnabled
      isEmailEnabled
      __typename
    }
    benchmark {
      isEnabled
      __typename
    }
    __typename
  }
  __typename
}
"""


QUERY_GET_DATA = """
query GET_DATA {
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
