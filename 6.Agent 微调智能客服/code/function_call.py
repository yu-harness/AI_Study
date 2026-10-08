import os
import json
from openai import OpenAI
from typing import Sequence
import requests

os.environ["OPENAI_BASE_URL"] = "http://localhost:8000/v1"
os.environ["OPENAI_API_KEY"] = "0"


def get_rubbish_category(keyword):
    url = f"https://api.timelessq.com/garbage?keyword={keyword}"
    response = requests.request("GET", url)
    output_str_list = []
    for item in response.json()['data']:
        output_str_list.append(f"{item['name']}: {item['categroy']}")
    return '\n'.join(output_str_list)


def get_song_information(keyword):
    url = f"https://api.timelessq.com/music/tencent/search?keyword={keyword}"
    response = requests.request("GET", url)
    song_infor = response.json()['data']['list'][0]
    singer = '' if not song_infor['singer'] else song_infor['singer'][0]['name']
    return f"歌曲: {keyword}\n歌手: {singer}\n时长: {song_infor['interval']}秒\n专辑名称: {song_infor['albumname']}"


def get_cartoon_information(title):
    url = f"https://api.timelessq.com/bangumi?title={title}"
    response = requests.request("GET", url)
    data = response.json()['data'][0]
    return f"标题: {data['title']}\n类型：{data['type']}\n语言：{data['lang']}\n出品方：{data['officialSite']}\n上映时间：{data['begin']}\n完结事件：{data['end']}"


tool_map = {"get_rubbish_category": get_rubbish_category,
            "get_song_information": get_song_information,
            "get_cartoon_information": get_cartoon_information}


if __name__ == "__main__":
    client = OpenAI()
    tools = [
        {
            "type": "function",
            "function": {
                            "name": "get_rubbish_category",
                            "description": "适用于生活垃圾分类时，判断物品属于哪种类型的垃圾？",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "keyword": {
                                        "type": "string",
                                        "description": "物品名称，用于垃圾分类",
                                    },
                                },
                                "required": ["keyword"],
                            }
                        }
        },
        {
            "type": "function",
            "function": {
                            "name": "get_cartoon_information",
                            "description": "根据用户提供的动漫标题，查询该动漫的相关信息。",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string",
                                        "description": "动漫",
                                    },
                                },
                                "required": ["title"],
                            }
                        }
        },
        {
            "type": "function",
            "function": {
                            "name": "get_song_information",
                            "description": "根据用户提供的歌曲名称，查询歌曲相关信息，包括歌手、时长、专辑名称等。",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "keyword": {
                                        "type": "string",
                                        "description": "歌曲名称",
                                    },
                                },
                                "required": ["keyword"],
                            }
                        }
        }
    ]

    messages = []
    messages.append({"role": "system", "content": "你是一个有用的小助手，请调用下面的工具来回答用户的问题，参考工具输出进行回答。"})
    #messages.append({"role": "user", "content": "鸡蛋壳属于哪种类型的垃圾？"})
    #messages.append({"role": "user", "content": "爱在西元前是谁唱的，来自哪张专辑？"})
    messages.append({"role": "user", "content": "凉凉是谁唱的"})
    #messages.append({"role": "user", "content": "动漫《棋魂》是哪个国家的，什么时候上映的？"})
    result = client.chat.completions.create(messages=messages, model="gpt-3.5-turbo", tools=tools)
    print("result")
    print(result)
    tool_call = result.choices[0].message.tool_calls[0].function
    print("tool_call")
    print(tool_call)
    name, arguments = tool_call.name, json.loads(tool_call.arguments)
    messages.append({"role": "function", "content": json.dumps({"name": name, "arguments": arguments}, ensure_ascii=False)})
    tool_result = tool_map[name](**arguments)
    messages.append({"role": "tool", "content": "工具输出结果为: " + tool_result})
    for msg in messages:
        print('--->', msg)
    result = client.chat.completions.create(messages=messages, model="gpt-3.5-turbo")
    print("Answer: ", result.choices[0].message.content)
