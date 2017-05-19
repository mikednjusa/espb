FILE="/home/ec2-user/es_rally_output.txt"
# In some cases, the esrally process is still running, but the actual test run is done.
# So we look at the logs to determine if esrally has truly stopped:
if [ -f $FILE ]; then
  if grep -q "Logs for this race are archived" $FILE ;then
    echo "Stopped"
  elif grep -q "esrally: error: unrecognized arguments:" $FILE ;then
    echo "Stopped"
  elif grep -q "Archiving logs" $FILE ;then
    echo "Stopped"
  elif grep -q " FAILURE " $FILE;then
    echo "Stopped"
  else
    echo "Running"
  fi
else
  echo "$FILE does not exist."
fi
