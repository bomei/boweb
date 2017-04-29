/**
 * Created by zannb on 2017/4/29.
 */

if (typeof GoEasy !== 'undefined') {
    var goEasy = new GoEasy({
        appkey: 'BC-659e091d3da74d17ba8934c6d195f1cc',
        userId: "bo",
        username: "bobo",
        onConnected: function () {
            console.log("Connect to GoEasy success.");
        },
        onDisconnected: function () {
            console.log("Disconnect to GoEasy server.");
        },
        onConnectFailed: function (error) {
            console.log("Connect to GoEasy failed, error code: " + error.code + " Error message: " + error.content);
        }
    });
}

function subscribe(chan) {
    goEasy.subscribe({
        channel: chan,
        onMessage: function (message) {
            console.log('Meessage received:' + message.content);
        },
        onSuccess: function () {

            console.log("Subscribe the Channel"+chan+" successfully.");

        },

        onFailed: function (error) {

            console.log("Subscribe the Channel"+chan+" failed, error code: " + error.code + " error message: " + error.content);

        }

    });

}

function publishMessage(chan, mess) {
    goEasy.publish({
        channel: chan,
        message: mess,
        onSuccess: function () {

            console.log("Publish message success.");

        },
        onFailed: function (error) {

            console.log("Publish message failed, error code: " + error.code + " Error message: " + error.content);

        }
    });

}

function unsubscribe(chan) {
    goEasy.unsubscribe({
        channel: chan,
        onSuccess: function () {

            console.log("Cancel Subscription of "+chan+" successfully.");

        },
        onFailed: function (error) {

            console.log("Cancel the subscription failed, error code: " + error.code + "error message: " + error.content);
        }

    });
}