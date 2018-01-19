



print("hello")
print("world")




export KEY=admintoken

curl -X POST http://localhost:63000/jobs/42/append_log/ \
-H "Authorization: $KEY" \
-d "hello"

 tar -zcvf \
 	abfe9911-ade7-44d9-b528-7a6fc731f590.tar.gz \
 	/tmp/abfe9911-ade7-44d9-b528-7a6fc731f590

curl \
  --request PUT \
  --upload-file /tmp/abfe9911-ade7-44d9-b528-7a6fc731f590.tar.gz \
  "https://tlapp.s3.amazonaws.com/abfe9911-ade7-44d9-b528-7a6fc731f590.tar.gz?AWSAccessKeyId=AKIAIROBNIBGQH5O7Q5A&Signature=roqc9VtLqHeEIqvbF1VL7SEyMHU%3D&Expires=1518833460"



Rscript --default-packages=methods,stats,utils /tmp/a8e184b7-8e7a-497a-9bb5-17466e0672a0/runner.R /tmp/a8e184b7-8e7a-497a-9bb5-17466e0672a0/script.Rmd /tmp/a8e184b7-8e7a-497a-9bb5-17466e0672a0/inputs.json /tmp/abfe9911-ade7-44d9-b528-7a6fc731f590 | python push_logs.py





tasks.py:

	- create wrapper.sh
	- execute in screen
	- receive logs via push_logs.py

wrapper.sh
	
	export TLAPP_TOKEN=...
	export S3_PUT_URL="..."
	Rscript --default-packages=methods,stats,utils /tmp/e592cef2-e190-4faa-9c10-6793f7c5be34/runner.R /tmp/e592cef2-e190-4faa-9c10-6793f7c5be34/script.Rmd /tmp/e592cef2-e190-4faa-9c10-6793f7c5be34/inputs.json /tmp/615d8b70-dc42-40b7-a682-d6c73d4ac5f8 | push_logs.py

	tar <outputdir>
	curl -put <outputdir> S3_PUT_URL

	curl -post tl-app/job/:id/finished -h token=tlapp_token


POST /job/:id/append_log

	body: log line(s)


screen -dmS foo ./foo.sh;





export TLAPP_TOKEN=admintoken
export TLAPP_LOGS_URL=https://dc10126c.ngrok.io/jobs/44/append_log/

Rscript --default-packages=methods,stats,utils /tmp/a8e184b7-8e7a-497a-9bb5-17466e0672a0/runner.R /tmp/a8e184b7-8e7a-497a-9bb5-17466e0672a0/script.Rmd /tmp/a8e184b7-8e7a-497a-9bb5-17466e0672a0/inputs.json /tmp/abfe9911-ade7-44d9-b528-7a6fc731f590 | python push_logs.py

tar -zcvf \
 	abfe9911-ade7-44d9-b528-7a6fc731f590.tar.gz \
 	/tmp/abfe9911-ade7-44d9-b528-7a6fc731f590

curl \
  --request PUT \
  --upload-file /tmp/abfe9911-ade7-44d9-b528-7a6fc731f590.tar.gz \
  "https://tlapp.s3.amazonaws.com/abfe9911-ade7-44d9-b528-7a6fc731f590.tar.gz?AWSAccessKeyId=AKIAIROBNIBGQH5O7Q5A&Signature=roqc9VtLqHeEIqvbF1VL7SEyMHU%3D&Expires=1518833460"






