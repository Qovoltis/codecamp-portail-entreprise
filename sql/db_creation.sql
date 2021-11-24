-- this script list all table creations and initial data for creating start.db

-- ############ User tables ###########
-- tables creation (user)
CREATE TABLE role(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(30) UNIQUE NOT NULL
);

CREATE TABLE organization(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE user(
id INTEGER PRIMARY KEY AUTOINCREMENT,
email VARCHAR(255) UNIQUE NOT NULL,
password VARCHAR(255) NOT NULL,
firstname VARCHAR(50) NOT NULL,
lastname VARCHAR(100) NOT NULL,
phone VARCHAR(20) NOT NULL,
organization_id INTEGER NOT NULL,
FOREIGN KEY(organization_id) REFERENCES organization(id)
);

CREATE TABLE user_role(
user_id INTEGER NOT NULL,
role_id INTEGER NOT NULL,
FOREIGN KEY(user_id) REFERENCES user(id),
FOREIGN KEY(role_id) REFERENCES role(id),
UNIQUE(user_id, role_id)
);

-- data insertion (user)
INSERT INTO role(name) VALUES
('administrator'),
('employee');

INSERT INTO organization(name) VALUES
('Qovoltis'),
('Etna');

INSERT INTO user(email, password, firstname, lastname, phone, organization_id) VALUES
('administrator@dummy.qovoltis.com', 'password', 'Johnny', 'Hopkins', '+33612345678', 1),
('ellen.willis@dummy.qovoltis.com', 'password', 'Ellen', 'Willis', '+33612345678', 1),
('alan.fleming@dummy.qovoltis.com', 'password', 'Alan', 'Fleming', '+33622345678',  1),
('larry.baker@dummy.qovoltis.com', 'password', 'Larry', 'Baker', '+33632345678', 1),
('samantha.hicks@dummy.qovoltis.com', 'password', 'Samantha', 'Hicks', '+33642345678', 1),
('carrie.holahan@dummy.qovoltis.com', 'password', 'Carrie', 'Holahan', '+33642345678', 1),
('june.roderiquez@dummy.qovoltis.com', 'password', 'June', 'Roderiquez', '+33652345678', 1),
('administrator@dummy.etna.com', 'password', 'Joshua', 'Cervantez', '+33662345678', 2),
('sandra.pawlak@dummy.etna.com', 'password', 'Sandra', 'Pawlak', '+33672345678', 2),
('nicholas.hamilton@dummy.etna.com', 'password', 'Nicholas', 'Hamilton', '+33682345678', 2),
('mark.frahm@dummy.etna.com', 'password', 'Mark', 'Frahm', '+33692345678', 2),
('edwin.daniels@dummy.etna.com', 'password', 'Edwin', 'Daniels', '+33611345678', 2),
('gary.remaley@dummy.etna.com', 'password', 'Gary', 'Remaley', '+33613345678', 2),
('byron.rodriguez@dummy.etna.com', 'password', 'Byron', 'Rodriguez', '+33614345678', 2);

-- all users are employees
INSERT INTO user_role(user_id, role_id)
SELECT u.id, 2 from user u;

-- there are only one admin by organization
INSERT INTO user_role(user_id, role_id)
SELECT u.id, 1 from user u where u.email in(
'administrator@dummy.qovoltis.com',
'administrator@dummy.etna.com'
);

-- ############ Address tables ###########
-- tables creation (address)
CREATE TABLE city(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(60) NOT NULL
);

CREATE TABLE zip_code(
id INTEGER PRIMARY KEY AUTOINCREMENT,
code VARCHAR(10) UNIQUE NOT NULL,
city_id INTEGER NOT NULL,
FOREIGN KEY(city_id) REFERENCES city(id)
);

CREATE TABLE address(
id INTEGER PRIMARY KEY AUTOINCREMENT,
label VARCHAR(150) NOT NULL,
zip_code_id INTEGER NOT NULL,
latitude DECIMAL(10,7) NOT NULL,
longitude DECIMAL(10,7) NOT NULL,
FOREIGN KEY(zip_code_id) REFERENCES zip_code(id)
);

-- data insertion (address)
INSERT INTO city(name) VALUES
('Montrouge'),
('Ivry-sur-Seine'),
('Strasbourg'),
('Lille');

INSERT INTO zip_code(code, city_id) VALUES
('92120', 1),
('94200', 2),
('67000', 3),
('59000', 4);

INSERT INTO address(label, zip_code_id, latitude, longitude) VALUES
('2A rue Danton', 1, 48.8182737, 2.3292709),
('121 avenue Verdier', 1, 48.816179, 2.3080785),
('7 rue Maurice Grandcoing', 2, 48.8139367, 2.3922497),
('29 rue François Mitterand', 2, 48.8226153, 2.3885851),
('44 boulevard du président Wilson', 3, 48.5894175, 7.7408748),
('22 Façade de l''esplanade', 4, 50.6409064, 3.0535028);


-- ############ Charge points tables ###########
-- tables creation (charge points)
CREATE TABLE charge_point_status(
id INTEGER PRIMARY KEY AUTOINCREMENT,
code VARCHAR(30) UNIQUE NOT NULL,
label VARCHAR(100) NOT NULL
);

CREATE TABLE charge_point(
id INTEGER PRIMARY KEY AUTOINCREMENT,
reference VARCHAR(50) UNIQUE NOT NULL,
address_id INTEGER NOT NULL,
organization_id INTEGER NOT NULL,
status_id INTEGER NOT NULL,
FOREIGN KEY(address_id) REFERENCES address(id),
FOREIGN KEY(organization_id) REFERENCES organization(id),
FOREIGN KEY(status_id) REFERENCES charge_point_status(id)
);

-- data insertion (charge point)
INSERT INTO charge_point_status(code, label) VALUES
('STUDY', 'En étude'),
('INSTALLATION', 'En installation'),
('PRODUCTION', 'En service');

INSERT INTO charge_point(reference, address_id, organization_id, status_id) VALUES
('FR*QOV*92120-0001-01', 1, 1, 3),
('FR*QOV*92120-0001-02', 1, 1, 3),
('FR*QOV*92120-0001-03', 1, 1, 3),
('FR*QOV*92120-0001-04', 1, 1, 3),
('FR*QOV*92120-0001-05', 1, 1, 2),
('FR*QOV*92120-0001-06', 1, 1, 2),
('FR*QOV*92120-0001-07', 1, 1, 1),
('FR*QOV*92120-0001-08', 1, 1, 1),
('FR*QOV*92120-0001-09', 1, 1, 1),
('FR*QOV*92120-0001-10', 1, 1, 1),
('FR*QOV*92120-0002-01', 2, 1, 3),
('FR*QOV*92120-0002-02', 2, 1, 2),
('FR*QOV*92120-0002-03', 2, 1, 1),
('FR*QOV*92120-0002-04', 2, 1, 1),
('FR*QOV*67000-0001-01', 5, 1, 3),
('FR*QOV*67000-0001-02', 5, 1, 3),
('FR*QOV*94200-0001-01', 3, 2, 3),
('FR*QOV*94200-0001-02', 3, 2, 3),
('FR*QOV*94200-0001-03', 3, 2, 3),
('FR*QOV*94200-0001-04', 3, 2, 3),
('FR*QOV*94200-0001-05', 3, 2, 1),
('FR*QOV*94200-0001-06', 3, 2, 1),
('FR*QOV*94200-0002-01', 4, 2, 3),
('FR*QOV*94200-0002-02', 4, 2, 3),
('FR*QOV*94200-0002-03', 4, 2, 3),
('FR*QOV*94200-0002-04', 4, 2, 2),
('FR*QOV*94200-0002-05', 4, 2, 2),
('FR*QOV*59000-0001-01', 6, 1, 3),
('FR*QOV*59000-0001-02', 6, 1, 3);


-- ############ Whitelists tables ###########
-- tables creation (whitelists)
CREATE TABLE whitelist(
id INTEGER PRIMARY KEY AUTOINCREMENT,
label VARCHAR(50) NOT NULL,
organization_id INTEGER NOT NULL,
paid_by_organization INTEGER NOT NULL DEFAULT 0,
created_at TEXT NOT NULL,
expires_at TEXT,
FOREIGN KEY(organization_id) REFERENCES organization(id),
UNIQUE(organization_id, label)
);

CREATE TABLE whitelist_user(
whitelist_id INTEGER NOT NULL,
user_id INTEGER NOT NULL,
created_at TEXT NOT NULL,
expires_at TEXT,
FOREIGN KEY(whitelist_id) REFERENCES whitelist(id),
FOREIGN KEY(user_id) REFERENCES user(id),
UNIQUE(whitelist_id, user_id)
);

CREATE TABLE whitelist_charge_point(
whitelist_id INTEGER NOT NULL,
charge_point_id INTEGER NOT NULL,
created_at TEXT NOT NULL,
FOREIGN KEY(whitelist_id) REFERENCES whitelist(id),
FOREIGN KEY(charge_point_id) REFERENCES charge_point(id),
UNIQUE(whitelist_id, charge_point_id)
);

-- data insertion (whitelist)
INSERT INTO whitelist(label, organization_id, paid_by_organization, created_at, expires_at) VALUES
('Premiere whitelist', 1, 1, '2021-11-22', null),
('whitelist test', 1, 0, '2021-11-23', null);

INSERT INTO whitelist_user(whitelist_id, user_id, created_at, expires_at) VALUES
(1, 1, '2021-11-22', '2021-12-03'),
(2, 1, '2021-11-23', '2021-11-24');

INSERT INTO whitelist_charge_point(whitelist_id, charge_point_id, created_at) VALUES
(1, 1, '2021-11-22'),
(1, 2, '2021-11-22'),
(1, 3, '2021-11-22'),
(1, 4, '2021-11-22'),
(2, 1, '2021-11-23');