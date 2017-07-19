module Views.FilterView exposing (filterSidebar, applyFilters)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (Model, EventInstance)


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h4)
import Html.Attributes exposing (class, classList, href)
import Html.Events exposing (onClick)
import Date.Extra exposing (Interval(..), equalBy)


applyFilters day model =
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

        videoFilters =
            List.map (\filter -> filter.filter)
                (if List.isEmpty model.filter.videoRecording then
                    videoRecordingFilters
                 else
                    model.filter.videoRecording
                )

        filteredEventInstances =
            List.filter
                (\eventInstance ->
                    (Date.Extra.equalBy Month eventInstance.from day.date)
                        && (Date.Extra.equalBy Date.Extra.Day eventInstance.from day.date)
                        && List.member eventInstance.location locations
                        && List.member eventInstance.eventType types
                        && applyVideoRecordingFilters videoFilters eventInstance
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
            ]
        ]
        [ h4 [] [ text "Filter" ]
        , div [ class "form-group" ]
            [ filterView "Type" model.eventTypes model.filter.eventTypes ToggleEventTypeFilter
            , filterView "Location" model.eventLocations model.filter.eventLocations ToggleEventLocationFilter
            , filterView "Video" videoRecordingFilters model.filter.videoRecording ToggleVideoRecordingFilter
            ]
        ]


notRecordedFilter : EventInstance -> Bool
notRecordedFilter eventInstance =
    eventInstance.videoRecording == False


recordedFilter : EventInstance -> Bool
recordedFilter eventInstance =
    eventInstance.videoRecording == True


hasRecordingFilter : EventInstance -> Bool
hasRecordingFilter eventInstance =
    eventInstance.videoUrl /= ""


videoRecordingFilters : List { name : String, filter : EventInstance -> Bool }
videoRecordingFilters =
    [ { name = "Will not be recorded", filter = notRecordedFilter }
    , { name = "Will recorded", filter = recordedFilter }
    , { name = "Has recording", filter = hasRecordingFilter }
    ]


applyVideoRecordingFilters : List (EventInstance -> Bool) -> EventInstance -> Bool
applyVideoRecordingFilters filters eventInstance =
    let
        results =
            List.map (\filter -> filter eventInstance) filters
    in
        List.member True results


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
