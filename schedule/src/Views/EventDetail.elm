module Views.EventDetail exposing (eventDetailView)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (..)


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

        eventInstances =
            List.filter (\instance -> instance.eventSlug == eventSlug) model.eventInstances
    in
        case event of
            Just event ->
                div [ class "row" ]
                    [ eventDetailContent event
                    , eventDetailSidebar event eventInstances
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
        , p [] [ Markdown.toHtml [] event.abstract ]
        ]


eventDetailSidebar : Event -> List EventInstance -> Html Msg
eventDetailSidebar event eventInstances =
    let
        videoRecordingLink =
            case event.videoUrl of
                "" ->
                    []

                _ ->
                    [ a [ href event.videoUrl, classList [ ( "btn", True ), ( "btn-success", True ) ] ]
                        [ i [ classList [ ( "fa", True ), ( "fa-film", True ) ] ] []
                        , text " Watch recording here!"
                        ]
                    ]
    in
        div
            [ classList
                [ ( "col-sm-3", True )
                , ( "schedule-sidebar", True )
                , ( "sticky", True )
                ]
            ]
            (videoRecordingLink
                ++ [ speakerSidebar event.speakers
                   , eventMetaDataSidebar event
                   , eventInstancesSidebar eventInstances
                   ]
            )


eventMetaDataSidebar : Event -> Html Msg
eventMetaDataSidebar event =
    let
        videoRecording =
            case event.videoRecording of
                True ->
                    "Yes"

                False ->
                    "No"
    in
        div []
            [ h4 [] [ text "Metadata" ]
            , ul []
                [ li [] [ strong [] [ text "Type: " ], text event.eventType ]
                , li [] [ strong [] [ text "Recording: " ], text videoRecording ]
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
        [ text speaker.name
        ]


eventInstancesSidebar : List EventInstance -> Html Msg
eventInstancesSidebar eventInstances =
    div []
        [ h4 []
            [ text "This event will occur at:" ]
        , ul
            []
            (List.map eventInstanceItem eventInstances)
        ]


eventInstanceItem : EventInstance -> Html Msg
eventInstanceItem eventInstance =
    let
        toFormat =
            if Date.day eventInstance.from == Date.day eventInstance.to then
                "HH:mm"
            else
                "E HH:mm"
    in
        li []
            [ text
                ((Date.Extra.toFormattedString "E HH:mm" eventInstance.from)
                    ++ " to "
                    ++ (Date.Extra.toFormattedString toFormat eventInstance.to)
                )
            ]
