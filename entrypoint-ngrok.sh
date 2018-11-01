#!/bin/sh
./ngrok authtoken $1
./ngrok http -subdomain=longbowdev webapp:5721