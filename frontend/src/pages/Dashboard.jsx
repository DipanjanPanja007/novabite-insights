import { useState, useEffect } from "react";
import client from "../api/client";
import KPICard from "../components/KPICard";
import RevenueChart from "../components/RevenueChart";

const formatRevenue = (val) =>
    "$" + Number(val).toLocaleString("en-US", { minimumFractionDigits: 2 });

const formatPercent = (val) => val + "%";

const Dashboard = () => {
    const [summary, setSummary] = useState(null);
    const [trends, setTrends] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                setError(null);

                // Fetch both in parallel
                const [summaryRes, trendsRes] = await Promise.all([
                    client.get("/api/summary"),
                    client.get("/api/trends"),
                ]);

                setSummary(summaryRes.data);
                setTrends(trendsRes.data);
            } catch (err) {
                setError("Failed to load data. Make sure the backend is running on port 8000.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // ── Loading ──────────────────────────────────────────────────────────────────
    if (loading) {
        return (
            <div className="flex items-center justify-center py-24">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-500">Loading...</span>
            </div>
        );
    }

    // ── Error ────────────────────────────────────────────────────────────────────
    if (error) {
        return (
            <div className="max-w-2xl mx-auto mt-12 px-6">
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
            </div>
        );
    }

    // ── Dashboard ────────────────────────────────────────────────────────────────
    return (
        <div className="min-h-screen bg-slate-50 px-6 py-8">
            <div className="max-w-6xl mx-auto">

                {/* Page Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">Sales Dashboard</h1>
                    <p className="mt-1 text-gray-500">
                        NovaBite Consumer Goods · Jan 2024 – Dec 2025
                    </p>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
                    <KPICard
                        title="Total Net Revenue"
                        value={formatRevenue(summary.total_net_revenue)}
                        icon="💰"
                        color="border-blue-500"
                    />
                    <KPICard
                        title="Gross Profit Margin"
                        value={formatPercent(summary.gross_profit_margin_pct)}
                        icon="📈"
                        color="border-emerald-500"
                    />
                    <KPICard
                        title="Top Region"
                        value={summary.top_region}
                        icon="🌍"
                        color="border-violet-500"
                    />
                </div>

                {/* Chart */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4">
                        Monthly Net Revenue Trend
                    </h2>
                    <RevenueChart data={trends} />
                </div>

            </div>
        </div>
    );
};

export default Dashboard;