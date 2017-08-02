module Main exposing (..)

-- Local modules

import Models exposing (..)
import Routing exposing (parseLocation)
import Update exposing (update)
import Messages exposing (Msg(..))
import WebSocketCalls exposing (sendInitMessage)
import Views exposing (view)


-- External modules

import WebSocket exposing (listen)
import Navigation exposing (Location)


main : Program Flags Model Msg
main =
    Navigation.programWithFlags
        OnLocationChange
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }


init : Flags -> Location -> ( Model, Cmd Msg )
init flags location =
    let
        currentRoute =
            parseLocation location

        emptyFilter =
            Filter [] [] []

        model =
            Model [] [] [] [] [] [] flags emptyFilter location currentRoute False
    in
        model ! [ sendInitMessage flags.camp_slug flags.websocket_server ]



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    WebSocket.listen model.flags.websocket_server WebSocketPayload
