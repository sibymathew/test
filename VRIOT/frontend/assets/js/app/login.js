/**
 * Created by aditya on 4/4/17
 */

app.controller('LoginController', ['$rootScope', '$scope', '$http', '$window',
    function ($rootScope, $scope, $http, $window) {
        $rootScope.showHeader = false;
        console.log('Logged in');
    }
]);