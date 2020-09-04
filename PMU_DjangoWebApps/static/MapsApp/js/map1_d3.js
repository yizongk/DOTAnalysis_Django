// const DUMMY_DATA = [
//     { id: 'id1', values: 2, region: 'USA'},
//     { id: 'id2', values: 5, region: 'China'},
//     { id: 'id3', values: 1, region: 'Canada'},
//     { id: 'id4', values: 10, region: 'Mexico'},
// ];

// // d3.select('#map_container')
// //     .selectAll('p')
// //     .data(DUMMY_DATA)    // Bind [1, 2, 3] to the <p>
// //     .enter()            // Find what's missing
// //     .append('p')        // Bind the missing one with a new <p>
// //     .text(dta => dta.region);

// const map_container = d3.select('#map_container')
//     .classed('container', true)
//     .style('border', '1px solid red');

// map_container.selectAll('.bar')
//     .data(DUMMY_DATA)
//     .enter()
//     .append('div')
//     .classed('bar', true)
//     .style('width', '50px')
//     .style('height', data => (data.values * 15) + 'px');


// // dimensions
// var w = 2000;
// var h = 2000;

// console.log(d3)

// var svg = d3.select("#map_container")
//     .append("svg")
//     .attr("width", w)
//     .attr("height", h);

// // create geo.path object, set the projection to merator bring it to the svg-viewport
// var projection = d3.geo.path().mercator()
//     // .scale(20000)
//     // .translate([0, 3800])
// var path = d3.geo.path()
//     .projection(projection);

// // console.log(path)

// d3.json(
//     "https://127.0.0.1:8033/static/MapsApp/geojsons/vzv_bike_priority_districts.geojson",

//     function(err, geojson) {
        
//         // draw svg lines of the boundries
//         svg.append("g")
//                 // .attr("class", "black")
//                 .selectAll("path")
//                 .data(geojson.features)
//                 .enter()
//                 .append("path")
//                 .attr("d", path(geojson));
//     }
// );


$(document).ready(function () {
    function createMap(geoJson) {
        // Place your mapping stuff here

        var projection = d3.geoEquirectangular();

        var geoGenerator = d3.geoPath()
            .projection(projection);

        // console.log(geoJson);
        // // console.log(typeof(geoJson));
        // // console.log(geoJson.type);
        // // console.log(geoJson['type']);
        // console.log(geoJson["features"][0]);
        // console.log(geoGenerator(geoJson["features"][0]));

        // Join the FeatureCollection's features array to path elements
        var svg = d3.select('#map_container')
            .selectAll('path')
            .data(geoJson.features);

        svg.enter()
            .append('path')
            .attr('d', geoGenerator)

    };

    // fetch('/static/MapsApp/geojsons/vzv_bike_priority_districts.geojson')
    // fetch('/static/MapsApp/geojsons/nyc.geojson')
    //     .then(response => response.text())
    //     .then(data => {
    //          var geoJson = JSON.parse(data);
    //         
    //     });

    d3.json('/static/MapsApp/geojsons/nyc.geojson', function(err, json) {
        console.log(json);
        createMap(json);
    })
});