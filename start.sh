rootdir = `dirname $0`
cd $rootdir
cd update/status
chmod +x vlicensegen

if [ ! -f license.xml ]
then
    echo "license.xml is missing,can not start !"
    exit(0)
fi

ps -fe | grep 0.0.0.0:8101 | grep -v grep
if [ $? -ne 0 ]
 then
   cd $rootdir
   nohup python manage.py runserver 0.0.0.0:8101  >/dev/null 2>&1  &
 else
   echo "runing product_manager"
fi