# Elasticsearch Esrally Benchmarking

## To run containers

docker run -d \
--ulimit nofile=65536:65536 \
--name benchmark \
  -p 9200:9200 \
  -p 9300:9300 \
  694991618556.dkr.ecr.us-east-1.amazonaws.com/benchmark/elasticsearch \
  bin/elasticsearch \
  -Ecluster.name=unicast \
  -Enetwork.publish_host="10.0.0.220" \
  -Ediscovery.zen.ping.unicast.hosts="10.0.0.253" \
  -Ediscovery.zen.ping_timeout=3s \
  -Ediscovery.zen.minimum_master_nodes=1


docker run -d \
--ulimit nofile=65536:65536 \
--name esrally \
--network es-net \
  -p 9200:9200 \
  -p 9300:9300 \
  694991618556.dkr.ecr.us-east-1.amazonaws.com/benchmark/esrally \
  bin/elasticsearch \
  -Ecluster.name=unicast \
  -Enetwork.publish_host=10.0.0.253 \
  -Ediscovery.zen.ping.unicast.hosts=["10.0.0.220","monitoring:9301"] \
  -Ediscovery.zen.ping_timeout=3s \
  -Ediscovery.zen.minimum_master_nodes=1

docker run -d \
--ulimit nofile=65536:65536 \
--name monitoring \
--network es-net \
  -p 9201:9200 \
  -p 9301:9300 \
  694991618556.dkr.ecr.us-east-1.amazonaws.com/benchmark/elasticsearch \
  bin/elasticsearch \
  -Ecluster.name=unicast \
  -Ediscovery.zen.ping.unicast.hosts="esrally" \
  -Ediscovery.zen.ping_timeout=3s \
  -Ediscovery.zen.minimum_master_nodes=1
