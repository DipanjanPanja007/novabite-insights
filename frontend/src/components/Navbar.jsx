import { NavLink } from "react-router-dom";

const Navbar = () => {
    return (
        <nav className="bg-slate-900 px-6 py-4 flex items-center justify-between shadow-md">
            {/* Logo */}
            <span className="text-white text-xl font-bold tracking-tight">
                ⚡ NovaBite
            </span>

            {/* Nav Links */}
            <div className="flex gap-6">
                <NavLink
                    to="/"
                    end
                    className={({ isActive }) =>
                        isActive
                            ? "text-blue-400 font-semibold border-b-2 border-blue-400 pb-0.5 transition-colors"
                            : "text-slate-300 hover:text-white transition-colors pb-0.5"
                    }
                >
                    Dashboard
                </NavLink>

                <NavLink
                    to="/chat"
                    className={({ isActive }) =>
                        isActive
                            ? "text-blue-400 font-semibold border-b-2 border-blue-400 pb-0.5 transition-colors"
                            : "text-slate-300 hover:text-white transition-colors pb-0.5"
                    }
                >
                    Chat
                </NavLink>
            </div>
        </nav>
    );
}

export default Navbar;