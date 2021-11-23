-- this scripts drop all tables from database allowing for further recreation and reinitialization

DROP TABLE IF EXISTS whitelist_charge_point;
DROP TABLE IF EXISTS whitelist_user;
DROP TABLE IF EXISTS whitelist;

DROP TABLE IF EXISTS charge_point;
DROP TABLE IF EXISTS charge_point_status;

DROP TABLE IF EXISTS address;
DROP TABLE IF EXISTS zip_code;
DROP TABLE IF EXISTS city;

DROP TABLE IF EXISTS organization;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS role;
DROP TABLE IF EXISTS user_role;