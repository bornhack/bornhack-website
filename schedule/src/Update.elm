module Update exposing (update)

-- Local modules

import Models exposing (Model, Route(OverviewRoute, EventRoute), Filter)
import Messages exposing (Msg(..))
import Decoders exposing (webSocketActionDecoder, initDataDecoder, eventDecoder)
import Routing exposing (parseLocation)


-- Core modules

import Json.Decode


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        WebSocketPayload str ->
            let
                newModel =
                    case Json.Decode.decodeString webSocketActionDecoder str of
                        Ok webSocketAction ->
                            case webSocketAction.action of
                                "init" ->
                                    case Json.Decode.decodeString initDataDecoder str of
                                        Ok m ->
                                            m model.flags Nothing (Filter [] []) model.route

                                        Err error ->
                                            model

                                _ ->
                                    model

                        Err error ->
                            model
            in
                newModel ! []

        MakeActiveday day ->
            { model | activeDay = Just day } ! []

        RemoveActiveDay ->
            { model | activeDay = Nothing } ! []

        ToggleEventTypeFilter eventType ->
            let
                eventTypesFilter =
                    if List.member eventType model.filter.eventTypes then
                        List.filter (\x -> x /= eventType) model.filter.eventTypes
                    else
                        eventType :: model.filter.eventTypes

                currentFilter =
                    model.filter

                newFilter =
                    { currentFilter | eventTypes = eventTypesFilter }
            in
                { model | filter = newFilter } ! []

        ToggleEventLocationFilter eventLocation ->
            let
                eventLocationsFilter =
                    if List.member eventLocation model.filter.eventLocations then
                        List.filter (\x -> x /= eventLocation) model.filter.eventLocations
                    else
                        eventLocation :: model.filter.eventLocations

                currentFilter =
                    model.filter

                newFilter =
                    { currentFilter | eventLocations = eventLocationsFilter }
            in
                { model | filter = newFilter } ! []

        OnLocationChange location ->
            let
                newRoute =
                    parseLocation location
            in
                { model | route = newRoute } ! []
