module Main exposing (..)

import Html exposing (Html, Attribute, div, input, text, li, ul, a, h4, label, i, span, hr, small, p)
import Html.Attributes exposing (class, classList, id, type_, for, style, href)
import Html.Events exposing (onClick)
import WebSocket exposing (listen)
import Json.Decode exposing (int, string, float, list, bool, Decoder)
import Json.Encode
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)
import Markdown
import Navigation exposing (Location)
import UrlParser exposing ((</>))


main : Program Flags Model Msg
main =
    Navigation.programWithFlags
        OnLocationChange
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }


scheduleServer : String
scheduleServer =
    "ws://localhost:8000/schedule/"



-- ROUTING


type Route
    = OverviewRoute
    | EventInstanceRoute EventInstanceId
    | NotFoundRoute


matchers : UrlParser.Parser (Route -> a) a
matchers =
    UrlParser.oneOf
        [ UrlParser.map OverviewRoute UrlParser.top
        , UrlParser.map EventInstanceRoute (UrlParser.s "event" </> UrlParser.int)
        ]


parseLocation : Location -> Route
parseLocation location =
    case UrlParser.parseHash matchers location of
        Just route ->
            route

        Nothing ->
            NotFoundRoute



-- MODEL


type alias Model =
    { days : List Day
    , eventInstances : List EventInstance
    , eventLocations : List EventLocation
    , eventTypes : List EventType
    , flags : Flags
    , activeDay : Day
    , filter : Filter
    , route : Route
    }


type alias Filter =
    { eventTypes : List EventType
    , eventLocations : List EventLocation
    }


type alias Day =
    { day_name : String
    , iso : String
    , repr : String
    }


type alias Speaker =
    { name : String
    , url : String
    }


type alias EventInstanceId =
    Int


type alias EventInstance =
    { title : String
    , id : EventInstanceId
    , url : String
    , abstract : String
    , eventSlug : String
    , eventType : String
    , backgroundColor : String
    , forgroundColor : String
    , from : String
    , to : String
    , timeslots : Float
    , location : String
    , locationIcon : String
    , speakers : List Speaker
    , videoRecording : Bool
    , videoUrl : String
    }


emptyEventInstance =
    { title = "This should not happen!"
    , id = 0
    , url = ""
    , abstract = ""
    , eventSlug = ""
    , eventType = ""
    , backgroundColor = ""
    , forgroundColor = ""
    , from = ""
    , to = ""
    , timeslots = 0.0
    , location = ""
    , locationIcon = ""
    , speakers = []
    , videoRecording = False
    , videoUrl = ""
    }


type alias EventLocation =
    { name : String
    , slug : String
    , icon : String
    }


type alias EventType =
    { name : String
    , slug : String
    , color : String
    , lightText : Bool
    }


type alias Flags =
    { schedule_timeslot_length_minutes : Int
    , schedule_midnight_offset_hours : Int
    , ics_button_href : String
    , camp_slug : String
    }


allDaysDay : Day
allDaysDay =
    Day "All Days" "" ""


init : Flags -> Location -> ( Model, Cmd Msg )
init flags location =
    ( Model [] [] [] [] flags allDaysDay (Filter [] []) (parseLocation location), sendInitMessage flags.camp_slug )


sendInitMessage : String -> Cmd Msg
sendInitMessage camp_slug =
    WebSocket.send scheduleServer
        (Json.Encode.encode 0
            (Json.Encode.object
                [ ( "action", Json.Encode.string "init" )
                , ( "camp_slug", Json.Encode.string camp_slug )
                ]
            )
        )



-- UPDATE


type Msg
    = NoOp
    | WebSocketPayload String
    | MakeActiveday Day
    | ToggleEventTypeFilter EventType
    | ToggleEventLocationFilter EventLocation
    | OnLocationChange Location


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        WebSocketPayload str ->
            let
                newModel =
                    case Json.Decode.decodeString initDataDecoder str of
                        Ok m ->
                            m model.flags allDaysDay (Filter [] []) model.route

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
                    parseLocation location
            in
                { model | route = newRoute } ! []



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    WebSocket.listen scheduleServer WebSocketPayload



-- DECODERS


dayDecoder : Decoder Day
dayDecoder =
    decode Day
        |> required "day_name" string
        |> required "iso" string
        |> required "repr" string


speakerDecoder : Decoder Speaker
speakerDecoder =
    decode Speaker
        |> required "name" string
        |> required "url" string


eventInstanceDecoder : Decoder EventInstance
eventInstanceDecoder =
    decode EventInstance
        |> required "title" string
        |> required "id" int
        |> required "url" string
        |> required "abstract" string
        |> required "event_slug" string
        |> required "event_type" string
        |> required "bg-color" string
        |> required "fg-color" string
        |> required "from" string
        |> required "to" string
        |> required "timeslots" float
        |> required "location" string
        |> required "location_icon" string
        |> required "speakers" (list speakerDecoder)
        |> required "video_recording" bool
        |> optional "video_url" string ""


eventLocationDecoder : Decoder EventLocation
eventLocationDecoder =
    decode EventLocation
        |> required "name" string
        |> required "slug" string
        |> required "icon" string


eventTypeDecoder : Decoder EventType
eventTypeDecoder =
    decode EventType
        |> required "name" string
        |> required "slug" string
        |> required "color" string
        |> required "light_text" bool


initDataDecoder : Decoder (Flags -> Day -> Filter -> Route -> Model)
initDataDecoder =
    decode Model
        |> required "days" (list dayDecoder)
        |> required "event_instances" (list eventInstanceDecoder)
        |> required "event_locations" (list eventLocationDecoder)
        |> required "event_types" (list eventTypeDecoder)



-- VIEW


dayButton : Day -> Day -> Html Msg
dayButton day activeDay =
    a
        [ classList
            [ ( "btn", True )
            , ( "btn-default", day /= activeDay )
            , ( "btn-primary", day == activeDay )
            ]
        , onClick (MakeActiveday day)
        ]
        [ text day.day_name
        ]


view : Model -> Html Msg
view model =
    div []
        [ div [ class "row" ]
            [ div [ id "schedule-days", class "btn-group" ]
                (List.map (\day -> dayButton day model.activeDay) (allDaysDay :: model.days))
            ]
        , hr [] []
        , case model.route of
            OverviewRoute ->
                scheduleOverviewView model

            EventInstanceRoute eventInstanceId ->
                eventInstanceDetailView eventInstanceId model.eventInstances

            NotFoundRoute ->
                div [] [ text "Not found!" ]
        ]


eventInstanceDetailView : EventInstanceId -> List EventInstance -> Html Msg
eventInstanceDetailView eventInstanceId eventInstances =
    let
        eventInstance =
            case List.head (List.filter (\e -> e.id == eventInstanceId) eventInstances) of
                Just eventInstance ->
                    eventInstance

                Nothing ->
                    emptyEventInstance
    in
        div [ class "row" ]
            [ div [ class "col-sm-9" ]
                [ a [ href "#" ]
                    [ text "Back"
                    ]
                , h4 [] [ text eventInstance.title ]
                , p [] [ Markdown.toHtml [] eventInstance.abstract ]
                ]
            , div
                [ classList
                    [ ( "col-sm-3", True )
                    , ( "schedule-sidebar", True )
                    ]
                ]
                [ h4 [] [ text "Speakers" ]
                ]
            ]


scheduleOverviewView : Model -> Html Msg
scheduleOverviewView model =
    div [ class "row" ]
        [ div
            [ classList
                [ ( "col-sm-3", True )
                , ( "col-sm-push-9", True )
                , ( "schedule-sidebar", True )
                , ( "schedule-filter", True )
                ]
            ]
            [ h4 [] [ text "Filter" ]
            , div [ class "form-group" ]
                [ filterView "Type" model.eventTypes model.filter.eventTypes ToggleEventTypeFilter
                , filterView "Location" model.eventLocations model.filter.eventLocations ToggleEventLocationFilter
                ]
            ]
        , div
            [ classList
                [ ( "col-sm-9", True )
                , ( "col-sm-pull-3", True )
                ]
            ]
            (List.map (\day -> dayRowView day model) model.days)
        ]


dayRowView : Day -> Model -> Html Msg
dayRowView day model =
    let
        types =
            List.map (\eventType -> eventType.slug)
                (if List.isEmpty model.filter.eventTypes then
                    model.eventTypes
                 else
                    model.filter.eventTypes
                )

        locations =
            List.map (\eventLocation -> eventLocation.slug)
                (if List.isEmpty model.filter.eventLocations then
                    model.eventLocations
                 else
                    model.filter.eventLocations
                )

        filteredEventInstances =
            List.filter
                (\eventInstance ->
                    ((String.slice 0 10 eventInstance.from) == day.iso)
                        && List.member eventInstance.location locations
                        && List.member eventInstance.eventType types
                )
                model.eventInstances
    in
        div []
            [ h4 []
                [ text day.repr ]
            , div [ class "schedule-day-row" ]
                (List.map dayEventInstanceView filteredEventInstances)
            ]


dayEventInstanceView : EventInstance -> Html Msg
dayEventInstanceView eventInstance =
    a
        [ class "event"
        , href ("#event/" ++ (toString eventInstance.id))
        , style
            [ ( "background-color", eventInstance.backgroundColor )
            , ( "color", eventInstance.forgroundColor )
            ]
        ]
        [ small []
            [ text ((String.slice 11 16 eventInstance.from) ++ " - " ++ (String.slice 11 16 eventInstance.to)) ]
        , i [ classList [ ( "fa", True ), ( "fa-" ++ eventInstance.locationIcon, True ), ( "pull-right", True ) ] ] []
        , p
            []
            [ text eventInstance.title ]
        ]


filterView :
    String
    -> List { a | name : String }
    -> List { a | name : String }
    -> ({ a | name : String } -> Msg)
    -> Html Msg
filterView name possibleFilters currentFilters action =
    div []
        [ text (name ++ ":")
        , ul [] (List.map (\filter -> filterChoiceView filter currentFilters action) possibleFilters)
        ]


filterChoiceView :
    { a | name : String }
    -> List { a | name : String }
    -> ({ a | name : String } -> Msg)
    -> Html Msg
filterChoiceView filter currentFilters action =
    let
        active =
            List.member filter currentFilters

        notActive =
            not active
    in
        li []
            [ div
                [ classList
                    [ ( "btn", True )
                    , ( "btn-default", True )
                    , ( "filter-choice-active", active )
                    ]
                , onClick (action filter)
                ]
                [ span []
                    [ i [ classList [ ( "fa", True ), ( "fa-minus", active ), ( "fa-plus", notActive ) ] ] []
                    , text (" " ++ filter.name)
                    ]
                ]
            ]
