module Views.DayPicker exposing (..)

-- Local modules

import Models exposing (..)
import Messages exposing (Msg(..))


-- External modules

import Html exposing (Html, text, a, div)
import Html.Attributes exposing (class, classList, href, id)
import Html.Events exposing (onClick)


dayPicker : Model -> Html Msg
dayPicker model =
    div [ class "row" ]
        [ div [ id "schedule-days", class "btn-group" ]
            (List.map (\day -> dayButton day model.activeDay) (allDaysDay :: model.days))
        ]


dayButton : Day -> Day -> Html Msg
dayButton day activeDay =
    a
        [ classList
            [ ( "btn", True )
            , ( "btn-default", day /= activeDay )
            , ( "btn-primary", day == activeDay )
            ]
        , onClick (MakeActiveday day)
        , href
            ("#"
                ++ case day.iso of
                    "" ->
                        ""

                    iso ->
                        "day/" ++ iso
            )
        ]
        [ text day.day_name
        ]
