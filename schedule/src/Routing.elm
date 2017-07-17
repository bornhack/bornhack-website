module Routing exposing (..)

-- Local modules

import Models exposing (DayIso, EventInstanceSlug, Route(..))


-- External modules

import Navigation exposing (Location)
import UrlParser exposing ((</>))


matchers : UrlParser.Parser (Route -> a) a
matchers =
    UrlParser.oneOf
        [ UrlParser.map OverviewRoute UrlParser.top
        , UrlParser.map DayRoute (UrlParser.s "day" </> UrlParser.string)
        , UrlParser.map EventInstanceRoute (UrlParser.s "event" </> UrlParser.string)
        ]


parseLocation : Location -> Route
parseLocation location =
    case UrlParser.parseHash matchers location of
        Just route ->
            route

        Nothing ->
            NotFoundRoute
