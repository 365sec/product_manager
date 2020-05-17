
kill -9 `ps -ef |grep 0.0.0.0:8101 |awk '{print $2}'`