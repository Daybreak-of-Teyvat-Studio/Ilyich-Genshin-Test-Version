set -e
echo "begin test"
echo "pwd = `pwd`"
echo "will test bracket"
python3 ci-test/CheckBracket.py
echo "test bracket end"
echo "finish test"
