# [application.py]

from flask import Flask, render_template, request
import sys
from common import model
from chatbot import Chatbot
from characters import system_role, instruction
from parallel_function_calling import FunctionCalling, tools 


# jjinchin 인스턴스 생성
jjinchin = Chatbot(
    model = model.basic,
    system_role = system_role,
    instruction = instruction
)

application = Flask(__name__)

func_calling = FunctionCalling(model=model.basic)

@application.route("/")
def hello():
    return "Hello Github"

@application.route("/chat_app")
def chat_app():
    return render_template("chat.html")

@application.route('/chat_api', methods=['POST'])
def chat_api(): 
    request_message = request.form.get('message', '')
    jjinchin.add_user_message(request_message)

    # ------------------------------------------------------------------
    # 수정 로직
    # ------------------------------------------------------------------

    # 1. send_request를 tools와 함께 한 번 호출합니다.
    # 이 호출은 페르소나, 지시어, tool 정의를 모두 포함합니다.
    response_dict = jjinchin.send_request(tools=tools)

    # 2. 응답 객체를 확인합니다. 
    if 'choices' not in response_dict:
        # 'makeup_response' 등으로 생성된 오류 응답 처리
        jjinchin.add_response(response_dict)
    else:
        # 3. 정상 응답에서 message 객체를 추출합니다.
        message_object = response_dict['choices'][0]['message']

        # 4. tool_calls가 있는지 확인하여 로직을 분기합니다.
        if message_object.get("tool_calls"):
            # 4_A. [Case 1: 함수 호출 필요]
            # run 메서드에 message_object와 현재 context를 전달합니다.
            # run 메서드는 내부적으로 2번째 API 호출을 수행하여 최종 답변을 반환합니다.
            final_response = func_calling.run(message_object, jjinchin.context[:])
            
            # add_response는 run이 반환한 최종 답변을 추가합니다.
            jjinchin.add_response(final_response)
        else:
            # 4_B. [Case 2: 함수 호출 불필요]
            # send_request가 반환한 응답이 이미 최종 답변이므로, 이 응답을 context에 추가합니다.
            jjinchin.add_response(response_dict)
            
    # ------------------------------------------------------------------

    # 공통 로직: 최종 응답을 가져오고 context를 정리합니다.
    response_message = jjinchin.get_response_content()
    
    jjinchin.handle_token_limit(response_dict) 
    
    jjinchin.clean_context()
    print("response_message:", response_message)
    return {"response_message": response_message}

if __name__ == "__main__":
    application.config['TEMPLATES_AUTO_RELOAD'] = True
    application.jinja_env.auto_reload = True
    port = int(os.environ.get("PORT", 5000))
    application.run(host="0.0.0.0", port=port)