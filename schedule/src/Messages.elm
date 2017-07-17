module Messages exposing (Msg(..))

-- Local modules

import Models exposing (Day, EventType, EventLocation)


-- External modules

import Navigation exposing (Location)


type Msg
    = NoOp
    | WebSocketPayload String
    | MakeActiveday Day
    | ToggleEventTypeFilter EventType
    | ToggleEventLocationFilter EventLocation
    | OnLocationChange Location
