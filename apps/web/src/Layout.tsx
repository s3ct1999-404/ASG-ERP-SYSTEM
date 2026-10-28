import { NavLink, Outlet } from "react-router-dom";
import { EfrisBanner } from "@/components/EfrisBanner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useAuth } from "@/auth";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/organisation", label: "Organisation" },
  { to: "/products", label: "Products" },
  { to: "/stock", label: "Stock" },
  { to: "/invoices", label: "Sales invoices" },
];

export function Layout() {
  const { email, tenants, tenantId, selectTenant, signOut, isPlatformOperator } = useAuth();
  return (
    <div className="flex min-h-svh flex-col md:flex-row">
      <aside className="flex flex-col gap-4 border-b bg-card p-4 md:w-60 md:border-r md:border-b-0">
        <div className="text-lg font-semibold">ASG ERP</div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="tenant">Organisation</Label>
          <Select
            id="tenant"
            value={tenantId ?? ""}
            onChange={(e) => selectTenant(e.target.value)}
            disabled={tenants.length < 2}
          >
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </Select>
        </div>
        <nav aria-label="Main" className="flex flex-row flex-wrap gap-1 md:flex-col">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                cn(
                  "rounded-md px-3 py-2 text-sm hover:bg-accent",
                  isActive && "bg-accent font-medium",
                )
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto flex flex-col gap-2 text-sm">
          <span className="truncate text-muted-foreground">{email}</span>
          <Button variant="outline" size="sm" onClick={() => void signOut()}>
            Sign out
          </Button>
        </div>
      </aside>
      <main className="flex flex-1 flex-col gap-6 p-6">
        {tenantId ? (
          <>
            <EfrisBanner />
            <Outlet />
          </>
        ) : (
          <Alert>
            <AlertTitle>No organisation access</AlertTitle>
            <AlertDescription>
              {isPlatformOperator
                ? "Platform operators manage tenants but have no access to business data."
                : "Your account is not a member of any organisation. Ask an administrator to invite you."}
            </AlertDescription>
          </Alert>
        )}
      </main>
    </div>
  );
}
