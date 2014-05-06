'use strict';

/* Controllers */


var sensorinoApp = angular.module('sensorinoApp', ['restangular', 'ngRoute', 'angularCharts' ]);
//var sensorinoApp = angular.module('sensorinoApp', []);

sensorinoApp.config(['$httpProvider', function($httpProvider) {
        $httpProvider.defaults.useXDomain = true;
        delete $httpProvider.defaults.headers.common['X-Requested-With'];
    }
]);

sensorinoApp.config(['$routeProvider', function($routeProvider) {
        $routeProvider.
        when('/sensorinos', {
            templateUrl: 'partials/listSensorinos.html',
            controller: 'MainCtrl'
        }).
        when('/charts', {
            templateUrl: 'partials/charts.html',
            controller: 'GraphsCtrl'
        }).
        when('/sensorino/:sId', {
            templateUrl: 'partials/sensorinoDetails.html',
            controller: 'SensorinoDetailsCtrl'
        }).
        when('/sensorino/:sId/dataServices/:serviceId', {
            templateUrl: 'partials/serviceDataLog.html',
            controller: 'ServiceDataLogCtrl'
        }).
        when('/sensorino/:sId/actuatorServices/:serviceId', {
            templateUrl: 'partials/serviceDetails.html',
            controller: 'ServiceDetailsCtrl'
        }).
        otherwise({
            redirectTo: '/sensorinos'
        });
}]);



sensorinoApp.controller('MainCtrl', function($scope, Restangular) {
		Restangular.setBaseUrl("/")
		var Rsensorinos =  Restangular.all('sensorinos');

        $scope.showForm=false;
        $scope.activateForm = function(){
            $scope.showForm=true;
        }
         $scope.hideForm = function(){
            $scope.showForm=false;
        }
       

        $scope.loadSensorinos=function(){
            Rsensorinos.getList().then(function(sensorinos){
			    $scope.sensorinos=sensorinos;
            });
		}

        $scope.loadSensorinos();			

		$scope.deleteSensorino = function(sid){
			console.log("delete sid");
			console.log(sid);
            Restangular.one('sensorinos', sid).remove().then(function(){
                 $scope.loadSensorinos();
            });
		}

		$scope.createSensorino = function(mySensorino){
			console.log("create one then clean");
			Rsensorinos.post(mySensorino).then(function(){
                $scope.reset();
                $scope.loadSensorinos();
            });
		}


		$scope.reset = function(){ 
			console.log("clear stuff");
            $scope.showForm=false;
		}

        var m = new Mosquitto();
        m.onmessage = function(topic, payload, qos){
            var p = document.createElement("p");
            p.innerHTML = "topic:"+topic+" pl: "+payload;
            document.getElementById("debug").appendChild(p);

            //    window.alert("topic:"+topic+" pl: "+payload);
        };
        m.onconnect = function(rc){
            var p = document.createElement("p");
            p.innerHTML = "CONNACK " + rc;
            document.getElementById("debug").appendChild(p);
        };

        m.ondisconnect = function(rc){
            var p = document.createElement("p");
            p.innerHTML = "Lost connection";
            document.getElementById("debug").appendChild(p);
        };


//        m.connect("ws://91.121.149.19/mqtt");
 //       m.subscribe("discover", 0);

});

sensorinoApp.controller('SensorinoDetailsCtrl', function($scope, $location, $routeParams, Restangular) {

        $scope.showForm=false;
        $scope.activateForm = function(){
            $scope.showForm=true;
        }
        $scope.hideForm = function(){
            $scope.showForm=false;
        }


        Restangular.setBaseUrl("/")
        var Rsensorino =   Restangular.all('sensorinos');
        Rsensorino.get($routeParams.sId).then( function(sensorino){
            $scope.sensorino=sensorino;
        });

        var RServices=Restangular.all("sensorinos/"+$routeParams.sId+"/dataServices");
        $scope.loadServices=function(){
            RServices.getList().then(function(services){
                $scope.services=services;
            });
        }

        $scope.createService = function(newService){
            console.log("createService:");
            console.log(newService);
            RServices.post(newService).then(function(){
                $scope.loadServices();
                newService.name="";
                newService.dataType="";
                $scope.hideForm();
            });
        }

        $scope.deleteService = function(serviceId){
            console.log("delete service :");
            console.log(serviceId);
            var RService=Restangular.one("sensorinos/"+$routeParams.sId+"/dataServices/"+serviceId);
            RService.remove().then($scope.loadServices());
        }

        $scope.move=function(newPath){
            console.log("move to "+newPath)
            $location.path(newPath);
        }

        $scope.loadServices();

});


sensorinoApp.controller('ServiceDataLogCtrl',  function($scope, $routeParams, Restangular) {

    Restangular.setBaseUrl("/")
    var RServicesData=Restangular.all("sensorinos/"+$routeParams.sId+"/dataServices/"+$routeParams.serviceId+"/data");
    $scope.loadData=function(){
        RServicesData.getList().then(function(logs){
            $scope.logs=logs;
        });
    }
    $scope.loadData()
  
 
    var RService=Restangular.one("sensorinos/"+$routeParams.sId+"/dataServices/"+$routeParams.serviceId);
    $scope.loadService=function(){
        RService.get().then(function(service){
            $scope.service=service;
        });
    }
    $scope.loadService();

});

sensorinoApp.controller('ServiceDetailsCtrl',  function($scope, $routeParams, Restangular) {

    $scope.service= { type: "relay"};
    $scope.currentState = 'on';
    $scope.validStates = [ 'on', 'off', 'blink', "failed"];


});


sensorinoApp.controller('GraphsCtrl',  function($scope, $routeParams, Restangular) {

    // 'pie', 'bar', 'line', 'point', 'area'
    $scope.chartType = 'line';

    $scope.config = {
        labels: false,
        title : "Not Products",
        legend : {
            display:true,
            position:'left'
        }
    }

    $scope.data = {
        series: ['Sales', 'Income', 'Expense', 'Laptops', 'Keyboards'],
        data : [{
                    x : "Sales",
                    y: [100,500, 0],
                    tooltip:"this is tooltip"
                },
                {
                    x : "Not Sales",
                    y: [300, 100, 100]
                },
                {
                    x : "Tax",
                    y: [351]
                },
                {
                    x : "Not Tax",
                    y: [54, 0, 879]
                }]
    }


});


