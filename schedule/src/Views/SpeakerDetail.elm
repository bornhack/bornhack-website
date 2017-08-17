module Views.SpeakerDetail exposing (..)

-- Local modules

import Messages exposing (Msg(BackInHistory))
import Models exposing (Model, SpeakerSlug, Speaker, Route(EventRoute), Event)
import Routing exposing (routeToString)


-- External modules

import Html exposing (Html, div, text, a, i, h3, img, ul, li, p)
import Html.Attributes exposing (classList, src, href)
import Html.Events exposing (onClick)
import Markdown


speakerDetailView : SpeakerSlug -> Model -> Html Msg
speakerDetailView speakerSlug model =
    let
        speaker =
            model.speakers
                |> List.filter (\speaker -> speaker.slug == speakerSlug)
                |> List.head

        image =
            case speaker of
                Just speaker ->
                    case speaker.smallPictureUrl of
                        Just smallPictureUrl ->
                            [ img [ src smallPictureUrl ] [] ]

                        Nothing ->
                            []

                Nothing ->
                    []
    in
        case speaker of
            Just speaker ->
                div []
                    ([ a [ onClick BackInHistory, classList [ ( "btn", True ), ( "btn-default", True ) ] ]
                        [ i [ classList [ ( "fa", True ), ( "fa-chevron-left", True ) ] ] []
                        , text " Back"
                        ]
                     , h3 [] [ text speaker.name ]
                     , div [] [ Markdown.toHtml [] speaker.biography ]
                     , speakerEvents speaker model
                     ]
                        ++ image
                    )

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
