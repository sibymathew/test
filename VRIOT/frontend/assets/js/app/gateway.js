/**
 * Created by aditya on 3/3/17.
 */

app.controller('GatewayController', ['$scope', '$http', '$window', 'ApiRequest',
    function ($scope, $http, $window, ApiRequest) {
        //$scope.login = function () {
        $scope.isContentLoaded = false;
        $scope.showHeader = true;
        var apiUrl = 'http://127.0.0.1:8000/app/v1/gateway/';

        var data = {
            requestType: 'GET',
            requestUrl: apiUrl,
            requestData: null
        };
        ApiRequest.sendRequest(data).then(function (result) {
            $scope.gateways = result.data;
            $scope.isContentLoaded = true;
            console.log($scope.gateways);
        })
            .catch(function (response) {
                if (response.status == 400) {
                    $scope.errorMessage = 'Something went wrong! Please try again.';
                }
                if (response.status == 404) {
                    $scope.noData = true;
                    $scope.isContentLoaded = true;
                }
                if (response.status == 200) {
                    $scope.noData = false;
                    $scope.isContentLoaded = true;
                }
            });

        $scope.deleteGateway = function (gateway_id) {
            var deleteGatewayApiUrl = 'http://127.0.0.1:8000/app/v1/gateway/'+gateway_id;
            var data = {
                requestType: 'DELETE',
                requestUrl: deleteGatewayApiUrl,
                requestData: null
            };

            ApiRequest.sendRequest(data).then(function (result) {
                var data = {
                    requestType: 'GET',
                    requestUrl: apiUrl,
                    requestData: null
                };

                ApiRequest.sendRequest(data).then(function (result) {
                    $scope.gateways = result.data;
                }, function(err){
                    $scope.gateways = null
                });
            })
                .catch(function (response) {
                    if (response.status == 400) {
                        $scope.errorMessage = 'Something went wrong! Please try again.';
                    }
                    if (response.status == 404) {
                        $scope.noData = true;
                        $scope.isContentLoaded = true;
                    }
                });

        }
        //}
    }
]);

app.controller('EditGatewayController', ['$routeParams', '$scope', '$http', '$window', 'ApiRequest', 'ApiFormRequest',
    '$location', function ($routeParams, $scope, $http, $window, ApiRequest, ApiFormRequest, $location) {

        //$scope.login = function () {
        $scope.isContentLoaded = false;
        $scope.showHeader = true;
        var gateway_id = $routeParams.id;
        var apiUrl = 'http://127.0.0.1:8000/app/v1/gateway/'+gateway_id;

        var data = {
            requestType: 'GET',
            requestUrl: apiUrl,
            requestData: null
        };
        ApiRequest.sendRequest(data).then(function (result) {
            $scope.gateway_data = result.data;
            $scope.isContentLoaded = true;
            if($scope.gateway_data['tags']!=null){
                $scope.gateway_tags = $scope.gateway_data['tags'].toString();
            }
            console.log($scope.gateway_tags);
        })
            .catch(function (response) {
                if (response.status == 400) {
                    $scope.errorMessage = 'Something went wrong! Please try again.';
                }
            });

        //Edit the details of Gateway
        $scope.editGateway = function () {
            var form_obj = new FormData();
            console.log($scope.gatewayTags);
            form_obj.gateway_name = $scope.gatewayName;
            form_obj.gateway_euid = $scope.gatewayMacAddress;
            if($scope.gatewayTags != null){
                form_obj.tags = $scope.gatewayTags.split(",");
            }
            console.log(JSON.stringify(form_obj));
            ApiFormRequest.sendRequest({
                requestType: 'PATCH',
                requestUrl: apiUrl,
                requestFormData: JSON.stringify(form_obj),
                requestHeaders: {headers: {'Content-Type': undefined}}
            }).then(
                function (result) {
                    if (result.status == 200) {
                        $location.path( "/gateway" );
                        //$log.info($scope.gatewaySettings.messages.success.suc_api_gateway_add);
                    }
                }
                ,function (err) {
                    if (err.data) {
                        console.log($scope.gatewayName+' already exists');
                    }
                }
            );

        }
        //}
    }
]);

app.controller('AddGatewayController', ['$scope', '$http', '$window', 'ApiRequest', 'ApiFormRequest', '$location',
    function ($scope, $http, $window, ApiRequest, ApiFormRequest, $location) {
        //$scope.login = function () {
        $scope.isContentLoaded = false;
        $scope.showHeader = true;
        var apiUrl = 'http://127.0.0.1:8000/app/v1/gateway/';
        $scope.addGateway = function () {
            var form_obj = new FormData();
            form_obj.gateway_name = $scope.gatewayName;
            form_obj.gateway_euid = $scope.gatewayMacAddress;
            if($scope.gatewayTags != null) {
                form_obj.tags = $scope.gatewayTags.split(",");
            }
            console.log(JSON.stringify(form_obj));
            ApiFormRequest.sendRequest({
                requestType: 'POST',
                requestUrl: apiUrl,
                requestFormData: JSON.stringify(form_obj),
                requestHeaders: {headers: {'Content-Type': undefined}}
            }).then(
                function (result) {
                    if (result.status == 201) {
                        $location.path( "/gateway" );
                        //$log.info($scope.gatewaySettings.messages.success.suc_api_gateway_add);
                    }
                }
                ,function (err) {
                    if (err.data) {
                        console.log($scope.gatewayName+' already exists');
                    }
                }
            );

        }
        //}
    }
]);