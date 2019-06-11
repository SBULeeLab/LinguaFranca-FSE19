mkdir raw-data 2>/dev/null
mkdir data 2>/dev/null
ERR_FILE=/tmp/$$.err
rm $ERR_FILE 2>/dev/null

echo "Redirecting stderr to $ERR_FILE"

set -e
set -x

./fetch-regexlib-html.sh 60 2>>$ERR_FILE
./parse-regexlib-html.py --html-dir raw-data --out-file data/internetSources-regExLib.json 2>>$ERR_FILE
set +x

echo "Regexes from www.regexlib.com are in data/internetSources-regExLib.json"
