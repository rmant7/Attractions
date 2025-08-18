import os
import pickle

import vk_api


def upload_photo(att_path, photo, session):
    file_path = os.path.join(att_path + '/' + photo)
    upload = vk_api.VkUpload(session)
    photo = upload.photo_messages(file_path)
    photo_data = photo[0]
    owner_id = photo_data['owner_id']
    photo_id = photo_data['id']
    access_key = photo_data['access_key']
    attachment = f'photo{owner_id}_{photo_id}_{access_key}'
    return attachment


def send_massage(token, user_id, message=None, attachment=None, att_path=None):
    session = vk_api.VkApi(token=token)
    vk = session.get_api()
    if attachment is not None:
        attachment = upload_photo(att_path=att_path, photo=attachment, session=session)
    vk.messages.send(user_id=user_id, random_id=0, message=message, attachment=attachment)

# Это только 1 раз пробовал погонять, черновой вариант.
# ______________________________________________________________________________________________________________________
# Отправляет сообщения 19 пользователям. Принимает список пользователей и текущий индекс
def process_users(users, index, message, token):
    for i in range(index, min(index + 19, len(users))):
        user = users[i]
        try:
            send_massage(user_id=user['id'], message=message, token=token)
        except Exception as e:
            continue
    return i + 1  # новый индекс после обработки


# Рассылает сообщения 19 пользователям, используя данные с файла со списком пользователей и файла с текущим индексом
# Принимает токен и сообщение
def send_19_users(message, token):
    users = load_data()
    index = load_index()
    new_index = process_users(users=users, index=index, message=message, token=token)
    save_index(new_index)


# загружает users из файла
def load_data():
    if os.path.exists('users.pkl'):
        with open('users.pkl', 'rb') as f:
            return pickle.load(f)
    else:
        return []


# загружает index из файла
def load_index():
    if os.path.exists('index.pkl'):
        with open('index.pkl', 'rb') as f:
            return pickle.load(f)
    else:
        return 0  # возвращаем 0, если файл с индексом не существует


# Сохраняет в файл текущий индекс
def save_index(index):
    with open('index.pkl', 'wb') as f:
        pickle.dump(index, f)