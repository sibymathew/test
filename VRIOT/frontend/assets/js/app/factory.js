/**
 * Created by aditya on 4/4/17.
 */
// Send API request
app.factory('ApiRequest', ['$rootScope', '$http', '$log', function ($rootScope, $http, $log) {
    var ApiRequest = {};
    ApiRequest.sendRequest = function (data) {
        try {
            return $http({
                method: data.requestType,
                url: data.requestUrl,
                data: data.requestData
            });
        }
        catch (e) {
            $log.error('ApiRequest  - ' + e.message);
            return false;
        }
    };
    return ApiRequest;
}]);

app.factory('ApiFormRequest', ['$rootScope', '$http', '$log',
    function ($rootScope, $http, $log) {
        var ApiFormRequest = {};
        ApiFormRequest.sendRequest = function (data) {
            try {
                switch (data.requestType) {
                    case 'POST':
                        return $http.post(data.requestUrl, data.requestFormData, data.requestHeaders);
                    case 'PATCH':
                        return $http.patch(data.requestUrl, data.requestFormData, data.requestHeaders);
                }
            }
            catch (e) {
                $log.error('ApiFormRequest Factory : ApiFormRequest.sendRequest  - ' + e.message);
                return false;
            }
        };
        return ApiFormRequest;
    }
]);

app.factory('httpPostFactory', function($http) {
  return function(file, data, callback) {
    $http({
      url: file,
      method: "POST",
      data: data,
      headers: {
        'Content-Type': undefined
      }
    }).success(function(response) {
      callback(response);
    });
  };
});


app.factory('AuthFactory', ['$location', function ($location) {
    return {
        validate_auth: function () {
            console.log("Inside Auth");
            $location.path('/editgateway');
            // $window.location.href = 'login';
        }
    }
}]);