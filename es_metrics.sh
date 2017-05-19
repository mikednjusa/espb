#!/bin/bash
while [[ "$#" > 1 ]]; do case $1 in
    --url) url="$2";;
    --version) version="$2";;
    --indexname) indexname="$2";;
    --user) user="$2";;
    --password) password="$2";;
    --mapping_time) mapping_time="$2";;
    --fieldlist) fieldlist="$2";;
    *) break;;
  esac; shift; shift
done

#Check if version is supported or not
if [ "$version" = "2" ] || [ "$version" = "5" ]
then
  echo ""
else
  echo "Entered Version is $version , which is not supported please use --version as 2 or 5"
  exit
fi

#Check if ES can be reached or not
cluster_status=`curl -s $user:$password@$url/_cluster/health?pretty | grep -Po '\"status\" : \K\"[a-z]+\"'`
if [ "$cluster_status" = "\"green\"" ] || [ "$cluster_status" = "\"yellow\"" ]
then
  echo ""
else
  echo "Cluster state should be \"green\" or \"yellow\" to proceed but found $cluster_status ,please check if ES is running and cluster is not red"
  exit
fi


# Read the index name given as comma separated and store it to an index array
IFS=',' read -r -a index_array <<< "$indexname"
echo -e "---------- List of indices to compute metrics are ----------"
printf '%s\n' "${index_array[@]}"

# Read the fieldlist given as comma separated and store it to an fields array
IFS=',' read -r -a fields_array <<< "$fieldlist"
#printf '%s\n' "${fields_array[@]}"


## now loop through the above index array
daytimestamp=`date +"%Y-%m-%d_%H:%M:%S"`
for i in "${index_array[@]}"
do
   log_file_name_json=${daytimestamp}_${i}.json
   log_file_name_csv=${daytimestamp}_${i}.csv
   echo "Metrics for Index $i would be dumped to $log_file_name_json and $log_file_name_csv"

   primary_shards=`curl -s $user:$password@$url/_cat/indices/$i | awk '{print $4}'`
   replica_shards=`curl -s $user:$password@$url/_cat/indices/$i | awk '{print $5}'`
   total_shards=`expr $replica_shards + $primary_shards`
   total_docs=`curl -s $user:$password@$url/_cat/indices/$i | awk '{print $6}'`
   primary_disk_used=`curl -s $user:$password@$url/_cat/indices/$i | awk '{print $9}'`
   total_disk_used=`curl -s $user:$password@$url/_cat/indices/$i | awk '{print $8}'`
   primary_disk_used_number=`curl -s $user:$password@$url/_cat/indices/$i | awk '{print $9}' | tr -dc '0-9.0-9'`
   primary_disk_used_unit=`curl -s $user:$password@$url/_cat/indices/$i | awk '{print $9}' | tr -dc 'a-z'`
   total_disk_used_number=`curl -s $user:$password@$url/_cat/indices/$i | awk '{print $8}' | tr -dc '0-9.0-9'`
   total_disk_used_unit=`curl -s $user:$password@$url/_cat/indices/$i | awk '{print $8}' | tr -dc 'a-z'`
   average_disk_used_per_docs_primary=`echo "scale=1;$primary_disk_used_number/$total_docs" | bc`
   average_disk_used_per_docs_total=`echo "scale=1;$total_disk_used_number/$total_docs" | bc`

   cardinal_output="{"
   cardinal_output_csv=""
   for j in "${fields_array[@]}"
   do
        cardinal_query="{\"size\":\"0\",\"aggs\":{\"${j}_count\":{\"cardinality\":{\"field\":\"$j\"}}}}"
        cardinal_count=`curl -s "$user:$password@$url/$i/_search?pretty" -d $cardinal_query | grep -Po '\"value\" : \K[0-9]+'`
        cardinal_output="$cardinal_output \"$j\":$cardinal_count,"
        cardinal_output_csv="$cardinal_output_csv $cardinal_count,"
   done
   cardinal_output=${cardinal_output%?}
   cardinal_output_csv=${cardinal_output_csv%?}
   cardinal_output="$cardinal_output  }"
#   echo -e "cardinal_output is $cardinal_output"

   #CSV Output Start
   csv_header="daytimestamp, url, version, indexname, primary_shards, replica_shards, total_shards, total_docs, primary_disk_used, total_disk_used, average_disk_used_per_docs_primary, average_disk_used_per_docs_total, avg_source_chars, avg_message_chars, $fieldlist"

   csv_value="$daytimestamp, $url, $version, $i, $primary_shards, $replica_shards, $total_shards, $total_docs, $primary_disk_used, $total_disk_used, $average_disk_used_per_docs_primary$primary_disk_used_unit, $average_disk_used_per_docs_total$total_disk_used_unit, NA, NA,$cardinal_output_csv"

   echo -e "$csv_header \n$csv_value" >> $log_file_name_csv

   #JSON Output Start
   echo -e "\n\n --------------- Getting stats for Index : $i ---------------------" >> $log_file_name_json
   echo -e "\n++ Index Mapping : `curl -s $user:$password@$url/$i/_mapping?pretty`" >> $log_file_name_json
   echo -e "\n++ total_shards for $i : $total_shards \n++ primary_shards for $i : $primary_shards \n++ replica_shards for $i : $replica_shards \n++ total_docs count for $i : $total_docs \n++ primary_disk_used for $i : $primary_disk_used \n++ total_disk_used for $i : $total_disk_used \n++ average_disk_used_per_docs_primary for $i : $average_disk_used_per_docs_primary$primary_disk_used_unit \n++ average_disk_used_per_docs_total for $i : $average_disk_used_per_docs_total$total_disk_used_unit" >> $log_file_name_json


   printf '\n\n{\n "daytimestamp":"%s", \n "url":"%s", \n "version":"%s",\n "indexname":"%s", \n "total_shards":"%s", \n "primary_shards":"%s", \n "replica_shards":"%s", \n "total_docs":"%s", \n "primary_disk_used":"%s", \n "total_disk_used":"%s", \n "average_disk_used_per_docs_primary":"%s", \n "average_disk_used_per_docs_total":"%s", \n "avg_source_chars":"%s", \n "avg_message_chars":"%s", \n "cardinal_fields": %s \n }\n' "$daytimestamp" "$url" "$version" "$i" "$total_shards" "$primary_shards" "$replica_shards" "$total_docs" "$primary_disk_used" "$total_disk_used" "$average_disk_used_per_docs_primary$primary_disk_used_unit" "$average_disk_used_per_docs_total$total_disk_used_unit" "NA" "NA" "$cardinal_output" >> $log_file_name_json

done
