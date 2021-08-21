#!/bin/bash
AppName="pr-latency-bot.py"
App="app/pr-latency-bot.py"

echo $1

function killProcess() {
    NAME=$1
    echo $NAME
    PID=$(ps -ef | grep $NAME | awk '{print $2}')
    echo "PID: $PID"
    kill -9 $PID
}

function start() {
    echo "start $AppName"
    nohup python -u $App > $AppName.log 2>&1 &
}

function stop() {
    echo "stop $AppName"
    killProcess $AppName
}

function restart() {
    echo "restart $AppName"
    stop
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
esac
