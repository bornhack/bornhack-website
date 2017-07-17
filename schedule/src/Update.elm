module Update exposing (update)

-- Local modules

import Models exposing (Model, Route(EventInstanceRoute), emptyEventInstance, allDaysDay, Filter)
import Messages exposing (Msg(..))
import Decoders exposing (webSocketActionDecoder, initDataDecoder, eventDecoder)
import Routing exposing (parseLocation)
import WebSocketCalls exposing (sendGetEventContent)


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
                                            m model.flags allDaysDay (Filter [] []) model.route

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
            { model | activeDay = day } ! []

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
                    parseLocation (Debug.log "location" location)

                onLoadCmd =
                    case newRoute of
                        EventInstanceRoute eventInstanceSlug ->
                            let
                                eventInstance =
                                    case List.head (List.filter (\x -> x.slug == eventInstanceSlug) model.eventInstances) of
                                        Just eventInstance ->
                                            eventInstance

                                        Nothing ->
                                            emptyEventInstance
                            in
                                sendGetEventContent model.flags.camp_slug eventInstance.eventSlug

                        _ ->
                            Cmd.none
            in
                { model | route = newRoute } ! [ onLoadCmd ]
