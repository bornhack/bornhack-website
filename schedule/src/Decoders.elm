module Decoders exposing (..)

-- Local modules

import Models exposing (Day, Speaker, Event, EventInstance, EventLocation, EventType, Model, Flags, Filter, Route(..))


-- Core modules

import Json.Decode exposing (int, string, float, list, bool, dict, Decoder)
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)


-- DECODERS


type alias WebSocketAction =
    { action : String
    }


webSocketActionDecoder : Decoder WebSocketAction
webSocketActionDecoder =
    decode WebSocketAction
        |> required "action" string


dayDecoder : Decoder Day
dayDecoder =
    decode Day
        |> required "day_name" string
        |> required "iso" string
        |> required "repr" string


speakerDecoder : Decoder Speaker
speakerDecoder =
    decode Speaker
        |> required "name" string


eventDecoder : Decoder Event
eventDecoder =
    decode Event
        |> required "title" string
        |> required "slug" string
        |> required "abstract" string
        |> required "speakers" (list speakerDecoder)


eventInstanceDecoder : Decoder EventInstance
eventInstanceDecoder =
    decode EventInstance
        |> required "title" string
        |> required "slug" string
        |> required "id" int
        |> required "url" string
        |> required "event_slug" string
        |> required "event_type" string
        |> required "bg-color" string
        |> required "fg-color" string
        |> required "from" string
        |> required "to" string
        |> required "timeslots" float
        |> required "location" string
        |> required "location_icon" string
        |> required "video_recording" bool
        |> optional "video_url" string ""


eventLocationDecoder : Decoder EventLocation
eventLocationDecoder =
    decode EventLocation
        |> required "name" string
        |> required "slug" string
        |> required "icon" string


eventTypeDecoder : Decoder EventType
eventTypeDecoder =
    decode EventType
        |> required "name" string
        |> required "slug" string
        |> required "color" string
        |> required "light_text" bool


initDataDecoder : Decoder (Flags -> Day -> Filter -> Route -> Model)
initDataDecoder =
    decode Model
        |> required "days" (list dayDecoder)
        |> required "event_instances" (list eventInstanceDecoder)
        |> required "event_locations" (list eventLocationDecoder)
        |> required "event_types" (list eventTypeDecoder)
        |> hardcoded []
