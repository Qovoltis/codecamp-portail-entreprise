-- this script list all table creations and initial data for creating start.db

-- tables creation
CREATE TABLE organization(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE user(
id INTEGER PRIMARY KEY AUTOINCREMENT,
email VARCHAR(255) UNIQUE NOT NULL,
firstname VARCHAR(50) UNIQUE NOT NULL,
lastname VARCHAR(100) UNIQUE NOT NULL,
organization_id INTEGER NOT NULL,
FOREIGN KEY(organization_id) REFERENCES organization(id)
);

CREATE TABLE role(
id INTEGER PRIMARY KEY,
name VARCHAR(30) UNIQUE NOT NULL
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

INSERT INTO user(email, firstname, lastname, organization_id) VALUES
('administrator@dummy.qovoltis.com', 'Johnny', 'Hopkins', 1),
('ellen.willis@dummy.qovoltis.com', 'Ellen', 'Willis', 1),
('alan.fleming@dummy.qovoltis.com', 'Alan', 'Fleming', 1),
('larry.baker@dummy.qovoltis.com', 'Larry', 'Baker', 1),
('samantha.hicks@dummy.qovoltis.com', 'Samantha', 'Hicks', 1),
('carrie.holahan@dummy.qovoltis.com', 'Carrie', 'Holahan', 1),
('june.roderiquez@dummy.qovoltis.com', 'June', 'Roderiquez', 1),
('administrator@dummy.etna.com', 'Joshua', 'Cervantez', 2),
('sandra.pawlak@dummy.etna.com', 'Sandra', 'Pawlak', 2),
('nicholas.hamilton@dummy.etna.com', 'Nicholas', 'Hamilton', 2),
('mark.frahm@dummy.etna.com', 'Mark', 'Frahm', 2),
('edwin.daniels@dummy.etna.com', 'Edwin', 'Daniels', 2),
('gary.remaley@dummy.etna.com', 'Gary', 'Remaley', 2),
('byron.rodriguez@dummy.etna.com', 'Byron', 'Rodriguez', 2);