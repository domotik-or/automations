DELETE FROM linky WHERE timestamp < DATETIME('NOW', '-5 DAY');
DELETE FROM on_off WHERE timestamp < DATETIME('NOW', '-5 DAY');
DELETE FROM pressure WHERE timestamp <  DATETIME('NOW', '-5 DAY');
DELETE FROM temperature_humidity WHERE timestamp <  DATETIME('NOW', '-5 DAY');
VACUUM;
