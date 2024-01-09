$(document).ready(function () {
    $("#start_point").change(function () {
        var cityId = $(this).val();
        var url = '/ajax/get_stations/?city_id=' + cityId;

        $.get(url, function (data) {
            var stationSelect = $("#departure_station");
            stationSelect.empty();

            $.each(data.results, function (index, item) {
                stationSelect.append('<option value="' + item.id + '">' + item.text + '</option>');
            });
        });
    });
    $("#end_point").change(function () {
        var cityId = $(this).val();
        var url = '/ajax/get_stations/?city_id=' + cityId;

        $.get(url, function (data) {
            var stationSelect = $("#arrival_station");
            stationSelect.empty();

            $.each(data.results, function (index, item) {
                stationSelect.append('<option value="' + item.id + '">' + item.text + '</option>');
            });
        });
    });
    var pointSelect_1 = $("#start_point");
    var targetField_1 = $("#departure_station");
    var pointSelect_2 = $("#end_point");
    var targetField_2 = $("#arrival_station");

    // Деактивируем поле при загрузке страницы
    targetField_1.prop("disabled", true);
    targetField_2.prop("disabled", true);

    // Обработчик изменения значения в поле выбора
    pointSelect_1.change(function() {
        // Если выбран какой-то вариант, активируем поле
        targetField_1.prop("disabled", !$(this).val());
    });

    pointSelect_2.change(function() {
        targetField_2.prop("disabled", !$(this).val());
    });
});