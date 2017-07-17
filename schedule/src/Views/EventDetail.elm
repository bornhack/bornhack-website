module Views.EventDetail exposing (eventDetailView)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (..)


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h4, a, p, hr)
import Html.Attributes exposing (class, classList, href)
import Markdown


eventDetailView : EventSlug -> Model -> Html Msg
eventDetailView eventSlug model =
    let
        event =
            case List.head (List.filter (\e -> e.slug == eventSlug) model.events) of
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
                [ h4 []
                    [ text "Speakers" ]
                , ul
                    []
                    (List.map speakerDetail event.speakers)
                ]
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
        [ text (eventInstance.from ++ " to " ++ eventInstance.to)
        ]
