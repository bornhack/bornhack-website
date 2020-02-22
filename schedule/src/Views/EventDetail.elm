module Views.EventDetail exposing (eventDetailView)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (..)
import Routing exposing (routeToString)


-- Core modules

import Date


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h3, h4, a, p, hr, strong)
import Html.Attributes exposing (class, classList, href)
import Html.Events exposing (onClick)
import Markdown
import Date.Extra


eventDetailView : EventSlug -> Model -> Html Msg
eventDetailView eventSlug model =
    let
        event =
            model.events
                |> List.filter (\e -> e.slug == eventSlug)
                |> List.head
    in
        case event of
            Just event ->
                div [ class "row" ]
                    [ eventDetailContent event
                    , eventDetailSidebar event model
                    ]

            Nothing ->
                div [ class "row" ]
                    [ h4 [] [ text "Event not found." ]
                    , a [ href "#" ] [ text "Click here to go the schedule overview." ]
                    ]


eventDetailContent : Event -> Html Msg
eventDetailContent event =
    div [ class "col-sm-9" ]
        [ a [ onClick BackInHistory, classList [ ( "btn", True ), ( "btn-default", True ) ] ]
            [ i [ classList [ ( "fa", True ), ( "fa-chevron-left", True ) ] ] []
            , text " Back"
            ]
        , h3 [] [ text event.title ]
        , div [] [ Markdown.toHtml [] event.abstract ]
        ]


getSpeakersFromSlugs : List Speaker -> List SpeakerSlug -> List Speaker -> List Speaker
getSpeakersFromSlugs speakers slugs collectedSpeakers =
    case speakers of
        [] ->
            collectedSpeakers

        speaker :: rest ->
            let
                foundSlug =
                    slugs
                        |> List.filter (\slug -> slug == speaker.slug)
                        |> List.head

                foundSpeaker =
                    case foundSlug of
                        Just slug ->
                            [ speaker ]

                        Nothing ->
                            []

                newSlugs =
                    case foundSlug of
                        Just slug ->
                            List.filter (\x -> x /= slug) slugs

                        Nothing ->
                            slugs

                newCollectedSpeakers =
                    collectedSpeakers ++ foundSpeaker
            in
                case slugs of
                    [] ->
                        collectedSpeakers

                    _ ->
                        getSpeakersFromSlugs rest newSlugs newCollectedSpeakers


eventDetailSidebar : Event -> Model -> Html Msg
eventDetailSidebar event model =
    let
        videoRecordingLink =
            case event.videoUrl of
                Nothing ->
                    []

                Just url ->
                    [ a [ href url, classList [ ( "btn", True ), ( "btn-success", True ) ] ]
                        [ i [ classList [ ( "fa", True ), ( "fa-film", True ) ] ] []
                        , text " Watch recording here!"
                        ]
                    ]

        eventInstances =
            List.filter (\instance -> instance.eventSlug == event.slug) model.eventInstances

        speakers =
            getSpeakersFromSlugs model.speakers event.speakerSlugs []
    in
        div
            [ classList
                [ ( "col-sm-3", True )
                ]
            ]
            (videoRecordingLink
                ++ [ speakerSidebar speakers
                   , eventMetaDataSidebar event eventInstances model
                   ]
            )


eventMetaDataSidebar : Event -> List EventInstance -> Model -> Html Msg
eventMetaDataSidebar event eventInstances model =
    let
        ( showVideoRecoring, videoRecording ) =
            case event.videoState of
                "to-be-recorded" ->
                    ( True, "Yes" )

                "not-to-be-recorded" ->
                    ( True, "No" )

                _ ->
                    ( False, "" )

        eventInstanceMetaData =
            case eventInstances of
                [ instance ] ->
                    eventInstanceItem instance model

                instances ->
                    [ h4 []
                        [ text "Multiple occurences:" ]
                    , ul
                        []
                        (List.map (\ei -> li [] <| eventInstanceItem ei model) instances)
                    ]

        feedbackUrl =
            [a [href <| "https://bornhack.dk/" ++ model.flags.camp_slug ++ "/program/" ++ event.slug ++ "/feedback/create/" ] [text "Give feedback"]]
    in
        div []
            ([ h4 [] [ text "Metadata" ]
             , ul []
                ([ li [] [ strong [] [ text "Type: " ], text event.eventType ]
                 ]
                    ++ (case showVideoRecoring of
                            True ->
                                [ li [] [ strong [] [ text "Recording: " ], text videoRecording ] ]

                            False ->
                                []
                       )
                )
             ]
                ++ eventInstanceMetaData
                ++ feedbackUrl
            )


eventInstanceItem : EventInstance -> Model -> List (Html Msg)
eventInstanceItem eventInstance model =
    let
        toFormat =
            if Date.day eventInstance.from == Date.day eventInstance.to then
                "HH:mm"
            else
                "E HH:mm"

        ( locationName, _ ) =
            model.eventLocations
                |> List.map unpackFilterType
                |> List.filter
                    (\( _, locationSlug ) ->
                        locationSlug == eventInstance.location
                    )
                |> List.head
                |> Maybe.withDefault ( "Unknown", "" )
    in
        [ p []
            [ strong [] [ text "When: " ]
            , text
                ((Date.Extra.toFormattedString "E HH:mm" eventInstance.from)
                    ++ " to "
                    ++ (Date.Extra.toFormattedString toFormat eventInstance.to)
                )
            ]
        , p []
            [ strong [] [ text "Where: " ]
            , text <| locationName ++ " "
            , i [ classList [ ( "fa", True ), ( "fa-" ++ eventInstance.locationIcon, True ) ] ] []
            ]
        ]


speakerSidebar : List Speaker -> Html Msg
speakerSidebar speakers =
    div []
        [ h4 []
            [ text "Speakers" ]
        , ul
            []
            (List.map speakerDetail speakers)
        ]


speakerDetail : Speaker -> Html Msg
speakerDetail speaker =
    li []
        [ a [ href <| routeToString <| SpeakerRoute speaker.slug ] [ text speaker.name ]
        ]
