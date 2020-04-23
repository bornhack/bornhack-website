module WebSocketCalls exposing (sendInitMessage)

-- Internal modules
-- External modules

import Json.Encode
import Messages exposing (Msg)
import WebSocket


sendInitMessage : String -> String -> Cmd Msg
sendInitMessage camp_slug scheduleServer =
    WebSocket.send scheduleServer
        (Json.Encode.encode 0
            (Json.Encode.object
                [ ( "action", Json.Encode.string "init" )
                , ( "camp_slug", Json.Encode.string camp_slug )
                ]
            )
        )
