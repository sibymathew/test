window.onload = function() {
    console.log( "ready!" );
    disableRequiredModulesCheckboxes();
    installHandlerForAAChkbox();
    installHandlerForSSLEnableChkbox();
    installHandlerForServiceStartButton();
    installHandlerForStatusRefreshButton();
    installHandlerForModuleActionButtons();
    installHandlerForConfigUpdateButton();

    if (window.location.pathname == '/manage'){
        $('.status-refresh-button').click();
    }
}

function disableRequiredModulesCheckboxes(){

    $("#modules-msg").hide();
    $('.field.required-on input').prop("checked",true).prop("disabled",true);
    $('.field.required-off input').prop("checked",false).prop("disabled",true);

    $('.field.required-on, .field.required-off').click(function(){
        console.log("disabled default selection clicked")
        $("#modules-msg").html("Can not change default selection for this option")
        $("#modules-msg").show().delay(1500).fadeOut();
    });
}
function installHandlerForAAChkbox(){
    $('.field.upon-aa-module').hide()
    $('.field.aa-module').click(function(ev){
        // console.log($('.field.aa-module input').checked());
        if ($('.field.aa-module input').is(":checked")){
            $('.field.upon-aa-module').show();
        }else{
            $('.field.upon-aa-module').hide();
        }
    });
}
function installHandlerForSSLEnableChkbox(){
    $('.field.upon-ssl-enable').hide()
    $('.field.ssl-enable').click(function(ev){
        // console.log($('.field.aa-module input').checked());
        if ($('.field.ssl-enable input').is(":checked")){
            $('.field.upon-ssl-enable').show();
        }else{
            $('.field.upon-ssl-enable').hide();
        }
    });
}
function installHandlerForServiceStartButton(){
    $('#start-service').click(function(){
        // get all values from check boxes.
        var modulesList = Array.map($('.modules-form input'), function(ele,i){
            if ($(ele).prop('checked')){
                return $(ele).attr('name');
            }else{
                return ""
            }
        }).filter(function(ele,i){
            return ele != "";
        });

        // get relevant values from configurations.
        var configurations = Array.map($('.config-field input, .config-field select'),function(ele,i){

            if ($(ele).is('select') || $(ele).attr('type') == 'text' ||
                $(ele).attr('type') == 'password' ){
                return [$(ele).attr('name'),$(ele).val()];
            }else if ($(ele).attr('type') == 'checkbox'){
                return [$(ele).attr('name'),$(ele).prop('checked')];
            }else if ($(ele).attr('type') == 'radio' && $(ele).prop('checked')){
                return [$(ele).attr('name'),$(ele).val()];
            }
        })
        .reduce(function (acc,val){
            if (val === undefined){
                return acc;
            }
            acc[val[0]]=val[1];
            return acc;
        },{});
        
        var postData = {
            "modules_list":modulesList,
            "configurations":configurations
        };

        $.ajax({
            url: "service/start",
            type: "post",
            headers:{
                'Content-Type':'application/json'
            },
            data: JSON.stringify(postData),
            dataType:'json',
            success: function (response) {
                console.log('successful start service');
                window.location.href = '/manage';

            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            }
        });
    });
}
function installHandlerForStatusRefreshButton(){
    $('.status-refresh-button').click(function(ev){
        $('a.status-refresh-button').addClass('is-loading');
        $.ajax({
            url: "service/status",
            type: "get",
            headers:{
                'Content-Type':'application/json'
            },
            success: function (response) {
                var res = JSON.parse(response);

                Array.map(res.modules,function(ele,i,arr){
                    var trChildren = $('tbody.modules-table tr[sname='+ele.sname+']')
                    .children();

                    // change the status text
                    $(trChildren[1]).html(ele.status);
                    // show all the buttons 
                    $(trChildren[2]).children().removeClass('is-hidden');
                    //and hide the unnecessary ones.
                    if (ele.status == 'absent'){
                        $(trChildren[2]).children().addClass('is-hidden');
                    }else if (ele.status == 'stopped' || ele.status == 'completed'){
                        $(trChildren[2]).find('.module-stop-button').addClass('is-hidden');
                        $(trChildren[2]).find('.module-restart-button').addClass('is-hidden');
                    }else if (ele.status == 'running'){
                        $(trChildren[2]).find('.module-start-button').addClass('is-hidden');
                    }else if (ele.status == 'starting' || ele.status == 'stopping'){
                        $(trChildren[2]).find('.module-start-button').addClass('is-hidden');
                        $(trChildren[2]).find('.module-stop-button').addClass('is-hidden');
                        $(trChildren[2]).find('.module-restart-button').addClass('is-hidden');
                    }

                });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            },
            complete: function(xmlHttpReq,successType){
                $('a.status-refresh-button').removeClass('is-loading');
            }
        });

    });
}
function installHandlerForModuleActionButtons(){
    
    $('.module-stop-button').click(function(ev){

        $.ajax({
            url: "module/stop",
            type: "post",
            headers:{
                'Content-Type':'application/json'
            },
            data: JSON.stringify({
                "process":$(ev.target).closest('tr').attr('sname')
            }),
            dataType:'json',
            success: function (response) {
                $('.status-refresh-button').click();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            }
        });
    });

    $('.module-start-button').click(function(ev){

        $.ajax({
            url: "module/start",
            type: "post",
            headers:{
                'Content-Type':'application/json'
            },
            data: JSON.stringify({
                "process":$(ev.target).closest('tr').attr('sname')
            }),
            dataType:'json',
            success: function (response) {
                $('.status-refresh-button').click();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            }
        });
    });

    $('.module-restart-button').click(function(ev){
        $.ajax({
            url: "module/restart",
            type: "post",
            headers:{
                'Content-Type':'application/json'
            },
            data: JSON.stringify({
                "process":$(ev.target).closest('tr').attr('sname')
            }),
            dataType:'json',
            success: function (response) {
                $('.status-refresh-button').click();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            }
        });
    });
}
function installHandlerForConfigUpdateButton(){
    $('.update-config-button').click(function(){
        // get relevant values from configurations.
        var configurations = Array.map($('.config-field input, .config-field select'),function(ele,i){

            if ($(ele).is('select') || $(ele).attr('type') == 'text' ||
                $(ele).attr('type') == 'password' ){
                return [$(ele).attr('name'),$(ele).val()];
            }else if ($(ele).attr('type') == 'checkbox'){
                return [$(ele).attr('name'),$(ele).prop('checked')];
            }else if ($(ele).attr('type') == 'radio' && $(ele).prop('checked')){
                return [$(ele).attr('name'),$(ele).val()];
            }
        })
        .reduce(function (acc,val){
            if (val === undefined){
                return acc;
            }
            acc[val[0]]=val[1];
            return acc;
        },{});

        var postData = {
            'configurations': configurations
        }

        $.ajax({
            url: "service/start",
            type: "patch",
            headers:{
                'Content-Type':'application/json'
            },
            data: JSON.stringify(postData),
            dataType:'json',
            success: function (response) {
                console.log('successful start service');
                window.location.href = '/manage';
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            }
        });

    });
}