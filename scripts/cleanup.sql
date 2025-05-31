DELETE FROM linky WHERE timestamp < NOW() - INTERVAL '5 DAY';
VACUUM linky;
DELETE FROM on_off WHERE timestamp < NOW() - INTERVAL '5 DAY';
VACUUM on_off;
DELETE FROM pressure WHERE timestamp < NOW() - INTERVAL '5 DAY';
VACUUM pressure;
DELETE FROM sonoff_snzb02p WHERE timestamp < NOW() - INTERVAL '5 DAY';
VACUUM sonoff_snzb02p ;
