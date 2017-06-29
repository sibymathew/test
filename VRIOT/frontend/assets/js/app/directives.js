/**
 * Created by aditya on 11/4/17.
 */

app.directive('a', function() {
    return {
        restrict: 'E',
        link: function(scope, elem, attrs) {
            if(attrs.ngClick || attrs.href === '' || attrs.href === '#'){
                elem.on('click', function(e){
                    e.preventDefault();
                });
            }
        }
    };
});

app.directive('slider', function() {
    return {
        restrict: 'A',
        scope: {
            ngModel: '='
        },
        link: function(scope, elem, attrs) {

            console.log(scope.ngModel);

            return $(elem).slider({
                min: 0,
                max: 255,
                range: "min",
                animate: true,
                value: scope.ngModel,
                slide: function(event, ui) {
                    return scope.$apply(function(){
                        scope.ngModel = ui.value;
                    });
                }
            });
        }
    };
});

app.directive('knob',['$timeout', function ($timeout) {
    return {
        restrict: 'EA',
        replace: true,
        template: '<input value="{{ knobData }}"/>',
        scope: {
            knobData: '=',
            knobMax: '=',
            knobReadonly: '=',
            knobOptions: '&'
        },
        link: function($scope, $element) {
            var knobInit = $scope.knobOptions() || { 'max': 256, 'readOnly': $scope.knobReadonly };

            knobInit.release = function(newValue) {
                $timeout(function() {
                    $scope.knobData = newValue;
                    $scope.$apply();
                }, 0, false);
            };

            $scope.$watch('knobData', function(newValue, oldValue) {
                if (newValue !== oldValue) {
                    $($element).val(newValue).change();
                }
            });

            $scope.$watch('knobMax', function (newValue) {
                $scope.knobMax = newValue;
            });

            $scope.$watch('knobReadonly', function (newValue) {
                $scope.knobReadonly = newValue;
            });

            $($element).val($scope.knobData).knob(knobInit);
        }
    };
}]);

app.directive('fileUpload', function(httpPostFactory) {
    return {
        restrict: 'A',
        link: function(scope, element, attr) {
            element.bind('change', function() {
                var formData = new FormData();
                formData.append('file', element[0].files[0]);

                // optional front-end logging
                var fileObject = element[0].files[0];
                console.log(fileObject);
                scope.fileLog = {
                    'lastModified': fileObject.lastModified,
                    'lastModifiedDate': fileObject.lastModifiedDate,
                    'name': fileObject.name,
                    'size': fileObject.size,
                    'type': fileObject.type
                };
                scope.$apply();

                /*  ---> post request to your php file and use $_FILES in your php file   < ----
                 httpPostFactory('your_upload_image_php_file.php', formData, function (callback) {
                 console.log(callback);
                 });
                 */
            });

        }
    };
});

app.directive('myUpload', [function () {
    return {
        restrict: 'A',
        link: function (scope, elem, attrs) {
            var reader = new FileReader();
            reader.onload = function (e) {
                scope.image = e.target.result;
                scope.$apply();
            }

            elem.on('change', function() {
                reader.readAsDataURL(elem[0].files[0]);
            });
        }
    };
}]);