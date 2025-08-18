import vk_api


def repost(token, owner_id, item_id, message=None):
    session = vk_api.VkApi(token=token)
    vk = session.get_api()
    obj = f'wall{owner_id}_{item_id}'
    vk.wall.repost(object=obj, message=message)