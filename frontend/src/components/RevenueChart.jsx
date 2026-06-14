import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

// "2024-01" → "Jan 24"
const formatMonth = (monthStr) => {
    const [year, month] = monthStr.split("-");
    const date = new Date(Number(year), Number(month) - 1);
    return date.toLocaleString("en-US", { month: "short" }) + " " + year.slice(2);
};

// Y axis tick: 8234 → "$8.2K"
const formatYAxis = (val) => `$${(val / 1000).toFixed(1)}K`;

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-md">
                <p className="text-sm font-semibold text-gray-700 mb-1">
                    {formatMonth(label)}
                </p>
                <p className="text-sm text-blue-600">
                    ${Number(payload[0].value).toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                    })}
                </p>
            </div>
        );
    }
    return null;
};

const RevenueChart = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height={320}>
            <AreaChart
                data={data}
                margin={{ top: 10, right: 20, left: 10, bottom: 0 }}
            >
                <defs>
                    <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                </defs>

                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />

                <XAxis
                    dataKey="month"
                    tickFormatter={formatMonth}
                    tick={{ fontSize: 12, fill: "#6b7280" }}
                    tickLine={false}
                    axisLine={{ stroke: "#e5e7eb" }}
                />

                <YAxis
                    tickFormatter={formatYAxis}
                    tick={{ fontSize: 12, fill: "#6b7280" }}
                    tickLine={false}
                    axisLine={false}
                    width={60}
                />

                <Tooltip content={<CustomTooltip />} />

                <Area
                    type="monotone"
                    dataKey="total_net_revenue"
                    stroke="#3b82f6"
                    strokeWidth={2.5}
                    fill="url(#revenueGradient)"
                    dot={false}
                    activeDot={{ r: 5, fill: "#3b82f6" }}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
};

export default RevenueChart;