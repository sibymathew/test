/**
 * Created by aditya on 03/03/17.
 */

app.controller('DeviceController', ['$scope', '$http', '$window', 'ApiRequest', 'ApiFormRequest',
    function ($scope, $http, $window, ApiRequest, ApiFormRequest) {
        //$scope.login = function () {
        $scope.isContentLoaded = false;
        var apiUrl = 'http://127.0.0.1:8000/app/v1/device/';

        var data = {
            requestType: 'GET',
            requestUrl: apiUrl,
            requestData: null
        };
        ApiRequest.sendRequest(data).then(function (result) {
            $scope.devices = result.data;
            $scope.isContentLoaded = true;
            // console.log($scope.devices);
        })
            .catch(function (response) {
                if (response.status == 400) {
                    $scope.errorMessage = 'Something went wrong! Please try again.';
                }
            });

        // $scope.brightness = 128;
        $scope.changeLux = function (device_id, sensor_id, value, sensor_type, function_id, capability_id,
                                     user_command) {
            console.log(device_id+ ' and '+capability_id+' and '+user_command);
            var patchDeviceApiUrl = 'http://127.0.0.1:8000/app/v1/device/'+device_id;

            var data_body = {
                "device_sensors":[{
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "function_id": function_id,
                    "capability":{

                    }
                }]
            };

            data_body['device_sensors'][0]['capability'][capability_id] = {
                "configured_value":{
                    "level": value
                },
                "user_command":user_command
            };

            console.log(JSON.stringify(data_body));
            ApiFormRequest.sendRequest({
                requestType: 'PATCH',
                requestUrl: patchDeviceApiUrl,
                requestFormData: JSON.stringify(data_body),
                requestHeaders: {headers: {'Content-Type': undefined}}
            }).then(
                function (result) {
                    if (result.status == 200) {
                        console.log('done');
                        //$location.path( "/device" );
                        //$log.info($scope.deviceSettings.messages.success.suc_api_device_add);
                    }
                }
                ,function (err) {
                    if (err.data) {
                        console.log(err.data);
                        console.log($scope.deviceName+' already exists');
                    }
                }
            );

        }

        $scope.changeColor = function (device_id, sensor_id, red, green, blue, sensor_type, function_id, capability_id,
                                       user_command) {
            console.log(device_id+ ' and '+capability_id+' and '+user_command);
            var patchDeviceApiUrl = 'http://127.0.0.1:8000/app/v1/device/'+device_id;

            var data_body = {
                "device_sensors":[{
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "function_id": function_id,
                    "capability":{

                    }
                }]
            };

            data_body['device_sensors'][0]['capability'][capability_id] = {
                "configured_value":{
                    "red": red, "green": green, "blue": blue
                },
                "user_command":user_command
            };

            console.log(JSON.stringify(data_body));
            ApiFormRequest.sendRequest({
                requestType: 'PATCH',
                requestUrl: patchDeviceApiUrl,
                requestFormData: JSON.stringify(data_body),
                requestHeaders: {headers: {'Content-Type': undefined}}
            }).then(
                function (result) {
                    if (result.status == 200) {
                        console.log('done');
                        //$location.path( "/device" );
                        //$log.info($scope.deviceSettings.messages.success.suc_api_device_add);
                    }
                }
                ,function (err) {
                    if (err.data) {
                        console.log(err.data);
                        console.log($scope.deviceName+' already exists');
                    }
                }
            );

        }

        $scope.deleteDevice = function (gateway_id) {
            console.log('del device');
            var deleteDeviceApiUrl = 'http://127.0.0.1:8000/app/v1/device/'+gateway_id;
            var data = {
                requestType: 'DELETE',
                requestUrl: deleteDeviceApiUrl,
                requestData: null
            };

            ApiRequest.sendRequest(data).then(function (result) {
                var data = {
                    requestType: 'GET',
                    requestUrl: apiUrl,
                    requestData: null
                };

                ApiRequest.sendRequest(data).then(function (result) {
                    $scope.devices = result.data;
                }, function(err){
                    $scope.devices = null
                });
            })
                .catch(function (response) {
                    if (response.status == 400) {
                        $scope.errorMessage = 'Something went wrong! Please try again.';
                    }
                });

        }
        $scope.patchDevice = function (device_id, sensor_id, value, sensor_type, function_id, capability_id,
                                       user_command) {
            console.log(device_id+ ' and '+capability_id+' and '+user_command);
            console.log(typeof(device_id)+ ' and '+typeof(capability_id)+' and '+typeof(user_command));
            var patchDeviceApiUrl = 'http://127.0.0.1:8000/app/v1/device/'+device_id;

            var data_body = {
                "device_sensors":[{
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "function_id": function_id,
                    "capability":{

                    }
                }]
            };

            data_body['device_sensors'][0]['capability'][capability_id] = {
                "configured_value":{
                    "on": value
                },
                "user_command":user_command
            };

            console.log(JSON.stringify(data_body));
            ApiFormRequest.sendRequest({
                requestType: 'PATCH',
                requestUrl: patchDeviceApiUrl,
                requestFormData: JSON.stringify(data_body),
                requestHeaders: {headers: {'Content-Type': undefined}}
            }).then(
                function (result) {
                    if (result.status == 200) {
                        console.log('done');
                        //$location.path( "/device" );
                        //$log.info($scope.deviceSettings.messages.success.suc_api_device_add);
                    }
                }
                ,function (err) {
                    if (err.data) {
                        console.log(err.data);
                        console.log($scope.deviceName+' already exists');
                    }
                }
            );

        }

        $scope.lockDevice = function (device_id, sensor_id, value, sensor_type, function_id, capability_id,
                                       user_command) {
            console.log(device_id+ ' and '+capability_id+' and '+user_command);
            console.log(typeof(device_id)+ ' and '+typeof(capability_id)+' and '+typeof(user_command));
            var patchDeviceApiUrl = 'http://127.0.0.1:8000/app/v1/device/'+device_id;

            var data_body = {
                "device_sensors":[{
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "function_id": function_id,
                    "capability":{

                    }
                }]
            };

            data_body['device_sensors'][0]['capability'][capability_id] = {
                "configured_value":{
                    "lock": value
                },
                "user_command":user_command
            };

            console.log(JSON.stringify(data_body));
            ApiFormRequest.sendRequest({
                requestType: 'PATCH',
                requestUrl: patchDeviceApiUrl,
                requestFormData: JSON.stringify(data_body),
                requestHeaders: {headers: {'Content-Type': undefined}}
            }).then(
                function (result) {
                    if (result.status == 200) {
                        console.log('done');
                        //$location.path( "/device" );
                        //$log.info($scope.deviceSettings.messages.success.suc_api_device_add);
                    }
                }
                ,function (err) {
                    if (err.data) {
                        console.log(err.data);
                    }
                }
            );

        }

        $scope.fetchDeviceInfo = function(device_id){
            var fetchDeviceDetailUrl = 'http://127.0.0.1:8000/app/v1/device/'+device_id;

            var data = {
                requestType: 'GET',
                requestUrl: fetchDeviceDetailUrl,
                requestData: null
            };
            ApiRequest.sendRequest(data).then(function (result) {
                $scope.deviceTabData = result.data;
                console.log($scope.deviceTabData);
                angular.forEach($scope.deviceTabData['device_sensor'][0]['capability'], function(value){
                    if(value['user_command']=='BRIGHTNESS'){
                        $scope.devBrightness = value['configured_value']['level'];
                    }
                    if(value['user_command']=='STATE'){
                        $scope.devState = value['configured_value']['on'];
                    }
                    if(value['user_command']=='LOCK_STATE'){
                        $scope.lockState = value['configured_value']['lock'];
                    }
                    if(value['user_command']=='COLOR'){
                        $scope.red = value['configured_value']['red'];
                        $scope.blue = value['configured_value']['blue'];
                        $scope.green = value['configured_value']['green'];
                    }
                });

            })
                .catch(function (response) {
                    if (response.status == 400) {
                        $scope.errorMessage = 'Something went wrong! Please try again.';
                    }
                });
        }
        //}
    }
]);

app.controller('TabController', function () {
    this.tab = 0;

    this.setTab = function (tabId) {
        this.tab = tabId;
    };

    this.isSet = function (tabId) {
        return this.tab === tabId;
    };
});

app.controller('EditDeviceController', ['$routeParams', '$scope', '$http', '$window', 'ApiRequest', 'ApiFormRequest',
    '$location', function ($routeParams, $scope, $http, $window, ApiRequest, ApiFormRequest, $location) {
        //$scope.login = function () {
        var device_id = $routeParams.id;
        $scope.isContentLoaded = false;
        var apiUrl = 'http://127.0.0.1:8000/app/v1/device/'+device_id;

        var data = {
            requestType: 'GET',
            requestUrl: apiUrl,
            requestData: null
        };
        ApiRequest.sendRequest(data).then(function (result) {
            $scope.device_data = result.data;
            console.log($scope.device_data['tags']);
            $scope.device_tags = $scope.device_data['tags'].toString();
            $scope.isContentLoaded = true;
        })
            .catch(function (response) {
                if (response.status == 400) {
                    $scope.errorMessage = 'Something went wrong! Please try again.';
                }
            });
        $scope.editDevice = function () {
            var form_obj = new FormData();
            form_obj.device_name = $scope.deviceName;
            if($scope.deviceTags != null) {
                form_obj.tags = $scope.deviceTags.split(",");
            }
            //form_obj.gateway = $scope.addGateway;
            console.log(JSON.stringify(form_obj));
            ApiFormRequest.sendRequest({
                requestType: 'PATCH',
                requestUrl: apiUrl,
                requestFormData: JSON.stringify(form_obj),
                requestHeaders: {headers: {'Content-Type': undefined}}
            }).then(
                function (result) {
                    if (result.status == 201 || result.status == 200) {
                        $location.path( "/device" );
                        //$log.info($scope.deviceSettings.messages.success.suc_api_device_add);
                    }
                }
                ,function (err) {
                    if (err.data) {
                        console.log($scope.deviceName+' already exists');
                    }
                }
            );
        }
        //}
    }
]);

app.controller('AddDeviceController', ['$rootScope', '$scope', '$http', '$window', 'ApiRequest', 'ApiFormRequest',
    '$location', function ($rootScope, $scope, $http, $window, ApiRequest, ApiFormRequest, $location) {
        var apiUrl = 'http://127.0.0.1:8000/app/v1/device/';
        var allGatewaysUrl = 'http://127.0.0.1:8000/app/v1/gateway/';

        var data = {
            requestType: 'GET',
            requestUrl: allGatewaysUrl,
            requestData: null
        };
        ApiRequest.sendRequest(data).then(function (result) {
            $scope.gateways = result.data;
            console.log($scope.gateways);
        })
        $scope.addDevice = function () {
            var form_obj = new FormData();
            form_obj.device_name = $scope.deviceName;
            form_obj.device_euid = $scope.deviceMacAddress;
            if($scope.deviceTags != null) {
                form_obj.tags = $scope.deviceTags.split(",");
            }
            form_obj.gateway_euid = $scope.addGateway;
            console.log(JSON.stringify(form_obj));
            ApiFormRequest.sendRequest({
                requestType: 'POST',
                requestUrl: apiUrl,
                requestFormData: JSON.stringify(form_obj),
                requestHeaders: {headers: {'Content-Type': undefined}}
            }).then(
                function (result) {
                    if (result.status == 201 || result.status == 200) {
                        $location.path( "/device" );
                        //$log.info($scope.deviceSettings.messages.success.suc_api_device_add);
                    }
                }
                ,function (err) {
                    if (err.data) {
                        console.log($scope.deviceName+' already exists');
                    }
                }
            );

        }
    }
]);

