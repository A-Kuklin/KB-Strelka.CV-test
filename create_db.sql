create table users
(
    chat_id   bigint            not null
        constraint users_pk
            primary key,
    name text,
    surname text,
    middle_name text,
    position_ text,
    email text,
    id        serial            not null
);

alter table users
    owner to postgres;

create unique index users_id_uindex
    on users (id);

create table project
(
    id serial                   not null
        constraint project_pk
            primary key,
    title text,
    project_date DATE,
    project_id   bigint            not null
        references users (chat_id)
);

create table meeting
(
    id serial                   not null
        constraint meeting_pk
            primary key,
    meeting_email text,
    meeting_date timestamp with time zone,
    meeting_id   bigint            not null
        references users (chat_id)
);