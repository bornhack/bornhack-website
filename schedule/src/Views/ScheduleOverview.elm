module Views.ScheduleOverview exposing (scheduleOverviewView)

-- Local modules
-- External modules

import Date.Extra
import Html exposing (Html, a, div, h4, i, li, p, small, span, text, ul)
import Html.Attributes exposing (class, classList, href, style)
import Html.Lazy exposing (lazy, lazy2)
import Messages exposing (Msg(..))
import Models exposing (Day, EventInstance, Filter, Model, Route(..))
import Routing exposing (routeToString)
import Views.FilterView exposing (applyFilters, filterSidebar, parseFilterFromQuery)


scheduleOverviewView : Model -> Html Msg
scheduleOverviewView model =
    div [ class "row" ]
        [ filterSidebar model
        , div
            [ classList
                [ ( "col-sm-9", True )
                , ( "col-sm-pull-3", True )
                ]
            ]
            (List.map (\day -> lazy2 dayRowView day model) model.days)
        ]


dayRowView : Day -> Model -> Html Msg
dayRowView day model =
    let
        filteredEventInstances =
            applyFilters day model
    in
    div []
        [ h4 []
            [ text day.repr ]
        , div [ class "schedule-day-row" ]
            (List.map (lazy dayEventInstanceView) filteredEventInstances)
        ]


dayEventInstanceView : EventInstance -> Html Msg
dayEventInstanceView eventInstance =
    a
        [ classList
            [ ( "event", True )
            , ( "event-in-overview", True )
            ]
        , href <| routeToString <| EventRoute eventInstance.eventSlug
        , style "background-color" eventInstance.backgroundColor
        , style "color" eventInstance.forgroundColor
        ]
        ([ small []
            [ text
                (Date.Extra.toFormattedString "HH:mm" eventInstance.from
                    ++ " - "
                    ++ Date.Extra.toFormattedString "HH:mm" eventInstance.to
                )
            ]
         ]
            ++ dayEventInstanceIcons eventInstance
            ++ [ p
                    []
                    [ text eventInstance.title ]
               ]
        )


dayEventInstanceIcons : EventInstance -> List (Html Msg)
dayEventInstanceIcons eventInstance =
    let
        videoIcon =
            case eventInstance.videoState of
                "has-recording" ->
                    [ i
                        [ classList [ ( "fa", True ), ( "fa-film", True ), ( "pull-right", True ), ( "fa-fw", True ) ] ]
                        []
                    ]

                "to-be-recorded" ->
                    [ i
                        [ classList [ ( "fa", True ), ( "fa-video", True ), ( "pull-right", True ), ( "fa-fw", True ) ] ]
                        []
                    ]

                "not-to-be-recorded" ->
                    [ i
                        [ classList [ ( "fa", True ), ( "fa-video-slash", True ), ( "pull-right", True ), ( "fa-fw", True ) ] ]
                        []
                    ]

                _ ->
                    []
    in
    [ i [ classList [ ( "fa", True ), ( "fa-" ++ eventInstance.locationIcon, True ), ( "pull-right", True ), ( "fa-fw", True ) ] ] []
    ]
        ++ videoIcon
