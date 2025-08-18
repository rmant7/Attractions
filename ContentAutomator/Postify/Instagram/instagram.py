from instagrapi import Client
from instagrapi.types import Usertag, Location
import time
import random


login = ""
password = ""

cl = Client()
cl.login(login, password)


class MakePost:
    def __init__(self, client):
        self.cl = client
        self.tags = ['strawberry', 'summer', 'fantastic']
        self.used_pictures = []

    def get_current_time(self):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        print(current_time)
        return current_time

    def random_choice_pictures(self):
        path_list = ['C:/Users/Sasha/Desktop/Python/instagram/images/1.jpg' 
                     'C:/Users/Sasha/Desktop/Python/instagram/images/2.jpg'
                     'C:/Users/Sasha/Desktop/Python/instagram/images/3.jpg'
                     ]

        pic = random.choice(path_list)

        if len(self.used_pictures) == len(path_list):
            exit()
        elif pic in self.used_pictures:
            return self.random_choice_pictures()
        if len(self.used_pictures) == len(path_list):
            time.sleep(60)
            exit()
        else:
            self.used_pictures.append(pic)
            return pic

    def make_post(self, picture):
        user = cl.user_info_by_username("User_Name")
        tags_list = ['#strawberry', '#summer', '#fantastic']
        media_first = cl.photo_upload(
            path=picture,
            caption=f'My strawberry! \n {random.sample(tags_list, 3)}',
            usertags=[Usertag(user=user, x=0.5, y=0.5)],
            location=Location(name='Ukraine, Kiev', lat=50.453919, lng=30.524226),
            extra_data={
                'custom_accessibility_caption': 'alt text example',
                'like_and_view_counts_disabled': False,
                'disable_comments': False,
            }
        )

    def wait_for_time(self):
        while True:
            current_time = self.get_current_time()
            time_list = ['18:04:00', '18:05:00']
            if current_time in time_list:
                pic = self.random_choice_pictures()
                self.make_post(pic)
                continue
            else:
                pass


start = MakePost(cl)
start.wait_for_time()
