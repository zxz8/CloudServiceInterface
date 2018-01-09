kill -9 `ps -ef|grep 0.0.0.0:9099|grep -v grep|awk '{print $2}'`
