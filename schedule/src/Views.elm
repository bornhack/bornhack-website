module Views exposing (..)

-- Local modules

import Models exposing (..)
import Messages exposing (Msg(..))


-- Core modules

import Html exposing (Html, Attribute, div, input, text, li, ul, a, h4, label, i, span, hr, small, p)
import Html.Attributes exposing (class, classList, id, type_, for, style, href)
import Html.Events exposing (onClick)


-- External modules

import Markdown


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


view : Model -> Html Msg
view model =
    div []
        [ div [ class "row" ]
            [ div [ id "schedule-days", class "btn-group" ]
                (List.map (\day -> dayButton day model.activeDay) (allDaysDay :: model.days))
            ]
        , hr [] []
        , case model.route of
            OverviewRoute ->
                scheduleOverviewView model

            DayRoute dayIso ->
                dayView dayIso model

            EventInstanceRoute eventInstanceSlug ->
                eventInstanceDetailView eventInstanceSlug model

            NotFoundRoute ->
                div [] [ text "Not found!" ]
        ]


dayView : DayIso -> Model -> Html Msg
dayView dayIso model =
    div []
        [ filterSideBar model
        ]


eventInstanceDetailView : EventInstanceSlug -> Model -> Html Msg
eventInstanceDetailView eventInstanceSlug model =
    let
        eventInstance =
            case List.head (List.filter (\e -> e.slug == eventInstanceSlug) model.eventInstances) of
                Just eventInstance ->
                    eventInstance

                Nothing ->
                    emptyEventInstance

        event =
            case List.head (List.filter (\e -> e.slug == eventInstance.eventSlug) model.events) of
                Just event ->
                    event

                Nothing ->
                    { title = "", slug = "", abstract = "", speakers = [] }
    in
        div [ class "row" ]
            [ div [ class "col-sm-9" ]
                [ a [ href "#" ]
                    [ text "Back"
                    ]
                , h4 [] [ text eventInstance.title ]
                , p [] [ Markdown.toHtml [] event.abstract ]
                , hr [] []
                , h4 [] [ text "TODO: Show all instances here!" ]
                ]
            , div
                [ classList
                    [ ( "col-sm-3", True )
                    , ( "schedule-sidebar", True )
                    ]
                ]
                [ h4 [] [ text "Speakers" ]
                ]
            ]


filterSideBar : Model -> Html Msg
filterSideBar model =
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


scheduleOverviewView : Model -> Html Msg
scheduleOverviewView model =
    div [ class "row" ]
        [ filterSideBar model
        , div
            [ classList
                [ ( "col-sm-9", True )
                , ( "col-sm-pull-3", True )
                ]
            ]
            (List.map (\day -> dayRowView day model) model.days)
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
                    ((String.slice 0 10 eventInstance.from) == day.iso)
                        && List.member eventInstance.location locations
                        && List.member eventInstance.eventType types
                )
                model.eventInstances
    in
        div []
            [ h4 []
                [ text day.repr ]
            , div [ class "schedule-day-row" ]
                (List.map dayEventInstanceView filteredEventInstances)
            ]


dayEventInstanceView : EventInstance -> Html Msg
dayEventInstanceView eventInstance =
    a
        [ class "event"
        , href ("#event/" ++ eventInstance.slug)
        , style
            [ ( "background-color", eventInstance.backgroundColor )
            , ( "color", eventInstance.forgroundColor )
            ]
        ]
        [ small []
            [ text ((String.slice 11 16 eventInstance.from) ++ " - " ++ (String.slice 11 16 eventInstance.to)) ]
        , i [ classList [ ( "fa", True ), ( "fa-" ++ eventInstance.locationIcon, True ), ( "pull-right", True ) ] ] []
        , p
            []
            [ text eventInstance.title ]
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
