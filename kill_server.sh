#!/bin/sh
NAME="testProject_uwsgi"
if [ ! -n "$NAME" ];then
    echo "no arguments"
    exit;
fi

echo $NAME

#kill -9 `ps -ef|grep $NAME|grep -v grep|awk 'NR==1{print $2}'`
PID=`ps -ef|grep $NAME|grep -v grep|awk 'NR==1{print $2}'`
if [ -z $PID ];
then      
    echo The server is not running...
else
    echo The server is running...
    echo "kill -9 $PID"
    kill -9 $PID
fi

