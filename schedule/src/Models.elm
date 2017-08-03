module Models exposing (..)

-- Core modules

import Date exposing (Date, now)


-- External modules

import Navigation exposing (Location)


type alias EventSlug =
    String


type alias EventInstanceSlug =
    String


type alias SpeakerSlug =
    String


type alias DaySlug =
    String


type alias FilterQuery =
    String



-- Route is defined here rather than in Routing.elm due to it being used in Model. If it were in Routing.elm we would have a circular dependency.


type Route
    = OverviewRoute
    | OverviewFilteredRoute FilterQuery
    | DayRoute DaySlug
    | EventRoute EventSlug
    | SpeakerRoute SpeakerSlug
    | NotFoundRoute


type alias Model =
    { days : List Day
    , events : List Event
    , eventInstances : List EventInstance
    , eventLocations : List EventLocation
    , eventTypes : List EventType
    , speakers : List Speaker
    , flags : Flags
    , filter : Filter
    , location : Location
    , route : Route
    , dataLoaded : Bool
    }


type alias Filter =
    { eventTypes : List EventType
    , eventLocations : List EventLocation
    , videoRecording : List VideoRecordingFilter
    }


type alias VideoRecordingFilter =
    { name : String
    , slug : String
    }


type alias Day =
    { day_name : String
    , date : Date
    , repr : String
    }


type alias Speaker =
    { name : String
    , slug : SpeakerSlug
    , biography : String
    , largePictureUrl : Maybe String
    , smallPictureUrl : Maybe String
    }


type alias EventInstance =
    { title : String
    , slug : EventInstanceSlug
    , id : Int
    , url : String
    , eventSlug : EventSlug
    , eventType : String
    , backgroundColor : String
    , forgroundColor : String
    , from : Date
    , to : Date
    , timeslots : Float
    , location : String
    , locationIcon : String
    , videoState : String
    , videoUrl : Maybe String
    , isFavorited : Maybe Bool
    }


type alias Event =
    { title : String
    , slug : EventSlug
    , abstract : String
    , speakerSlugs : List SpeakerSlug
    , videoState : String
    , videoUrl : Maybe String
    , eventType : String
    }


type alias EventLocation =
    { name : String
    , slug : String
    , icon : String
    }


type alias EventType =
    { name : String
    , slug : String
    , color : String
    , lightText : Bool
    }


type alias Flags =
    { schedule_timeslot_length_minutes : Int
    , schedule_midnight_offset_hours : Int
    , ics_button_href : String
    , camp_slug : String
    , websocket_server : String
    }
