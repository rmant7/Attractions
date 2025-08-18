### Description
This is an app that collects users of vk.ru

### Instalation

Create account on vk.ru

Instructions https://dev.vk.com/ru/api/access-token/implicit-flow-user

Generate token https://vkhost.github.io/

Create database, add tables

<pre>
# clone the repository
$ git cone <link>

# change the working directory
$ cd vk_users

# create .env and copy content from the sample
$ cp .env.sample .env

# fill .env with your values

# define your search parameters in vk_users.search_parameters.py

# install dependencies
$ make install

# first, collect cities to the db
$ make start-cities

# second, collect users to the db
$ make start

</pre>
