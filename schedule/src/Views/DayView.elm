module Views.DayView exposing (dayView)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (Model, Day, EventInstance)


-- Core modules

import Date exposing (Date)


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h4, table, p, a)
import Html.Attributes exposing (classList, style, href)
import Date.Extra


blockHeight : Int
blockHeight =
    15


headerHeight : Int
headerHeight =
    50


px : Int -> String
px value =
    (toString value) ++ "px"


dayView : Day -> Model -> Html Msg
dayView day model =
    let
        start =
            Date.Extra.add Date.Extra.Hour model.flags.schedule_midnight_offset_hours day.date

        lastHour =
            Date.Extra.add Date.Extra.Day 1 start

        minutes =
            Date.Extra.range Date.Extra.Minute 15 start lastHour

        filteredEventInstances =
            List.filter (\x -> Date.Extra.equalBy Date.Extra.Day x.from day.date) model.eventInstances
    in
        div
            [ classList [ ( "row", True ) ] ]
            [ gutter minutes
            , locationColumns minutes filteredEventInstances model.eventLocations
            ]


locationColumns minutes eventInstances eventLocations =
    let
        columnWidth =
            100.0 / toFloat (List.length eventLocations)
    in
        div
            [ style
                [ ( "display", "flex" )
                , ( "justify-content", "space-around" )
                ]
            ]
            (List.map (\x -> locationColumn columnWidth minutes eventInstances x) eventLocations)


locationColumn columnWidth minutes eventInstances location =
    let
        locationInstances =
            List.filter (\x -> x.location == location.slug) eventInstances
    in
        div
            [ style
                [ ( "width", (toString columnWidth) ++ "%" )
                ]
            , classList
                [ ( "location-column", True ) ]
            ]
            ([ div
                [ style
                    [ ( "height", px headerHeight )
                    ]
                , classList
                    [ ( "location-column-header", True )
                    ]
                ]
                [ text location.name ]
             ]
                ++ (List.map (\x -> hourBlock locationInstances x) minutes)
            )


hourBlock eventInstances minutes =
    let
        filteredEventInstances =
            List.filter (\x -> Date.Extra.equalBy Date.Extra.Minute minutes x.from) eventInstances
    in
        div
            [ style
                [ ( "display", "flex" )
                , ( "height", px blockHeight )
                ]
            , classList
                [ ( "location-column-slot", True )
                ]
            ]
            (List.map eventInstanceBlock filteredEventInstances)


eventInstanceBlock : EventInstance -> Html Msg
eventInstanceBlock eventInstance =
    let
        length =
            (toFloat (Date.Extra.diff Date.Extra.Minute eventInstance.from eventInstance.to)) / 15

        height =
            (toString (length * toFloat blockHeight)) ++ "px"
    in
        a
            [ classList
                [ ( "event", True )
                , ( "event-in-dayview", True )
                ]
            , style
                [ ( "height", height )
                , ( "background-color", eventInstance.backgroundColor )
                , ( "color", eventInstance.forgroundColor )
                ]
            , href ("#event/" ++ eventInstance.eventSlug)
            ]
            [ p [] [ text ((Date.Extra.toFormattedString "HH:mm" eventInstance.from) ++ " " ++ eventInstance.title) ]
            ]


gutter : List Date -> Html Msg
gutter hours =
    div
        [ classList
            [ ( "col-sm-1", True )
            , ( "day-view-gutter", True )
            ]
        ]
        ([ div [ style [ ( "height", px headerHeight ) ] ]
            [ text ""
            ]
         ]
            ++ (List.map gutterHour hours)
        )


gutterHour : Date -> Html Msg
gutterHour date =
    let
        textToShow =
            case Date.minute date of
                0 ->
                    (Date.Extra.toFormattedString "HH:mm" date)

                30 ->
                    (Date.Extra.toFormattedString "HH:mm" date)

                _ ->
                    ""
    in
        div [ style [ ( "height", px blockHeight ) ] ]
            [ text textToShow
            ]
