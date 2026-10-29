ALTER TABLE players
ADD COLUMN email VARCHAR(320) NULL,
ADD UNIQUE KEY uq_players_email (email);
