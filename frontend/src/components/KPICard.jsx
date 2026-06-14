
const KPICard = ({ title, value, icon, color }) => {
    return (
        <div
            className={`bg-white rounded-lg shadow-md border-l-4 ${color} p-5 flex items-center justify-between hover:shadow-lg transition-shadow duration-200`}
        >
            {/* Left: title + value */}
            <div>
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                    {title}
                </p>
                <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
            </div>

            {/* Right: icon */}
            <span className="text-3xl opacity-80">{icon}</span>
        </div>
    );
}

export default KPICard;