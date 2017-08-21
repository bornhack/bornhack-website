module Views.DayView exposing (dayView)

-- Local modules

import Messages exposing (Msg(..))
import Models exposing (Model, Day, EventInstance, Route(EventRoute), FilterType(..), getSlugFromFilterType, getNameFromFilterType)
import Routing exposing (routeToString)


-- Core modules

import Date exposing (Date)


-- External modules

import Html exposing (Html, text, div, ul, li, span, i, h4, table, p, a)
import Html.Attributes exposing (classList, style, href, alt, title)
import Date.Extra
import List.Extra


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
            , locationColumns filteredEventInstances model.eventLocations model.flags.schedule_midnight_offset_hours minutes
            ]


locationColumns : List EventInstance -> List FilterType -> Int -> List Date -> Html Msg
locationColumns eventInstances eventLocations offset minutes =
    let
        columnWidth =
            100.0 / toFloat (List.length eventLocations)
    in
        div
            [ style
                [ ( "display", "flex" )
                , ( "justify-content", "space-around" )
                ]
            , classList
                [ ( "col-sm-11", True )
                ]
            ]
            (List.map (\location -> locationColumn columnWidth eventInstances offset minutes location) eventLocations)


locationColumn : Float -> List EventInstance -> Int -> List Date -> FilterType -> Html Msg
locationColumn columnWidth eventInstances offset minutes location =
    let
        locationInstances =
            List.filter (\instance -> instance.location == getSlugFromFilterType location) eventInstances

        overlappingGroups =
            List.Extra.groupWhile
                (\instanceA instanceB ->
                    (Date.Extra.isBetween instanceB.from instanceB.to instanceA.from) && not (Date.Extra.equal instanceA.from instanceB.to)
                )
                locationInstances
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
                [ text <| getNameFromFilterType location ]
             ]
                ++ (List.map
                        (\x ->
                            div
                                [ style
                                    [ ( "backgroundColor"
                                      , if Date.minute x == 30 || Date.minute x == 45 then
                                            "#f8f8f8"
                                        else
                                            "#fff"
                                      )
                                    , ( "height", px blockHeight )
                                    ]
                                ]
                                []
                        )
                        minutes
                   )
                ++ (List.map (\group -> renderGroup offset group) overlappingGroups)
            )


renderGroup : Int -> List EventInstance -> Html Msg
renderGroup offset group =
    let
        sortedGroup =
            List.sortWith
                (\x y ->
                    case Date.Extra.compare x.from y.from of
                        z ->
                            z
                )
                group

        findLefts instanceA =
            ( instanceA
            , List.foldl
                (+)
                0
                (List.map
                    (\instanceB ->
                        if instanceA == instanceB then
                            0
                        else if (Date.Extra.equal instanceB.from instanceA.from) && (Date.Extra.equal instanceB.to instanceA.to) then
                            -- Set to 0 and then fix it further down in the code
                            0
                        else if (Date.Extra.equal instanceB.from instanceA.from) && not (Date.Extra.equal instanceB.to instanceA.to) then
                            -- Set to 0 and then fix it further down in the code
                            0
                        else if (Date.Extra.isBetween instanceB.from instanceB.to instanceA.from) then
                            1
                        else
                            0
                    )
                    sortedGroup
                )
            )

        lefts =
            List.map findLefts sortedGroup

        numberInGroup =
            lefts
                |> List.map (\( _, left ) -> left)
                |> List.maximum
                |> Maybe.withDefault 1

        fixedLefts =
            if numberInGroup == 0 then
                List.map
                    (\( instance, x ) ->
                        ( instance
                        , lefts
                            |> List.Extra.elemIndex ( instance, x )
                            |> Maybe.withDefault 0
                        )
                    )
                    lefts
            else
                lefts

        fixedNumberInGroup =
            fixedLefts
                |> List.map (\( _, left ) -> left)
                |> List.maximum
                |> Maybe.withDefault 1
    in
        div
            [ style
                [ ( "display", "flex" )
                ]
            ]
            (List.map (\instance -> eventInstanceBlock offset fixedNumberInGroup instance) fixedLefts)


eventInstanceBlock : Int -> Int -> ( EventInstance, Int ) -> Html Msg
eventInstanceBlock offset numberInGroup ( eventInstance, lefts ) =
    let
        length =
            (toFloat (Date.Extra.diff Date.Extra.Minute eventInstance.from eventInstance.to)) / 15

        height =
            (toString (length * toFloat blockHeight)) ++ "px"

        hourInMinutes =
            (Date.hour eventInstance.from) * 60

        minutes =
            Date.minute eventInstance.from

        topOffset =
            ((((toFloat (hourInMinutes + minutes)) / 60)
                - (toFloat offset)
             )
                * 4.0
                * (toFloat blockHeight)
            )
                + (toFloat headerHeight)

        width =
            100 / (toFloat (numberInGroup + 1))

        timeInString =
            (Date.Extra.toFormattedString "HH:mm" eventInstance.from)
    in
        a
            [ classList
                [ ( "event", True )
                , ( "event-in-dayview", True )
                ]
            , style
                [ ( "height", height )
                , ( "width", (toString width) ++ "%" )
                , ( "top", (toString topOffset) ++ "px" )
                , ( "left", (toString (toFloat (lefts) * width)) ++ "%" )
                , ( "background-color", eventInstance.backgroundColor )
                , ( "color", eventInstance.forgroundColor )
                ]
            , href <| routeToString <| EventRoute eventInstance.eventSlug
            ]
            [ p
                [ title <|
                    timeInString
                        ++ " "
                        ++ eventInstance.title
                ]
                [ text <| timeInString ++ " " ++ (ellipsis 20 eventInstance.title) ]
            ]


ellipsis : Int -> String -> String
ellipsis cutOff value =
    if String.length value > cutOff then
        (value
            |> String.dropRight ((String.length value) - cutOff)
        )
            ++ "..."
    else
        value


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
