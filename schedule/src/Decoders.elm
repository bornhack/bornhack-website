module Decoders exposing (..)

-- Local modules
-- Core modules
-- External modules

import Date exposing (Date, Month(..))
import Date.Extra
import Json.Decode exposing (Decoder, bool, dict, float, int, list, nullable, string, succeed)
import Json.Decode.Pipeline exposing (hardcoded, optional, required)
import Models exposing (Day, Event, EventInstance, Filter, FilterType(..), Flags, Model, Route(..), Speaker)
import Navigation exposing (Location)



-- DECODERS


type alias WebSocketAction =
    { action : String
    }


webSocketActionDecoder : Decoder WebSocketAction
webSocketActionDecoder =
    succeed WebSocketAction
        |> required "action" string


dayDecoder : Decoder Day
dayDecoder =
    succeed Day
        |> required "day_name" string
        |> required "iso" dateDecoder
        |> required "repr" string


speakerDecoder : Decoder Speaker
speakerDecoder =
    succeed Speaker
        |> required "name" string
        |> required "slug" string
        |> required "biography" string


eventDecoder : Decoder Event
eventDecoder =
    succeed Event
        |> required "title" string
        |> required "slug" string
        |> required "abstract" string
        |> required "speaker_slugs" (list string)
        |> required "video_state" string
        |> optional "video_url" (nullable string) Nothing
        |> required "event_type" string


dateDecoder : Decoder Date
dateDecoder =
    let
        unpacked isoString =
            isoString
                |> Date.Extra.fromIsoString
                |> Maybe.withDefault (Date.Extra.fromParts 1970 Jan 1 0 0 0 0)
    in
    Json.Decode.map unpacked string


eventInstanceDecoder : Decoder EventInstance
eventInstanceDecoder =
    succeed EventInstance
        |> required "title" string
        |> required "slug" string
        |> required "id" int
        |> required "url" string
        |> required "event_slug" string
        |> required "event_type" string
        |> required "event_track" string
        |> required "bg-color" string
        |> required "fg-color" string
        |> required "from" dateDecoder
        |> required "to" dateDecoder
        |> required "timeslots" float
        |> required "location" string
        |> required "location_icon" string
        |> required "video_state" string
        |> optional "video_url" (nullable string) Nothing
        |> optional "is_favorited" (nullable bool) Nothing


eventLocationDecoder : Decoder FilterType
eventLocationDecoder =
    succeed LocationFilter
        |> required "name" string
        |> required "slug" string
        |> required "icon" string


eventTypeDecoder : Decoder FilterType
eventTypeDecoder =
    succeed TypeFilter
        |> required "name" string
        |> required "slug" string
        |> required "color" string
        |> required "light_text" bool


eventTrackDecoder : Decoder FilterType
eventTrackDecoder =
    succeed TrackFilter
        |> required "name" string
        |> required "slug" string


initDataDecoder : Decoder (Flags -> Filter -> Location -> Route -> Bool -> Model)
initDataDecoder =
    succeed Model
        |> required "days" (list dayDecoder)
        |> required "events" (list eventDecoder)
        |> required "event_instances" (list eventInstanceDecoder)
        |> required "event_locations" (list eventLocationDecoder)
        |> required "event_types" (list eventTypeDecoder)
        |> required "event_tracks" (list eventTrackDecoder)
        |> required "speakers" (list speakerDecoder)
