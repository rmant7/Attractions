# import asyncio
# from datetime import datetime, timedelta
#
# from socials.fb import add_task_facebook
# from socials.inst import add_task_instagram, account_authentication
# from socials.vk import add_task_vk
# from utils.config import config
# from utils.methods import start_func
#
#
# async def main():
#     # Instagram
#     # inst_account = account_authentication(username=config.inst_username.get_secret_value(),
#     #                                       password=config.inst_password.get_secret_value())
#     # instagram = {'client': inst_account, 'task': add_task_instagram}
#
#     # Facebook
#     page_name = ''
#     facebook = {'page_name': page_name, 'acc_token': config.fb_token.get_secret_value(), 'task': add_task_facebook}
#
#     # Vk
#     vkontakte = {'owner_id': config.owner_id.get_secret_value(), 'token': config.vk_token.get_secret_value(),
#                  'task': add_task_vk}
#
#     # Tg
#     # telegram = {'task': add_task_telegram}
#
#     # Fill In this fields
#     data_folder_path = 'files/ru'
#     posting_start_date = datetime.strptime('06/27/2023, 22:30:00', '%m/%d/%Y, %H:%M:%S')
#     posting_interval = timedelta(minutes=1)
#     social = vkontakte
#
#     await start_func(data_folder_path=data_folder_path, start_date=posting_start_date, interval=posting_interval,
#                      **social)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
