from pydantic import BaseSettings, SecretStr
import os


class Settings(BaseSettings):
    # Желательно вместо str использовать SecretStr
    # для конфиденциальных данных, например, токена бота
    bot_token: SecretStr

    # Telegram
    channel_id: SecretStr

    # FaceBook
    fb_token: SecretStr

    # Vkontakte
    owner_id: SecretStr
    vk_token: SecretStr

    # Instagram
    inst_username: SecretStr
    inst_password: SecretStr

    # Вложенный класс с дополнительными указаниями для настроек
    class Config:
        # Имя файла, откуда будут прочитаны данные
        # (относительно текущей рабочей директории)
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        # Кодировка читаемого файла
        env_file_encoding = 'utf-8'


# При импорте файла сразу создастся
# и провалидируется объект конфига,
# который можно далее импортировать из разных мест
config = Settings()
