module Update exposing (update)

-- Local modules

import Models exposing (Model, Route(OverviewRoute, EventRoute), Filter)
import Messages exposing (Msg(..))
import Decoders exposing (webSocketActionDecoder, initDataDecoder, eventDecoder)
import Routing exposing (parseLocation)
import WebSocketCalls exposing (sendGetEventContent, sendInitMessage)


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
                                            let
                                                newModel_ =
                                                    m model.flags Nothing (Filter [] []) model.route
                                            in
                                                { model
                                                    | days = newModel_.days
                                                    , eventInstances = newModel_.eventInstances
                                                    , eventLocations = newModel_.eventLocations
                                                    , eventTypes = newModel_.eventTypes
                                                }

                                        Err error ->
                                            model

                                "get_event_content" ->
                                    case Json.Decode.decodeString eventDecoder str of
                                        Ok event ->
                                            { model | events = event :: model.events }

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

                onLoadCmd =
                    case newRoute of
                        EventRoute eventSlug ->
                            case List.head (List.filter (\x -> x.slug == eventSlug) model.events) of
                                Just event ->
                                    Cmd.none

                                Nothing ->
                                    sendGetEventContent model.flags.camp_slug (Debug.log "eventSlug" eventSlug)

                        OverviewRoute ->
                            case List.head model.days of
                                Just day ->
                                    Cmd.none

                                Nothing ->
                                    sendInitMessage model.flags.camp_slug

                        _ ->
                            Cmd.none
            in
                { model | route = newRoute } ! [ onLoadCmd ]
