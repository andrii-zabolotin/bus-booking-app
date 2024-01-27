$(document).ready(function () {
    function updateStations(cityId, stationSelect) {
        var url = '/ajax/get_stations/?city_id=' + cityId;

        $.get(url, function (data) {
            stationSelect.empty();

            $.each(data.results, function (index, item) {
                stationSelect.append('<option value="' + item.id + '">' + item.text + '</option>');
            });
        });
    }

    $("#start_point").change(function () {
        var cityId = $(this).val();
        var stationSelect = $("#departure_station");
        updateStations(cityId, stationSelect);
    });

    $("#end_point").change(function () {
        var cityId = $(this).val();
        var stationSelect = $("#arrival_station");
        updateStations(cityId, stationSelect);
    });

    // Вызов функции при загрузке страницы
    var startCityId = $("#start_point").val();
    var endCityId = $("#end_point").val();

    if (startCityId) {
        updateStations(startCityId, $("#departure_station"));
    }

    if (endCityId) {
        updateStations(endCityId, $("#arrival_station"));
    }


    var pointSelect_1 = $("#start_point");
    var targetField_1 = $("#departure_station");
    var pointSelect_2 = $("#end_point");
    var targetField_2 = $("#arrival_station");

    // Деактивируем поле при загрузке страницы
    if ($.trim(pointSelect_1.val()) === "") {
        targetField_1.prop("disabled", true);
    }

    if ($.trim(pointSelect_2.val()) === "") {
        targetField_2.prop("disabled", true);
    }

    // Обработчик изменения значения в поле выбора
    pointSelect_1.change(function() {
        // Если выбран какой-то вариант, активируем поле
        targetField_1.prop("disabled", !$(this).val());
    });

    pointSelect_2.change(function() {
        targetField_2.prop("disabled", !$(this).val());
    });
});