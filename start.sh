rootdir = `dirname $0`
cd $rootdir
cd update/stats
chmod +x vlicengen

if [ ! -f liense.xml ]
then
    echo "license.xml is missing,can not start !"
fi

ps -fe | grep 0.0.0.0:8101 | grep -v grep
if [ $? -ne 0 ]
 then
   cd $rootdir
   nohup python manage.py runserver 0.0.0.0:8101  >/dev/null 2>&1  &
 else
   echo "runing product_manager"
fi