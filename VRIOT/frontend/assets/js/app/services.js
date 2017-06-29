/**
 * Created by aditya on 11/4/17.
 */

/* Common service to fetch all gateways */
app.service('allGateways', ['$scope', '$http', 'ApiRequest', function ($scope, $http, ApiRequest) {
    console.log('service called');
    // var gateways = null;
    // var apiUrl = 'http://127.0.0.1:8000/app/v1/gateway/';
    //
    // var data = {
    //     requestType: 'GET',
    //     requestUrl: apiUrl,
    //     requestData: null
    // };
    // ApiRequest.sendRequest(data).then(function (result) {
    //     gateways = result.data;
    //     console.log(gateways);
    // })
    // return gateways;


}]);