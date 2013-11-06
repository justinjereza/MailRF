MailRF
======

The mailrfd.py script is a daemon that accepts a data regarding an e-mail's sender and recipients from a milter like mailfromd. Specifically, these are envelop and recipients as well as from, to, and cc headers. Upon receiving a "PROCESS" message, it returns a list of recipients to remove from the envelop. The restrict.txt file contains the list of e-mail addresses to be removed in the event one or more recipient addresses are found in the secure.txt file.

If \_\_debug\_\_ == True, the daemon will listen on localhost port 8027, log to STDERR, and assume $WORKING_DIR is the same directory where the script is located. Otherwise (if the script is executed with python -O), it will listen as a UNIX socket at $WORKING_DIR/socket and log to syslog.

The restrict.txt and secure.txt files must always be located in $WORKING_DIR. On SIGHUP, the daemon will re-initialize the e-mail address list using those two files. On SIGUSR1, the address list loaded in memory will be written to the log.

An example of the data the daemon expects can be found in tests.py. To run the tests, execute "make test". The test will send data for processing to the daemon and print the response as well as print what would have been written to the log file. Running "make clean" removes the _trial_temp directory as well as *.py[co].
