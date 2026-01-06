
CREATE TABLE device_runtime (
    id serial PRIMARY KEY,
    topic varchar,
    start_time timestamp default NOW(),
    elapsed_seconds integer NOT NULL
);

CREATE TABLE sensor (
    id serial PRIMARY KEY,
    sensor varchar,
    reading float,
    time timestamp default NOW()
);

CREATE TABLE event (
    id serial PRIMARY KEY,
    name varchar,
    state_from varchar,
    state_to   varchar,
    opaque     jsonb,
    time timestamp default NOW()
);