module Views.FilterView exposing (filterSidebar, applyFilters, parseFilterFromQuery, filterToQuery, maybeFilteredOverviewRoute)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (Model, EventInstance, Filter, Day, FilterQuery, Route(OverviewRoute, OverviewFilteredRoute), VideoRecordingFilter, EventType, EventLocation)
import Routing exposing (routeToString)


-- Core modules

import Regex


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h4, small)
import Html.Attributes exposing (class, classList)
import Html.Events exposing (onClick)
import Date.Extra exposing (Interval(..), equalBy)


applyFilters : Day -> Model -> List EventInstance
applyFilters day model =
    let
        slugs default filters =
            List.map .slug
                (if List.isEmpty filters then
                    default
                 else
                    filters
                )

        types =
            slugs model.eventTypes model.filter.eventTypes

        locations =
            slugs model.eventLocations model.filter.eventLocations

        videoFilters =
            slugs videoRecordingFilters model.filter.videoRecording

        filteredEventInstances =
            List.filter
                (\eventInstance ->
                    (Date.Extra.equalBy Month eventInstance.from day.date)
                        && (Date.Extra.equalBy Date.Extra.Day eventInstance.from day.date)
                        && List.member eventInstance.location locations
                        && List.member eventInstance.eventType types
                        && List.member eventInstance.videoState videoFilters
                )
                model.eventInstances
    in
        filteredEventInstances


filterSidebar : Model -> Html Msg
filterSidebar model =
    div
        [ classList
            [ ( "col-sm-3", True )
            , ( "col-sm-push-9", True )
            , ( "schedule-sidebar", True )
            , ( "schedule-filter", True )
            , ( "sticky", True )
            ]
        ]
        [ h4 [] [ text "Filter" ]
        , div [ class "form-group" ]
            [ filterView
                "Type"
                model.eventTypes
                model.filter.eventTypes
                ToggleEventTypeFilter
                model.eventInstances
                .eventType
            , filterView
                "Location"
                model.eventLocations
                model.filter.eventLocations
                ToggleEventLocationFilter
                model.eventInstances
                .location
            , filterView
                "Video"
                videoRecordingFilters
                model.filter.videoRecording
                ToggleVideoRecordingFilter
                model.eventInstances
                .videoState
            ]
        ]


videoRecordingFilters : List VideoRecordingFilter
videoRecordingFilters =
    [ { name = "Will not be recorded", slug = "not-to-be-recorded" }
    , { name = "Will recorded", slug = "to-be-recorded" }
    , { name = "Has recording", slug = "has-recording" }
    ]


filterView :
    String
    -> List { a | name : String, slug : String }
    -> List { a | name : String, slug : String }
    -> ({ a | name : String, slug : String } -> Msg)
    -> List EventInstance
    -> (EventInstance -> String)
    -> Html Msg
filterView name possibleFilters currentFilters action eventInstances slugLike =
    div []
        [ text (name ++ ":")
        , ul []
            (possibleFilters
                |> List.map
                    (\filter ->
                        filterChoiceView
                            filter
                            currentFilters
                            action
                            eventInstances
                            slugLike
                    )
            )
        ]


filterChoiceView :
    { a | name : String, slug : String }
    -> List { a | name : String, slug : String }
    -> ({ a | name : String, slug : String } -> Msg)
    -> List EventInstance
    -> (EventInstance -> String)
    -> Html Msg
filterChoiceView filter currentFilters action eventInstances slugLike =
    let
        active =
            List.member filter currentFilters

        notActive =
            not active

        eventInstanceCount =
            eventInstances
                |> List.filter (\eventInstance -> slugLike eventInstance == filter.slug)
                |> List.length
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
                    , small [] [ text <| " (" ++ (toString eventInstanceCount) ++ ")" ]
                    ]
                ]
            ]


findFilter : List { a | slug : String } -> String -> Maybe { a | slug : String }
findFilter modelItems filterSlug =
    List.head (List.filter (\x -> x.slug == filterSlug) modelItems)


getFilter : String -> List { a | slug : String } -> String -> List { a | slug : String }
getFilter filterType modelItems query =
    let
        filterMatch =
            query
                |> Regex.find (Regex.AtMost 1) (Regex.regex (filterType ++ "=([\\w,_-]+)&*"))
                |> List.concatMap .submatches
                |> List.head
                |> Maybe.withDefault Nothing
                |> Maybe.withDefault ""

        filterSlugs =
            String.split "," filterMatch
    in
        List.filterMap (\x -> findFilter modelItems x) filterSlugs


parseFilterFromQuery : FilterQuery -> Model -> Filter
parseFilterFromQuery query model =
    let
        types =
            getFilter "type" model.eventTypes query

        locations =
            getFilter "location" model.eventLocations query

        videoFilters =
            getFilter "video" videoRecordingFilters query
    in
        { eventTypes = types
        , eventLocations = locations
        , videoRecording = videoFilters
        }


filterToString : Filter -> String
filterToString filter =
    let
        typePart =
            case String.join "," (List.map .slug filter.eventTypes) of
                "" ->
                    ""

                types ->
                    "type=" ++ types

        locationPart =
            case String.join "," (List.map .slug filter.eventLocations) of
                "" ->
                    ""

                locations ->
                    "location=" ++ locations

        videoPart =
            case String.join "," (List.map .slug filter.videoRecording) of
                "" ->
                    ""

                video ->
                    "video=" ++ video
    in
        String.join "&" (List.filter (\x -> x /= "") [ typePart, locationPart, videoPart ])


filterToQuery : Filter -> FilterQuery
filterToQuery filter =
    let
        result =
            filterToString filter
    in
        routeToString <| OverviewFilteredRoute result


maybeFilteredOverviewRoute : Model -> Route
maybeFilteredOverviewRoute model =
    case filterToString model.filter of
        "" ->
            OverviewRoute

        query ->
            OverviewFilteredRoute query
