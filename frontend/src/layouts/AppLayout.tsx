import { Link, Outlet } from "react-router-dom";

export function AppLayout() {
  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <img src="/brand/logo.svg" alt="GNK Algo" className="logo" />
          <span>GNK Algo</span>
        </Link>
        <nav>
          <Link to="/">Status</Link>
          <Link to="/login">Login</Link>
          <Link to="/dashboard">Dashboard</Link>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
