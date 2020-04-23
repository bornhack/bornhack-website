module Views exposing (..)

-- Local modules
-- Core modules
-- External modules

import Date exposing (Month(..))
import Date.Extra
import Html exposing (Attribute, Html, a, div, h4, hr, i, input, label, li, p, small, span, text, ul)
import Messages exposing (Msg(..))
import Models exposing (..)
import Views.DayPicker exposing (dayPicker)
import Views.DayView exposing (dayView)
import Views.EventDetail exposing (eventDetailView)
import Views.ScheduleOverview exposing (scheduleOverviewView)
import Views.SpeakerDetail exposing (speakerDetailView)


view : Model -> Html Msg
view model =
    case model.dataLoaded of
        True ->
            div []
                [ dayPicker model
                , hr [] []
                , case model.route of
                    OverviewRoute ->
                        scheduleOverviewView model

                    OverviewFilteredRoute _ ->
                        scheduleOverviewView model

                    DayRoute dayIso ->
                        let
                            day =
                                model.days
                                    |> List.filter (\x -> Date.Extra.toFormattedString "y-MM-dd" x.date == dayIso)
                                    |> List.head
                                    |> Maybe.withDefault (Day "" (Date.Extra.fromParts 1970 Jan 1 0 0 0 0) "")
                        in
                        dayView day model

                    EventRoute eventSlug ->
                        eventDetailView eventSlug model

                    SpeakerRoute speakerSlug ->
                        speakerDetailView speakerSlug model

                    NotFoundRoute ->
                        div [] [ text "Not found!" ]
                ]

        False ->
            h4 [] [ text "Loading schedule..." ]
