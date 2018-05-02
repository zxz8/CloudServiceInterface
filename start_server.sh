#!/bin/sh
NAME="testProject_uwsgi"
if [ ! -n "$NAME" ];then
    echo "no arguments"
    exit;
fi

echo $NAME

PID=`ps -ef|grep $NAME|grep -v grep|awk 'NR==1{print $2}'`
if [ -z $PID ];
then
    echo Ready to run server...
#      > logFile.txt
      > uwsgi.log
    uwsgi --ini $NAME.ini &
else
    echo The server is running...
fi

