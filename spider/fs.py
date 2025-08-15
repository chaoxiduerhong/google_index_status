import json
import requests


class FeiShu:
    def __init__(self):
        self.api = "https://open.feishu.cn/open-apis/bot/v2/hook/44b55167-3277-40fc-8f2f-b41b162f0b08"

    def send_msg(self, title, content):
        header = {
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "content": title,
                        "tag": "plain_text"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": """%s \n <at id=all></at> """ % content,
                            "tag": "lark_md"
                        }
                    },
                ]
            }
        }
        response = requests.post(self.api, data=json.dumps(data))
        print("已经发送")
        print(response.text)