module Main exposing (..)

-- Local modules

import Models exposing (..)
import Routing exposing (parseLocation)
import Update exposing (update)
import Messages exposing (Msg(..))
import WebSocketCalls exposing (scheduleServer, sendInitMessage)
import Views exposing (view)


-- External modules

import Html.Lazy exposing (lazy)
import WebSocket exposing (listen)
import Navigation exposing (Location)


main : Program Flags Model Msg
main =
    Navigation.programWithFlags
        OnLocationChange
        { init = init
        , view = lazy view
        , update = update
        , subscriptions = subscriptions
        }


init : Flags -> Location -> ( Model, Cmd Msg )
init flags location =
    let
        currentRoute =
            parseLocation location

        emptyFilter =
            Filter [] []

        initModel =
            (Model [] [] [] [] [] flags Nothing emptyFilter currentRoute)

        -- To ensure we load data on right momens we call update with the
        -- OnLocationChange message which is in charge of all that
        ( model, cmd ) =
            update (OnLocationChange location) initModel
    in
        model ! [ cmd ]



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    WebSocket.listen scheduleServer WebSocketPayload
