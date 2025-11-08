# 학번 : 20241858
# 이름 : 김수영
# [chatbot.py]

from common import client, model, makeup_response, gpt_num_tokens
import math
import tiktoken
from pprint import pprint


class Chatbot:
    def __init__(self, model, system_role, instruction):
        self.context = [{"role": "system", "content": system_role}]
        self.model = model
        self.instruction = instruction
        self.max_token_size = 16 * 1024

    def add_user_message(self, user_message):
        self.context.append({"role": "user", "content": user_message})

    # tools=None을 인수로 받도록 수정
    def _send_request(self, tools=None):
        try:
            if gpt_num_tokens(self.context) > self.max_token_size:
                self.context.pop()
                return makeup_response("메시지 조금 짧게 보내줄래?")
            else:
                # API 호출 파라미터를 동적으로 구성
                api_params = {
                    "model": self.model,
                    "messages": self.context
                }
                
                # tools가 제공된 경우에만 API 파라미터에 추가
                if tools:
                    api_params["tools"] = tools
                    api_params["tool_choice"] = "auto"
                
                response = client.chat.completions.create(
                    **api_params
                )
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생:{e}")
            return makeup_response("[내 찐친 챗봇에 문제가 발생했습니다. 잠시 뒤 이용해주세요]")
        
        return response.model_dump()

    # tools=None을 인수로 받도록 수정
    def send_request(self, tools=None):
        self.context[-1]['content'] += self.instruction
        # _send_request로 tools를 전달
        return self._send_request(tools=tools)

    def add_response(self, response):
        pprint(("add_response -->", response))
        
        # choices 키가 있는지 먼저 확인 (makeup_response 예외 처리)
        if 'choices' not in response:
            self.context.append({
                "role": "assistant",
                "content": "[오류 발생] 응답 형식이 올바르지 않습니다."
            })
            return

        message = response['choices'][0]['message']

        # tool_calls 응답과 일반 텍스트 응답을 구분하여 context에 추가
        if message.get("tool_calls"):
            # tool_calls 메시지 객체 전체를 추가 (Pydantic 객체가 아닌 dict로 추가)
            self.context.append(message)
        else:
            # 일반 텍스트 응답 추가
            self.context.append({
                "role": "assistant",
                "content": message.get("content") or ("NO Text")
            })
    
    def get_response_content(self):
        return self.context[-1]['content']

    def clean_context(self):
        for idx in reversed(range(len(self.context))):
            if self.context[idx]["role"] == "user":
                self.context[idx]["content"] = self.context[idx]["content"].split("instruction:\n")[0].strip()
                break

    def handle_token_limit(self, response):
        try:
            print(response['usage']['total_tokens'])
            if int(response['usage']['total_tokens']) > self.max_token_size:
                remove_size = math.ceil(len(self.context) / 10)
                self.context = [self.context[0]] + self.context[remove_size+1:]
        except Exception as e:
            print(f"handle_token_limit exception:{e}")