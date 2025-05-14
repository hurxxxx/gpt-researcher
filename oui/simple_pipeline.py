from typing import List, Union, Generator, Iterator, Any
from schemas import OpenAIChatMessage
from pydantic import BaseModel

from open_webui.utils.chat import generate_chat_completion


class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.name = "Pipeline Example"
        pass

    async def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict,
        __request__: Any,
        user: Any,
    ) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}")

        print(messages)
        print(user_message)
        print(body)

        response = await generate_chat_completion(
            request=__request__,
            form_data=body,
            user=user,
        )

        print(response)

        return response
