var express = require('express');
var router = express.Router();
var csv = require('fast-csv');
var fs = require('fs');
var yacsv = require('ya-csv');
var exec = require('child_process').exec;
var cmd = 'python forwarder.py';
require('shelljs/global');

/* GET home page. */
router.get('/', function (req, res) {
  
    var stream = fs.createReadStream("entries.csv");
    var entries = [];
    
    var csvStream = csv()
      .on("data", function(data){
          //console.log(data);
          entries.push(data);
      })
      .on("end", function(data){
          console.log(entries);
          
          res.render('index', { title: 'Port Forwarder', entries: JSON.stringify(entries) });
      });
    
    stream.pipe(csvStream);
    
    exec("python forwarder.py", function(error, stdout, stderr) {
       console.log(stdout);
    });
});

router.post('/addEntry', function (req, res) {
    
    var writableStream = fs.createWriteStream("entries.csv", {'flags':'a'});
    
   var csvStream = yacsv.createCsvStreamWriter(writableStream);

    csvStream.writeRecord( [req.body.name, req.body.sourcePort, req.body.destinationIP, req.body.destinationPort]);

    console.log(req.body);
    res.send(req.body);
    
     csvStream.on("finish", function(){
      console.log("DONE!");
	
	    exec("killall python", function (error, stdout, stderr) {
		    exec("python forwarder.py", function(error, stdout, stderr) {
		       console.log(stdout);
		    });
	    });
    });

     
});


router.post('/deleteEntry', function (req, res) {
   
   var entries = JSON.parse(req.body.entries);
   
   var csvStream = csv.createWriteStream({headers: true}),
    writableStream = fs.createWriteStream("entries.csv");
 
    writableStream.on("finish", function(){
      console.log("DONE!");
	
	    exec("killall python", function (error, stdout, stderr) {
		    exec("python forwarder.py", function(error, stdout, stderr) {
		       console.log(stdout);
		    });
	    });
    });
    
    
    csvStream.pipe(writableStream);
    for (var i = 0; i < entries.length; i++) {
      
      csvStream.write(entries[i]);
    }
    csvStream.end();
   
});

module.exports = router;
