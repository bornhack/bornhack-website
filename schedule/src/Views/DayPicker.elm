module Views.DayPicker exposing (..)

-- Local modules

import Models exposing (..)
import Messages exposing (Msg(..))


-- External modules

import Html exposing (Html, text, a, div)
import Html.Attributes exposing (class, classList, href, id)
import Html.Events exposing (onClick)
import Date.Extra as Date


dayPicker : Model -> Html Msg
dayPicker model =
    let
        isAllDaysActive =
            case model.activeDay of
                Just activeDay ->
                    False

                Nothing ->
                    True
    in
        div [ class "row" ]
            [ div [ id "schedule-days", class "btn-group" ]
                ([ a
                    [ classList
                        [ ( "btn", True )
                        , ( "btn-default", not isAllDaysActive )
                        , ( "btn-primary", isAllDaysActive )
                        ]
                    , href ("#")
                    , onClick (RemoveActiveDay)
                    ]
                    [ text "All Days"
                    ]
                 ]
                    ++ (List.map (\day -> dayButton day model.activeDay) model.days)
                )
            ]


dayButton : Day -> Maybe Day -> Html Msg
dayButton day activeDay =
    let
        isActive =
            case activeDay of
                Just activeDay ->
                    day == activeDay

                Nothing ->
                    False
    in
        a
            [ classList
                [ ( "btn", True )
                , ( "btn-default", not isActive )
                , ( "btn-primary", isActive )
                ]
            , href ("#day/" ++ (Date.toFormattedString "y-M-d" day.date))
            , onClick (MakeActiveday day)
            ]
            [ text day.day_name
            ]
