Influxdb image

docker run -d --name influxdb -p 8086:8086 -v /Users/bulgarelli/dbms/gammaflash/influxdb:/var/lib/influxdb2 influxdb

You should add the userid also

docker run -u 1001:1001 -d --name influxdb -p 8086:8086 -v /Users/bulgarelli/dbms/gammaflash/influxdb:/var/lib/influxdb2 influxdb

Username = gammaflash
Org = GAMMA-FLASH
Bucket = RP-COUNTS
BucketHk = HK 

