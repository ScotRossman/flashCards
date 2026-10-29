ALTER TABLE players
ADD COLUMN cognito_sub VARCHAR(255) NULL,
ADD UNIQUE KEY uq_players_cognito_sub (cognito_sub);
