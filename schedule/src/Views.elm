module Views exposing (..)

-- Local modules

import Models exposing (..)
import Messages exposing (Msg(..))
import Views.DayPicker exposing (dayPicker)
import Views.DayView exposing (dayView)
import Views.EventDetail exposing (eventInstanceDetailView)
import Views.ScheduleOverview exposing (scheduleOverviewView)


-- External modules

import Html exposing (Html, Attribute, div, input, text, li, ul, a, h4, label, i, span, hr, small, p)


view : Model -> Html Msg
view model =
    div []
        [ dayPicker model
        , hr [] []
        , case model.route of
            OverviewRoute ->
                scheduleOverviewView model

            DayRoute dayIso ->
                dayView dayIso model

            EventInstanceRoute eventInstanceSlug ->
                eventInstanceDetailView eventInstanceSlug model

            NotFoundRoute ->
                div [] [ text "Not found!" ]
        ]
