In order to run the tests you need to have mocha and chai installed. You can do it by running the following command
Go into tests/javascript and run:
```bash
npm install mocha chai --save-dev
```
Then you can run a server from the root of the project:
```bash
python -m SimpleHTTPServer 7800 --bind 127.0.0.1
```
or with python3
```bash
python3 -m http.server 7800
```
And then access:
[Test runner](http://localhost:7800/tests/javascript/testrunner.html)
