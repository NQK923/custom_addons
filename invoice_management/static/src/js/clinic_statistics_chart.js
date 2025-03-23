odoo.define('invoice_management.clinic_statistics_chart', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var registry = require('web.field_registry');
    var core = require('web.core');

    var ClinicStatisticsChart = AbstractField.extend({
        className: 'o_clinic_statistics_chart',
        supportedFieldTypes: ['text'],

        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            this.chart = null;
        },

        /**
         * @override
         */
        _render: function () {
            var self = this;
            if (!this.value) {
                return;
            }

            if (this.$el.find('canvas').length === 0) {
                this.$el.empty();
                this.$el.append($('<canvas/>'));
            }

            try {
                var data = JSON.parse(this.value.replace(/'/g, '"'));
                self._renderChart(data);
            } catch (e) {
                console.error("Cannot parse chart data", e);
                this.$el.empty();
                this.$el.append($('<div/>', {
                    text: "Không thể hiển thị biểu đồ: " + e.message,
                    class: 'alert alert-danger'
                }));
            }
        },

        /**
         * Render chart with provided data
         *
         * @private
         * @param {Object} data
         */
        _renderChart: function (data) {
            if (this.chart) {
                this.chart.destroy();
            }

            var ctx = this.$el.find('canvas')[0].getContext('2d');
            this.chart = new Chart(ctx, {
                type: 'bar',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Doanh thu (VND)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Ngày'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Thống kê doanh thu theo ngày'
                        },
                        legend: {
                            position: 'top',
                        }
                    }
                }
            });
        },

        /**
         * @override
         */
        destroy: function () {
            if (this.chart) {
                this.chart.destroy();
            }
            this._super.apply(this, arguments);
        }
    });

    registry.add('clinic_statistics_chart', ClinicStatisticsChart);

    return ClinicStatisticsChart;
});