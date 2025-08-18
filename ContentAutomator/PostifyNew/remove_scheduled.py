from utils.config import config
from utils.methods import remove_scheduled_tasks_fb


if __name__ == "__main__":
    page_name = 'CheapTrip. Pay less, visit more.'
    remove_scheduled_tasks_fb(acc_token=config.fb_token.get_secret_value(), page_name=page_name)
