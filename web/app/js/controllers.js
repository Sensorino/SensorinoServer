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
        when('/sensorino/:sId/services/:serviceId', {
            templateUrl: 'partials/serviceDataLog.html',
            controller: 'ServiceDataLogCtrl'
        }).
        when('/sensorino/:sId/services/:serviceId/channels/:channelId/charts', {
            templateUrl: 'partials/serviceCanalCharts.html',
            controller: 'ServiceCanalChartsCtrl'
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

        var RServices=Restangular.all("sensorinos/"+$routeParams.sId+"/services");
        $scope.loadServices=function(){
            RServices.getList().then(function(services){
                $scope.services=services;
                if (services.length>0){
                    $scope.selectedService=services[0];
                }
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
            var RService=Restangular.one("sensorinos/"+$routeParams.sId+"/services/"+serviceId);
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
    var RServicesData=Restangular.all("sensorinos/"+$routeParams.sId+"/services/"+$routeParams.serviceId+"/data");
    $scope.loadData=function(){
        RServicesData.getList().then(function(logs){
            $scope.logs=logs;
        });
    }
    $scope.loadData()
  
 
    var RService=Restangular.one("sensorinos/"+$routeParams.sId+"/services/"+$routeParams.serviceId);
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


sensorinoApp.controller('SalesController',  function($scope, $routeParams, $compile, Restangular) {

    Restangular.setBaseUrl("/");
    $scope.graphData=[];
//    var RServicesData=Restangular.all("sensorinos/"+$routeParams.sId+"/services/"+$routeParams.serviceId+"/channels/"+$routeParams.channelId+"/data");
    var RServicesData=Restangular.all("sensorinos/10/services/3/channels/1/data");
    $scope.loadData=function(){
            RServicesData.getList().then(function(logs){
                $scope.graphData=logs;
        console.log("got data");
        var template='<div linear-chart chart-data="graphData"></div>'
        angular.element(document.body).append($compile(template)($scope));


            });
        }
        $scope.loadData()
});


// http://bl.ocks.org/marufbd/7191340 has a nice d3 irregular chart stuff that we could use

            sensorinoApp.directive('linearChart', function($window){
               return{
                  restrict:'EA',
                  template:"<svg width='850' height='400'></svg>",
                   link: function(scope, elem, attrs){
                       var graphDataToPlot=scope[attrs.chartData];
                       var padding = 60;
                       var pathClass="path";
                       var xScale, yScale, xAxisGen, yAxisGen, lineFun;

                       var d3 = $window.d3;
                       var rawSvg=elem.find('svg');
                       var svg = d3.select(rawSvg[0]);

                       function setChartParameters(){

                           xScale = d3.time.scale()
                               .domain([new Date(graphDataToPlot[0].timestamp.replace(" ","T")), new Date(graphDataToPlot[graphDataToPlot.length-1].timestamp.replace(" ","T"))])
                               .range([0, 850-padding]);
                    

                           yScale = d3.scale.linear()
                               .domain([0, d3.max(graphDataToPlot, function (d) {
                                   return d.value.Speed;
                               })])
                               .range([ 340, 60]);
                            


                           xAxisGen = d3.svg.axis()
                               .scale(xScale)
                               .orient("bottom")
            //                   .ticks(d3.time.hours, 2)
                               .tickSize(10)
                               .tickFormat(d3.time.format('%b %d %H:%M:%S'))
                               .tickPadding(8);

                           yAxisGen = d3.svg.axis()
                               .scale(yScale)
                               .orient("left")
                                .tickSize(0)
                               .ticks(10)
                               .tickPadding(8);


                           lineFun = d3.svg.line()
                               .x(function (d) {
                                    console.log(d.timestamp);
                                   return xScale(new Date(d.timestamp.replace(" ","T")));
                               })
                               .y(function (d) {
                                    console.log(d.value);
                                   return yScale(d.value.Speed);
                               })
                               .interpolate("basis");


                       }


                    
                     function drawLineChart() {

                           setChartParameters();

                           svg.append("svg:g")
                               .attr("class", "x axis")
                               .attr("transform", "translate(60,340)")
                               .call(xAxisGen);

                           svg.append("svg:g")
                               .attr("class", "y axis")
                               .attr("transform", "translate(60,0)")
                               .call(yAxisGen);

                           svg.append("svg:path")
                               .attr({
                                   d: lineFun(graphDataToPlot),
                                   "stroke": "blue",
                                   "stroke-width": 2,
                                   "fill": "none",
                                   "class": pathClass
                               })
                              .attr("transform", "translate(60,0)");
                       }

                       drawLineChart();
                   }
               }});



