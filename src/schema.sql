CREATE DATABASE IF NOT EXISTS trailer_week_radar CHARACTER SET utf8mb4;
USE trailer_week_radar;

CREATE TABLE IF NOT EXISTS films (
    film_id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    language VARCHAR(30) NOT NULL,
    release_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS trailers (
    video_id VARCHAR(32) PRIMARY KEY,
    film_id VARCHAR(64) NOT NULL UNIQUE,
    trailer_at DATETIME NOT NULL,
    history_complete BOOLEAN NOT NULL,
    FOREIGN KEY (film_id) REFERENCES films(film_id)
);

CREATE TABLE IF NOT EXISTS daily_collections (
    film_id VARCHAR(64) NOT NULL,
    day INT NOT NULL,
    date DATE NOT NULL,
    india_net_cr DOUBLE,
    PRIMARY KEY (film_id, day),
    FOREIGN KEY (film_id) REFERENCES films(film_id)
);

CREATE TABLE IF NOT EXISTS comments (
    comment_id VARCHAR(128) PRIMARY KEY,
    film_id VARCHAR(64) NOT NULL,
    published_at DATETIME NOT NULL,
    text_clean LONGTEXT NOT NULL,
    in_trailer_week BOOLEAN,
    FOREIGN KEY (film_id) REFERENCES films(film_id)
);
