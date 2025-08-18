CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255),
    area VARCHAR(255),
    region VARCHAR(255)
    );

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    city_id INTEGER REFERENCES cities (id),
    country_id INTEGER,
    can_post BOOLEAN,
    can_write_private_message BOOLEAN,
    mobile_phone VARCHAR(30),
    home_phone VARCHAR(30),
    last_seen timestamp,
    followers_count INTEGER,
    sex INTEGER,
    can_access_closed BOOLEAN,
    is_closed BOOLEAN,
    bdate VARCHAR(11),
    relation INTEGER,
    interests VARCHAR(500)
    );
