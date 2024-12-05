-- Create the user if not exists (using backticks for username)
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'asdf1234';

-- Grant all privileges to the user for the specific database (not global)
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%';

-- Ensure privileges are flushed so they take effect
FLUSH PRIVILEGES;

CREATE DATABASE IF NOT EXISTS Asetto_Asset_Management;

