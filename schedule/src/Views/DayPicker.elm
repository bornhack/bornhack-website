module Views.DayPicker exposing (..)

-- Local modules

import Models exposing (..)
import Messages exposing (Msg(..))
import Routing exposing (routeToString)
import Views.FilterView exposing (maybeFilteredOverviewRoute)


-- Core modules

import Date exposing (Date)


-- External modules

import Html exposing (Html, text, a, div)
import Html.Attributes exposing (class, classList, href, id)
import Date.Extra


dayPicker : Model -> Html Msg
dayPicker model =
    let
        activeDate =
            case model.route of
                DayRoute iso ->
                    Date.Extra.fromIsoString iso

                _ ->
                    Nothing

        isAllDaysActive =
            case activeDate of
                Just _ ->
                    False

                Nothing ->
                    True
    in
        div
            [ classList
                [ ( "row", True )
                , ( "sticky", True )
                ]
            , id "daypicker"
            ]
            [ div [ id "schedule-days", class "btn-group" ]
                ([ a
                    [ classList
                        [ ( "btn", True )
                        , ( "btn-default", not isAllDaysActive )
                        , ( "btn-primary", isAllDaysActive )
                        ]
                    , href <| routeToString <| maybeFilteredOverviewRoute model
                    ]
                    [ text "All Days"
                    ]
                 ]
                    ++ (List.map (\day -> dayButton day activeDate) model.days)
                )
            ]


dayButton : Day -> Maybe Date -> Html Msg
dayButton day activeDate =
    let
        isActive =
            case activeDate of
                Just activeDate ->
                    day.date == activeDate

                Nothing ->
                    False
    in
        a
            [ classList
                [ ( "btn", True )
                , ( "btn-default", not isActive )
                , ( "btn-primary", isActive )
                ]
            , href <| routeToString <| DayRoute <| Date.Extra.toFormattedString "y-MM-dd" day.date
            ]
            [ text day.day_name
            ]
