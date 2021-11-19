-- this script list all table creations and initial data for creating start.db

-- tables creation
CREATE TABLE role(
id INTEGER PRIMARY KEY,
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


-- data insertion
INSERT INTO role(name) VALUES
('administrator'),
('employee');

INSERT INTO organization(name) VALUES
('Qovoltis'),
('Etna'),
('Coop Agricole Vendee Approv vente Cereale'),
('Lavage de l''est');

INSERT INTO user(email, password, firstname, lastname, organization_id) VALUES
('administrator@dummy.qovoltis.com', 'password', 'Johnny', 'Hopkins', 1),
('ellen.willis@dummy.qovoltis.com', 'password', 'Ellen', 'Willis', 1),
('alan.fleming@dummy.qovoltis.com', 'password', 'Alan', 'Fleming', 1),
('larry.baker@dummy.qovoltis.com', 'password', 'Larry', 'Baker', 1),
('samantha.hicks@dummy.qovoltis.com', 'password', 'Samantha', 'Hicks', 1),
('carrie.holahan@dummy.qovoltis.com', 'password', 'Carrie', 'Holahan', 1),
('june.roderiquez@dummy.qovoltis.com', 'password', 'June', 'Roderiquez', 1),
('administrator@dummy.etna.com', 'password', 'Joshua', 'Cervantez', 2),
('sandra.pawlak@dummy.etna.com', 'password', 'Sandra', 'Pawlak', 2),
('nicholas.hamilton@dummy.etna.com', 'password', 'Nicholas', 'Hamilton', 2),
('mark.frahm@dummy.etna.com', 'password', 'Mark', 'Frahm', 2),
('edwin.daniels@dummy.etna.com', 'password', 'Edwin', 'Daniels', 2),
('gary.remaley@dummy.etna.com', 'password', 'Gary', 'Remaley', 2),
('byron.rodriguez@dummy.etna.com', 'password', 'Byron', 'Rodriguez', 2);

-- all users are employees
INSERT INTO user_role(user_id, role_id)
SELECT u.id, 2 from user u;

-- there are only one admin by organization
INSERT INTO user_role(user_id, role_id)
SELECT u.id, 1 from user u where u.email in(
'administrator@dummy.qovoltis.com',
'administrator@dummy.etna.com'
);