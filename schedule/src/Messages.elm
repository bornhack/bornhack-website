module Messages exposing (Msg(..))

-- Local modules

import Models exposing (Day, EventInstance, FilterType)


-- External modules

import Navigation exposing (Location)


type Msg
    = NoOp
    | WebSocketPayload String
    | ToggleFilter FilterType
    | OnLocationChange Location
    | BackInHistory
