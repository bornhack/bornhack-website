module Models exposing (..)


type Route
    = OverviewRoute
    | DayRoute DayIso
    | EventInstanceRoute EventInstanceSlug
    | NotFoundRoute


type alias Model =
    { days : List Day
    , eventInstances : List EventInstance
    , eventLocations : List EventLocation
    , eventTypes : List EventType
    , events : List Event
    , flags : Flags
    , activeDay : Day
    , filter : Filter
    , route : Route
    }


type alias Filter =
    { eventTypes : List EventType
    , eventLocations : List EventLocation
    }


type alias DayIso =
    String


type alias Day =
    { day_name : String
    , iso : DayIso
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
    , from : String
    , to : String
    , timeslots : Float
    , location : String
    , locationIcon : String
    , videoRecording : Bool
    , videoUrl : String
    }


type alias Event =
    { title : String
    , slug : EventSlug
    , abstract : String
    , speakers : List Speaker
    }


emptyEventInstance : EventInstance
emptyEventInstance =
    { title = "This should not happen!"
    , slug = "this-should-not-happen"
    , id = 0
    , url = ""
    , eventSlug = ""
    , eventType = ""
    , backgroundColor = ""
    , forgroundColor = ""
    , from = ""
    , to = ""
    , timeslots = 0.0
    , location = ""
    , locationIcon = ""
    , videoRecording = False
    , videoUrl = ""
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
    }


allDaysDay : Day
allDaysDay =
    Day "All Days" "" ""
