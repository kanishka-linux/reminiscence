

$('.dropdown-menu span').click(function(){dropdown_menu_clicked(this)});

function dropdown_menu_clicked(element){
    var link = $(element).attr('data-val');
    console.log(link);
    if (link == 'url'){
        var title = $(element).attr('title');
        var t_val = $(element).attr('data-val');
        var nlink = $(element).attr('data-link');
        var csrftoken = getCookie('csrftoken');
        var post_data = "";
        var el = $(element).closest("tr");
        var al = el.find('a').eq(0);
        var footer_al = el.find('a').eq(1);
        var badges = el.find('.badges').find('.badge');
        var badge_str = '';
        var move_bookmark = false;
        var msg = null;
        badges.each(function(index){
            if(badge_str){
                badge_str = badge_str + ','+ $(this).text().trim();
            }else{
                badge_str = $(this).text().trim();
            }
            console.log(badge_str, index);
            });
        console.log(nlink, title, t_val);
        if(nlink.endsWith('remove') || nlink.endsWith('edit-bookmark') || nlink.endsWith('move-bookmark')){
            if (nlink.endsWith('edit-bookmark')){
                var url_value = al.attr('href');
                var title_value = al.text();
                var post_url = 'new_url=';
                var post_title = 'new_title=';
                var mel = el.find('.dropdown-item[data-val=url_media_public]');
                if(mel.length){
                    var media_element = 'checked';
                }else{
                    var media_element = '';
                }
                console.log(mel, mel.length);
                msg = getstr(title_value, url_value, badge_str, media_element);
                post_data = null;
            }else if (nlink.endsWith('move-bookmark')){
                post_data = 'listdir=yes';
                var api_link = $(element).attr('data-url');
                msg = '';
                move_bookmark = true;
            }else{
                var msg = `</html>Are you sure, you want to delete,  <b>${title}</b>? This is irreversible and will also delete associated archived file</html>`;
                var title_value = null;
                var post_var = 'remove_url=';
                post_data = 'remove_url=yes';
            }
            if (msg != '' && msg != null && !move_bookmark){
                var resp = bootbox.confirm(msg, function(resp){
                    console.log(resp);
                    if (resp && !move_bookmark){
                        if (post_data == null){
                            var info = $('#infos');
                            var ititle = info.find('input[name=title]').val();
                            if (ititle != info.find('input[name=title]').attr('value')){
                                al.text(ititle);
                                ititle = encodeURIComponent(ititle);
                                post_data = `new_title=${ititle}`;
                            }
                            var iurl = info.find('input[name=url]').val();
                            if (iurl != info.find('input[name=url]').attr('value')){
                                al.attr('href', iurl);
                                footer_al.attr('href', iurl);
                                iurl = encodeURIComponent(iurl);
                                post_data = post_data + `&new_url=${iurl}`;
                            }
                            var itag = info.find('input[name=tags]').val();
                            if (itag != badge_str){
                                clear_and_apply_badges(el, itag.split(','), badge_str);
                                itag = encodeURIComponent(itag);
                                badge_str = encodeURIComponent(badge_str);
                                post_data = post_data + `&new_tags=${itag}&old_tags=${badge_str}`;
                            }
                            var media_link = $('#media-element-check').is(':checked');
                            post_data = post_data + `&media_link=${media_link}`;
                            console.log(post_data);
                        }else{
                            el.remove();
                        }
                        if(post_data != null && post_data != ""){
                            var client = new postRequest();
                            client.post(nlink, post_data, csrftoken, function(response) {
                                console.log(response);
                                window.location.reload();
                            })
                        }
                    }
                })
            }else if(move_bookmark){
                move_to_bookmark(post_data, api_link, nlink, csrftoken, el, '', false);
            }
        }
    }else if(link == 'url_read'){
        var nlink = $(element).attr('data-link');
        window.location.href = nlink;
    }else if (link == 'import-settings'){
        var nlink = $(element).attr('api-url');
        var csrftoken = getCookie('csrftoken');
        var html = create_upload_field(nlink, 'import');
        var resp = bootbox.confirm(html, function(resp){
            if(resp){
                var file = document.getElementById('upload-file-field').files[0];
                var formdata = new FormData();
                formdata.append('import-bookmark', 'yes');
                formdata.append('file-upload', file);
                var dialog = bootbox.dialog({message:'<p class="text-center">Please Wait..</p>', closebutton:false});
                var client = new postRequestUpload();
                client.post(nlink, formdata, csrftoken, function(response) {
                    console.log(response);
                    dialog.find('.bootbox-body').html(`<p class="text-center">OK, ${file.name} file uploaded.\
                                                       You can close the dialog, if it is not auto-closed!`);
                    setTimeout(function(){dialog.modal('hide')}, 1000);
                })
                
            }
        })
    }else if(link == 'upload-settings'){
        var nlink = $(element).attr('api-url');
        var dirname = $('.breadcrumb-item').find('a').eq(1).text().trim();
        console.log(dirname)
        var csrftoken = getCookie('csrftoken');
        var html = create_upload_field(nlink, 'upload');
        var resp = bootbox.confirm(html, function(resp){
            if(resp){
                var file = document.getElementById('upload-file-field');
                var formdata = new FormData();
                formdata.append('upload-binary', 'yes');
                formdata.append('dirname', dirname);
                var index = 0;
                for(var x =0 ; x < file.files.length; x++){
                    formdata.append(`file-upload-${index}`, file.files[x]);
                    console.log(file.files[x].name);
                    index += 1;
                }
                var dialog = bootbox.dialog({message:'<p class="text-center">Please Wait..</p>', closebutton:false});
                var client = new postRequestUpload();
                client.post(nlink, formdata, csrftoken, function(response) {
                    console.log(response);
                    dialog.find('.bootbox-body').html(`<p class="text-center">OK, ${file.name} file uploaded.\
                                                       You can close the dialog, if it is not auto-closed!`);
                    setTimeout(function(){dialog.modal('hide')}, 1000);
                })
                
            }
        })
    }else if(link == 'settings'){ 
        var nlink = $(element).attr('api-url');
        var csrftoken = getCookie('csrftoken');
        var client = new postRequest();
        console.log(nlink);
        client.post(nlink, 'get_settings=yes', csrftoken, function(response) {
            console.log(response);
            var json = JSON.parse(response);
            var autotag = json['autotag'];
            if (autotag){
                autotag = 'checked';
            }else{
                autotag = '';
            }
            var auto_summary = json['auto_summary'];
            if (auto_summary){
                auto_summary = 'checked';
            }else{
                auto_summary = '';
            }
            var media_streaming = json['media_streaming'];
            if (media_streaming){
                media_streaming = 'checked';
            }else{
                media_streaming = '';
            }
            var save_pdf = json['save_pdf'];
            if (save_pdf){
                save_pdf = 'checked';
            }else{
                save_pdf = '';
            }
            var save_png = json['save_png'];
            if (save_png){
                save_png = 'checked';
            }else{
                save_png = '';
            }
            var auto_archive = json['auto_archive'];
            if (auto_archive){
                auto_archive = 'checked';
            }else{
                auto_archive = '';
            }
            var png_quality = json['png_quality'];
            var total_tags = json['total_tags'];
            var buddy_list = json['buddy'];
            var public_dir = json['public_dir'];
            var group_dir = json['group_dir'];
            var pagination_value = json['pagination_value'];
            
            var download_manager = json['download_manager'];
            var msg = getsettings_html(autotag, auto_summary, total_tags,
                                       buddy_list, public_dir, group_dir,
                                       save_pdf, save_png, png_quality,
                                       auto_archive, pagination_value,
                                       media_streaming, download_manager);
            console.log(autotag, auto_summary, total_tags, buddy_list);
            var resp = bootbox.confirm(msg, function(resp){
                if (resp){
                    console.log(resp);
                    var autotag = $('#autotag').is(':checked');
                    var auto_summary = $('#auto_summary').is(':checked');
                    var auto_archive = $('#auto_archive').is(':checked');
                    var save_pdf = $('#arch-pdf').is(':checked');
                    var save_png = $('#arch-png').is(':checked');
                    var media_streaming = $('#media-streaming').is(':checked');
                    console.log(autotag, auto_summary);
                    var total_tags = $('#total_tags').val();
                    var buddy_list = $('#buddy_list').val();
                    var public_dir = $('#public_dir').val();
                    var group_dir = $('#group_dir').val();
                    var png_quality = $('#arch-png-quality').val();
                    var pagination_value = $('#pagination-value').val();
                    var download_manager = $('#download-manager').val();
                    if(buddy_list == null){
                        buddy_list = "";
                    }
                    if (public_dir == null){
                        public_dir = "";
                    }
                    if (group_dir == null){
                        group_dir = "";
                    }
                    var post_data = `set_settings=yes&autotag=${autotag}&auto_summary=${auto_summary}&total_tags=${total_tags}`;
                    post_data = post_data + `&buddy_list=${buddy_list}&public_dir=${public_dir}&group_dir=${group_dir}`;
                    post_data = post_data + `&save_pdf=${save_pdf}&save_png=${save_png}&png_quality=${png_quality}`;
                    post_data = post_data + `&auto_archive=${auto_archive}&pagination_value=${pagination_value}`;
                    post_data = post_data + `&media_streaming=${media_streaming}&download_manager=${download_manager}`;
                    console.log(total_tags, buddy_list, post_data);
                    var client = new postRequest();
                    client.post(nlink, post_data, csrftoken, function(response) {
                        console.log(response);
                    })
                }
            })
            
        })
    }else if(link == 'url_summary'){
        var nlink = $(element).attr('data-link');
        var csrftoken = getCookie('csrftoken');
        var api_link = $(element).attr('data-url');
        var url_id = nlink.split('/').reverse()[1];
        post_data = `req_summary=yes&url_id=${url_id}`;
        console.log(post_data);
        var client = new postRequest();
        client.post(
                    api_link,
                    post_data,
                    csrftoken,
                    function(response) {
                        var json = JSON.parse(response);
                        var summary = json['summary'];
                        var summary_str = getsummary(summary);
                        var resp = bootbox.confirm(summary_str, function(resp){
                            if(resp){
                                var newsum = $('#summary-text').val().trim();
                                if(summary != newsum){
                                    console.log(newsum);
                                    var formdata = new FormData;
                                    formdata.append('req_summary', 'modify');
                                    formdata.append('url_id', url_id);
                                    formdata.append('modified_summary', newsum)
                                    var client = new postRequestUpload();
                                    client.post(api_link, formdata, csrftoken, function(response) {
                                        console.log(response);
                                    })
                                    
                                }
                            }
                        })
                    })
    }else if(link == 'select-multiple' || link == 'select-all'){
        var el = $('#tbody').find('tr td:first-child');
        var checked = '';
        if(link == 'select-all'){
            checked = 'checked';
        }
        el.each(function(index){
            var idd = $(this).nextAll().eq(1).find('footer').attr('link-id');
            var folder_ico = $(this).find('img').attr('src');
            html = `<div class="form-check">
            <input class="form-check-input" type="checkbox" value="check-box" id="multiple-select-box" check-id="${idd}" ${checked}>
            </div>`
            var fm = $(this).find('input');
            if(fm.length){
                if (checked == 'checked'){
                    fm.prop('checked', true);
                }else{
                    fm.prop('checked', false);
                }
            }else{
                if (folder_ico && folder_ico.includes('/folder.svg')){
                    console.log("subfolder: excluding");
                }else{
                    $(this).append(html);
                }
            }
        })
    }else if(link == 'move-multiple' || link == 'merge-bookmark-with'){
        var [elpar, elar_join] = get_selected_items();
        post_data = 'listdir=yes';
        var api_link = $(element).attr('api-url');
        var nlink = $(element).attr('data-link');
        var csrftoken = getCookie('csrftoken');
        console.log(api_link, nlink, post_data);
        if(link == 'move-multiple'){
            var merge = false;
        }else{
            var merge = true;
        }
        move_to_bookmark(post_data, api_link, nlink, csrftoken, elpar, elar_join, merge);
    }else if(link == 'create-subdir'){
        var api_link = $(element).attr('api-url');
        var dirname = $(element).attr('data-dir');
        var csrftoken = getCookie('csrftoken');
        console.log(api_link, dirname);
        var subdir = prompt("Enter Sub-Directory", "");
        if (subdir == null || subdir == "") {
          txt = "User cancelled the prompt.";
        } else {
          post_data = `create_subdir=yes&parent_dir=${dirname}&subdir_name=${subdir}`;
          var client = new postRequest();
            client.post(api_link, post_data, csrftoken, function(response) {
            console.log(response);
            window.location.reload();
            })
        } 
    }else if(link == 'archive-bookmark-multiple'){
        var [elpar, elar_join] = get_selected_items();
        post_data = `link_ids=${elar_join}`;
        var api_link = $(element).attr('api-url');
        var nlink = $(element).attr('data-link');
        var csrftoken = getCookie('csrftoken');
        console.log(api_link, nlink, post_data);
        var msg = 'This option will try to archive content of multiple selected entries. It will also overwrite existing archived content. Are You Sure?';
        var resp = bootbox.confirm(msg, function(resp){
                if(resp){
                    var client = new postRequest();
                    client.post(nlink, post_data, csrftoken, function(response) {
                    console.log(response);
                    })
                }else{
                    console.log('cancelled');
                }
            })
    }else if(link == 'chromium_pdf' || link == 'chromium_dom'){
        var api_link = $(element).attr('data-url');
        var csrftoken = getCookie('csrftoken');
        var url_id = $(element).attr('link-id');
        var post_data = `chromium-backend=yes&url_id=${url_id}`;
        if (link == 'chromium_pdf'){
            mode = 'pdf';
        }else{
            mode = 'dom';
        }
        post_data = post_data + `&mode=${mode}`
        var client = new postRequest();
        console.log(post_data)
        client.post(api_link, post_data, csrftoken, function(response) {
            console.log(response);
        })
    }else if(link == 'generate-media-playlist'){
        var api_link = $(element).attr('api-url');
        var csrftoken = getCookie('csrftoken');
        var data_link = $(element).attr('data-link');
        var directory = $(element).attr('data-dir');
        var server_url = window.location.protocol + '//' + window.location.hostname;
        if(window.location.port){
            server_url = server_url + ':' + window.location.port;
        }
        var post_data = `generate-media-playlist=yes&directory=${directory}&ip=${server_url}`;
        var client = new postRequest();
        console.log(post_data)
        client.post(api_link, post_data, csrftoken, function(response) {
            console.log(response);
            window.location = response;
        })
    }else if(link == 'url_media_public' ){
        var api_link = $(element).attr('data-url');
        var csrftoken = getCookie('csrftoken');
        var url_id = $(element).attr('link-id');
        var post_data = `get-media-path=yes&url_id=${url_id}`;
        var client = new postRequest();
        console.log(post_data)
        client.post(api_link, post_data, csrftoken, function(response) {
            console.log(response);
            var json = JSON.parse(response);
            var nurl = json['link'];
            var final_url = window.location.protocol + '//' + window.location.hostname;
            if(window.location.port){
                final_url = final_url + ':' + window.location.port;
            }
            final_url = final_url + '/' + nurl;
            console.log(final_url);
            bootbox.alert(getsummary(final_url));
        })
        
    }else if(link == 'edit-tags-multiple'){
        var [elpar, elar_join] = get_selected_items();
        post_data = `link_ids=${elar_join}`;
        var api_link = $(element).attr('api-url');
        var nlink = $(element).attr('data-link');
        var csrftoken = getCookie('csrftoken');
        console.log(api_link, nlink, post_data);
        var str = `<form id='infos-tag' novalidate>\
        <div class="form-group row">
            <label class="col-sm-2 col-form-label" for="tagid-multiple"><b>Tags</b></label>
            <div class="col-sm-10">
                <input id='tagid-multiple' type='text' name='tags' value=''\
                 class="form-control" placeholder="Edit Tags of Multiple Entries"/>
            </div>
        </div>
        <div class="dropdown-divider"></div>
        <div class="form-group row">
            <label class="col-sm-12 col-form-label"><b>This option will clear\
             existing tags of selected entries and will apply new tags. So use with care.\
             Refresh the page after tags are applied.</b></label>
        </div>
        </form>`;
        var resp = bootbox.confirm(str, function(resp){
                if(resp && elar_join){
                   console.log('yes');
                   var tags = $('#tagid-multiple').val();
                   if(tags){
                        console.log('--', tags, '--');
                        var formdata = new FormData;
                        formdata.append('link_ids', elar_join);
                        formdata.append('link_tags', tags);
                        var client = new postRequestUpload();
                        client.post(nlink, formdata, csrftoken, function(response) {
                            console.log(response);
                        })
                   }else{
                       console.log('Empty tag not allowed for multiple entries');
                   }
                }else{
                    console.log('cancelled', elar_join, '--');
                }
            })
    }else if(link == 'url_archive'){
        var nlink = $(element).attr('data-link');
        console.log(nlink)
        var csrftoken = getCookie('csrftoken');
        var post_data = "";
        var el = $(element).closest("tr");
        var al = el.find('a').eq(0);
        var footer_al = el.find('#netloc-muted');
        var dirname = $(element).attr('dir-name');
        var idlink = $(element).attr('find-id');
        var api_link = $(element).attr('data-url');
        var url_id = idlink.split('/').reverse()[1];
        post_data = `archive=force&dirname=${dirname}&url_id=${url_id}`;
        console.log(post_data);
        console.log(idlink);
        console.log(nlink, footer_al.attr('href'));
        if (nlink == footer_al.attr('href')){
            var client = new postRequest();
            client.post(
                    api_link,
                    post_data,
                    csrftoken,
                    function(response) {
                        console.log(response);
                        var json = JSON.parse(response);
                        var nurl = json['url'];
                        al.attr('href', nurl);
                        $(element).attr('data-link', nurl);
                        html = `<span> | </span><small><span class="badge\
                                badge-success">OK</span></small>`;
                        al.append(html)
                    })
        }else{
            msg = "</htm>URL Already Archived. Do you want to overwrite existing file?<html>";
            var resp = bootbox.confirm(msg, function(resp){
                console.log(resp);
                if (resp){
                    var client = new postRequest();
                    client.post(
                        api_link, 
                        post_data,
                        csrftoken,
                        function(response) {
                            console.log(response);
                            html = `<span> | </span><small><span class="badge\
                                    badge-success">OK</span></small>`;
                            al.append(html)
                        })
                }
            })
        }
    }
}

function get_selected_items(){
    var el = $('#tbody').find('tr td:first-child');
    var elar = [];
    var elpar = [];
    el.each(function(index){
        var elmid = $(this).find('#multiple-select-box:checked');
        if (elmid.length){
            elar.push(elmid.attr('check-id'));
            elpar.push($(this).parent());
        }
    })
    var elar_join = elar.join();
    console.log(elar_join);
    return [elpar, elar_join];
}

function clear_and_apply_badges(el, newtaglist, oldtaglist){
    if (oldtaglist != ''){
        var badges = el.find('.badges').find('.badge');
        var badge = badges.eq(0);
        var href = badge.attr('href');
        var usr = href.split('/')[1];
        badges.each(function(index){
            $(this).remove();
        })
        var badge_html = create_badge_nodes(usr, newtaglist, 'nodiv', '');
        el.find('.badges').append(badge_html);
    }else{
        var td = el.find('td').eq(1);
        var badge_html = create_badge_nodes(usr, newtaglist, 'div', '');
        td.append(badge_html);
    }
}


function enter_directory(id){
    var nid = `#${id}`;
    var elm = document.getElementById(id);
    console.log(elm.innerHTML);
    var nlink = elm.getAttribute('api-link');
    var loc = elm.getAttribute('data-link');
    var search = elm.getAttribute('dir-name');
    search = 'dir:'+ search;
    //generate_table_body(nlink, search, 'dir');
    console.log(nlink, search);
    window.location.href = loc;
}

function search_entered_input(event, code){
    var elm = document.getElementById("search-box-top");
    var search = elm.value;
    if(event.keyCode == 13 && search.length > 2){
        search_entered(event, code);
    }
}

function search_entered(event, code){
    var elm = document.getElementById("search-box-top");
    var search = elm.value;
    var nlink = elm.getAttribute("api-url");
    console.log(nlink, search);
    elm.value = "";
    $('#search-box-top').blur();
    generate_table_body(nlink, search, 'search');
}
 
function generate_table_body(nlink, search, mode){
    var post_data = `search=${search}`;
    var csrftoken = getCookie('csrftoken');
    var client = new postRequest();
    client.post(nlink, post_data, csrftoken, function(response) {
        var thd = document.getElementById("thead-dark");
        if(thd != null){
            thd.innerHTML = "";
            var thead = get_table_head();
            $("#thead-dark").append(thead);
            console.log('thead appended');
        }
        var tlm = document.getElementById("tbody");
        console.log(tlm);
        var json = JSON.parse(response);
        var root_loc = json['root'];
        tlm.innerHTML="";
        for (var key in json){
            var value = json[key];
            var taglist = value['tag'];
            if(!taglist){
                var taglist = [];
            }
            var usr = value['usr'];
            var title = value['title'];
            var index = key
            var netloc = value['netloc'];
            var loc = value['url'];
            var timestamp = value['timestamp'];
            var edit_b = value['edit-bookmark'];
            var ms = value['move-bookmark'];
            var remove_link = value['remove-url'];
            var archive_media = value['archive-media'];
            var directory = value['directory'];
            var read_url = value['read-url'];
            var fav_path = value['fav-path'];
            var idd = value['id'];
            var is_subdir = value['is-subdir'];
            
            var badges = create_badge_nodes(usr, taglist, 'div', root_loc);
            if (mode == 'dir'){
                var dir_badge = "";
            }else{
                var dir_badge = create_directory_badge(usr, directory, is_subdir, root_loc);
            }
            var table_content = create_table_rows(
                    usr, badges, index, title, netloc, loc,
                    timestamp, edit_b, ms, remove_link,
                    archive_media, directory, dir_badge,
                    read_url, idd, fav_path, root_loc, is_subdir);
            $("#tbody").append(table_content);
        }
    })
    
};

function get_table_head(){
    var string = `
        <tr>
        <th>Sr</th>
        <th>Title</th>
        <th class="align-middle">Action</th>
        </tr>`
}

function move_to_bookmark(post_data, api_link, nlink, csrftoken, el, idlist, merge){
    var client = new postRequest();
    client.post(api_link, post_data, csrftoken, function(response) {
        console.log(response);
        var json = JSON.parse(response);
        console.log(json.dir);
        msg = getselectbox_string(json.dir);
        var resp = bootbox.confirm(msg, function(resp){
            console.log(resp);
            if (resp){
                var info = $('#select-dir-form');
                var val = info.find("#select-dir-box option:selected").text();
                console.log(val)
                if(val){
                    console.log(val);
                    if(merge){
                        post_data = `merge_dir=${val}`;
                    }else{
                        post_data = `move_to_dir=${val}`;
                        if (idlist){
                            post_data = post_data + `&move_links=${idlist}`;
                        }
                    }
                    console.log(post_data);
                    var client = new postRequest();
                    client.post(
                        nlink, post_data,
                        csrftoken,
                        function(response) {
                            console.log(response);
                            if(idlist){
                                for(i=0; i< el.length; i++){
                                    el[i].remove();
                                }
                            }else{
                                el.remove();
                            }
                        })
                }else{
                    console.log('Select Something');
                }
            }
        })
    })
}

function create_badge_nodes(usr, taglist, mode, root_loc){
    var string = '';
    if (usr == null){
        usr = root_loc + '/' + '.';
    }else{
        usr = root_loc + '/' + usr
    }
    for(i=0; i< taglist.length; i++){
        var tag = taglist[i].trim();
        string = string + `<a href="${usr}/tag/${tag}" class="badge badge-light font-weight-normal">${tag}</a><span> </span>`;
    }
    if (string != '' && mode == 'div'){
        string = `<div class="badges">${string}</div>`;
    }
    return string;
}

function create_directory_badge(usr, dirname, is_subdir, root_loc){
    if (dirname && dirname.includes('/')){
        string = `<span> | </span>
            <small>
            <a class="text-success" href="${root_loc}/${usr}/subdir/${dirname}">${dirname} </a>
            </small>`
    }
    else{
        string = `<span> | </span>
            <small>
            <a class="text-success" href="${root_loc}/${usr}/${dirname}">${dirname} </a>
            </small>`
    }
    return string
}

function create_upload_field(api, value){
    var label_text = 'Import Netscape Bookmark File in HTML Format';
    var multiple = "";
    if (value == 'upload'){
        label_text = 'Select Multiple Files To Upload';
        multiple = 'multiple';
    }
    string = `<form>
                <div class="row py-4">
                    <label class="col-sm-4 btn btn-primary" id="upload-input-button">
                        Browse for file ... <input id="upload-file-field" ${multiple} type="file" onchange="display_upload_file_name(event)" hidden>
                    </label>
                    <label class="col-sm-8" id="upload-label">
                        ${label_text}
                    <label>
                </div>
                </form>
            `;
    return string;
}

function display_upload_file_name(event){
    var file = document.getElementById('upload-file-field');
    var nfilename = ""
    for(var x = 0; x < file.files.length; x++){
        var filename = file.files[x].name;
        if (filename.length > 20){
            var last_5 = filename.substr(filename.length - 5);
            filename = filename.slice(0, 20) + '...' + last_5;
        }
        if (x == 0){
            nfilename = filename;
        }else{
            nfilename = nfilename + '; ' +filename;
        }
        
    }
    $('#upload-label').text(nfilename);
}

function create_table_rows(usr, badge_nodes, index, title, netloc,
                           loc, timestamp, edit_b, ms, remove_link,
                           archive_media, dirname, dir_badge,
                           read_url, idd, fav_path, root, is_subdir){
    console.log(root);
    var string = `<tr>
        <td><img width="24" src="${fav_path}"></td>
      <td>
        <a href="${archive_media}"><span class="text-lg-left">${title} </span></a>
            ${dir_badge}
            </br>
            <small>
                <a href="${loc}" class="text-muted" id="netloc-muted">${netloc}</a>
            </small>
            ${badge_nodes}
        </td>
        <td>
        <div class="btn-group m-r-10 px-3">
        
            <button aria-expanded="false" data-toggle="dropdown"\
             class="btn btn-link dropdown-toggle waves-effect waves-light"\
             type="button"><span class="caret"><img src="/static/menu.svg" width="20"></span></button>
             
            <ul role="menu" class="dropdown-menu dropdown-menu-right" id="dropdown-menu-${index}">
            
                <span id="drop-edit-${index}" class="dropdown-item" \
                 data-link="${edit_b}" title="${title}" data-val="url"\
                 onclick="onsearch_dropdown(event, id)">Edit Bookmark</span>
                 
                <div class="dropdown-divider"></div>
                
                <span id="drop-read-${index}" onclick="onsearch_dropdown(event, id)"\
                 class="dropdown-item" data-link="${read_url}" title="${title}" data-val="url_read"\
                 data-url="${root}/${usr}/api/request">Read</span>
                
                <div class="dropdown-divider"></div>
                
                <span id="drop-move-${index}" onclick="onsearch_dropdown(event, id)"\
                 class="dropdown-item" data-link="${ms}" title="${title}" data-val="url"\
                 data-url="${root}/${usr}/api/request">Move To</span>
                
                <div class="dropdown-divider"></div>
                
                <span id="drop-archive-${index}" onclick="onsearch_dropdown(event, id)"\
                 class="dropdown-item" data-link="${archive_media}" title="${title}" \
                 data-val="url_archive" data-url="${root}/${usr}/api/request"\
                 dir-name="${dirname}" find-id="${ms}">Archive</span>
                 
                <div class="dropdown-divider"></div>
                
                <span id="drop-remove-${index}" onclick="onsearch_dropdown(event, id)"\
                 class="dropdown-item" data-link="${remove_link}" title="${title}"\
                 data-val="url">Remove</span>
                 
            </ul>
        </div>
        </br>
        <small>
            <footer class="text-muted px-2 py-2" link-id="${idd}" data-url="${root}/${usr}/api/request" dir-name="${dirname}">${timestamp}</footer>
        </small>
        </td>
    </tr>`
    return string;
}

function onsearch_dropdown(event, id){
    console.log(id);
    var nlm = $(`#${id}`);
    console.log(nlm.text());
    dropdown_menu_clicked(nlm);
}

function getsettings_html(autotag, auto_summary, total_tags, buddy_list,
                          public_dir, group_dir, arch_pdf, arch_png,
                          arch_png_quality, auto_archive, pagination_value,
                          media_streaming, download_manager){
    var html = `<div class="form-check">
        <input class="form-check-input" type="checkbox" value="autotag" id="autotag" ${autotag}>
        <label class="form-check-label" for="autotag">
        Automatic Tagging of URL
        </label>
    </div>
    <div class="form-check">
        <input class="form-check-input" type="checkbox" value="auto_summary" id="auto_summary" ${auto_summary}>
        <label class="form-check-label" for="auto_summary">
        Automatic Summary Extract
        </label>
    </div>
    <div class="form-group row py-1">
        <label class="col-sm-6 col-form-label">Total Tags Per URL</label>
        <div class="col-sm-6">
        <input class="form-control" type="text" value="${total_tags}" id="total_tags">
        </div>
    </div>
    
    <div class="dropdown-divider"></div>
    <div class="form-check">
        <input class="form-check-input" type="checkbox" value="auto_archive" id="auto_archive" ${auto_archive}>
        <label class="form-check-label" for="auto_archive">
        Automatic Archive Generation
        </label>
    </div>
    <div class="row">
        <div class="col-sm-4">
            Archive Formats
        </div>
        <div class="col-sm-8">
            <div class="form-check-inline">
                <input class="form-check-input" type="checkbox" value="arch-html" id="arch-html" Disabled checked>
                <label class="form-check-label" for="arch-html">
                HTML
                </label>
            </div>
            <div class="form-check-inline">
                <input class="form-check-input" type="checkbox" value="arch-pdf" id="arch-pdf" ${arch_pdf}>
                <label class="form-check-label" for="arch-pdf">
                PDF
                </label>
            </div>
            <div class="form-check-inline">
                <input class="form-check-input" type="checkbox" value="arch-png" id="arch-png" ${arch_png}>
                <label class="form-check-label" for="arch-png">
                PNG
                </label>
            </div>
        </div>
    </div>
    <div class="form-group row py-1">
        <label class="col-sm-6 col-form-label">Screenshot PNG Quality</label>
        <div class="col-sm-6">
        <input class="form-control" type="text" id="arch-png-quality" value="${arch_png_quality}" placeholder="0-100">
        </div>
    </div>
    <div class="dropdown-divider"></div>
    <div class="form-group row py-1">
        <label class="col-sm-5 col-form-label">Download Manager</label>
        <div class="col-sm-7">
        <input class="form-control" type="text" id="download-manager" value="${download_manager}" placeholder="Enter Download manager template">
        </div>
    </div>
    <div class="form-check-inline">
        <input class="form-check-input" type="checkbox" value="media-streaming" id="media-streaming" ${media_streaming}>
        <label class="form-check-label" for="media-streaming">
        Allow Streaming of Archived Media
        </label>
    </div>
    <div class="dropdown-divider"></div>
    <div class="form-group row py-1">
        <label class="col-sm-6 col-form-label">Display Links Per Directory</label>
        <div class="col-sm-6">
        <input class="form-control" type="text" id="pagination-value" value="${pagination_value}">
        </div>
    </div>
    
    <div class="dropdown-divider"></div>
    <div class="form-group row">
        <label class="col-sm-2 col-form-label">Public Directory</label>
        <div class="col-sm-4 py-2">
        <input class="form-control" type="text" value="${public_dir}" id="public_dir">
        </div>
        <label class="col-sm-2 col-form-label">Group Directory</label>
        <div class="col-sm-4 py-2">
        <input class="form-control" type="text" value="${group_dir}" id="group_dir">
        </div>
    </div>
    <div class="form-group row">
        <label class="col-sm-4 col-form-label">Group Users</label>
        <div class="col-sm-8">
        <input class="form-control" type="text" value="${buddy_list}" id="buddy_list"\
         placeholder="Comma separated list of users for group access">
        </div>
    </div>`;
    return html;
}

function getselectbox_string(list){
    var str = '';
    for(i=0;i<list.length;i++){
        dirname = list[i];
        str = str + `<option value=${dirname}>${dirname}</option>`
    }
    return `</br><div class="card"><div class="card-header">Select Directory</div></div></br>
            <form id="select-dir-form" novalidate>
                <select id="select-dir-box" class="form-control">${str}</select>
                <label class="form-select-label" for="select-dir-box"></label>
            </form>`;
}

function getstr(title, url, tags, media_element){
    var placeholder = "Comma separated list of tags"
    var str = `<form id='infos' novalidate>\
    <label></label>
    <div class="form-group row">
        <label class="col-sm-2 col-form-label" for="titleid"><b>Title</b></label>
        <div class="col-sm-10">
            <input id='titleid' type='text' name='title' value='${title}' class="form-control"/>
        </div>
    </div>
    <div class="form-group row">
        <label class="col-sm-2 col-form-label" for="urlid"><b>URL</b></label>
        <div class="col-sm-10">
            <input id='urlid' type='text' name='url' value='${url}' class="form-control"/>
        </div>
    </div>
    <div class="form-group row">
        <label class="col-sm-2 col-form-label" for="tagid"><b>Tags</b></label>
        <div class="col-sm-10">
            <input id='tagid' type='text' name='tags' value='${tags}' class="form-control" placeholder="${placeholder}"/>
        </div>
    </div>
    <div class="form-check-inline">
        <input class="form-check-input" type="checkbox" value="media-element-check" id="media-element-check" ${media_element}>
        <label class="form-check-label" for="media-element-check">
        Consider the link as media link
        </label>
    </div>
    </form>`;
    return str;
}

function getsummary(summary){
    var str = `
    <div class="form-group row">
        <textarea rows=10 id='summary-text' type='text' name='summary-text' class="form-control">
            ${summary}
        </textarea>
    </div>`;
    return str;
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var getRequest = function() {
    this.get = function(url, callbak) {
        var http_req = new XMLHttpRequest();
        http_req.onreadystatechange = function() { 
            if (http_req.readyState == 4 && http_req.status == 200)
                {callbak(http_req.responseText);}
        }

        http_req.open( "GET", url, true );            
        http_req.send( null );
    }
};

var postRequest = function() {
    this.post = function(url, params, token, callbak) {
        var http_req = new XMLHttpRequest();
        http_req.onreadystatechange = function() { 
            if (http_req.readyState == 4 && http_req.status == 200)
                {callbak(http_req.responseText);}
        }
        http_req.open( "POST", url, true );
        http_req.setRequestHeader("X-CSRFToken", token);
        http_req.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
        //http_req.send(JSON.stringify(params));
        http_req.send(params);
    }
};

var postRequestUpload = function() {
    this.post = function(url, params, token, callbak) {
        var http_req = new XMLHttpRequest();
        http_req.onreadystatechange = function() { 
            if (http_req.readyState == 4 && http_req.status == 200)
                {callbak(http_req.responseText);}
        }
        http_req.open( "POST", url, true );
        http_req.setRequestHeader("X-CSRFToken", token);
        http_req.send(params);
    }
};

$(document).ready(function(){
    var refresh_page = $('.table').attr('data-refresh');
    if (refresh_page == 'yes'){
        setTimeout(function(){window.location.href = window.location.href;}, 5000);
        console.log('refresh after 5 seconds');
    };
});
