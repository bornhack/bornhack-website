module Routing exposing (..)

-- Local modules

import Models exposing (Route(..))


-- External modules

import Navigation exposing (Location)
import UrlParser exposing (Parser, (</>), oneOf, map, top, s, string, parseHash)


matchers : Parser (Route -> a) a
matchers =
    oneOf
        [ map OverviewRoute top
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
