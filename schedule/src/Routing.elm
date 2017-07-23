module Routing exposing (..)

-- Local modules

import Models exposing (Route(..))


-- External modules

import Navigation exposing (Location)
import UrlParser exposing (Parser, (</>), oneOf, map, top, s, string, parseHash)


{--
URLs to support:

- #
    This show the overview of the schedule

- #?type={types},location={locations},video={no,yes,link}
    This is the overview, just with filters enable

- #day/{year}-{month}-{day}
    Show a particular day

- #event/{slug}
    Show a particular event

--}


matchers : Parser (Route -> a) a
matchers =
    oneOf
        [ map OverviewRoute top
        , map OverviewFilteredRoute (top </> string)
        , map DayRoute (s "day" </> string)
        , map EventRoute (s "event" </> string)
        ]


parseLocation : Location -> Route
parseLocation location =
    case parseHash matchers location of
        Just route ->
            route

        Nothing ->
            NotFoundRoute
