module Views.ScheduleOverview exposing (scheduleOverviewView)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (Model, Day, EventInstance)
import Views.FilterView exposing (filterSidebar)


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h4, p, small, a)
import Html.Lazy exposing (lazy, lazy2)
import Html.Attributes exposing (class, classList, href, style)
import Date.Extra as Date exposing (Interval(..), equalBy)


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
        types =
            List.map (\eventType -> eventType.slug)
                (if List.isEmpty model.filter.eventTypes then
                    model.eventTypes
                 else
                    model.filter.eventTypes
                )

        locations =
            List.map (\eventLocation -> eventLocation.slug)
                (if List.isEmpty model.filter.eventLocations then
                    model.eventLocations
                 else
                    model.filter.eventLocations
                )

        filteredEventInstances =
            List.filter
                (\eventInstance ->
                    (Date.equalBy Month eventInstance.from day.date)
                        && (Date.equalBy Date.Day eventInstance.from day.date)
                        && List.member eventInstance.location locations
                        && List.member eventInstance.eventType types
                )
                model.eventInstances
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
        [ class "event"
        , href ("#event/" ++ eventInstance.eventSlug)
        , style
            [ ( "background-color", eventInstance.backgroundColor )
            , ( "color", eventInstance.forgroundColor )
            ]
        ]
        [ small []
            [ text
                ((Date.toFormattedString "H:m" eventInstance.from)
                    ++ " - "
                    ++ (Date.toFormattedString "H:m" eventInstance.to)
                )
            ]
        , i [ classList [ ( "fa", True ), ( "fa-" ++ eventInstance.locationIcon, True ), ( "pull-right", True ) ] ] []
        , p
            []
            [ text eventInstance.title ]
        ]
