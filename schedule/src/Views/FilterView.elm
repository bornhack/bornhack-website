module Views.FilterView exposing (filterSidebar)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (Model)


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h4)
import Html.Attributes exposing (class, classList, href)
import Html.Events exposing (onClick)


filterSidebar : Model -> Html Msg
filterSidebar model =
    div
        [ classList
            [ ( "col-sm-3", True )
            , ( "col-sm-push-9", True )
            , ( "schedule-sidebar", True )
            , ( "schedule-filter", True )
            ]
        ]
        [ h4 [] [ text "Filter" ]
        , div [ class "form-group" ]
            [ filterView "Type" model.eventTypes model.filter.eventTypes ToggleEventTypeFilter
            , filterView "Location" model.eventLocations model.filter.eventLocations ToggleEventLocationFilter
            ]
        ]


filterView :
    String
    -> List { a | name : String }
    -> List { a | name : String }
    -> ({ a | name : String } -> Msg)
    -> Html Msg
filterView name possibleFilters currentFilters action =
    div []
        [ text (name ++ ":")
        , ul [] (List.map (\filter -> filterChoiceView filter currentFilters action) possibleFilters)
        ]


filterChoiceView :
    { a | name : String }
    -> List { a | name : String }
    -> ({ a | name : String } -> Msg)
    -> Html Msg
filterChoiceView filter currentFilters action =
    let
        active =
            List.member filter currentFilters

        notActive =
            not active
    in
        li []
            [ div
                [ classList
                    [ ( "btn", True )
                    , ( "btn-default", True )
                    , ( "filter-choice-active", active )
                    ]
                , onClick (action filter)
                ]
                [ span []
                    [ i [ classList [ ( "fa", True ), ( "fa-minus", active ), ( "fa-plus", notActive ) ] ] []
                    , text (" " ++ filter.name)
                    ]
                ]
            ]
