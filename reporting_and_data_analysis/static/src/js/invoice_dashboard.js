/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formatFloat, formatMonetary } from "@web/views/fields/formatters";
import { Component, useState, onWillStart, onMounted, useRef } from "@odoo/owl";

function formatNumber(num) {
    return formatFloat(num, { digits: [false, 0] });
}

/**
 * Widget cho biểu đồ doanh thu hóa đơn
 */
export class InvoiceDashboardGraph extends Component {
    static template = "reporting_and_data_analysis.InvoiceDashboardGraph";
    static props = {
        record: Object,
        name: { type: String },
        value: { type: String, optional: true },
    };

    setup() {
        this.state = useState({
            data: null,
        });
        this.graphRef = useRef("graph");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.company = useService("company");

        onWillStart(async () => {
            this.chartData = null;
            this.parseData();
        });

        onMounted(() => {
            if (this.graphRef.el) {
                this.renderGraph();
            }
        });
    }

    parseData() {
        if (!this.props.value) {
            return;
        }

        try {
            this.chartData = JSON.parse(this.props.value);
            this.state.data = this.chartData;
        } catch (e) {
            console.error('Không thể phân tích dữ liệu JSON:', e);
        }
    }

    renderGraph() {
        if (!this.chartData || !this.graphRef.el) {
            return;
        }

        // Clear any existing graph
        const container = this.graphRef.el;
        container.innerHTML = "";

        // Create SVG element
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "300px");
        container.appendChild(svg);

        const fieldName = this.props.name;

        if (fieldName === 'revenue_by_month_data' || fieldName === 'revenue_by_day_data') {
            const labelKey = fieldName === 'revenue_by_month_data' ? 'month' : 'day';
            this.renderBarChart(svg, labelKey);
        } else if (fieldName === 'service_vs_medicine_data' || fieldName === 'insurance_vs_patient_data') {
            this.renderPieChart(svg);
        } else if (fieldName === 'invoice_status_data') {
            this.renderDonutChart(svg);
        }
    }

    renderBarChart(svg, labelKey) {
        // In a real implementation, you would use a library like Chart.js, D3.js or ApexCharts
        // For simplicity, we'll just render a placeholder with text

        if (!this.chartData || !this.chartData.length) {
            this.renderNoDataPlaceholder(svg);
            return;
        }

        // Placeholder implementation - in a real app, you'd use a visualization library
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", "50%");
        text.setAttribute("y", "50%");
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("dominant-baseline", "middle");
        text.setAttribute("font-size", "14px");
        text.textContent = `Biểu đồ cột doanh thu - ${this.chartData.length} mục dữ liệu`;
        svg.appendChild(text);
    }

    renderPieChart(svg) {
        if (!this.chartData || !this.chartData.labels || !this.chartData.data) {
            this.renderNoDataPlaceholder(svg);
            return;
        }

        // Placeholder implementation
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", "50%");
        text.setAttribute("y", "50%");
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("dominant-baseline", "middle");
        text.setAttribute("font-size", "14px");
        text.textContent = `Biểu đồ tròn - ${this.chartData.labels.join(' vs ')}`;
        svg.appendChild(text);
    }

    renderDonutChart(svg) {
        if (!this.chartData || !this.chartData.length) {
            this.renderNoDataPlaceholder(svg);
            return;
        }

        // Placeholder implementation
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", "50%");
        text.setAttribute("y", "50%");
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("dominant-baseline", "middle");
        text.setAttribute("font-size", "14px");
        text.textContent = `Biểu đồ tròn trạng thái - ${this.chartData.length} trạng thái`;
        svg.appendChild(text);
    }

    renderNoDataPlaceholder(svg) {
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", "50%");
        text.setAttribute("y", "50%");
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("dominant-baseline", "middle");
        text.setAttribute("font-size", "14px");
        text.setAttribute("fill", "#6c757d");
        text.textContent = "Không có dữ liệu để hiển thị";
        svg.appendChild(text);
    }
}

/**
 * Widget để hiển thị bảng top dịch vụ, thuốc và bệnh nhân
 */
export class InvoiceTopDataWidget extends Component {
    static template = "reporting_and_data_analysis.InvoiceTopDataWidget";
    static props = {
        record: Object,
        name: { type: String },
        value: { type: String, optional: true },
    };

    setup() {
        this.state = useState({
            data: [],
        });
        this.company = useService("company");

        onWillStart(() => {
            this.parseData();
        });
    }

    parseData() {
        if (!this.props.value) {
            return;
        }

        try {
            const data = JSON.parse(this.props.value);
            this.state.data = data;

            // Format numbers and monetary values
            if (Array.isArray(data)) {
                this.state.data = data.map(item => ({
                    ...item,
                    count_formatted: formatNumber(item.count || 0),
                    total_formatted: formatMonetary(item.total || 0, {
                        currencyId: this.company.currentCompany.currency_id,
                    }),
                }));
            } else if (this.props.name === 'monthly_comparison_data' && data) {
                const formatGrowth = (value) => {
                    return {
                        value: Math.abs(value || 0).toFixed(1) + '%',
                        positive: (value || 0) >= 0,
                    };
                };

                this.state.data = {
                    ...data,
                    total: {
                        ...data.total,
                        current_formatted: formatMonetary(data.total?.current || 0, {
                            currencyId: this.company.currentCompany.currency_id,
                        }),
                        growth_formatted: formatGrowth(data.total?.growth),
                    },
                    service: {
                        ...data.service,
                        current_formatted: formatMonetary(data.service?.current || 0, {
                            currencyId: this.company.currentCompany.currency_id,
                        }),
                        growth_formatted: formatGrowth(data.service?.growth),
                    },
                    medicine: {
                        ...data.medicine,
                        current_formatted: formatMonetary(data.medicine?.current || 0, {
                            currencyId: this.company.currentCompany.currency_id,
                        }),
                        growth_formatted: formatGrowth(data.medicine?.growth),
                    },
                };
            }
        } catch (e) {
            console.error('Lỗi khi phân tích dữ liệu:', e);
        }
    }
}

// Register the components in the field registry
registry.category("fields").add("invoice_dashboard_graph", InvoiceDashboardGraph);
registry.category("fields").add("invoice_top_data", InvoiceTopDataWidget);