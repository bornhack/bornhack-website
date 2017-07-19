module Views.EventDetail exposing (eventDetailView)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (..)


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h4, a, p, hr)
import Html.Attributes exposing (class, classList, href)
import Html.Events exposing (onClick)
import Markdown
import Date.Extra


eventDetailView : EventSlug -> Model -> Html Msg
eventDetailView eventSlug model =
    let
        event =
            case List.head (List.filter (\e -> e.slug == eventSlug) model.events) of
                Just event ->
                    event

                Nothing ->
                    { title = "", slug = "", abstract = "", speakers = [], videoRecording = False, videoUrl = "" }
    in
        div [ class "row" ]
            [ div [ class "col-sm-9" ]
                [ a [ onClick BackInHistory, classList [ ( "btn", True ), ( "btn-default", True ) ] ]
                    [ i [ classList [ ( "fa", True ), ( "fa-chevron-left", True ) ] ] []
                    , text " Back"
                    ]
                , h4 [] [ text event.title ]
                , p [] [ Markdown.toHtml [] event.abstract ]
                , hr [] []
                , eventInstancesList eventSlug model.eventInstances
                ]
            , div
                [ classList
                    [ ( "col-sm-3", True )
                    , ( "schedule-sidebar", True )
                    ]
                ]
                [ videoRecordingSidebar event
                , speakerSidebar event.speakers
                ]
            ]


videoRecordingSidebar : Event -> Html Msg
videoRecordingSidebar event =
    let
        ( video, willBeRecorded ) =
            if event.videoUrl /= "" then
                ( h4 [] [ text "Watch the video here!" ], True )
            else if event.videoRecording == True then
                ( h4 [] [ text "This event will be recorded!" ], True )
            else
                ( h4 [] [ text "This event will NOT be recorded!" ], False )
    in
        div [ classList [ ( "alert", True ), ( "alert-danger", not willBeRecorded ), ( "alert-info", willBeRecorded ) ] ]
            [ video ]


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


eventInstancesList : String -> List EventInstance -> Html Msg
eventInstancesList eventSlug eventInstances =
    let
        instances =
            List.filter (\instance -> instance.eventSlug == eventSlug) eventInstances
    in
        div []
            [ h4 []
                [ text "This event will occur at:" ]
            , ul
                []
                (List.map eventInstanceItem instances)
            ]


eventInstanceItem : EventInstance -> Html Msg
eventInstanceItem eventInstance =
    li []
        [ text
            ((Date.Extra.toFormattedString "y-MM-dd HH:mm" eventInstance.from)
                ++ " to "
                ++ (Date.Extra.toFormattedString "y-MM-d HH:mm" eventInstance.to)
            )
        ]
