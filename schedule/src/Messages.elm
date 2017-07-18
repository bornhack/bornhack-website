module Messages exposing (Msg(..))

-- Local modules

import Models exposing (Day, EventType, EventLocation, EventInstance)


-- External modules

import Navigation exposing (Location)


type Msg
    = NoOp
    | WebSocketPayload String
    | MakeActiveday Day
    | RemoveActiveDay
    | ToggleEventTypeFilter EventType
    | ToggleEventLocationFilter EventLocation
    | ToggleVideoRecordingFilter { name : String, filter : EventInstance -> Bool }
    | OnLocationChange Location
