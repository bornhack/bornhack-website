module Update exposing (update)

-- Local modules

import Models exposing (Model, Route(..), Filter, FilterType(..))
import Messages exposing (Msg(..))
import Decoders exposing (webSocketActionDecoder, initDataDecoder, eventDecoder)
import Routing exposing (parseLocation)
import Views.FilterView exposing (parseFilterFromQuery, filterToQuery)


-- Core modules

import Json.Decode


-- External modules

import Navigation


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
                                            m model.flags model.filter model.location model.route True

                                        Err error ->
                                            model

                                _ ->
                                    model

                        Err error ->
                            model

                ( newModel_, _ ) =
                    update (OnLocationChange model.location) newModel
            in
                newModel_ ! []

        ToggleFilter filter ->
            let
                currentFilter =
                    model.filter

                newFilter =
                    case filter of
                        TypeFilter name slug color lightText ->
                            let
                                eventType =
                                    TypeFilter name slug color lightText
                            in
                                { currentFilter
                                    | eventTypes =
                                        if List.member eventType model.filter.eventTypes then
                                            List.filter (\x -> x /= eventType) model.filter.eventTypes
                                        else
                                            eventType :: model.filter.eventTypes
                                }

                        LocationFilter name slug icon ->
                            let
                                eventLocation =
                                    LocationFilter name slug icon
                            in
                                { currentFilter
                                    | eventLocations =
                                        if List.member eventLocation model.filter.eventLocations then
                                            List.filter (\x -> x /= eventLocation) model.filter.eventLocations
                                        else
                                            eventLocation :: model.filter.eventLocations
                                }

                        VideoFilter name slug ->
                            let
                                videoRecording =
                                    VideoFilter name slug
                            in
                                { currentFilter
                                    | videoRecording =
                                        if List.member videoRecording model.filter.videoRecording then
                                            List.filter (\x -> x /= videoRecording) model.filter.videoRecording
                                        else
                                            videoRecording :: model.filter.videoRecording
                                }

                query =
                    filterToQuery newFilter

                cmd =
                    Navigation.newUrl query
            in
                { model | filter = newFilter } ! [ cmd ]

        OnLocationChange location ->
            let
                newRoute =
                    parseLocation location

                newFilter =
                    case newRoute of
                        OverviewFilteredRoute query ->
                            parseFilterFromQuery query model

                        _ ->
                            model.filter
            in
                { model | filter = newFilter, route = newRoute, location = location } ! []

        BackInHistory ->
            model ! [ Navigation.back 1 ]
