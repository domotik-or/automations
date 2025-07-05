DELETE FROM linky WHERE timestamp < DATETIME('NOW', '-5 DAY');
DELETE FROM on_off WHERE timestamp < DATETIME('NOW', '-5 DAY');
DELETE FROM pressure WHERE timestamp <  DATETIME('NOW', '-5 DAY');
DELETE FROM sonoff_snzb02p WHERE timestamp <  DATETIME('NOW', '-5 DAY');
VACUUM;
