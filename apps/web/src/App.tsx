import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/auth";
import { Layout } from "@/Layout";
import { InvoicesPage } from "@/pages/InvoicesPage";
import { LoginPage } from "@/pages/LoginPage";
import { OrganisationPage } from "@/pages/OrganisationPage";
import { ProductsPage } from "@/pages/ProductsPage";
import { StockPage } from "@/pages/StockPage";

function Gate() {
  const { email } = useAuth();
  if (!email) return <LoginPage />;
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/organisation" element={<OrganisationPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/stock" element={<StockPage />} />
        <Route path="/invoices" element={<InvoicesPage />} />
        <Route path="*" element={<Navigate to="/organisation" replace />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  );
}
