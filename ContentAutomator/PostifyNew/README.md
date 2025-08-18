# Postify

#### Postify is a Python-based solution designed to automate the process of posting content on various social media platforms, such as Facebook, Instagram, and Telegram. The code uses different APIs provided by these platforms to publish posts. The project is structured in a way that each social media platform has a separate python module to handle interactions with the respective platform.

## Requirements

The project requires Python 3.6 or newer. Dependencies include:

facebook-sdk: For interacting with the Facebook Graph API.
instagrapi: A modern, easy-to-use, feature-rich, and async-ready API wrapper for Instagram written in Python.
aiogram: A pretty simple and fully asynchronous framework for Telegram Bot API written in Python with asyncio and aiohttp.
Pillow: A python imaging library used for opening, manipulating, and saving many different image file formats.
requests: A simple, yet elegant HTTP library used to make HTTP requests simpler and more human-friendly.
geopy: A client for several popular geocoding web services used for geolocation functionalities.
logging: For logging errors and messages.
## Usage

### Facebook
The fb.py module is used for posting content on Facebook. The add_task_facebook function is used to schedule a post on Facebook. It uses the post_facebook_immediate and post_facebook_planned functions for immediate and scheduled posts, respectively​1​.
### [startFB.py](startFB.py)
For automatic planning of posts on ru language to Facebook. Just enter start posting date in future and renew the Facebook API Token in .env file.
### [startFB_EN_new.py](startFB_EN.py)
For automatic planning of English posts to Facebook. Just enter start posting date in future and renew the Facebook API Token in .env file.


### Instagram
The inst.py module is used for posting content on Instagram. The make_post function is used to create a post on Instagram. This module also includes functions for downloading and saving images and for uploading a single photo or an album​2​.

### Telegram
The tg.py module is used for posting content on Telegram. The add_task_telegram function is used to schedule a post on Telegram. It uses the post_telegram_immediate function for immediate posts​3​.

## Info
#### Please note that the application requires various access tokens to interact with the respective social media platform's API. Make sure to provide those in the appropriate module.

This is a high-level overview of the codebase. There's more specific detail within each Python module about how images are processed, how posts are scheduled, and how error handling is managed. Please refer to the respective files for more information.

Contributions are welcome! Please feel free to submit a pull request.

For any issues, questions, or suggestions, please open an issue in the GitHub repository.

This README was last updated on June 30, 2023.

