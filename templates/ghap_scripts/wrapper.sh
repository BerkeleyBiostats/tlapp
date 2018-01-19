export TLAPP_TOKEN={{ token }}
export TLAPP_LOGS_URL={{ logs_url }}

echo "Starting analysis" | python push_logs.py

{{ r_cmd }} | python push_logs.py

cd /tmp
tar -zcvf {{ tar_file }} {{ output_dir }}

curl \
  --request PUT \
  --upload-file {{ tar_file }} \
  "{{ put_url | safe }}"

curl \
  --request POST \
  -H "Authorization: $TLAPP_TOKEN" \
  -d "{}" \
  "{{ finish_url | safe }}"