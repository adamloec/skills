-- Runs only when the postgres volume is first created. One database per service.
CREATE DATABASE {{app}}_api;
