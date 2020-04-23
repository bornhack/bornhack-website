module Messages exposing (Msg(..))

-- Local modules
-- External modules

import Models exposing (Day, EventInstance, FilterType)
import Navigation exposing (Location)


type Msg
    = NoOp
    | WebSocketPayload String
    | ToggleFilter FilterType
    | OnLocationChange Location
    | BackInHistory
