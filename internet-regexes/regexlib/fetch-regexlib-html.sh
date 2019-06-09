set -e
set -x

curl -L "http://regexlib.com/Search.aspx?k=&c=-1&m=-1&ps=100" > "raw-data/regexLibDump_Page1.html" 2>/tmp/fetchRegExLib.err
for (( c=2; c<$1; c++ ))
do
   curl -L "http://regexlib.com/Search.aspx?k=&c=-1&m=-1&ps=100&p=$c"  > "raw-data/regexLibDump_Page$c.html" 2>/tmp/fetchRegExLib.err
done
