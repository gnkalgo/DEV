import { Link, NavLink, Outlet } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../hooks/useAuth";

const LINKS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/broker", label: "Broker" },
  { to: "/orders", label: "Orders" },
  { to: "/positions", label: "Positions" },
  { to: "/settings", label: "Settings" },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/dashboard" className="brand">
          <img src="/brand/logo.svg" alt="GNK Algo" className="logo" />
          <span>GNK Algo</span>
        </Link>
        <button type="button" className="menu-toggle" aria-label="Menu" onClick={() => setOpen((v) => !v)}>
          Menu
        </button>
        <div className="topbar-meta">
          <span className="muted">{user?.full_name}</span>
          <button type="button" className="secondary" onClick={() => void logout()}>
            Logout
          </button>
        </div>
      </header>
      <div className="shell-body">
        <aside className={open ? "sidebar open" : "sidebar"}>
          <nav>
            {LINKS.map((link) => (
              <NavLink key={link.to} to={link.to} onClick={() => setOpen(false)}>
                {link.label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="shell-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
