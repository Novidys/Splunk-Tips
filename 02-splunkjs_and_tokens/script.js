$("#refreshButton").html($("<button class=\"btn btn-primary\">Refresh</button>").click(function() {
    kvstore_search.startSearch();
}))

$("#saveButton").css("display", "inline").html($("<button class=\"btn btn-primary\">Save comment</button>").click(function() {
    postNewEntry()
    $("[id^=key]").val('');
    $("[id^=comment]").attr('disabled','disabled');
    $("[id^=comment]").val('');
    kvstore_search.startSearch();
}))

function postNewEntry() {
    var record = [{
    	"_key": $("#key").val(),
    	"comment": $("#comment").val()
    }]
    $.ajax({
        url: '/en-US/splunkd/__raw/servicesNS/nobody/search/storage/collections/data/kvstore/batch_save',
        type: 'POST',
        contentType: "application/json",
        async: false,
        data: JSON.stringify(record),
        success: function(returneddata) { newkey = returneddata }
    })
}

function deleteEntry(mykey) {
    $.ajax({
        url: '/en-US/splunkd/__raw/servicesNS/nobody/search/storage/collections/data/kvstore/'+mykey,
        type: 'DELETE',
        contentType: "application/json",
        async: false
    })
}

require([
        "underscore",
        "splunkjs/mvc",
        "splunkjs/mvc/searchmanager",
        "splunkjs/mvc/savedsearchmanager",
        "splunkjs/mvc/tableview",
        "splunkjs/mvc/simplexml/ready!"
    ], function(_, mvc, SearchManager, SavedSearchManager, TableView) {
    
    var dashboard1 = splunkjs.mvc.Components.get("dashboard1");
    var view_name = dashboard1.options.model.view.associated.entry.attributes.name;
    
    //csv_search = new SavedSearchManager({
    //    id: "csv_search",
    //    autostart: false,
    //    searchname: view_name+"_basesearch"
    //}, {tokenNamespace: "submitted"});
  
    // get default token model
    var tokens = mvc.Components.getInstance("default");
    // build the list of tokens
    var k = tokens.keys();
    // parse the list to keep the form token
    form_tokens = _.filter(k, function(token){ return token.startsWith('form.'); });
    form_tokens.sort();

    // build the params list
    search_params = "";
    _(form_tokens).each(function(token) {
      search_params = search_params.concat(token+"=$"+token+"$ "); 
    });
  
    csv_search = new SearchManager({
      id: "csv_search",
      search: "| savedsearch "+view_name+"_basesearch "+search_params
    }, {tokens: true});
    
    kvstore_search = new SearchManager({
        id: "kvstore_search",
        autostart: false,
        search: "| inputcsv MetroComment.csv | lookup kvstore_comment _key AS cd1 OUTPUT comment | eval Update=\"Update\" | eval Delete=\"Delete\" | table cd1, username, function, comment, Update, Delete"
    });

    mytable = new TableView({
        id: "eviewer1",
        type: "list",
        managerid: "kvstore_search",
        drilldownRedirect: false,
        el: $("#mytable")
    }).render();

    csv_search.on("search:done", function() {
       kvstore_search.startSearch();
   });
});

require([
    "splunkjs/mvc",
    "splunkjs/mvc/simplexml/ready!"
], function(mvc) {
  
  mytable.on("click", function(e) {
        e.preventDefault();
    	console.log(e);
        value = e.data['click.value2'];
	key = e.data['row.cd1'];
        comment = e.data['row.comment'];
	if (value == 'Update') {
            $("[id^=key]").val(key);
            $("[id^=comment]").val(comment);
            $("[id^=comment]").attr('disabled',false);
        }
	else if (value == 'Delete') {
            $("[id^=key]").val('');
            $("[id^=comment]").val('');
            $("[id^=comment]").attr('disabled','disabled');
            deleteEntry(key);
            kvstore_search.startSearch();
        }
        console.log("Clicked the table:", e.data);
    });
});

require(["jquery", "splunkjs/mvc/simplexml/ready!"], function($) {
    $("[id^=key]").attr('disabled','disabled');
    $("[id^=comment]").attr('disabled','disabled');
});
