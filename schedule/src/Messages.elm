module Messages exposing (Msg(..))

-- Local modules

import Models exposing (Day, EventType, EventLocation, EventInstance, VideoRecordingFilter)


-- External modules

import Navigation exposing (Location)


type Msg
    = NoOp
    | WebSocketPayload String
    | ToggleEventTypeFilter EventType
    | ToggleEventLocationFilter EventLocation
    | ToggleVideoRecordingFilter VideoRecordingFilter
    | OnLocationChange Location
    | BackInHistory
