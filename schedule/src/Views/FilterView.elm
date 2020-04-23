module Views.FilterView exposing (applyFilters, filterSidebar, filterToQuery, maybeFilteredOverviewRoute, parseFilterFromQuery)

-- Local modules
-- Core modules
-- External modules

import Date.Extra exposing (Interval(..), equalBy)
import Html exposing (Html, a, div, h4, i, li, small, span, text, ul)
import Html.Attributes exposing (class, classList, href, style)
import Html.Events exposing (onClick)
import Messages exposing (Msg(..))
import Models exposing (Day, EventInstance, Filter, FilterQuery, FilterType(..), Model, Route(..), getSlugFromFilterType, unpackFilterType)
import Regex
import Routing exposing (routeToString)


applyFilters : Day -> Model -> List EventInstance
applyFilters day model =
    let
        slugs default filters =
            List.map getSlugFromFilterType
                (if List.isEmpty filters then
                    default

                 else
                    filters
                )

        types =
            slugs model.eventTypes model.filter.eventTypes

        locations =
            slugs model.eventLocations model.filter.eventLocations

        tracks =
            slugs model.eventTracks model.filter.eventTracks

        videoFilters =
            slugs videoRecordingFilters model.filter.videoRecording

        filteredEventInstances =
            List.filter
                (\eventInstance ->
                    Date.Extra.equalBy Month eventInstance.from day.date
                        && Date.Extra.equalBy Date.Extra.Day eventInstance.from day.date
                        && List.member eventInstance.location locations
                        && List.member eventInstance.eventType types
                        && List.member eventInstance.eventTrack tracks
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
            , ( "schedule-filter", True )
            ]
        ]
        [ h4 [] [ text "Filter" ]
        , div [ class "form-group" ]
            [ filterView
                "Type"
                model.eventTypes
                model.filter.eventTypes
                model.eventInstances
                .eventType
            , filterView
                "Location"
                model.eventLocations
                model.filter.eventLocations
                model.eventInstances
                .location
            , filterView
                "Track"
                model.eventTracks
                model.filter.eventTracks
                model.eventInstances
                .eventTrack
            , filterView
                "Video"
                videoRecordingFilters
                model.filter.videoRecording
                model.eventInstances
                .videoState
            ]
        , icsButton model
        ]


icsButton : Model -> Html Msg
icsButton model =
    let
        filterString =
            case filterToString model.filter of
                "" ->
                    ""

                filter ->
                    "?" ++ filter

        icsURL =
            model.flags.ics_button_href ++ filterString
    in
    a
        [ classList
            [ ( "btn", True )
            , ( "btn-default", True )
            ]
        , href <| icsURL
        ]
        [ i [ classList [ ( "fa", True ), ( "fa-calendar", True ) ] ]
            []
        , text " ICS file with these filters"
        ]


videoRecordingFilters : List FilterType
videoRecordingFilters =
    [ VideoFilter "Will not be recorded" "not-to-be-recorded"
    , VideoFilter "Will be recorded" "to-be-recorded"
    , VideoFilter "Has recording" "has-recording"
    ]


filterView :
    String
    -> List FilterType
    -> List FilterType
    -> List EventInstance
    -> (EventInstance -> String)
    -> Html Msg
filterView name possibleFilters currentFilters eventInstances slugLike =
    div []
        [ text (name ++ ":")
        , ul []
            (possibleFilters
                |> List.map
                    (\filter ->
                        filterChoiceView
                            filter
                            currentFilters
                            eventInstances
                            slugLike
                    )
            )
        ]


filterChoiceView :
    FilterType
    -> List FilterType
    -> List EventInstance
    -> (EventInstance -> String)
    -> Html Msg
filterChoiceView filter currentFilters eventInstances slugLike =
    let
        active =
            List.member filter currentFilters

        notActive =
            not active

        ( name, slug ) =
            unpackFilterType filter

        eventInstanceCount =
            eventInstances
                |> List.filter (\eventInstance -> slugLike eventInstance == slug)
                |> List.length

        buttonStyle =
            case filter of
                TypeFilter _ _ color lightText ->
                    [ style "backgroundColor" color
                    , style "color"
                        (if lightText then
                            "#fff"

                         else
                            "#000"
                        )
                    , style "border" "1px solid black"
                    , style "margin-bottom" "2px"
                    ]

                _ ->
                    []

        locationIcon =
            case filter of
                LocationFilter _ _ icon ->
                    [ i
                        [ classList
                            [ ( "fa", True )
                            , ( "fa-" ++ icon, True )
                            , ( "pull-right", True )
                            ]
                        ]
                        []
                    ]

                _ ->
                    []

        videoIcon =
            case filter of
                VideoFilter _ slug ->
                    let
                        icon =
                            case slug of
                                "has-recording" ->
                                    "film"

                                "to-be-recorded" ->
                                    "video"

                                "not-to-be-recorded" ->
                                    "video-slash"

                                _ ->
                                    ""
                    in
                    [ i
                        [ classList
                            [ ( "fa", True )
                            , ( "fa-" ++ icon, True )
                            , ( "pull-right", True )
                            ]
                        ]
                        []
                    ]

                _ ->
                    []
    in
    li
        []
        [ div
            ([ classList
                [ ( "btn", True )
                , ( "btn-default", True )
                , ( "filter-choice-active", active )
                ]
             , onClick (ToggleFilter filter)
             ]
                ++ buttonStyle
            )
            [ span []
                ([ span [ classList [ ( "pull-left", True ) ] ]
                    [ i
                        [ classList
                            [ ( "fa", True )
                            , ( "fa-minus", active )
                            , ( "fa-plus", notActive )
                            ]
                        ]
                        []
                    , text (" " ++ name)
                    , small [] [ text <| " (" ++ String.fromInt eventInstanceCount ++ ")" ]
                    ]
                 ]
                    ++ locationIcon
                    ++ videoIcon
                )
            ]
        ]


findFilter : List FilterType -> String -> Maybe FilterType
findFilter modelItems filterSlug =
    List.head
        (List.filter
            (\x ->
                let
                    ( _, slug ) =
                        unpackFilterType x
                in
                slug == filterSlug
            )
            modelItems
        )


getFilter : String -> List FilterType -> String -> List FilterType
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

        tracks =
            getFilter "tracks" model.eventTracks query

        videoFilters =
            getFilter "video" videoRecordingFilters query
    in
    { eventTypes = types
    , eventLocations = locations
    , eventTracks = tracks
    , videoRecording = videoFilters
    }


filterToString : Filter -> String
filterToString filter =
    let
        typePart =
            case String.join "," (List.map getSlugFromFilterType filter.eventTypes) of
                "" ->
                    ""

                types ->
                    "type=" ++ types

        locationPart =
            case String.join "," (List.map getSlugFromFilterType filter.eventLocations) of
                "" ->
                    ""

                locations ->
                    "location=" ++ locations

        videoPart =
            case String.join "," (List.map getSlugFromFilterType filter.videoRecording) of
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
