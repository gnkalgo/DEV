import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={<Placeholder title="Dashboard" phase="Phase 4" />} />
        <Route path="/broker" element={<Placeholder title="Broker" phase="Phase 4–6" />} />
        <Route path="/orders" element={<Placeholder title="Orders" phase="Phase 4–6" />} />
        <Route path="/positions" element={<Placeholder title="Positions" phase="Phase 4–6" />} />
        <Route path="/settings" element={<Placeholder title="Settings" phase="Phase 4" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

function Placeholder({ title, phase }: { title: string; phase: string }) {
  return (
    <section className="card">
      <h1>{title}</h1>
      <p>
        This route is reserved. Implementation arrives in <strong>{phase}</strong>.
      </p>
    </section>
  );
}
