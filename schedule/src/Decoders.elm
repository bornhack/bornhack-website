module Decoders exposing (..)

-- Local modules

import Models exposing (Day, Speaker, Event, EventInstance, Model, Flags, Filter, Route(..), FilterType(..))


-- Core modules

import Json.Decode exposing (int, string, float, list, bool, dict, Decoder, nullable)
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)
import Date exposing (Date, Month(..))


-- External modules

import Date.Extra
import Navigation exposing (Location)


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
        |> required "iso" dateDecoder
        |> required "repr" string


speakerDecoder : Decoder Speaker
speakerDecoder =
    decode Speaker
        |> required "name" string
        |> required "slug" string
        |> required "biography" string
        |> optional "large_picture_url" (nullable string) Nothing
        |> optional "small_picture_url" (nullable string) Nothing


eventDecoder : Decoder Event
eventDecoder =
    decode Event
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
    decode EventInstance
        |> required "title" string
        |> required "slug" string
        |> required "id" int
        |> required "url" string
        |> required "event_slug" string
        |> required "event_type" string
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
    decode LocationFilter
        |> required "name" string
        |> required "slug" string
        |> required "icon" string


eventTypeDecoder : Decoder FilterType
eventTypeDecoder =
    decode TypeFilter
        |> required "name" string
        |> required "slug" string
        |> required "color" string
        |> required "light_text" bool


initDataDecoder : Decoder (Flags -> Filter -> Location -> Route -> Bool -> Model)
initDataDecoder =
    decode Model
        |> required "days" (list dayDecoder)
        |> required "events" (list eventDecoder)
        |> required "event_instances" (list eventInstanceDecoder)
        |> required "event_locations" (list eventLocationDecoder)
        |> required "event_types" (list eventTypeDecoder)
        |> required "speakers" (list speakerDecoder)
