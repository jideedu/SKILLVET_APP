$(document).ready(function() {
   $('[data-toggle="tooltip"]').tooltip();

    /**
        INITIALSIING THE DATATABLES used
    **/
  $('#data-table').DataTable({
        //"scrollY": "300px",
        "scrollCollapse": false,
        "info": false,
        "ordering": true,
        "searching": true,
        //'scroller': true,
        'sScrollX': true, //this let the header scroll
        // 'scrollH': true,
    });


    $('#table-skill').DataTable({
        // "scrollY": "250px",
        "scrollCollapse": false,
        "paging": false,
        "info": false,
        "ordering": true,
        "searching": false,
        'scroller': false,
    });

    $('#table-dev').DataTable({
        // "scrollY": "450px",
        "scrollCollapse": false,
        "paging": false,
        "info": false,
        "ordering": true,
        "searching": false,
        'scroller': false,
    });

    $('#table-allskillstable').DataTable({
        "scrollY": "500px",
        "scrollCollapse": false,
        "paging": true,
        "info": false,
        "ordering": true,
        "searching": true,
        'scroller': false,
	'sScrollX': true,  //for header to scroll horizontally
	'scrollH': true,
    });


    //this snippet lets you hover on the table with differnt color used
    $(document).on({
        mouseenter: function() {
            trIndex = $(this).index() + 1;
            $("#table-skill").each(function(index) {
                $(this).find("tr:eq(" + trIndex + ")").addClass("hover-skill")
            });
        },
        mouseleave: function() {
            trIndex = $(this).index() + 1;
            $("#table-skill").each(function(index) {
                $(this).find("tr:eq(" + trIndex + ")").removeClass("hover-skill")
            });
        }
    }, "#table-skill tr");
    $(document).on({
        mouseenter: function() {
            trIndex = $(this).index() + 1;
            $("#table-dev").each(function(index) {
                $(this).find("tr:eq(" + trIndex + ")").addClass("hover-dev")
            });
        },
        mouseleave: function() {
            trIndex = $(this).index() + 1;
            $("#table-dev").each(function(index) {
                $(this).find("tr:eq(" + trIndex + ")").removeClass("hover-dev")
            });
        }
    }, "#table-dev tr");
    $(document).on({
        mouseenter: function() {
            trIndex = $(this).index() + 1;
            $("#table-allskillstable").each(function(index) {
                $(this).find("tr:eq(" + trIndex + ")").addClass("hover-allskillstable")
            });
        },
        mouseleave: function() {
            trIndex = $(this).index() + 1;
            $("#table-allskillstable").each(function(index) {
                $(this).find("tr:eq(" + trIndex + ")").removeClass("hover-allskillstable")
            });
        }
    }, "#table-allskillstable tr");

    $('.toggle').on('click', function(e) {
        var t = $(this).html();

        if (t[0] == '+') {
            $(this).html('- show less');
            $(this).parent().find('.tohide').removeClass('hidden');
        } else {
            $(this).html('+ show more');
            $(this).parent().find('.tohide').addClass('hidden');
        }
    });

});

function showdetails() {
    inputelm = document.getElementById('MoreResultdetails');
    if (inputelm.style.display === "none") {
        inputelm.style.display = "block";
    } else {
        inputelm.style.display = "none";
    }
    var table = $('#data-table').DataTable();
    table.columns.adjust().draw();
}
