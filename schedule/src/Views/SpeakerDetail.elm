module Views.SpeakerDetail exposing (..)

-- Local modules
-- External modules

import Html exposing (Html, a, div, h3, i, img, li, p, text, ul)
import Html.Attributes exposing (classList, href, src)
import Html.Events exposing (onClick)
import Markdown
import Messages exposing (Msg(..))
import Models exposing (Event, Model, Route(..), Speaker, SpeakerSlug)
import Routing exposing (routeToString)


speakerDetailView : SpeakerSlug -> Model -> Html Msg
speakerDetailView speakerSlug model =
    let
        speaker =
            model.speakers
                |> List.filter (\speaker -> speaker.slug == speakerSlug)
                |> List.head
    in
    case speaker of
        Just speaker ->
            div []
                [ a [ onClick BackInHistory, classList [ ( "btn", True ), ( "btn-default", True ) ] ]
                    [ i [ classList [ ( "fa", True ), ( "fa-chevron-left", True ) ] ] []
                    , text " Back"
                    ]
                , h3 [] [ text speaker.name ]
                , div [] [ Markdown.toHtml [] speaker.biography ]
                , speakerEvents speaker model
                ]

        Nothing ->
            div [] [ text "Unknown speaker..." ]


speakerEvents : Speaker -> Model -> Html Msg
speakerEvents speaker model =
    let
        events =
            model.events
                |> List.filter (\event -> List.member speaker.slug event.speakerSlugs)
    in
    case events of
        [] ->
            p [] [ text "This speaker has no events!" ]

        events ->
            div []
                [ h3 [] [ text "Events:" ]
                , ul []
                    (List.map
                        eventItem
                        events
                    )
                ]


eventItem : Event -> Html Msg
eventItem event =
    li []
        [ a [ href <| routeToString <| EventRoute event.slug ] [ text event.title ] ]
