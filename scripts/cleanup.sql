DELETE FROM linky WHERE timestamp < STRFTIME('%s', 'NOW', '-5 DAY');
DELETE FROM on_off WHERE timestamp < STRFTIME('%s', 'NOW', '-5 DAY');
DELETE FROM pressure WHERE timestamp <  STRFTIME('%s', 'NOW', '-5 DAY');
DELETE FROM temperature_humidity WHERE timestamp <  STRFTIME('%s', 'NOW', '-5 DAY');
VACUUM;
