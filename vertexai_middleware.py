import json

from starlette.datastructures import MutableHeaders
from starlette.types import Message


class VertexAiMiddleware:
    applied_urls = ["/v1/chat/completions"]

    def __init__(self, app):
        self.app = app
        self.initial_message: Message = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def modify_body():
            message = await receive()
            assert message["type"] == "http.request"

            body: bytes = message.get("body", b"{}")
            body: str = body.decode()
            data = json.loads(body)

            if "instances" in data:
                instances = data["instances"]
                message["body"] = json.dumps(instances[0]).encode()
            else:
                message["body"] = body.encode()

            return message

        async def send_wrapper(message: Message) -> None:
            message_type = message["type"]
            if message_type == "http.response.start":
                self.initial_message = message
            elif message_type == "http.response.body" and len(message["body"]) and any([scope["path"].startswith(endpoint) for endpoint in VertexAiMiddleware.applied_urls]):
                response_body = json.loads(message["body"].decode())
                new_body = { "predictions": [ response_body ] }
                data_to_be_sent_to_user = json.dumps(new_body, default=str).encode("utf-8")
                message["body"] = data_to_be_sent_to_user

                headers = MutableHeaders(raw=self.initial_message["headers"])
                headers["Content-Length"] = str(len(data_to_be_sent_to_user))
                await send(self.initial_message)
                await send(message)
            else:
                await send(self.initial_message)
                await send(message)

        await self.app(scope, modify_body, send_wrapper)
