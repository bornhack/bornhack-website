module Routing exposing (..)

-- Local modules

import Models exposing (Route(..))


-- External modules

import Navigation exposing (Location)
import UrlParser exposing (Parser, (</>), oneOf, map, top, s, string, parseHash)


{--
URLs to support:

- #/
    This show the overview of the schedule

- #/?type={types},location={locations},video={not-to-be-recorded,to-be-recorded,has-recording}
    This is the overview, just with filters enable

- #/day/{year}-{month}-{day}
    Show a particular day

- #/event/{slug}
    Show a particular event

--}


matchers : Parser (Route -> a) a
matchers =
    oneOf
        [ map OverviewRoute top
        , map OverviewFilteredRoute (top </> string)
        , map DayRoute (s "day" </> string)
        , map EventRoute (s "event" </> string)
        , map SpeakerRoute (s "speaker" </> string)
        ]


parseLocation : Location -> Route
parseLocation location =
    parseHash matchers location
        |> Maybe.withDefault NotFoundRoute


routeToString : Route -> String
routeToString route =
    let
        parts =
            case route of
                OverviewRoute ->
                    []

                OverviewFilteredRoute query ->
                    [ query ]

                DayRoute iso ->
                    [ "day", iso ]

                EventRoute slug ->
                    [ "event", slug ]

                SpeakerRoute slug ->
                    [ "speaker", slug ]

                NotFoundRoute ->
                    []
    in
        "#/" ++ String.join "/" parts
