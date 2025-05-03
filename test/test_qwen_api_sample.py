from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

model =['qwen2.5-vl-7b-instruct']

completion = client.chat.completions.create(
    model= model[0],
    messages=[
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful assistant."}],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"
                    },
                },
                {"type": "text", "text": "What scene is depicted in the image?"},
            ],
        },
    ],
)

print(completion.choices[0].message.content)