# -*- coding: utf-8 -*-
"""
cron: 12 6 * * *
new Env('WPS');
"""

import json
import random
import time

import requests

from notify_mtr import send
from utils import get_data


class WPS:
    def __init__(self, check_items):
        self.check_items = check_items
        self.is_sign = False

    # 判断Cookie是否失效 和 今日是否签到
    def check(self, cookie):
        url0 = "https://vip.wps.cn/sign/mobile/v3/get_data"
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
        }
        res = requests.get(url=url0, headers=headers)
        if "会员登录" in res.text:
            print("cookie 失效")
            exit()
        is_sign = res.json().get("data", {}).get("is_sign")
        if is_sign:
            self.is_sign = True

    def sign(self, cookie):
        url = "https://vip.wps.cn/sign/v2"
        yz_url = "https://vip.wps.cn/checkcode/signin/captcha.png?platform=8&encode=0&img_witdh=275.164&img_height=69.184"
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
        }
        if self.is_sign:
            msg = "今日已签到"
        else:
            data0 = {"platform": "8"}  # 不带验证坐标的请求
            data = {
                "platform": "8",
                "captcha_pos": "137.00431974731889, 36.00431593261568",
                "img_witdh": "275.164",
                "img_height": "69.184",
            }  # 带验证坐标的请求
            res = requests.post(url=url, headers=headers, data=data0)
            if not ("msg" in res.text):
                msg = "cookie 失效"
            else:
                sus = json.loads(res.text)["result"]
                msg = f"免验证签到 --> {sus}\n"
                if sus == "error":
                    for n in range(10):
                        requests.get(url=yz_url, headers=headers)
                        res = requests.post(url=url, headers=headers, data=data)
                        sus = json.loads(res.text)["result"]
                        msg += f"{str(n + 1)} 尝试验证签到 --> {sus}\n"
                        time.sleep(random.randint(0, 5) / 10)
                        if sus == "ok":
                            break
                msg += f"最终签到结果 --> {sus}\n"
                # {"result":"ok","data":{"exp":0,"wealth":0,"weath_double":0,"count":5,"double":0,"gift_type":"space_5","gift_id":133,"url":""},"msg":""}
        return msg

    def main(self):
        msg_all = ""
        for check_item in self.check_items:
            cookie = check_item.get("cookie")
            self.check(cookie)
            msg = self.sign(cookie)
            msg_all += msg + "\n\n"
        return msg_all


if __name__ == "__main__":
    data = get_data()
    _check_items = data.get("WPS", [])
    res = WPS(check_items=_check_items).main()
    send("WPS", res)
