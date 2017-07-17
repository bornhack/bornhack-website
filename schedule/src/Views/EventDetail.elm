module Views.EventDetail exposing (eventInstanceDetailView)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (..)


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h4, a, p, hr)
import Html.Attributes exposing (class, classList, href)
import Markdown


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
