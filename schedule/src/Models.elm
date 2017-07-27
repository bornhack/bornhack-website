module Models exposing (..)

-- Core modules

import Date exposing (Date, now)


-- External modules

import Navigation exposing (Location)


type Route
    = OverviewRoute
    | OverviewFilteredRoute String
    | DayRoute String
    | EventRoute EventSlug
    | NotFoundRoute


type alias Model =
    { days : List Day
    , events : List Event
    , eventInstances : List EventInstance
    , eventLocations : List EventLocation
    , eventTypes : List EventType
    , flags : Flags
    , filter : Filter
    , location : Location
    , route : Route
    , dataLoaded : Bool
    }


type alias Filter =
    { eventTypes : List EventType
    , eventLocations : List EventLocation
    , videoRecording : List { name : String, slug : String, filter : EventInstance -> Bool }
    }


type alias Day =
    { day_name : String
    , date : Date
    , repr : String
    }


type alias Speaker =
    { name : String
    }


type alias EventSlug =
    String


type alias EventInstanceSlug =
    String


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
    , videoRecording : Bool
    , videoUrl : String
    , isFavorited : Maybe Bool
    }


type alias Event =
    { title : String
    , slug : EventSlug
    , abstract : String
    , speakers : List Speaker
    , videoRecording : Bool
    , videoUrl : String
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
