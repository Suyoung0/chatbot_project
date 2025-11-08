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

    def _send_request(self):
        try:
            if gpt_num_tokens(self.context) > self.max_token_size:
                self.context.pop()
                return makeup_response("메시지 조금 짧게 보내줄래?")
            else:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=self.context,
                    #temperature=1,
                    #top_p=1,
                    #max_completion_tokens = 256, # max_tokens=256,  # 
                    #frequency_penalty=0,
                    #presence_penalty=0
                ) #.model_dump()
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생:{e}")
            return makeup_response("[내 찐친 챗봇에 문제가 발생했습니다. 잠시 뒤 이용해주세요]")
        
        return response.model_dump() #.output_text   #response

    def send_request(self):
        self.context[-1]['content'] += self.instruction
        return self._send_request()

    def add_response(self, response):
        pprint(("add_response -->", response))
        self.context.append({
                "role" : "assistant",     #  response['choices'][0]['message']["role"],
                "content" : response['choices'][0]['message']["content"] or ("NO Text")
                #"role" : "role":response['choices'][0]['message']["role"], #
                #"content" : response['choices'][0]['message']["content"] # response # response['output'][1]['content'][0]['text']   #  response['choices'][0]['message']["content"],
                                                                          #  response.output_text 
            }
        )
    
    def get_response_content(self):
        return self.context[-1]['content']

    def clean_context(self):
        for idx in reversed(range(len(self.context))):
            if self.context[idx]["role"] == "user":
                self.context[idx]["content"] = self.context[idx]["content"].split("instruction:\n")[0].strip()
                break

    def handle_token_limit(self, response):
        # 누적 토큰 수가 임계점을 넘지 않도록 제어한다.
        try:
            print(response['usage']['total_tokens'])
            if int(response['usage']['total_tokens']) > self.max_token_size:  # response.usage.total_tokens 
                remove_size = math.ceil(len(self.context) / 10)
                self.context = [self.context[0]] + self.context[remove_size+1:]
        except Exception as e:
            print(f"handle_token_limit exception:{e}")