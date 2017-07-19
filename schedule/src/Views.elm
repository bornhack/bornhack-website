module Views exposing (..)

-- Local modules

import Models exposing (..)
import Messages exposing (Msg(..))
import Views.DayPicker exposing (dayPicker)
import Views.DayView exposing (dayView)
import Views.EventDetail exposing (eventDetailView)
import Views.ScheduleOverview exposing (scheduleOverviewView)


-- Core modules

import Date exposing (Month(..))


-- External modules

import Html exposing (Html, Attribute, div, input, text, li, ul, a, h4, label, i, span, hr, small, p)
import Date.Extra


view : Model -> Html Msg
view model =
    div []
        [ dayPicker model
        , hr [] []
        , case model.route of
            OverviewRoute ->
                scheduleOverviewView model

            DayRoute dayIso ->
                let
                    day =
                        case (List.head (List.filter (\x -> (Date.Extra.toFormattedString "y-MM-dd" x.date) == dayIso) model.days)) of
                            Just day ->
                                day

                            Nothing ->
                                Day "" (Date.Extra.fromParts 1970 Jan 1 0 0 0 0) ""
                in
                    dayView day model

            EventRoute eventSlug ->
                eventDetailView eventSlug model

            NotFoundRoute ->
                div [] [ text "Not found!" ]
        ]
