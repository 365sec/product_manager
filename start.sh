cd  `dirname $0`
cd update/status
chmod +x vlicensegen

if [ ! -f license.xml ]
then
    echo "license.xml is missing,can not start !"
    exit 0
else
    echo "find license.xml"
fi

ps -fe | grep 0.0.0.0:8101 | grep -v grep
if [ $? -ne 0 ]
 then
   cd ../
   nohup python manage.py runserver 0.0.0.0:8101  >error.txt 2>&1  &
   echo "start product_manager"
 else
   echo "product_manager is already running"
fi