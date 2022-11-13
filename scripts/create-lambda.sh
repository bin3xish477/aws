#!/bin/bash

if [[ "$#" -ne 5 ]]
then
  echo 'usage: $0 [profile] [code_file] [func_name] [func_role] [runtime]'
  exit 1
fi

PROFILE=$1
FUNC_CODE=$2
FUNC_NAME=$3
FUNC_ROLE=$4
RUNTIME=$5

zip function.zip $FUNC_CODE

aws --profile $PROFILE lambda create-function \
  --function-name $FUNC_NAME \
  --zip-file fileb://function.zip \
  --handler ${FUNC_NAME}.handler \
  --runtime $RUNTIME \
  --role $FUNC_ROLE

rm function.zip
