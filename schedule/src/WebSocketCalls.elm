module WebSocketCalls exposing (scheduleServer, sendInitMessage, sendGetEventContent)

-- Internal modules

import Models exposing (EventSlug)
import Messages exposing (Msg)


-- External modules

import WebSocket
import Json.Encode


scheduleServer : String
scheduleServer =
    "ws://localhost:8000/schedule/"


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


sendGetEventContent : String -> EventSlug -> Cmd Msg
sendGetEventContent campSlug eventSlug =
    WebSocket.send scheduleServer
        (Json.Encode.encode 0
            (Json.Encode.object
                [ ( "action", Json.Encode.string "get_event_content" )
                , ( "event_slug", Json.Encode.string eventSlug )
                , ( "camp_slug", Json.Encode.string campSlug )
                ]
            )
        )
