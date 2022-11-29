# -*- encoding: utf-8 -*-
"""
Created on 2022/09/28 07:58:19
@ Author : Oliver Yuan
@ Email  : zhuimengdisheng@outlook.com
@ Description: auto attendance in TJUPT
"""

import os
import pickle
import random
import re
import time
from argparse import ArgumentParser
from configparser import ConfigParser

import requests
from requests.cookies import RequestsCookieJar
from bs4 import BeautifulSoup

from lib import debug, error, info, warn


class Bot:
    def __init__(
        self, username, password, base_url, cookies_path, img_path, *args, **kw_args
    ):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.cookies_path = cookies_path
        self.img_path = img_path

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
            }
        )
        self.session.cookies = self.load_cookies()

    """
        self.douban_session = requests.Session()
        self.douban_session.headers.update(
            {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh-TW;q=0.9,zh;q=0.8",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "DNT": "1",
                "Host": "movie.douban.com",
                "Pragma": "no-cache",
                "Referer": "https://movie.douban.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36",
                "sec-ch-ua": '"Chromium";v="100", " Not A;Brand";v="99", "Google Chrome";v="100"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        self.douban_data = self.load_douban_data()
    """

    # def log(self, *args, **kw) -> None:
    #     return print("[%s]" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"), *args, **kw)

    def load_cookies(self) -> RequestsCookieJar:
        '''
        从`cookie_path尝试加载cookie

        如果不存在则返回一个空的
        '''
        cookies = None
        if os.path.isfile(self.cookies_path):
            try:
                with open(self.cookies_path, "rb") as file:
                    cookies = pickle.load(file)
                debug(f"Cookies loaded from file: {self.cookies_path}")
                return cookies
            except Exception as e:
                warn(f"Reading cookies error: {e}")
        else:
            warn(f"Cookies file not exists: {self.cookies_path}")
        if cookies:
            return cookies
        else:
            return RequestsCookieJar()

    # 用 retry 库写一下应该会好看点
    def login(self) -> bool:
        '''
        尝试登陆

        重试次数为10次
        '''
        try_time = 10
        while True:
            _ = self.session.get(f"{self.base_url}login.php")
            resopnse = self.session.post(
                f"{self.base_url}takelogin.php",
                {
                    "username": self.username,
                    "password": self.password,
                },
            )
            if "logout.php" in resopnse.text:
                info("Logged in successfully")
                os.makedirs(os.path.dirname(self.cookies_path), 0o755, True)
                with open(self.cookies_path, "wb") as f:
                    pickle.dump(self.session.cookies, f)
                debug(f"Cookies wrote to file: {self.cookies_path}")
                return True
            try_time -= 1
            if try_time > 0:
                debug(f"Log in error, try again ({try_time} left)")
            else:
                error(f"Log in error after 10 tries")
                return False

    """
    def load_douban_data(self) -> dict:
        douban_data = {}
        if os.path.exists(self.img_path):
            try:
                with open(self.img_path, encoding="utf-8") as file:
                    douban_data = json.load(file)
                self.log(f"Douban data loaded from file: {self.img_path}")
                return douban_data
            except Exception as e:
                self.log(f"Reading douban data error: {e}")
        else:
            self.log(f"Douban data file not exists: {self.img_path}")
        return douban_data

    def save_douban_data(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.img_path), 0o755, True)
            with open(self.img_path, "w", encoding="utf-8") as f:
                json.dump(self.douban_data, f, ensure_ascii=False, indent=1)
                self.log(f"Douban data wrote to file: {self.img_path}")
            return True
        except:
            return False

    def get_id(self, title: str) -> str:
        if title in self.douban_data:
            return self.douban_data[title]

        time.sleep(random.random() * 5)
        response = self.douban_session.get(
            f"https://movie.douban.com/j/subject_suggest?q={requests.utils.requote_uri(title)}"
        )
        try:
            url_id = re.findall(r"(?<=/)p\d+(?=\.)", response.json()[0]["img"])[0]
            self.douban_data[title] = url_id
            self.log(f'Title "{title}" returned id "{url_id}"')
            return url_id
        except Exception as e:
            self.log(f"Error: {e}, title: {title}, response: {response.text}")
            return None
    """

    def auto_attendance(self) -> bool:
        '''
        尝试5次签到
        '''
        try_time = 5
        while True:
            if self.auto_attendance_once():
                info("Attended successfully")
                return True
            time.sleep(random.random() * 5)
            try_time -= 1
            if try_time > 0:
                debug(f"Attend error, try again ({try_time} left)")
            else:
                error(f"Attend error after 5 tries")
                return False

    def save_image(self, captcha_image_url: str) -> bool:
        '''
        保存图片

        如果成功返回 `True`

        :param captcha_image_url: 验证码链接
        '''
        try:
            captcha_image_response = requests.get(
                f"{self.base_url}{captcha_image_url}", stream=True
            )
            if captcha_image_response.status_code != 200:
                debug("Captcha image response failed!")
                return False
            os.makedirs(os.path.dirname(self.img_path), 0o755, True)
            with open(self.img_path, "wb") as f:
                f.write(captcha_image_response.content)
            info(f"Image wrote to file: {self.img_path}")
            return True
        except:
            return False

    def auto_attendance_once(self) -> bool:
        '''
        仅尝试一次签到
        '''
        try:
            response = self.session.get(f"{self.base_url}attendance.php")
            if "login.php" in response.url:
                debug("Needed to log in")
                if not self.login():
                    return False
                response = self.session.get(f"{self.base_url}attendance.php")

            text = response.text
            if "今日已签到" in text:
                debug('"今日已签到" found, already attended')
                return True

            tree = BeautifulSoup(text, "html.parser")

            captcha_image = tree.select_one(".captcha > tr > td > img")
            if not captcha_image:
                warn("No captcha image found")
                return False
            captcha_image_url = captcha_image.attrs["src"]
            if not self.save_image(captcha_image_url):
                error("Save image failed!")
                return False

            # captcha_image_id = re.findall(r"(?<=/)p\d+(?=\.)", captcha_image_url)[0]

            captcha_options = set(
                re.findall(
                    r'<input name="answer" type="radio" value="(\d+-\d+-\d+ \d+:\d+:\d+&amp;(\d+))"/>([^<>]*?)<',
                    str(tree.select_one(".captcha form table")),
                )
            )
            captcha_options_list = []
            for value, _id, title in captcha_options:
                value = value.replace("&amp;", "&")
                captcha_options_list.append((value, title))

            """
            for value, id, title in captcha_options:
                value = value.replace("&amp;", "&")
                url_id = self.get_id(title)
                if captcha_image_id == url_id:
                    available_choices.append(
                        {
                            "value": value,
                            "id": id,
                            "title": title,
                            "url_id": url_id,
                            "captcha_image": captcha_image_url,
                        }
                    )
                    self.log(
                        f"Available choice found: {json.dumps(available_choices[-1], ensure_ascii=False)}"
                    )

            self.save_douban_data()
            """

            baidu_url = "https://graph.baidu.com/upload"
            files = {
                "tn": (None, "pc"),
                "image": (self.img_path, open(self.img_path, "rb"), "image/png"),
                "from": (None, "pc"),
                "image_source": (None, "PC_UPLOAD_SEARCH_HERE"),
                "range": (None, "{'page_from': 'searchIndex'}"),
            }
            baidu_response = requests.post(baidu_url, files=files)
            baidu_response_url = baidu_response.json()["data"]["url"]

            baidu_result = requests.get(baidu_response_url)
            tree = BeautifulSoup(baidu_result.text, "html.parser")
            title = tree.select("script")
            text = title[1].text
            s = text.encode().decode("unicode_escape")
            s = "".join(re.findall("[\u4e00-\u9fa5]", s))

            available_choices = []
            for item in captcha_options_list:
                if item[1] in s:
                    available_choices.append(item[0])

            if len(available_choices) == 0:
                warn(f"No choice found!")
                return False
            elif len(available_choices) > 1:
                debug(f"{len(available_choices)} choices found!")
                return False
            else:
                data = {"answer": available_choices[0], "submit": "提交"}
                response = self.session.post(
                    f"{self.base_url}attendance.php", data)
                if "签到成功" in response.text:
                    return True
                else:
                    warn(
                        f'"签到成功" not found, response_text: {response.text}')
                    return False
        except Exception as e:
            error(f"Error: {e}")
            return False


if __name__ == "__main__":
    config = {
        "username": None,
        "password": None,
        "base_url": "https://www.tjupt.org/",
        "cookies_path": "data/cookies.pkl",
        "img_path": "data/image.png",
    }

    argument_parser = ArgumentParser(
        description="Auto adttendance bot for TJUPT.")
    argument_parser.add_argument(
        "-i",
        "--ini-path",
        default="config/config.ini",
        help="File path for config.ini (default: config/config.ini). The arguments provided by command line will override the settings in this file.",
    )
    argument_parser.add_argument(
        "-u", "--username", help="Your username for TJUPT.")
    argument_parser.add_argument(
        "-p", "--password", help="Your password for TJUPT.")
    argument_parser.add_argument(
        "-b",
        "--base-url",
        help="Base url path for TJUPT (default: https://www.tjupt.org/).",
    )
    argument_parser.add_argument(
        "-c",
        "--cookies-path",
        help="File path for cookies.pkl (default: data/cookies.pkl).",
    )
    argument_parser.add_argument(
        "-f",
        "--file-path",
        help="File path for image.png (default: data/image.png).",
    )
    args = argument_parser.parse_args()

    if args.ini_path and os.path.isfile(args.ini_path):
        config_parser = ConfigParser()
        config_parser.read(args.ini_path, "utf-8")
        for key in config:
            config[key] = str(config_parser.get(
                "Bot", key, fallback=config[key]))

    for key, value in args._get_kwargs():
        if value:
            config[key] = value

    bot = Bot(**config)
    if not bot.auto_attendance():
        raise
