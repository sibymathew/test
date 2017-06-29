/**
 * Created by aditya on 4/4/17.
 */


var app = angular.module('ruckus-iot', ['ngResource', 'ngRoute']);

app.config(['$routeProvider', '$locationProvider', '$httpProvider',
    function ($routeProvider, $locationProvider) {
        $routeProvider.when("/login",
            {
                templateUrl: 'html/login.html',
                controller: 'LoginController'
            })
            .when("/dashboard",
                {
                    templateUrl: 'html/dashboard.html'
                })
            .when("/gateway",
                {
                    templateUrl: 'html/gateway.html'
                })
            .when("/device",
                {
                    templateUrl: 'html/device.html'
                })
            .when("/addgateway",
                {
                    templateUrl: 'html/add_gateway.html',
                    controller: 'AddGatewayController'
                })
            .when("/editgateway/:id",
                {
                    templateUrl: 'html/edit_gateway.html',
                    controller: 'EditGatewayController'
                })
            .when("/adddevice",
                {
                    templateUrl: 'html/add_device.html',
                    controller: 'AddDeviceController'
                })
            .when("/editdevice/:id",
                {
                    templateUrl: 'html/edit_device.html',
                    controller: 'EditDeviceController'
                })
            .when("/floormap",
                {
                    templateUrl: 'html/floormap.html'
                })
            .otherwise(
                {
                    redirectTo: '/login'
                }
            );
        $locationProvider.html5Mode(true);
    }
]);

app.run(['$rootScope', 'AuthFactory', function ($rootScope, AuthFactory) {
    $rootScope.$on('$locationChangeStart', function () {
        $rootScope.showHeader = true;
        // This factory checks for authentication in the local storage and redirects to login if auth fails
        //AuthFactory.validate_auth();
    });
}]);